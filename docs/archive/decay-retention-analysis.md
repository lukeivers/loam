# Decay-Retention Opportunities — Review of Sealed Components

**Date:** 2026-04-19. **Status:** Analysis for potential later patch. **No code changes.**

---

## Why this review exists

The owner's retention preference (surfaced on the observability aggregator) is decaying granularity — fine recent, progressively coarser as data ages. The observability aggregator adopts this natively. The question: are there places in the seven sealed components where a similar decay pattern would usefully bound storage without losing important information, analogous to log-rotation with summarisation?

This review identifies candidates. It does not patch anything.

## The principle decay must respect

Five of the seven sealed components are event-sourced: memory, scope-of-work, primary-persona layer, objective tracker, orchestrator, graceful-degradation (with memory using Graphiti and JSONL sinks rather than a SQLite event log). In an event-sourced system, deleting events breaks state reconstruction. Any decay therefore splits events into two classes:

- **State-defining events** — `ScopeCreated`, `ObjectiveCreated`, `ScopeBound`, `StateTransitioned`, etc. The system replays these to rebuild current state. Decay without a snapshot-and-truncate-events discipline corrupts the store.
- **Informational events** — `heartbeat`, `BudgetDebited` (for terminal scopes), `detection_events`, audit entries. These record history but the current running state does not depend on replaying them. They can be rolled up to period summaries without breaking anything.

The review treats these separately. Where a state-defining event is a decay candidate, the pattern becomes "classical event-sourcing snapshot": capture a projection, write a snapshot event, truncate the events that fed it. More complex; flagged where relevant.

---

## Ranked candidates (high → low)

### 1. Orchestrator `events` table — heartbeat rows

**Location.** `/orchestrator/src/local_state.py`, event type `heartbeat` in the single `events` table.
**Volume.** One row per tick. At a typical 30-second heartbeat, that's 2,880/day, ~1 million/year. Dominates the table.
**Value with age.** Recent heartbeats prove liveness and crash-recovery state. Aged heartbeats (older than a day or so) prove nothing beyond "the process was alive." Zero operational value.
**Replay impact.** Heartbeats are informational only — the orchestrator's state reconstruction does not depend on replaying the full heartbeat sequence. Safe to roll up.
**Suggested pattern.** After N days (default 1), replace a day's heartbeats with a single `heartbeat_summary` event: `{count, first_tick_at, last_tick_at, any_gaps_over_threshold}`. Preserves gap detection (the one thing you might want historically) at ~0.05% of the storage.
**Priority.** ⭐⭐⭐ — clearest win. Easy pattern, big volume reduction.

### 2. Memory `spans.jsonl` and `tokens.jsonl`

**Location.** `/memory-system/src/observability.py` — three JSONL sinks.
**Volume.** `spans.jsonl` writes one line per memory operation (ingest, search, classify_ephemeral, summarise_stream). `tokens.jsonl` writes one line per LLM call with per-prompt breakdown. At typical ingest rates these are **the highest-volume text files in the new pOS**, unbounded, file-based.
**Value with age.** Recent lines are tailed by the observability aggregator (which will maintain its own decaying retention). Aged lines are redundant — the aggregator has already consumed them. Keeping them raw is useful only until the aggregator has confirmed ingestion; after that they're pure duplication.
**Replay impact.** None. Memory's state lives in Graphiti, not in these files. The files are emission-only.
**Suggested pattern.** Log rotation with rolling retention: daily rotation; keep 7 rotations raw; drop older (or compress and move to archive). The observability aggregator has already ingested them and holds the canonical record.
**Priority.** ⭐⭐⭐ — storage benefit large, pattern trivial (log rotation is stdlib-friendly).

### 3. Graceful-degradation `detection_events` table

**Location.** `/graceful-degradation/src/state.py`, `detection_events` table.
**Volume.** One row per Claude call observed (every LLM invocation across pOS generates a detection event). HIGH volume at steady state; spikes during outages.
**Value with age.** Recent events drive the per-mode FSM. Aged events are archival: "how often did we see rate-limits last quarter?" — useful for reports, not operational.
**Replay impact.** The FSM state cache is rebuildable from events (that's in the design). **However**, `fsm_state` is a singleton-per-mode cache derived from the recent events, not the full history. Rebuilding the FSM from events *after* the latest FSM closed transition doesn't need history before that transition. So truncating detection events older than the last-mode-closed for each mode is safe.
**Suggested pattern.** Period rollup: daily aggregates per mode (count, success_rate, p95_latency, max_retry_after) replace raw events older than N days. Keep the most recent K events per mode raw so the FSM has signal to process.
**Priority.** ⭐⭐⭐ — high volume, natural rollup statistics.

### 4. Scope-of-work — `BudgetDebited` rows for terminal scopes

**Location.** `/scope-of-work/src/events.py` — `BudgetDebited` event in the `scope_events` table.
**Volume.** One row per LLM call under a scope. The dominant volume source in scope-of-work's log at steady state.
**Value with age.** For **in-flight scopes**: every debit matters because current-budget-remaining is derived from sum-of-debits-minus-refunds. For **terminal scopes** (completed / failed / cancelled): debits are historical — the scope is closed, nobody is computing its remaining budget.
**Replay impact.** Terminal-scope debits are still part of the projection's historical record. Rolling them up means the projection gets a "scope X total_input_tokens Y, total_output_tokens Z, total_money A" summary instead of the individual calls. Classical event-sourcing snapshot pattern.
**Suggested pattern.** When a scope transitions to terminal, compute a `scope_budget_summary` event per prompt-type and truncate the individual `BudgetDebited` events. v1.1 R12 per-prompt-type cost attribution still works because the summary preserves the prompt_name grouping. Observability aggregator has the raw data by then anyway.
**Priority.** ⭐⭐ — significant savings but needs the snapshot-and-truncate discipline. Cost is implementation complexity; benefit is bounded `scope_events` storage over long usage.

### 5. Orchestrator `events` — `bind_refused`, `scope_activated` rows

**Location.** Same file as heartbeats.
**Volume.** Proportional to scope-creation rate. Moderate — noticeable at steady state, not dominant.
**Value with age.** Similar to detection events: recent rows are operational context, aged rows are archival. `bind_refused` events in particular are diagnostic — "why did activation fail on this scope a month ago" is a debugging question.
**Replay impact.** Informational. Orchestrator doesn't reconstruct state from these.
**Suggested pattern.** Period rollup: daily counts by type. Keep `bind_refused` rows longer than `scope_activated` (the former carry diagnostic value; the latter are pure flow markers).
**Priority.** ⭐⭐ — modest volume, straightforward rollup.

### 6. Scope-of-work — state-defining events for terminal scopes

**Location.** `scope_events` table — `ScopeCreated`, `StateTransitioned`, `ObserverAdded`, `TriggerFired`, `ExtensionRequested`, etc.
**Volume.** Moderate — events per scope × scopes over time. Long-run accumulation.
**Value with age.** Terminal-scope history is auditable. "What happened to scope X" three months ago is a real query (which the observability aggregator handles). Structurally, the scope's projection row is the durable answer.
**Replay impact.** Significant — these events define the projection. Snapshot-and-truncate is the only safe pattern.
**Suggested pattern.** When a scope becomes terminal + ages past a retention window, emit a `scope_archived` event containing the final projection state + a hash of the truncated event history (for audit), then truncate the underlying state-defining events. The scope's projection row survives; the event history is replaced by the archive summary.
**Priority.** ⭐ — last to tackle. High complexity (snapshot-and-truncate event sourcing), moderate benefit. Probably only worth it if `scope_events` becomes a storage problem in practice, which at single-user scale may never happen.

---

## Non-candidates (leave alone)

- **Objective tracker `objective_events`.** Objectives are coarse; volume is low; retention serves the archaeology use case (replay the chain of decisions). Decay adds risk without meaningful benefit.
- **Memory `audit.jsonl`.** Free-text audit of "why did memory do X" — precisely the thing users may query years later. Low volume, high long-tail value. Rotate but don't drop.
- **Memory's Graphiti knowledge graph.** Memory's own retention story (v1.1 R10 retention class + supersession + time-lock) is the correct model; don't impose secondary decay on top.
- **Projection caches across all components.** Derived state, rebuildable from events. Decay would break semantic round-trip upgrade (v1.1 R1).
- **Compaction flags, bootstrap-refused events.** Binary state, tiny volume, zero decay benefit.
- **FSM state singletons (graceful-degradation).** Already constant size.

---

## Cross-cutting design pattern worth extracting

If two or more of the above candidates get built, a shared **"rollup-and-truncate" utility module** is worth extracting — similar in spirit to the orchestrator's event-log pattern but for summarisation:

1. A declarative rollup specification (event-type → summary-event-type, aggregation fields, period).
2. A scheduler-driven job (the orchestrator's scheduling surface already exists) that applies the spec daily.
3. Upgrade-fidelity: summaries must round-trip semantically like any other event.
4. Observability: rollup jobs emit OTel so the aggregator records "we rolled up N events to 1 summary on date D."

This would be a small Phase 2 or Phase 3 component on its own — call it **rollup-framework** — or a library consumed by the candidates above. If only one or two candidates land, a shared module is over-engineering; if four or five, it's correct.

---

## Recommended patch ordering (when the time comes)

1. **Orchestrator heartbeat rollup** — easy, big win, no event-sourcing complexity. Good pilot for the pattern.
2. **Memory JSONL rotation** — log rotation is trivially implementable; zero replay concerns.
3. **Graceful-degradation detection_events rollup** — once the rollup pattern exists from #1, this reuses it.
4. **Scope-of-work terminal-scope budget rollup** — larger engineering effort; tackle after the pattern is proven.
5. **Extract rollup-framework** — only if #1–#3 happen; probably defer until after Phase 2 completes.

None of these are urgent. All are storage-bounded — the problem shows up at multi-month usage scale, not at rebuild-verification scale.
