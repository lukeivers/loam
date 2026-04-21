# Observability Aggregator — Proposal

**Component:** Observability Aggregator (third Phase 2 component)

**Status:** DRAFT — awaiting owner's review and approval before a handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 + v1.2 addenda
**Informed by:** `research-plan.md`, `research.md` (returned 2026-04-19 10:36 CDT). the owner's rulings on the three halt signals + NL-surface question 2026-04-19 10:45 CDT.

---

## Summary

Build the observability aggregator as a single-user local-first trace store that subscribes to every sealed component's emission surfaces without amending any of them. Ingestion is in-process: a custom `SpanProcessor` + `SpanExporter` registered via the orchestrator's existing `~/.pos/bootstrap.py` workspace hook (Python OTel's late-binding `ProxyTracer` routes the six OTel-emitting components automatically), plus a JSONL tailer for memory's hand-rolled sinks. Storage is DuckDB (MIT-licensed, embedded, columnar — approved as a new permitted dependency); SQLite fallback exists for users who opt out. Query surface has three layers: a structured Pydantic API, a Claude-powered natural-language path for "why did you do X at time T," and a `pos obs` CLI. Replay is read-only playback — reconstruct the decision chain from stored records (Reading A; ruling recorded). Retention is three-tier with v1.1 R10 retention-class honoured at ingest.

## Direction

### Ingestion — in-process subscription via bootstrap.py

- The aggregator registers a custom `SpanProcessor` and `SpanExporter` via the orchestrator's existing `~/.pos/bootstrap.py` workspace hook. No sealed-component amendment.
- Python OTel's late-binding `ProxyTracer` means the six OTel-emitting components (scope-of-work, primary-persona, objective-tracker, orchestrator, graceful-degradation, plus test infra) route through automatically on first tracer acquisition.
- Memory-system uses three hand-rolled JSONL sinks (`spans.jsonl`, `tokens.jsonl`, `audit.jsonl`) rather than OTel directly. The aggregator reads these via a JSONL tailer — same logical ingestion path, different transport.
- Local spool file buffers emissions against aggregator downtime. On aggregator restart, spooled entries replay into the store.

### Storage — DuckDB (the owner-approved new dep)

- **DuckDB** as the primary store: columnar, embedded, MIT-licensed, SQL-native, ~5 MB binary.
- SQLite fallback mode for users who opt out of DuckDB — same schema, slower on analytic queries over long ranges.
- Schema: normalised `spans`, `span_events`, `span_attributes`, `resource_attributes` tables plus a rollup table for post-90-day data.
- Size projection: ~1.3 MB/day raw; ~130 MB steady state at 2 years under DuckDB compression.

### Query surface — three layers

1. **Structured Pydantic API:** `find_spans(filter)`, `get_trace(trace_id)`, `cost_by_prompt(window)`, `replay_session(session_id)`, `replay_scope(scope_id)`, `replay_objective(objective_id)`.
2. **NL path for "why did you do X at time T":** two-LLM-call pattern via Claude (Max) — first call translates natural-language question into a structured Pydantic filter; second call formats the resulting spans into a cited narrative answer. Both calls tagged `pos.prompt.type` for reflexive v1.1 R12 cost attribution (the aggregator's own queries show up in the same cost view it serves). Output is a Pydantic-validated structured response, not free-form SQL.
3. **`pos obs` CLI:** thin wrapper over the structured API for direct user access.

### Replay — Reading A (read-only playback)

- `replay_session / replay_scope / replay_objective` reconstruct the decision chain from stored spans + events + attributes. No re-execution of LLM calls.
- Output is a deterministic rendering of what was observed: the ordered sequence of decisions, their inputs, their outputs, and the objectives / constraints / knowledge cited at each step.
- Reading B (deterministic re-execution) is explicitly rejected because it would require amending every LLM-calling sealed component.

### Retention — decaying granularity with v1.1 R10 honoured

Per the owner's rollup decision 2026-04-19 10:51, retention follows a decaying-granularity pattern — finer-grained recent data, progressively coarser as it ages. Default tiers (workspace-tunable):

- **0–7 days:** full fidelity (raw spans + events + attributes).
- **7–30 days:** daily rollup (one aggregate per day + top-N longest spans retained raw).
- **30–365 days:** monthly rollup (one aggregate per month).
- **365+ days:** yearly rollup, or audit-only at a workspace-set cutoff.

Rollup jobs scheduled via the orchestrator's scheduling surface, running daily; each day's run advances the boundaries and summarises data crossing each tier threshold. Top-N longest spans within a rolled-up period are kept raw as a "smoking gun" reserve for audit queries.
- **v1.1 R10 retention-class propagation at ingest:**
    - `normal` → stored fully.
    - `derived-only` → structured metadata kept, payload attributes dropped at ingest.
    - `ephemeral` → minimal "time T, op X happened" stub with no payload (ruling recorded — observability-of-ephemeral is distinct from memory-of-ephemeral).

### Integration with primary-persona's "show me why"

- When the user asks "why did you do X at time T" the primary persona calls the aggregator's NL path; receives a structured response with cited spans; formats conversationally for the user.
- Anti-deskilling principle (v1.0): the cited spans are surfaced — the user sees the actual evidence, not just the narrative. They can drill in via the CLI or further NL queries.

---

## Deliverables

Nine deliverables D1–D9.

### D1. Bootstrap-based OTel ingestion

**Objective:** custom `SpanProcessor` + `SpanExporter` registered via `~/.pos/bootstrap.py`; the six OTel-emitting sealed components' spans flow into the aggregator with no amendment.
**Acceptance:**
- Running the aggregator alongside any sealed component captures that component's spans at the aggregator.
- Zero amendments to sealed components — test suites for all six OTel-emitting components still pass at baseline after bootstrap registration.
- Local spool file buffers spans when the aggregator is down; spooled spans replay into the store on restart.

### D2. Memory JSONL tailer

**Objective:** a tailer reads memory-system's three JSONL sinks (`spans.jsonl`, `tokens.jsonl`, `audit.jsonl`) and ingests them into the same store.
**Acceptance:**
- New memory JSONL lines reach the aggregator within a bounded tail latency.
- Memory's 30 tests still pass at baseline (no amendment).
- JSONL format matches the expected schema; malformed lines are logged and skipped, not fatal.

### D3. DuckDB storage + SQLite fallback

**Objective:** DuckDB primary store with the full schema; SQLite fallback mode for users who opt out.
**Acceptance:**
- DuckDB database file at `~/.pos/observability.duckdb` (configurable); schema matches the research's specification.
- SQLite fallback mode produces identical query results for the structured API (slower but correct).
- Size projection sanity-check: 1 day of synthetic load produces storage within 20% of the 1.3 MB/day projection.
- v1.1 R1 semantic round-trip upgrade test passes.

### D4. Structured Pydantic query API

**Objective:** `find_spans`, `get_trace`, `cost_by_prompt`, `replay_session`, `replay_scope`, `replay_objective` all work against the store.
**Acceptance:**
- Each method has Pydantic-validated input + output schemas.
- Representative queries against a populated store return the correct results.
- `cost_by_prompt` aggregates tokens by `pos.prompt.type` across all components — workspace-scoped cost attribution per v1.1 R12.

### D5. NL-path query ("show me why")

**Objective:** two-LLM-call pattern via Claude-via-Max translates natural language into a structured filter, then formats the results into a cited narrative.
**Acceptance:**
- A test-set of representative "show me why" questions produces structured-filter calls that return the right span sets (acceptance threshold per test, ≥80%).
- The formatted output always includes cited span IDs — no uncited claims.
- Both LLM calls tagged with `pos.prompt.type` (distinct values for translate and format) — they appear in the cost view at their own attribution.
- A test verifies the aggregator querying its own NL output doesn't produce an infinite loop (self-observation is a noop).

### D6. Replay — Reading A (read-only playback)

**Objective:** reconstruct the decision chain from stored records; output is a deterministic rendering of what was observed; no re-execution.
**Acceptance:**
- `replay_session(session_id)` returns the ordered sequence of spans + events + attributes for that session.
- `replay_scope(scope_id)` returns the same for a scope execution.
- `replay_objective(objective_id)` returns all activity under that objective tree.
- Representative round-trip test: populate store with synthetic spans; replay; verify the rendered chain matches the input ordering + content.

### D7. Retention + rollup + retention-class handling

**Objective:** three-tier retention (0–90 days full / 90–540 days rollup / 540+ days audit); daily rollup job; v1.1 R10 retention-class honoured at ingest per ruling recorded.
**Acceptance:**
- `normal` episodes stored fully.
- `derived-only` episodes: structured metadata kept, payload attributes dropped at ingest.
- `ephemeral` episodes: minimal stub only (time + op name); no payload; no raw text.
- Daily rollup job runs via orchestrator's scheduling surface; converts 90-day-old entries to rollup-only.
- Retention-class is queryable in the structured API so users can audit what's been dropped.

### D8. `pos obs` CLI

**Objective:** thin CLI wrapper over the structured Pydantic API for direct user access.
**Acceptance:**
- Commands for each API method (`pos obs find-spans`, `pos obs get-trace`, `pos obs cost-by-prompt`, `pos obs replay-session`, etc.).
- Formatted output is human-readable and cites span IDs.
- `pos obs why "<question>"` invokes the NL path.

### D9. Bundled documentation + OTel-self + privacy verification

**Objective:** v1.1 R4 bundled docs plus explicit self-observability verification and privacy-handling verification.
**Acceptance:**
- Prose, architecture diagram, data-flow, relationship map, API reference, CLI reference, bootstrap-registration guide.
- Self-observability verified: the aggregator's own operations emit OTel but are filtered at ingest (otherwise it observes its own observation recursively).
- Privacy test: a workload producing `derived-only` and `ephemeral` spans is ingested; the stored records match the retention-class rules (no payload leakage).
- NL-path evaluation: Garbage-detector-style FPR measurement on a synthetic corpus of NL questions with ground-truth filter outputs.

---

## Spec coverage

| Criterion | Delivered by |
|---|---|
| v1.0 Observability — every action produces an auditable record | D1 + D2 + D3 |
| v1.0 Observability — replay reproduces the decision chain | D6 (Reading A) |
| v1.0 Observability — "why did you do X at time T" queries return cited answers | D5 + D4 |
| v1.1 R1 — semantic round-trip upgrade | D3 |
| v1.1 R4 — bundled documentation | D9 |
| v1.1 R10 — per-episode retention class propagation | D7 |
| v1.1 R11 — OpenTelemetry as internal trace format | D1 (consumption side; emission already landed in sealed components) |
| v1.1 R12 — per-prompt-type cost attribution at workspace scope | D4 `cost_by_prompt` |
| v1.0 anti-deskilling — "show me why" surfaces cited evidence, not just narrative | D5 + D8 |

---

## Dependencies

### Hard dependencies (no amendments)

- All seven sealed components. Aggregator subscribes via standard OTel mechanisms (bootstrap-based SpanProcessor) and a JSONL tailer for memory's hand-rolled sinks. No sealed-component amendment.

### Soft dependencies (future)

- Self-upgrade framework (later Phase 2) — aggregator's store participates in pOS-wide upgrade-fidelity story.

### Permitted runtime dependencies

- Existing: stdlib, pydantic, pyee, opentelemetry-api/sdk, PyYAML.
- **New (the owner-approved 2026-04-19 10:45):** `duckdb`. MIT-licensed, embedded, no network. SQLite fallback mode available.
- No other additions without halt-and-signal.

---

## Assumptions (inference recorded — flagged so the builder can challenge)

1. **Python OTel's `ProxyTracer` late-binding behaviour survives bootstrap registration** in real integration against all six OTel-emitting components simultaneously. Research asserts this works; untested in practice. If the builder finds components initialise their tracers before the bootstrap hook fires (defeating late-binding), halt and surface.
2. **Memory's JSONL sinks maintain their current format stability.** Memory's docs describe three specific sinks; the tailer builds against that format. If memory's format has drifted since the docs were written, halt and surface with what was found.
3. **NL-path test corpus:** the primary persona's inclination is ~20–30 representative "show me why" questions with ground-truth filter outputs. If the builder finds a cleaner evaluation pattern (e.g. generated directly from sealed-component docs), halt and surface.

---

## Open questions for the owner (resolved 2026-04-19 10:51)

1. **Rollup granularity — decaying retention.** the owner's preferred pattern: daily for a week, weekly/daily rollup for a month, monthly rollup for a year, yearly rollup thereafter. Adopted as the default; workspace-tunable per tier.
2. **Default retention of `derived-only` payload attributes at ingest.** Drop immediately — matches R10's spirit.

---

## What happens on approval

1. I draft the handoff brief. All four the owner rulings from research (Reading A, DuckDB approved, ephemeral stub, keep NL surface) baked in. Plus the two the primary persona leans above on approval.
2. On brief review, a general-purpose agent is dispatched.
3. Halt-on-deviation applies. Any sealed-component amendment genuinely required → halt and surface.

---

## Complexity honesty

The research's "~505 AI-minutes" is a tool-call-count proxy; calendar reality runs 5–10× faster. Honest estimate for this build: **25–35 minutes of wall-clock time**, consistent with the rebuild's track record.
