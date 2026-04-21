# Handoff Brief — Observability Aggregator

**Component:** Observability Aggregator (third Phase 2 component)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-19 10:51 CDT, all decisions resolved)
**Spec:** objectives spec v1.0 + v1.1 + v1.2 addenda

---

## Objective

Deliver a production-ready observability aggregator: a single-user local-first trace store that subscribes to every sealed component's emission surface, stores spans durably in DuckDB (SQLite fallback available), serves structured + natural-language + CLI queries, supports session/scope/objective replay as read-only playback, and honours v1.1 R10 retention class. No sealed component is amended.

---

## Hard constraints

1. **Implementation language:** Python 3.13 dev target, `pos-v2` branch. Work lives under `pos-v2/observability-aggregator/` (mirror prior component layouts).
2. **No amendments to any of the seven sealed components.** Memory, scope-of-work, primary-persona layer, objective tracker, orchestrator, graceful-degradation — all stay as they are. Aggregator subscribes via standard OTel mechanisms (bootstrap-registered SpanProcessor) and a JSONL tailer for memory's sinks. If the build genuinely requires any sealed-component amendment, halt and surface.
3. **A1 correction held rigorously.** Every sealed component was built expecting no consumer. Aggregator's arrival must not require any component to know about it.
4. **Zero carryover from current pOS.**
5. **Permitted runtime dependencies:** stdlib, `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`, `PyYAML`, **`duckdb`** (approved 2026-04-19 10:45 as a new permitted dep for this component). Test-only (pytest, pytest-asyncio) permitted. Anything else requires halt-and-signal.
6. **Max-first.** LLM inference via Claude-via-Max is expected for the NL "show me why" path; not used elsewhere.
7. **No personas in pOS core.**
8. **Halt-on-deviation.** Silent deviation forbidden.
9. **Bundled documentation per v1.1 R4.** Ships at `observability-aggregator/docs/`.

## rulings recorded baked into this brief

- **Ingestion:** in-process custom SpanProcessor + SpanExporter registered via the orchestrator's existing `~/.pos/bootstrap.py` workspace hook. Python OTel's late-binding ProxyTracer routes the six OTel-emitting components. Memory's three JSONL sinks read via a tailer.
- **Storage:** DuckDB primary at `~/.pos/observability.duckdb`; SQLite fallback mode at the same schema.
- **Query surface:** structured Pydantic API + NL path via Claude-via-Max + `pos obs` CLI.
- **Replay:** Reading A — read-only playback, reconstruct the decision chain from stored records. No re-execution.
- **Retention — decaying granularity** (workspace-tunable defaults):
    - 0–7 days: full fidelity.
    - 7–30 days: daily rollup + top-N longest spans kept raw.
    - 30–365 days: monthly rollup.
    - 365+ days: yearly rollup, or audit-only at a workspace-set cutoff.
- **v1.1 R10 retention-class handling:** `normal` stored fully; `derived-only` drops payload attributes immediately at ingest (ruling recorded — matches R10's spirit); `ephemeral` minimal stub only (time + op name, no payload).
- **Self-observability:** aggregator's own operations emit OTel but are filtered at ingest — no observing-its-own-observation recursion.

---

## Deliverables

Nine deliverables D1–D9 as named in the proposal. Objective-level acceptance; no prescribed module names, class hierarchies, file layout, or function signatures beyond the API surface the proposal has sketched.

### D1. Bootstrap-based OTel ingestion

**Objective:** custom `SpanProcessor` + `SpanExporter` registered via `~/.pos/bootstrap.py`; the six OTel-emitting sealed components' spans flow into the aggregator without any sealed-component amendment.
**Acceptance:**
- Running the aggregator alongside each of the six OTel-emitting components captures their spans.
- Zero amendments to sealed components — their existing test counts still pass (scope-of-work 77+1 skipped, objective-tracker 86, primary-persona 101, orchestrator 56, graceful-degradation 93 + any test-infra).
- Local spool file buffers spans during aggregator downtime; spooled spans replay into the store on restart.
- A test verifies bootstrap-registration timing: if component tracers initialise before the bootstrap hook fires, defeating late-binding, the test halts with a clear diagnostic.

### D2. Memory JSONL tailer

**Objective:** a tailer reads memory's three hand-rolled JSONL sinks (`spans.jsonl`, `tokens.jsonl`, `audit.jsonl`) and ingests them into the same store.
**Acceptance:**
- New JSONL lines reach the aggregator within a bounded tail latency (target: <1 s p95).
- Memory's 30 tests still pass at baseline.
- Malformed lines are logged and skipped, not fatal.
- JSONL format is verified against memory's docs; if the format has drifted, halt and surface.

### D3. DuckDB storage + SQLite fallback

**Objective:** DuckDB primary store with the full schema; SQLite fallback mode that produces identical query results (slower but correct).
**Acceptance:**
- DuckDB database at `~/.pos/observability.duckdb` (configurable); schema has `spans`, `span_events`, `span_attributes`, `resource_attributes`, plus rollup tables per retention tier.
- SQLite fallback mode selectable via config; structured API returns identical results (test verifies parity on a synthetic workload).
- 1 day of synthetic load produces storage within 20% of the research's 1.3 MB/day projection.
- v1.1 R1 semantic round-trip upgrade test passes.

### D4. Structured Pydantic query API

**Objective:** `find_spans`, `get_trace`, `cost_by_prompt`, `replay_session`, `replay_scope`, `replay_objective` all work against the store.
**Acceptance:**
- Pydantic-validated input and output schemas for each method.
- Representative queries against a populated store return the correct results.
- `cost_by_prompt` aggregates tokens by `pos.prompt.type` across all components — workspace-scoped cost attribution for v1.1 R12.

### D5. NL-path query ("show me why")

**Objective:** two-LLM-call pattern via Claude-via-Max translates a natural-language question into a structured filter, then formats the resulting spans into a cited narrative. Both calls tagged with distinct `pos.prompt.type` values for v1.1 R12 reflexive cost attribution.
**Acceptance:**
- A test-set of 20–30 representative "show me why" questions (builder-drafted; structure matches graceful-degradation's synthetic corpus approach) produces structured filters that return the right span sets at ≥80% accuracy.
- Formatted output always cites span IDs; no uncited claims.
- Both LLM calls appear in the cost-view (v1.1 R12) at their distinct `pos.prompt.type` tags (`obs-nl-translate` and `obs-nl-format` or equivalent).
- Self-observation test: the aggregator running its own NL queries does not produce an infinite observation loop.

### D6. Replay — Reading A (read-only playback)

**Objective:** `replay_session`, `replay_scope`, `replay_objective` reconstruct the decision chain from stored spans + events + attributes; no re-execution.
**Acceptance:**
- `replay_session(session_id)` returns the ordered span/event sequence for that session.
- `replay_scope(scope_id)` returns the same for a scope execution.
- `replay_objective(objective_id)` returns all activity under the objective's tree.
- Round-trip test: populate store with synthetic spans; replay; verify the rendered chain matches input ordering and content.

### D7. Decaying retention + retention-class handling

**Objective:** decaying-granularity retention per the pattern; v1.1 R10 retention-class honoured at ingest.
**Acceptance:**
- 0–7 days: full fidelity.
- 7–30 days: daily rollup + top-N longest spans kept raw (N tunable, sensible default).
- 30–365 days: monthly rollup.
- 365+ days: yearly rollup or audit-only (workspace-tunable cutoff).
- Daily rollup job runs via orchestrator's scheduling surface; synthetic-aged data crossing each threshold is correctly rolled up.
- Retention-class propagation: `normal` stored fully; `derived-only` drops payload attributes at ingest; `ephemeral` stub-only.
- Retention class is queryable — users can see what's been dropped.

### D8. `pos obs` CLI

**Objective:** thin CLI wrapper over the structured API for direct user access.
**Acceptance:**
- Commands for each API method (`pos obs find-spans`, `pos obs get-trace`, `pos obs cost-by-prompt`, `pos obs replay-session`, etc.).
- `pos obs why "<question>"` invokes the NL path.
- Formatted output is human-readable and cites span IDs.

### D9. Bundled documentation + self-observability + privacy verification

**Objective:** v1.1 R4 docs plus explicit verification of self-observability filtering and privacy handling.
**Acceptance:**
- Prose, architecture diagram (bootstrap → SpanProcessor → Store → Query surface), data flow for a representative session, relationship map, structured API reference, NL-path reference, CLI reference, bootstrap-registration guide.
- Self-observability: aggregator's own spans are filtered at ingest — no recursion when the aggregator is observed by itself.
- Privacy test: a workload producing `derived-only` and `ephemeral` spans is ingested; stored records strictly match the retention-class rules (no payload leakage).
- NL-path evaluation: structured measurement of translate-accuracy on the 20–30-question corpus, plus format-correctness on cited-output completeness.

---

## Dependencies

### Hard dependencies (no amendments)

- All seven sealed components — integration via bootstrap-registered SpanProcessor + memory JSONL tailer.

### Soft dependencies (future)

- Self-upgrade framework (later Phase 2) — aggregator's DuckDB participates in pOS-wide upgrade-fidelity.

### Permitted runtime dependencies

As enumerated above. `duckdb` added for this component. No other additions without halt-and-signal.

---

## Halt conditions

Halt and return with a named failure signal if:

- Any hard constraint cannot be honoured.
- A spec acceptance criterion becomes unsatisfiable under the approved direction.
- Any sealed-component amendment appears genuinely required — do not modify silently.
- An additional runtime dependency appears necessary beyond DuckDB — do not add; surface.
- Bootstrap-registration timing turns out not to capture all six OTel-emitting components (tracers initialised before the hook fires) — surface.
- Memory's JSONL sink format has drifted from the docs — surface with what was found.
- NL-path accuracy on the test corpus falls materially below the 80% threshold — surface measurement, don't silently ship.
- Any ambiguity requiring an invented constraint not in owner's words.

---

## Return format

On completion, return a summary (≤700 words):

1. Which deliverables D1–D9 completed, which halted.
2. Which spec criteria now pass (cite v1.0 behaviour or v1.1/v1.2 revision).
3. Confirmation that all seven sealed components' tests still pass at baseline.
4. Test counts on the aggregator itself.
5. NL-path accuracy measurement on the 20–30-question test corpus.
6. Self-observability verification result.
7. Privacy test result (retention-class propagation).
8. Complexity outcome — AI-time actually taken (with honesty note: research estimate 505 AI-min, calibrated wall-clock expectation 25–35 min).
9. Commits on `pos-v2`.
10. Any halt signals raised.
11. Recommended next action.

---

## What this brief is NOT

- Not a specification of module names, class hierarchies, file layout, or function signatures beyond the API surface the proposal has sketched.
- Not a step-by-step execution plan.
- Not a commitment to designing the self-upgrade framework (the last Phase 2 component). That has its own brief.
- Not a commitment to a UI layer over the query surface.

---

## inferences recorded in this brief (flagged so the builder can challenge)

Three items come from the primary persona's interpretation rather than the owner's verbatim words:

- *Top-N raw spans retained within the 7–30-day rollup window.* Research didn't prescribe N; the primary persona's inclination is a sensible default (e.g. top 20 longest spans per day) with workspace tunability. If the builder finds a better default from measurements, halt and flag.
- *Daily rollup boundary (7 days) + weekly→monthly→yearly tiers (30, 365).* the owner's pattern was informative example. the primary persona's chosen specific boundaries; if the builder finds measurement-driven boundaries land meaningfully different, halt and flag.
- *NL-path test-corpus of 20–30 questions* at 80% accuracy threshold. the primary persona's inclination from graceful-degradation's synthetic-corpus precedent. If the builder finds the corpus size insufficient to be statistically meaningful, halt and flag with recommended size.
