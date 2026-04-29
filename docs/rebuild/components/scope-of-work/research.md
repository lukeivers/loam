# Research — Scope-of-Work Primitive

**Component:** Scope-of-Work Primitive. **Status:** RESEARCH COMPLETE — no halt signals raised.
**Authored by:** general-purpose Agent dispatched per the research plan. **Date:** 2026-04-18.
**Against:** objectives spec v1.0 + v1.1 addendum (see `docs/rebuild/spec/loam-objectives-spec.md`).
**Constraints honoured:** Python-native; Max-first (no LLM inference inside the primitive); zero carryover from current pOS; no code, no proposal, no brief; ODD-compatible (every recommendation traces to a spec objective).

---

## 0 — Method note and scope

This document answers the seven question-groups in `research-plan.md`. It does not select libraries with finality (the proposal does that); it surfaces options, scores them against the seven spec fields, and recommends a coherent design shape with rationale. Where a candidate is rejected, the rejection is justified against a spec objective. Where two options are roughly equivalent, both are kept and the proposal layer chooses.

The seven spec fields are referenced throughout in canonical order: **goal, constraints, budget, reversibility class, success criteria, observers, escalation triggers.** "Spec coverage" tables map design pieces back to objectives.

The "future components" the spec names — **objective tracker, primary persona loader, observability consumer, cost governance, safety layer, reversibility primitive** — are referenced as *consumers of this primitive's emission and API surface*. None are assumed to exist when scope-of-work ships. The primitive is shippable on its own; downstream components subscribe when built. (A1 correction.)

---

## 1 — Survey results

### 1.1 Agent frameworks

| Framework | Native unit | Goal | Constraints | Budget | Reversibility | Success criteria | Observers | Escalation |
|---|---|---|---|---|---|---|---|---|
| **Anthropic Claude Agent SDK** | Agent invocation / `Task` (subagent dispatch) | implicit (`initialPrompt`) | partial (`disallowedTools`, `maxTurns`) | partial (`task_budget` for tokens, recent) | none | none | hooks (`PreToolUse`, `PostToolUse`, `Stop`, `SubagentStart`, `Notification`, `PermissionRequest`) | none (PermissionRequest is a gate, not a budget-driven escalation) |
| **Letta** | Agent + perpetual thread; `run` per invocation; `step` per LLM pass | implicit (memory blocks, system prompt) | implicit (tool gating) | none | none | none | persistent message store; no first-class subscriber API | none |
| **LangChain / LangGraph** | `thread` (persistent state) + `run` (graph execution) + `super-step` (atomic checkpoint unit) | implicit (graph-defined) | implicit (graph nodes) | none (token tracking is per-LLM-call, not per-thread) | partial (time-travel: replay from any checkpoint) | none formalised (the user's graph defines completion) | hooks via callbacks; checkpointer subscribes implicitly | interrupts (`interrupt_before`, `interrupt_after`) but not condition-driven escalation |
| **LlamaIndex Workflows** | `Workflow` (event-driven step graph) | implicit (StartEvent → StopEvent) | implicit (typed events) | none | none | typed `StopEvent` payload | step decorators emit events; event bus is the observer surface | none |

**Verdicts (one paragraph each):**

- **Anthropic Agent SDK** — closest to pOS in spirit (Claude-native, hook-driven). The recently added `task_budget` is the only first-class budget primitive in the surveyed set. But three of the seven fields (reversibility, success criteria, observers as a typed list) are absent; the SDK's "task" is an in-process unit, not a durable, observable, externally-addressable scope. Reuse direction: the **hook event vocabulary** (PreToolUse / PostToolUse / Stop / Notification / PermissionRequest) is a strong model for scope lifecycle event names.
- **Letta** — strong on memory persistence and threading (perpetual thread = state continuity across invocations); weak on every other field. The `run` ↔ `step` distinction is useful: a single user input produces one `run` containing many LLM `steps`. pOS scope-of-work is closer to `run` granularity than `step`. Reuse direction: the **run-contains-many-steps** hierarchy informs how scopes contain work units without becoming the work-unit themselves.
- **LangGraph** — by far the most mature on persistence and durable execution (checkpointer protocol, super-step atomicity, time-travel). Reuse direction: the **`BaseCheckpointSaver` shape** (put / put_writes / get_tuple / list) is a model for scope persistence; the **super-step boundary as the atomic checkpoint unit** is a model for when scope state hits durable storage; the **thread / run / super-step hierarchy** is a model for nesting. None of LangGraph's primitives carry a budget, reversibility class, or escalation trigger natively, but its lifecycle skeleton transfers cleanly.
- **LlamaIndex Workflows** — pure event-driven, async-first; thin and elegant. Reuse direction: the **typed-event design** (every state change is an event with a Pydantic-style schema) is a model for scope's observability emission. Not chosen as a base layer: too thin; pOS needs durability and budgets that Workflows leaves to the caller.

**No surveyed AI-harness library is designed around budgeted-observed-escalatable units of work.** The closest is the Anthropic SDK with `task_budget` plus the hook ecosystem, but it does not carry reversibility, success criteria, or escalation triggers as first-class fields. This confirms the spec's framing: scope-of-work as *defined* in objectives v1.0 is a **novel primitive**, not a re-skin of an existing one.

### 1.2 Workflow engines

| Engine | Native unit | Reusable patterns for pOS |
|---|---|---|
| **Temporal** | `WorkflowExecution` + `Activity` + `ChildWorkflow` | Durable execution via event-history replay; `parent_close_policy` (TERMINATE / ABANDON / REQUEST_CANCEL) for parent-cancels-children semantics; **typed search attributes** for indexed querying of in-flight work; signal/query separation (signals mutate state, queries read it); test-time skipping |
| **Prefect 3** | `Flow` + `Task` (both have `run` instances with state) | Rich state-type vocabulary (Pending, Running, Completed, Failed, Crashed, Cancelling, Cancelled, Paused, Suspended, Late) — the most expressive lifecycle vocabulary surveyed; **state-change hooks** with `(flow, run, state)` signatures; final-state derivation rule (any FAILED in returned iterable → run is FAILED) |
| **Dagster** | `Op` / `Asset` / `Run` | Structured **event log** as first-class primitive (every op yields events; events are typed, queryable, replayable); **AssetObservation** and **ExpectationResult** events are useful precedents for scope-emitted "I observed X" / "I checked Y" records |
| **Airflow** | `DAG` + `TaskInstance` + `XCom` | Task-instance state vocabulary (running, success, failed, skipped, up_for_retry, queued, scheduled, removed); XCom = inter-task small-payload state passing; trigger rules for downstream-on-upstream conditions |

**Patterns worth reusing across all four:**

1. **State as first-class.** Every engine treats lifecycle state as a typed enumeration with explicit transition rules — not a free-text "status" string. This survives across language ecosystems for a reason.
2. **Durable event log as substrate.** Temporal's event history, Dagster's event log, and Prefect's run-state history all treat *the sequence of events* as the source of truth, with current state as a derivation. This is event-sourcing in workflow clothes; it gives replay, time-travel, and audit for free. Memory's adaptation #3 (observability emission adapter) is already designed to publish in this shape.
3. **Parent-close policies.** Temporal's three-way policy (TERMINATE / ABANDON / REQUEST_CANCEL) is the cleanest model for what should happen to children when a parent ends. The pOS spec needs the same axis — the cascade-halt question is not "do children stop" but "what *kind* of stop."
4. **Typed search attributes.** Temporal's `TypedSearchAttributes` lets the engine index in-flight workflows by user-defined attributes (CustomerId, etc.). pOS needs the same — querying scopes by owner persona, by goal, by budget-remaining, by reversibility class — and this is a clean abstraction.
5. **Hooks at lifecycle boundaries.** Prefect's `(flow, run, state)` and `(task, run, state)` hook signatures are the cleanest API for observers to register against state transitions.

### 1.3 Is there an AI-harness library designed for budgeted-observed-escalatable units of work?

**No.** The closest claimants:

- **Anthropic Agent SDK + `task_budget` + hooks** — partial; lacks reversibility, success criteria, observer-typed-list, escalation triggers. Could be **wrapped** (build the seven-field primitive on top of SDK invocations) but cannot **be** the primitive.
- **AgentBudget / agent-cost-guardrails** — narrow tools that patch SDK calls to enforce token ceilings. Useful as building blocks for the budget enforcement mechanism (§4 below), not as a scope primitive.

**Conclusion:** the seven-field scope-of-work primitive does not exist off-the-shelf. pOS must build it. The build is informed by the survey above — borrow the durable-event-log substrate from Temporal/Dagster, the state vocabulary from Prefect, the typed-search-attributes pattern from Temporal, the parent-close-policy axis from Temporal, the hook signatures from Prefect, the run/step hierarchy from Letta, the typed-event schema discipline from LlamaIndex, and the Claude-native hook vocabulary from the Anthropic SDK.

---

## 2 — Recommended design shape

Each recommendation lists alternatives considered, the rationale for the chosen direction, and the spec acceptance criterion it serves.

### 2.1 Lifecycle model

**Recommendation:** **event-sourced finite state machine.** A canonical state enum drives transitions; the source of truth is an append-only event log; current state is a derived projection.

**State enum (proposed):** `proposed → active → {paused → active}* → {completed | failed | cancelled | escalated}`. `escalated` is a terminal-pending-resolution state (the scope hit an escalation trigger; an observer must resolve before it can move to a final terminal state).

**Alternatives considered:**

- *Plain FSM with state column.* Cheaper at write time; loses replay, audit, time-travel. Spec criterion v1.0 observability ("user can replay a session's decisions") and v1.1 R1 (semantic round-trip on upgrade) both want history-as-source-of-truth — plain FSM trades durable history for write speed pOS does not need.
- *Actor model with supervisor.* Overkill for the cardinality (a personal OS at single-user scale; estimated <10⁴ scopes/year per the memory-system cost baseline of ~3,000 events/year). Adds asyncio complexity that does not pay back.
- *Pure event-sourcing with no state enum.* All state derived on read. Slow for hot reads; harder to reason about. The hybrid — events as truth, state as cached projection — is the standard event-sourcing pattern (per the `eventsourcing` Python library docs) and what every workflow engine surveyed actually does under the hood.

**Spec coverage:**
- Objectives spec v1.0 — "every autonomous action produces an auditable record" → satisfied by event-log substrate.
- v1.0 — "the user can replay a session's decisions" → events replay deterministically.
- v1.0 — self-correction / four-part loop ("name failure class, fix instance, diagnose cause, structural remedy") → failure events carry typed `failure_class` field; correction events reference the failure they address.
- v1.1 R1 — semantic round-trip on upgrade → upgrade harness replays events pre/post-upgrade; drift report against declared threshold (re-uses the same probe pattern memory adopted).
- v1.0 reversibility — every state transition is reversibly addressable (replay back to any prior checkpoint).

### 2.2 Concurrency and hierarchy model

**Recommendation:** **strict tree of scopes with declared parent-close policy per child.** Multiple children may run in parallel under one parent. A child scope's outcome propagates to its parent as an event the parent's observers see. Parent cancellation respects each child's declared policy: `TERMINATE` (default), `ABANDON` (child runs to completion independently), `REQUEST_CANCEL` (parent sends a cancel signal; child's cleanup hooks run).

**Why a tree, not a graph:** the spec's hierarchical objective model (objectives decompose into child/grandchild objectives, each tracing to a parent) is a tree. Scope-of-work mirrors objective hierarchy. A DAG of scopes (where one scope has multiple parents) is a YAGNI violation — the spec does not require it and no surveyed system needs it for the personal-OS cardinality.

**Concurrency primitive:** Python `asyncio.TaskGroup` for in-process parallel children (Python 3.11+ structured concurrency: if a child raises, siblings are cancelled, exceptions wrapped in `ExceptionGroup`). Cross-process scopes (a scope dispatched to a long-running background worker) are addressed by the durability substrate (§2.4) — the parent does not hold an in-memory handle; it observes the child via the event log.

**Alternatives considered:**

- *Flat scope list with pointer-to-parent.* Simpler schema; loses cascade semantics. Each cascade operation re-walks the pointer graph at runtime — fine until cardinality hits ~10⁴ scopes, painful after. Tree-with-explicit-children avoids this without adding meaningful complexity.
- *Graph of dependencies (Airflow-style DAG).* Needed only if scopes have many-to-many dependencies. The spec's objective tree is one-to-many. YAGNI.
- *Single global scope queue with priority.* Discards hierarchy. Spec acceptance ("alignment is re-checked at every scope boundary") requires the parent-child relationship to be addressable.

**Spec coverage:**
- v1.0 objective hierarchy — scope tree mirrors objective tree; alignment check at every boundary.
- v1.0 / v1.1 self-correction — cascade halt: when a parent is cancelled mid-execution due to a discovered correctness violation, all children's parent-close policies fire deterministically. (Prime rule 5 — running task that is wrong must be stopped.)

### 2.3 Persistence substrate

**Recommendation:** **SQLite in WAL mode** as the primary substrate, with the schema modelled as event-sourcing — one append-only `scope_events` table plus one cached `scope_state` projection table maintained by a deterministic projector. Use `pyeventsourcing` v9.x as the library if its `SQLiteApplication` shape fits cleanly; otherwise hand-rolled with the same shape (the substrate is small enough to own).

**Why SQLite:**

- **Durable** (ACID with `synchronous=FULL` + WAL).
- **Embedded** — no network dependency; survives laptop reboot; aligns with pOS's local-first posture (same posture as memory's Kuzu choice).
- **WAL mode** — readers don't block writers; a 10× concurrency improvement over default mode for the read-heavy workload scopes will see (the primary persona reads scope state on every turn; writes are bursty).
- **Python-native** via stdlib `sqlite3`; no extra dependency.
- **Survives session restart, system restart, Claude outage** — file persists; on startup the projector reconstructs current state from events. (Spec graceful-degradation criterion: "simulated one-hour Claude outage does not corrupt in-flight scope state.")
- **Snapshot-friendly** — file copy = snapshot, satisfying the upgrade-fidelity reversibility clause (v1.1 R1 substrate-level snapshot).

**Alternatives considered and rejected:**

- **Graphiti on Kuzu (reuse memory's substrate).** Tempting (zero new infrastructure, scopes-as-entities in the knowledge graph). Rejected because: (a) couples scope-of-work durability to the memory subsystem's release cadence — a memory upgrade could break scope state, violating Prime rule 14 (prefer reversible) and the "memory is buildable independently" principle; (b) Graphiti's bitemporal model is rich for *facts about the world over time* but a poor fit for *operational state of a process*; (c) the spec's semantic round-trip test (R1) is for *knowledge*, not for *runtime state* — different test design. The right boundary is: scope **events emit** to the memory system as facts (e.g. "scope X completed at T with outcome Y" becomes a memory episode), and scope **runtime state lives** in its own substrate. One-way emission, not shared substrate.
- **Append-only JSONL log + JSON index.** What current pOS does. Light, but loses queryability — listing all scopes by owner persona requires a full-file scan. SQLite gives indexed queries free; for the same complexity budget the stronger substrate is the obvious win.
- **Embedded key-value store (RocksDB, LMDB).** Faster point reads; worse query story; no SQL ergonomics. Wrong tool for queryable runtime state.
- **Pickled Python data files.** Not durable across schema changes; not queryable; fragile. Rejected on first principles.
- **PostgreSQL.** Network dependency; overkill for single-user scale; violates local-first.

**Schema sketch (illustrative, not prescriptive):**

```
scope_events:
  event_id PRIMARY KEY  -- monotonic, used as "checkpoint id" analog to LangGraph
  scope_id NOT NULL
  parent_scope_id        -- NULL for root scopes
  event_type NOT NULL    -- 'created' | 'state_changed' | 'budget_debited' | 'observer_added' | 'escalation_triggered' | 'success_criterion_evaluated' | ...
  event_data JSON        -- validated by Pydantic discriminated-union schema
  created_at NOT NULL
  emitted_otel_span_id   -- for cross-correlation with the observability stream
  INDEX (scope_id, event_id)
  INDEX (parent_scope_id, event_id)

scope_state:               -- cached projection; rebuildable from scope_events alone
  scope_id PRIMARY KEY
  state                    -- proposed | active | paused | completed | failed | cancelled | escalated
  goal_text
  reversibility_class      -- fully_reversible | compensatable | irreversible
  budget_time_remaining_seconds
  budget_tokens_remaining
  budget_money_remaining_cents
  parent_scope_id
  owner_persona
  current_state_event_id   -- pointer back to the event that established current state
  -- additional indexed search attributes (Temporal-style); discriminated by tag
  INDEX (state)
  INDEX (owner_persona, state)
  INDEX (parent_scope_id)
```

The `scope_state` table is **a cache, not the source of truth**. It can be dropped and rebuilt from `scope_events`. This is what makes upgrades safe (R1): pre-upgrade event log is replayed post-upgrade by the new projector; if the reconstructed projection drifts from the pre-upgrade snapshot beyond the declared threshold, the upgrade fails.

**Spec coverage:**
- v1.0 session-resilience — survives restart (file persists; projector rebuilds on startup).
- v1.0 graceful degradation — Claude outage does not corrupt state (no LLM in the substrate write path).
- v1.0 observability — every action audited; replay-capable.
- v1.1 R1 — semantic round-trip + substrate-level snapshot (file copy pre-upgrade).

### 2.4 Budget enforcement

**Recommendation:** **hybrid debit model.** Three budget axes (time, tokens, money) tracked independently. Each axis has its own debit mechanism:

- **Time budget** — wall-clock from `state == active` entry; checked by a poll on every state transition and on every event emission, plus a heartbeat poll at a configurable interval (default 30s) for long-running scopes that sit idle in `active`.
- **Token budget** — per-LLM-call debit. The LLM client wrapper (separate component, future) reports `(input_tokens, output_tokens, prompt_name)` to the active scope after each call. The scope projector debits the budget atomically with the event write. Per-prompt-name aggregation (v1.1 R12) is a derived view on the event log — no separate write path.
- **Money budget** — derived from the token budget by a configurable per-model rate table (e.g. Sonnet input cents/Mtok, Opus output cents/Mtok). Updated when the token budget is debited. Money budget is the user-facing expression; tokens are the engineering reality.

**On budget exhaustion** — the spec answer to question 7 is **scope-dependent**, declared at scope creation time as a `budget_exhaustion_policy`:

- `halt_and_signal` (default, conservative) — scope transitions to `escalated`; an `escalation_triggered` event fires with reason `budget_exhausted`; observers are notified.
- `throttle` — scope pauses (state `paused`); no new LLM calls dispatched until an observer resumes or extends the budget.
- `request_extension` — scope emits an escalation but continues running until the observer responds with `granted` (resume with new budget) or `denied` (transition to `failed`). Bounded by a hard wall-clock timeout to prevent indefinite limbo.

The default is `halt_and_signal` because it is the only policy that fails-safe — the other two require an observer to be present and responsive, which the system cannot guarantee at all times.

**Cooperation with future cost-governance component:** the primitive emits `budget_debited` events to the observability stream in OTel format (using `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, plus a custom `pos.scope.budget.*` attribute namespace for the three axes and the policy). A future cost-governance component subscribes to these emissions and aggregates system-wide. The scope primitive does not import, reference, or assume the existence of any cost-governance API. (Spec A1.)

**Why per-LLM-call debit (and not poll-based metering or external rate-limiter):**

- **Per-LLM-call debit** — accurate; aligns with Anthropic's reported token counts in API responses (free, exact); event-sourced cleanly (one event per debit). Best for accuracy and auditability.
- **Poll-based metering** — necessary fallback only if the LLM call path is opaque (it is not — Claude returns token counts).
- **External rate-limiter** — a system-wide concern (different component); not the scope primitive's job. The scope primitive enforces *per-scope* budgets; the rate-limiter enforces *cross-scope* throttling.

**Spec coverage:**
- v1.0 cost governance — every scope declares a budget at creation; missing budget rejects creation.
- v1.0 — throttling activates at a declared threshold below the ceiling and produces a notification before the ceiling is reached → the `throttle` policy handles this; the `escalation_triggered` event at the threshold is the notification surface.
- v1.1 R12 — per-prompt-type aggregation queryable from the event log.
- v1.0 reversibility — budget debit events are reversible (a refund event reverses a debit; useful when an LLM call fails after the debit was recorded).

### 2.5 Observers and escalation triggers

**Recommendation:** **declarative trigger registry + pyee-style event emitter.** Observers register against scope events; triggers are declarative predicates evaluated on each event.

**Observer mechanism:**

An observer is `(observer_id, scope_id, event_filter, callback)`. The event filter is a Pydantic-discriminated-union pattern (event_type plus optional attribute predicates). The callback is async; it receives the event payload and the current scope projection.

**Library candidate:** `pyee` (specifically `AsyncIOEventEmitter`) is the closest off-the-shelf fit — Node-style EventEmitter with native asyncio integration. Alternative: `bubus` (production event bus from browser-use, with WAL persistence and parent-event tracking — possibly over-featured for pOS scope; flagged as a prototype-time choice). Alternative: hand-rolled around `asyncio.Queue` per observer (~30 lines; gives full control). Recommendation order: `pyee` > hand-rolled > `bubus`.

**Trigger declaration:**

A trigger is `(trigger_id, scope_id, condition, action)`. Condition is a typed predicate (Pydantic discriminated union) — examples:

- `BudgetThresholdCondition(axis='tokens', op='lt', value=10000)` — fires when tokens-remaining falls below 10k.
- `TimeElapsedCondition(seconds=3600)` — fires after one hour of `active` time.
- `EventTypeCondition(event_type='child_failed', scope_id_pattern='descendant')` — fires when any descendant fails.
- `SuccessCriterionCondition(criterion_id='X', evaluation='not_yet_met')` — fires when an evaluation event reports the criterion has not been satisfied after a configured number of attempts.

Action is `escalate(reason)` (transition to `escalated`, notify observers), `pause()`, `notify(message)`, or a custom callback (future-extension surface).

**Why declarative not procedural:** spec criterion v1.0 self-correction "every failure record contains an immediate-fix field" requires triggers to be inspectable and replayable. A declarative trigger is part of the scope's persisted state; a closure-based trigger is not.

**Why no pub-sub broker (Redis, RabbitMQ):** YAGNI for single-process single-user scale. The event emitter lives in-process; for cross-process observers (a future dashboard, a future Telegram notifier), the durable event log itself is the queue — consumers tail the SQLite events table by `event_id > last_seen` (this is what Dagster does; it works at this cardinality).

**Observer list mutability:** observers are added/removed via events (`observer_added`, `observer_removed`) — itself part of the audit trail. The scope can declare an immutable observer at creation (e.g. the dispatching persona is always an observer); it can add additional observers mid-flight.

**Spec coverage:**
- v1.0 spec — scope declares observers and escalation triggers as fields → both are first-class, persisted, replayable, auditable.
- v1.0 safety layer — "always-ask" actions and irreversible-blast-radius gates → implemented as triggers with `action=escalate` and a high-priority observer mapping (the primary persona).
- v1.0 self-correction — escalation triggers as the formalised mechanism for the four-part loop's class-closure step.

### 2.6 Observability emission

**Recommendation:** **OpenTelemetry-native, GenAI semantic conventions where they fit, custom `pos.scope.*` namespace where they don't.**

**Span structure:**

- One **invoke_scope** span per scope from `state == active` entry to terminal state. Span kind `INTERNAL`. Attributes use `gen_ai.agent.name` (= owner persona handle), `gen_ai.agent.id` (= scope_id), `gen_ai.agent.description` (= goal text), plus pOS-namespaced attributes:
  - `pos.scope.id`, `pos.scope.parent_id`, `pos.scope.reversibility_class`
  - `pos.scope.budget.time.remaining_seconds`, `pos.scope.budget.tokens.remaining`, `pos.scope.budget.money.remaining_cents`
  - `pos.scope.success_criteria.count`, `pos.scope.success_criteria.met`
- One **child** span per LLM call (using OTel GenAI's `chat {model}` span shape) parented to the invoke_scope span. Token-usage attributes use the standard `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`.
- **Span events** mark scope lifecycle transitions inside the parent span: `scope.state_changed`, `scope.budget_debited`, `scope.escalation_triggered`, `scope.success_criterion_evaluated`. Attributes carry the typed event payload.

**Why OTel:** spec v1.1 R11 — "pOS observability exposes OpenTelemetry as the internal-operation trace format." The GenAI semantic conventions cover the agent-invocation case directly; the scope-specific custom attributes extend it.

**Why a custom `pos.scope.*` namespace and not pure GenAI:** the GenAI conventions do not yet define attributes for budget, reversibility, escalation, or success criteria (verified against the current spec at `opentelemetry.io/docs/specs/semconv/gen-ai/`). pOS contributes its own namespace cleanly; if the GenAI WG later defines equivalents, mapping is straightforward.

**Persistence of the OTel stream:** the scope primitive emits OTel; a downstream exporter writes to wherever the future observability consumer wants (file, Jaeger, Honeycomb, etc.). For local-first defaults, the proposal layer should choose an OTLP-to-file exporter. The scope primitive does not own the exporter; it owns the emission. (A1.)

**Spec coverage:**
- v1.1 R11 — OTel as internal-operation trace format.
- v1.0 observability — every autonomous action writes a record; sample reconstructs from records alone.
- v1.1 R12 — per-prompt-type aggregation; the `gen_ai.request.model` + custom `pos.prompt.name` attributes give the cost-governance component what it needs.

### 2.7 API surface

**Recommendation:** **async Python API with a small synchronous compatibility layer.** Pydantic models for all schemas. The API is intentionally thin — just enough to create, observe, transition, and query.

**Core API (illustrative, not prescriptive):**

```
async def create_scope(spec: ScopeSpec, parent: ScopeId | None = None) -> ScopeHandle: ...
async def activate(scope: ScopeId) -> None: ...
async def pause(scope: ScopeId, reason: str) -> None: ...
async def resume(scope: ScopeId) -> None: ...
async def complete(scope: ScopeId, outcome: ScopeOutcome) -> None: ...
async def fail(scope: ScopeId, failure: ScopeFailure) -> None: ...
async def cancel(scope: ScopeId, *, cascade: ParentClosePolicy = TERMINATE) -> CancellationReport: ...
async def debit_budget(scope: ScopeId, *, tokens: TokenUsage | None = None, money_cents: int | None = None) -> BudgetState: ...
async def add_observer(scope: ScopeId, observer: Observer) -> None: ...
async def add_trigger(scope: ScopeId, trigger: Trigger) -> None: ...
async def get_scope(scope: ScopeId) -> ScopeProjection: ...
async def list_scopes(*, where: ScopeQuery) -> list[ScopeProjection]: ...
async def stream_events(scope: ScopeId, *, since: EventId | None = None) -> AsyncIterator[ScopeEvent]: ...
```

`ScopeSpec` is a Pydantic model with the seven required fields (goal, constraints, budget, reversibility_class, success_criteria, observers, escalation_triggers). Missing any of the seven raises `ValidationError` at construction → satisfies the spec's "missing any field rejects scope creation" criterion deterministically, with no runtime branch.

**Async-first because:** Graphiti is async (memory's substrate); the Anthropic SDK is async; LlamaIndex Workflows is async; LangGraph supports both. Async-first matches every consumer pOS will integrate with. A sync wrapper (`asyncio.run`-based) covers callers from sync contexts (CLI scripts, test fixtures).

**Composition with Graphiti's async patterns:** scope events emit to memory via `memory.ingest(scope_id=..., episode=...)` — the same async call shape memory already exposes. No new coupling; no shared substrate.

**Why not synchronous-first:** would force `asyncio.run` boundaries everywhere consumers are themselves async. Wrong default.

**Spec coverage:**
- v1.0 spec — "scope of work carries all seven declared fields … missing any field rejects scope creation." Schema validation at the API boundary, deterministic.
- v1.0 spec — "scope can be defined, created, completed, extended, maintained" → API verbs are complete (create, activate, complete, [extend via add_observer / add_trigger / debit_budget refund / new child], pause/resume = maintain).

---

## 3 — Acceptance-criterion coverage

This table maps every relevant acceptance criterion from spec v1.0 + v1.1 (the bits scope-of-work must honour) to the design piece that delivers it.

| Spec source | Criterion | Design piece |
|---|---|---|
| v1.0 Core primitives | Scope carries all seven fields | §2.7 — Pydantic schema validation; missing-field rejection at construction |
| v1.0 Core primitives | Objective carries parentage, measurability, time-bound | (Out of scope — objective tracker is a separate component. Scope provides parent_scope_id and success_criteria; the tracker layers on top.) |
| v1.0 Core primitives | Primary persona carries three responsibilities | (Out of scope — persona loader is a separate component. Scope provides `owner_persona` field as the binding.) |
| v1.0 Session-resilience | Work queued before session ends completes after restart | §2.3 — SQLite WAL substrate persists; on startup the projector rebuilds state and the scheduler resumes `active` scopes |
| v1.0 Session-resilience | Tasks survive system restart | §2.3 — same |
| v1.0 Session-resilience | Process killed mid-run self-heals or marks failed | §2.1 — startup recovery: any scope in `active` with no recent heartbeat transitions to `failed` with reason `process_died` (recoverable from event log) |
| v1.0 Session-resilience | Compaction events preserve persona/work/decisions | (Compaction is a session-mode concern; scope state lives outside the LLM context window — not affected by compaction at all. This is a strength of the externalised-state design.) |
| v1.0 Graceful degradation | Claude outage does not corrupt in-flight scope state | §2.3 — substrate has no Claude dependency; §2.4 — token debits only fire on successful API responses; §2.5 — escalation trigger `EventTypeCondition('llm_unavailable')` can be registered for safe-mode behaviour |
| v1.0 Self-upgrade | Active sessions continue without restart after upgrade | §2.3 — events are append-only; new projector reads old events; in-flight scopes resume |
| v1.0 Self-upgrade | All in-flight tasks preserved with correct state | §2.3 — projection rebuild deterministic from event log |
| v1.1 R1 | Semantic round-trip on upgrade + substrate snapshot | §2.3 — event-log replay is the round-trip; SQLite file copy is the substrate snapshot |
| v1.0 Cost governance | Every scope declares budget at creation; missing budget rejects | §2.7 — Pydantic schema; budget is required field |
| v1.0 Cost governance | Throttling at threshold below ceiling; user notification before ceiling | §2.4 — `throttle` exhaustion policy; declarative `BudgetThresholdCondition` triggers fire above the ceiling |
| v1.1 R12 | Per-prompt-type cost aggregation queryable | §2.4 + §2.6 — events carry `prompt_name`; aggregation is a SQL view on `scope_events` |
| v1.0 Observability | Auditable record per autonomous action | §2.3 + §2.6 — every state transition writes to event log AND emits OTel span/event |
| v1.0 Observability | Sample action reconstructible from record alone | §2.3 — event payload schema (Pydantic) carries actor, timestamp, inputs, outputs; replay from `event_id` reconstructs |
| v1.1 R11 | OTel as internal-operation trace format | §2.6 — OTel-native emission with GenAI semantic conventions plus `pos.scope.*` namespace |
| v1.0 Reversibility | Class declared per scope | §2.7 — `reversibility_class` is a required field |
| v1.0 Reversibility | Reversible preferred over irreversible | (Out of scope at the primitive — this is a *selection* policy applied by the persona/dispatcher when proposing scopes. Scope provides the field; the chooser uses it.) |
| v1.0 Reversibility | Irreversible escalated | §2.5 — declarative trigger: `ReversibilityCondition(class='irreversible') → escalate` is a default trigger seeded at scope creation when class is irreversible |
| v1.0 Safety | Kill switches at scope/session/system level, bounded stop time | §2.7 — `cancel(scope, cascade=TERMINATE)` is the scope-level kill; cascade halt walks descendants; bounded by Python `asyncio` cancellation semantics |
| v1.0 Safety | "Always-ask" list enforced at deterministic layer | §2.5 — declarative trigger registry: an "always-ask" condition is a trigger added to every scope at creation by the safety component (when built); the scope primitive supplies the trigger-registration API |
| v1.0 Self-correction | Every failure record contains immediate-fix field | §2.3 — `ScopeFailure` schema includes `immediate_fix_event_id`; failure events without it fail validation at construction |
| v1.0 Self-correction | Every completed scope runs outcome-vs-objective check | §2.5 — declarative trigger seeded at completion: `SuccessCriterionCondition` fires evaluation events; check is recorded as part of the event log |
| v1.0 Objective-based | Alignment re-checked at every scope boundary | §2.5 — trigger fires `success_criterion_evaluated` event on every state transition; scope cannot transition to `completed` without all criteria evaluated |
| v1.0 Objective-based | Parentage & traceability | §2.2 — `parent_scope_id` is a first-class field; tree query is one indexed lookup |

**Halt signals raised:** **none.** Every spec acceptance criterion in the "Core primitives" section and every dependent v1.1 revision (R1, R11, R12) is satisfiable by the design above. Two criteria (reversibility-preference selection, the four-part self-correction loop's class-closure step) are noted as *partially out of primitive scope* — the primitive supplies the field/trigger surface; the *policy* of how those fields drive selection lives in the future safety/correction layer. This is consistent with the spec's architectural separation and the A1 correction (consumers are future work).

---

## 4 — Memory-mock retirement path

Memory's `MockScopeSource` (at `pos-v2/memory-system/src/scope.py`) defines a `ScopeSource` protocol with three methods:

```
def get_scope(self, scope_id: str) -> ScopeRecord | None
def register_scope(self, scope_id: str, **metadata) -> ScopeRecord
def list_scopes(self) -> list[ScopeRecord]
```

`ScopeRecord` carries `scope_id`, `name`, `created_at`, `description?`, `metadata: dict`.

Memory's two consumption points (per the mock's docstring and `MemoryAPI` shape):

1. **`MemoryAPI.ingest(scope_id=...)`** — needs to translate `scope_id` to a Graphiti `group_id` for namespace partitioning. Requires only that the scope exists; it does not read scope state, budget, observers, or any of the seven fields.
2. **`MemoryAPI.search(scope_id=...)`** — same: needs the scope_id as a partition key for filtered retrieval.

**The minimum interface memory needs from the real primitive:**

```
async def get_scope(scope_id: ScopeId) -> ScopeProjection | None
async def list_scopes() -> list[ScopeProjection]
```

(`register_scope` is not needed — memory does not create scopes; the dispatching layer does. The mock's `register_scope` exists only to fabricate scopes for tests where no real primitive runs. With the real primitive, memory's `ensure(scope_id)` mock-only helper drops out.)

`ScopeProjection` is the §2.3 cached-projection record. Memory needs a strict subset of its fields: `scope_id`, `owner_persona` (already in the projection; useful as a cross-reference field on episodes), and presence/absence-as-boolean. Memory does not need budget, reversibility, observers, triggers, or event-log access from the primitive.

**Retirement path (concrete integration test the proposal must include):**

1. **Adapter shim.** Implement a `ScopeSource` adapter (in pOS, not in memory) that wraps the real primitive's `get_scope` and `list_scopes` and exposes the memory-side protocol. Ten lines of glue. The wrapping is an adapter so memory's protocol stays stable across primitive evolution.
2. **Wiring change.** `MemoryAPI`'s constructor takes a `ScopeSource` by injection (already true per the mock's docstring: "MemoryAPI takes a ScopeSource by injection, so the change is one line at wiring time"). One line: replace `MockScopeSource()` with `RealScopeSourceAdapter(scope_runtime)`.
3. **Acceptance test (the integration assertion):**
   - Create a scope via the real primitive's `create_scope(...)`.
   - Memory ingests an episode with `scope_id=<that scope_id>`. Episode is stored in the Kuzu group corresponding to that scope.
   - Memory searches with `scope_id=<that scope_id>`. The episode is returned.
   - Memory's mock-only `auto_register` and `ensure(scope_id)` paths are exercised against the real primitive: an unknown scope_id is rejected (the mock's "auto_register=False" branch becomes the production behaviour). This is a *strengthening* of the contract memory was already prepared for — line 160 of `scope.py`: "the real primitive will reject unknown scopes instead of auto-registering."
4. **Mock removal.** After the integration test passes, `MockScopeSource` and the `data/scope_registry.json` file move to a test-only fixture location (or are deleted entirely; the adapter test set replaces them).

**No memory-side code rewrite is required.** The mock was designed to make this exactly the one-line change it claims to be.

---

## 5 — Dependency map

### What scope-of-work depends on (at ship time)

**Nothing.** The primitive is shippable on its own. The substrate (SQLite stdlib + WAL) is in the Python standard library. The only external dependencies are well-maintained libraries:

- `pydantic` v2 — schema validation, discriminated unions for the typed event registry.
- `pyee` (or hand-rolled equivalent) — observer event emitter.
- `opentelemetry-api` + `opentelemetry-sdk` — observability emission.

Optional (for the proposal layer to choose):
- `pyeventsourcing` v9.x — if its `SQLiteApplication` shape fits cleanly. Otherwise the substrate is small enough to own.
- `python-statemachine` or `transitions` — if a library state machine is preferred over a hand-rolled enum + transition table. Both are well-maintained; the choice is ergonomic, not architectural.

### What depends on scope-of-work (consumers; all are future components)

| Consumer (named as spec objective, not current-pOS component) | Direction | What they consume |
|---|---|---|
| **Memory system** | one-way (memory reads scope identity) | `get_scope(scope_id)`, `list_scopes()` — minimum interface per §4 |
| **Objective tracker** | bidirectional | reads scope's success_criteria; writes evaluations as events scope subscribes to |
| **Primary persona loader** | one-way (persona reads scopes it owns) | `list_scopes(where=ScopeQuery(owner_persona=X))`, `get_scope(scope_id)` |
| **Observability consumer** | one-way (consumer subscribes to OTel emission) | OTel spans + events; subscribes to the OTel exporter the proposal chooses |
| **Cost governance** | one-way (cost reads scope budgets) | `list_scopes()` for system-wide aggregation; subscribes to `budget_debited` events |
| **Safety layer** | bidirectional | writes default triggers (always-ask, irreversible-escalate) into scopes at creation; reads escalation events |
| **Reversibility primitive** | bidirectional | reads `reversibility_class`; writes compensation actions as scope events |
| **Self-correction loop** | bidirectional | reads `failure` events; writes `correction` events linking back to failures |
| **Dispatch primitive** | bidirectional | creates scopes; writes process-of-arrival events into the scope's event log (per memory's adaptation #7) |
| **Channel-agnostic interaction (R13)** | one-way (channels surface scope events) | subscribes to escalation events; routes notifications |

The primitive **names its emission shape (OTel + custom `pos.scope.*` namespace) and its API surface (the §2.7 verbs)**. Every consumer is future work and is *not* a prerequisite for shipping scope-of-work.

---

## 6 — Complexity estimate

AI-time, honest, with surprises called out. Memory's adaptation layer was estimated at 120–180 minutes (proposal §"Complexity estimate"); this primitive is core-build-from-nothing, so the comparison anchor is "larger than memory's adaptation."

### Core build (well-understood)

| Slice | Estimate | Notes |
|---|---|---|
| Pydantic schemas (ScopeSpec, ScopeEvent discriminated union, all sub-schemas) | 15–25 min | Well-defined; 8–12 typed event classes |
| SQLite event log + projection table + projector | 20–40 min | Standard event-sourcing pattern; rebuilds on startup |
| FSM state transition table + validation | 10–15 min | Small enum; transition map is data, not code |
| Async API surface (the §2.7 verbs) | 30–50 min | Each verb is a thin wrapper; cancel/cascade is the longest |
| Observer registry + pyee integration | 15–25 min | If pyee fits cleanly; +20 min if hand-rolled |
| Trigger registry + declarative predicate evaluation | 25–40 min | Discriminated-union predicates; eval at every event emission |
| Budget enforcement (three axes + three exhaustion policies) | 25–40 min | The token-debit hot path needs care; refund semantics for failed LLM calls |
| OTel emission (spans, events, attributes) | 15–25 min | OTel SDK is verbose but mechanical |

**Subtotal core:** ~155–260 minutes.

### Tests and docs (must-ship)

| Slice | Estimate | Notes |
|---|---|---|
| Acceptance tests against every spec criterion in §3 | 60–100 min | One test per criterion; some share fixtures |
| Memory-mock retirement integration test (§4) | 20–30 min | The single named integration assertion |
| Bundled documentation (v1.1 R4) | 30–50 min | Architecture diagram, data-flow diagram, relationship map, prose |

**Subtotal tests/docs:** ~110–180 minutes.

### Surprises called out

1. **Cascade halt with cross-process scopes is the hardest single piece.** In-process children stop via `asyncio.TaskGroup` cleanly. A child running in a separate process (a long-running background dispatch) requires the cancel signal to propagate via the event log — the child polls for cancellation. This polling cadence is a tuning parameter; getting it wrong means slow cancellation. **Plan to prototype before final build.**
2. **Refund semantics for failed LLM calls.** A `budget_debited` event was written, then the LLM call failed at the network layer. The token debit needs reversal. This is solvable (`budget_refunded` event; projector handles both) but the failure path is the kind of thing easy to overlook in the happy-path implementation. Calls out a test the acceptance suite should include explicitly.
3. **Trigger evaluation cost on hot scopes.** Every event emission evaluates every registered trigger. For scopes with many triggers and many events, this could be O(events × triggers). Trivial at the personal-OS scale (single-user, ~10⁴ events/year), but worth a note: trigger evaluation should be indexed by event_type so most triggers short-circuit on the first attribute match.
4. **OTel exporter choice is the proposal's call, not the primitive's.** The primitive emits to whichever exporter is wired. Local-first default would be OTLP-to-file; a production deployment might switch to OTLP-to-Jaeger. The primitive does not care.

**Total AI-time estimate:** ~265–440 minutes (~4.5–7.5 hours of agent execution). This is meaningfully larger than memory's adaptation (120–180 min). The proposal-layer review should treat this as *core-build* not *adaptation* — the builder starts from nothing rather than wrapping an existing library.

---

## 7 — Open questions for prototyping

These are questions only a prototype can answer. Each is paired with the minimum prototype that resolves it.

### Q1 — Cross-process cascade-halt latency

**Question:** what is the actual latency for parent-cancel-propagates-to-child-process? Does the polling cadence affect user-perceived "snappy cancel"?

**Minimum prototype:** create a parent scope; spawn three child scopes, two in-process, one as a subprocess running a 30-second sleep loop with a 1-second cancel-poll. Cancel the parent. Measure time-to-cancel for each child. Tune the poll cadence to a value where worst-case cancel is under 2 seconds.

### Q2 — pyee vs hand-rolled emitter

**Question:** does pyee's `AsyncIOEventEmitter` integrate cleanly with the discriminated-union event schema, or does its dynamic-event-name model fight Pydantic's typing?

**Minimum prototype:** wire pyee against a 3-event-type scope; emit 1,000 events; verify type checking holds end-to-end. If it fights, hand-roll (~30 lines around `asyncio.Queue`).

### Q3 — pyeventsourcing fit

**Question:** does the `pyeventsourcing` library's `SQLiteApplication` fit cleanly enough to use as-is, or does its domain-driven-design framing add ceremony pOS does not need?

**Minimum prototype:** implement the `scope_events` table and projector both ways — bare `sqlite3` and `pyeventsourcing.SQLiteApplication`. Compare line counts, performance on a 10,000-event replay, and complexity of the upgrade-path code.

### Q4 — OTel exporter under offline conditions

**Question:** what does the OTel SDK do when the configured exporter (e.g. OTLP-over-HTTP) is unreachable? Does it block, drop, or queue? This matters for the graceful-degradation criterion.

**Minimum prototype:** configure OTLP-to-localhost-port-9999 (nothing listening); emit 100 spans; observe behaviour. Tune exporter to file-based fallback if blocking is observed. Local-first default likely makes this moot but the failure mode should be characterised.

### Q5 — Budget-debit projector contention

**Question:** when many scopes are active and many LLM calls are in-flight, does the projector become a write-contention point on the SQLite event log?

**Minimum prototype:** simulate 50 concurrent active scopes, each emitting one `budget_debited` event per second, for 60 seconds. Measure write throughput, p99 latency, and any "database is locked" errors. SQLite WAL should handle this trivially at this scale; the prototype confirms.

### Q6 — Pydantic discriminated-union performance on event replay

**Question:** how long does it take to replay 100,000 events through Pydantic-validated discriminated-union deserialisation?

**Minimum prototype:** populate a fixture with 100,000 events; replay; measure. If under 5 seconds, no concern. If slower, consider raw deserialisation for the hot replay path.

### Q7 — Trigger-eval indexing

**Question:** does indexing triggers by event_type meaningfully outperform linear scan at the cardinality scope-of-work will see?

**Minimum prototype:** synthetic 1,000-trigger scope (extreme upper bound); emit 1,000 events; measure both linear and indexed eval. If linear is fast enough at this scale (likely), do not over-engineer.

---

## 8 — Constraints satisfied (audit)

| Constraint from research plan | Status |
|---|---|
| Python-native | satisfied — every recommendation is a Python library or stdlib |
| Max-first; vendor-free outside Max | satisfied — primitive contains no LLM inference; no vendor dependency |
| Zero carryover from current pOS | satisfied — no reading of `ops/orchestrator/`; design derives from the surveyed external systems and the spec |
| ODD-compatible (every recommendation traces to a spec objective) | satisfied — §3 maps every design piece to a spec criterion |
| No code, no proposal, no brief | satisfied — this is a research document |
| Halt-on-deviation | not triggered — every spec acceptance criterion is satisfiable |

---

## 9 — Summary: the recommended design shape in one paragraph

A **seven-field Pydantic-validated scope** persisted as an **event-sourced finite state machine** in **SQLite WAL mode** (events are truth, projection is cache, both rebuildable from the event log alone), with a **strict tree of parent-child scopes** under Temporal-style **parent-close policies** (TERMINATE / ABANDON / REQUEST_CANCEL), **per-LLM-call token-debit budgets** along three axes (time / tokens / money) with three configurable exhaustion policies (halt-and-signal default; throttle; request-extension), **declarative trigger predicates** evaluated on every event emission with **pyee-backed observers** subscribed to typed event filters, **OTel-native observability emission** using GenAI semantic conventions plus a `pos.scope.*` custom namespace, and a **thin async Python API** whose schema-validation rejects scope creation when any of the seven fields is missing. Memory's `MockScopeSource` retires via a ten-line adapter shim; one line of wiring change. No spec acceptance criterion is unsatisfiable; no halt signals are raised; the primitive is shippable on its own with no consumer assumed. AI-time estimate: 265–440 minutes for the core build plus tests and bundled documentation.
