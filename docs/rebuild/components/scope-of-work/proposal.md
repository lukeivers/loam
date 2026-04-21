# Scope-of-Work Primitive — Proposal

**Component:** Scope-of-Work Primitive

**Status:** DRAFT — awaiting owner's review and approval before a handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 addendum (`docs/rebuild/spec/pos-v2-objectives-spec.md`)
**Informed by:** `research.md` (returned 2026-04-18 12:41 CDT, approved 13:13 CDT)
**pyee dependency approved** 2026-04-18 13:13 CDT.

---

## Summary

Build scope-of-work as a first-class Python primitive on the `pos-v2` branch, shipped on its own. It uses an event-sourced finite-state machine for lifecycle, SQLite WAL via stdlib `sqlite3` for persistence, a three-axis budget (time / tokens / money) with per-LLM-call debit, `pyee` for async observer emission, Pydantic discriminated-union predicates for escalation triggers, and OTel-native emission using the GenAI semantic conventions plus a `pos.scope.*` namespace. The API is thin, async, Pydantic-validated at construction — missing any of the seven spec fields rejects scope creation. The primitive ships standalone; every downstream consumer (objective tracker, primary persona loader, observability aggregator, cost governance, safety layer, reversibility primitive) subscribes to the emission surface when built. On landing, a 10-line adapter retires memory's `MockScopeSource`.

## Direction

### Lifecycle

- **Model:** event-sourced finite-state machine. Events are truth; state is a projection.
- **States:** `proposed → active → {paused ↔ active}* → {completed | failed | cancelled | escalated}`.
- **Parent-close policy on child scopes:** Temporal-inspired — TERMINATE default, ABANDON, REQUEST_CANCEL as alternatives.
- **Concurrency:** `asyncio.TaskGroup` for in-process children. Event-log polling is the cross-process coordination substrate (no additional IPC mechanism).

### Persistence

- **Substrate:** SQLite WAL mode via stdlib `sqlite3`.
- **Schema:** one append-only `scope_events` table as the system of record; one cached `scope_state` projection rebuildable from events.
- **Durability:** WAL mode + `fsync` at configurable intervals. Upgrade-fidelity (v1.1 R1) tests by replaying the event log.
- **Rejected candidates:** Graphiti-on-Kuzu (couples scope runtime durability to memory release cadence, wrong substrate for hot-path state); flat append-only log without index (no queries); dedicated KV store (loses SQL ergonomics); Postgres (overkill for single-user local).

### Budget

- **Three axes:** time (wall-clock seconds elapsed), tokens (input + output per model), money (derived from tokens via a model-rate table).
- **Hot path:** per-LLM-call token debit. Money and time are derived on query, not debited per-call.
- **Refunds:** failed LLM calls emit refund events so the ledger remains accurate.
- **Per-prompt-name aggregation:** a SQL view over `scope_events` delivers v1.1 R12 per-prompt cost attribution without additional machinery.
- **Exhaustion policies:** halt-and-signal (default), throttle, request-extension-from-owner. Policy per-scope, declared at creation.

### Observers and escalation triggers

- **Observer emission:** `pyee.AsyncIOEventEmitter`. Observer list is itself stored as events in the audit log — adding or removing an observer is an auditable operation.
- **Escalation triggers:** Pydantic discriminated-union predicates — `BudgetThreshold`, `TimeElapsed`, `EventType`, `SuccessCriterion`, `Reversibility`. Declarative at scope creation; evaluated by the primitive on each state transition and on each LLM-call debit.
- **Trigger firing produces an `escalated` state event** with the triggering predicate and value; downstream consumers subscribe to the `escalated` event name.

### Observability

- **Native OTel emission** using the GenAI semantic conventions (`gen_ai.agent.*`, `gen_ai.usage.*`) plus a `pos.scope.*` custom namespace for scope-specific attributes (budget remaining, reversibility class, escalation reason).
- **One `invoke_scope` INTERNAL span per scope**, wrapping the active duration.
- **Child `chat {model}` spans per LLM call**, standard GenAI convention.
- **Span events for state transitions** (proposed→active, paused, resumed, completion, escalation).
- **No downstream consumer assumed** (A1 correction). Emission shape and channel are specified; consumption is future work.

### API

- **Thin async Python.** Pydantic-validated `ScopeSpec` at construction — missing any of the seven spec fields raises a validation error that rejects scope creation.
- **Sync compatibility shim** for CLI / test callers who cannot easily adopt async.
- **Surface:** `create(spec) → Scope`, `start(scope) → ScopeHandle`, `pause(scope)`, `resume(scope)`, `complete(scope, result)`, `fail(scope, reason)`, `cancel(scope, reason)`, `get(scope_id) → Scope`, `list(filter) → list[Scope]`, plus observer subscription via the `pyee` emitter.

## Deliverables (what the builder ships)

### D1. Core scope primitive

**Objective:** the seven-field primitive exists in Python, Pydantic-validated at construction, with the lifecycle FSM and event-log persistence working in-process.
**Acceptance:** creating a scope with any missing field raises; creating with all seven fields succeeds; state transitions produce events; replaying the event log reconstructs state identically.

### D2. Budget ledger

**Objective:** three-axis budget (time / tokens / money) tracked via the event log; per-LLM-call token debit works; refund semantics land.
**Acceptance:** ingesting a synthetic LLM-call sequence produces accurate budget-remaining at any point; a refund event corrects a prior debit; the per-prompt-name SQL view returns per-prompt costs matching a hand-calculated ground truth.

### D3. Observer and trigger system

**Objective:** observer subscription via `pyee` and declarative triggers via Pydantic discriminated-union predicates both work.
**Acceptance:** an observer subscribed to a scope receives events on state transitions and debits; a declared `BudgetThreshold` trigger fires an `escalated` event when its threshold is crossed; a declared `TimeElapsed` trigger fires when wall-clock elapsed crosses its value.

### D4. Parent-child hierarchy

**Objective:** scopes can spawn child scopes; parent-close policies (TERMINATE / ABANDON / REQUEST_CANCEL) are honoured; cancellation cascades correctly.
**Acceptance:** creating a child scope under a parent links them in the event log; cancelling the parent under TERMINATE policy cascades to active children; under ABANDON, children continue; under REQUEST_CANCEL, children receive a cancel request they can honour or reject.

### D5. OTel observability emission

**Objective:** scope lifecycle produces OTel spans and events using GenAI semantic conventions + `pos.scope.*` attributes.
**Acceptance:** starting a scope produces an `invoke_scope` INTERNAL span; LLM calls produce child `chat {model}` spans; state transitions produce span events; budget attributes appear on the scope's span; no consumer is required for emission to succeed.

### D6. Memory-mock retirement

**Objective:** `MockScopeSource` in the memory system is replaced by a real adapter against the primitive; memory continues to function.
**Acceptance:** a 10-line `RealScopeSourceAdapter` wraps the primitive to match memory's `ScopeSource` protocol; `MemoryAPI` constructor accepts the adapter; an integration test creates a scope, ingests memory under that scope_id, searches memory and finds the entry, and rejects an unknown scope_id with a clear error.

### D7. Upgrade-fidelity test harness

**Objective:** the primitive's event log passes a semantic round-trip test across an upgrade.
**Acceptance:** a probe set of scope creations, transitions, and queries is captured pre-upgrade; replayed post-upgrade; output-equivalence is asserted; drift above a declared threshold fails the upgrade.

### D8. Bundled documentation

**Objective:** v1.1 R4 — human-readable documentation bundled with the primitive.
**Acceptance:** prose explanation; architecture diagram (event-sourced FSM + event log + projection cache); relationship map showing what subscribes (memory, future components); one-page API reference; data-flow diagram for a representative scope lifecycle including LLM-call debits and an escalation.

---

## Spec coverage

| Criterion | Delivered by |
|---|---|
| v1.0 Core primitive — scope declares all seven fields at creation; missing any rejects | D1 (Pydantic validation at construction) |
| v1.0 Observability — every action produces an auditable record | D5 (OTel emission) + event log durability (D1) |
| v1.0 Reversibility — every action declares reversibility class | D1 (field mandatory) + triggers can fire on reversibility mismatch (D3) |
| v1.0 Cost governance — per-scope budgets declared at creation; ceilings cannot be exceeded silently | D2 (budget ledger, exhaustion policies) |
| v1.0 Safety — kill switches stop work within bounded time | D3 (escalation trigger → cancel) + D4 (parent-close cascade) |
| v1.1 R1 — semantic round-trip upgrade | D7 |
| v1.1 R4 — bundled documentation | D8 |
| v1.1 R11 — OTel observability | D5 |
| v1.1 R12 — per-prompt-type cost attribution | D2 (per-prompt SQL view) |

Two criteria are noted as *partially out of primitive scope*, consistent with A1: **reversible-preference selection** (choosing the reversible option between two equivalent approaches) and the **four-part correction loop's class-closure step** are policy decisions belonging to the safety layer and self-correction loop respectively. The primitive supplies the fields and trigger surface those layers consume; the policies themselves are authored when those layers are designed.

---

## Dependencies and assumptions

### Hard dependencies (must exist or be mocked before the primitive ships)

- None. The primitive is foundational — it depends on nothing pOS-side.

### Soft dependencies (the primitive emits; consumers come later)

- Observability consumer (subscribes to OTel emission)
- Cost governance (subscribes to budget events; enforces system-wide ceilings)
- Safety layer (subscribes to escalation events; kill switches)
- Reversibility primitive (consumes reversibility class field; enforces policy)
- Self-correction loop (subscribes to failure events; runs the four-part protocol)
- Objective tracker (links scopes to parent objectives)
- Primary persona loader (creates scopes as the user speaks to the persona)

### Assumptions (marked as inference recorded — not verbatim from the owner)

1. **`pyee` is acceptable as a single third-party dependency** for async event emission. confirmed 2026-04-18 13:13 CDT. No other third-party dependencies anticipated for the primitive itself. *Confirmed — not an inference.*
2. **SQLite WAL handles the single-user long-running workload** without contention issues. Workload projection: scope creation at interactive cadence (seconds between creates), budget debits at LLM-call cadence (up to ~10 per second during bursts), queries at arbitrary cadence. *inference recorded — prototype can verify at D7 timescale.*
3. **The event log remains tractable in size over multi-year use.** Budget debit events are the highest-frequency entry; at ~3,000 scopes per year and ~10 events each, that's ~30K events per year — well inside SQLite's operating envelope. *inference recorded.*

---

## Prototyping priorities

Research surfaced seven questions only a prototype can answer. I'd tackle these in this order before the full build:

1. **Cross-process cascade-halt latency.** Polling the event log vs. SQLite NOTIFY / other signalling. What's the actual latency on kill-parent-kill-children?
2. **Trigger evaluation cost on hot scopes.** How expensive is re-evaluating declarative predicates on every debit for a scope with many triggers?
3. **Refund semantics for interrupted LLM calls.** What marks a call as "failed and refundable" vs "failed but consumed"? API design implication.

Remaining four prototyping questions are smaller and can fold into the main build rather than needing standalone prototypes.

---

## Complexity estimate

265–440 AI-minutes for the full build (research's estimate, which I accept). Breakdown:

- Core build: 155–260 AI-minutes
- Tests + documentation: 110–180 AI-minutes

Larger than memory's adaptation layer (120–180) as expected — this is core-primitive work built from nothing, not adaptation around an existing library.

---

## What this proposal is NOT

- Not a specification of module names, class names, file layout, or function signatures beyond the API surface sketched above. Those are the builder's call.
- Not a commitment to every library beyond `sqlite3` (stdlib), `pydantic`, `pyee`, and `opentelemetry-api` + `opentelemetry-sdk`. If the builder finds that one more dependency is genuinely unavoidable, they flag it rather than inventing.
- Not a substitute for the future safety-layer, reversibility-primitive, or self-correction-loop components. This primitive provides the field and trigger surface those layers consume.

---

## Open questions for the owner (resolved 2026-04-18 13:39 CDT)

1. **Prototype vs fold-in:** FOLD IN. Builder detects design problems mid-build and halts cleanly rather than running a separate prototyping round.
2. **Default exhaustion policy:** REQUEST-EXTENSION across all three budget axes. When a scope hits its time / token / money budget, it pauses in a "pending-extension-request" state and surfaces the request; it does not halt silently, throttle, or keep running. User responds yes-with-amount (scope resumes with extended budget) or no (scope ends). Per-scope override still available for scope authors who want halt-and-signal or throttle instead.
3. **Default parent-close policy:** TERMINATE. Cancelling a parent scope immediately stops all active children. Scope authors can override per-scope (ABANDON or REQUEST_CANCEL) where child independence is desired.

**One consequence of decision 2 worth naming:** the primitive now needs a user-notification channel when extension requests fire, and a response API (accept-with-amount or reject). Until the primary persona loader is built, extension requests emit to the OTel stream and to a local file (`scope_events` table entry + a human-readable pending-extension log). the primary persona (or a calling workspace) can poll or subscribe to surface the request. Default timeout for unanswered extension requests: **indefinite** — the scope stays paused until answered, matching the rebuild's ADHD-friendly "silence by choice" posture. Per-scope override for hard timeouts available.

---

## What happens on approval

On your approval of this proposal:

1. I draft the handoff brief for the builder. Objectives, constraints, acceptance criteria, dependencies — no prescribed file paths, class names, or step-by-step execution. You review the brief to catch overspecification.
2. On your review, a general-purpose agent is dispatched against the brief.
3. If the agent cannot execute per the proposal, it halts and signals — per the rebuild rules.
