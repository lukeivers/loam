# Handoff Brief — Scope-of-Work Primitive

**Component:** Scope-of-Work Primitive
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-18 13:39 CDT, with three open questions resolved)
**Spec:** objectives spec v1.0 + v1.1 addendum (`docs/rebuild/spec/pos-v2-objectives-spec.md`)
**Predecessor artifacts:** `research-plan.md`, `research.md`, `proposal.md`

---

## Objective

Deliver a production-ready scope-of-work primitive for the new pOS. Build the eight deliverables D1–D8 from the proposal. The primitive ships standalone on the `pos-v2` branch; every downstream consumer (objective tracker, primary persona loader, observability aggregator, cost governance, safety layer, reversibility primitive) will subscribe to the primitive's emission and API surface when those components are built. When this component lands, memory's `MockScopeSource` retires via a 10-line adapter.

---

## Hard constraints

1. **Implementation language:** Python.
2. **Branch discipline:** `pos-v2` on the existing the existing workspace repo repository. No modifications to `main`. No modifications anywhere in the existing workspace outside the branch's `pos-v2` scope.
3. **Zero carryover from current pOS / the existing workspace.** No reading of `ops/orchestrator/`, existing task/workflow/job schemas, current-pOS Ruby code, or any workspace-specific content for design inspiration. All test fixtures are synthetic or extend the `memory-system` Aldermere world (already synthetic).
4. **Dependencies:** Python stdlib wherever possible (including `sqlite3`, `asyncio`, `dataclasses`, `uuid`). Permitted third-party: `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`. Any further dependency requires halt-and-signal — do not add without surfacing.
5. **Max-first.** No LLM inference inside the primitive itself is expected. If a design question surfaces a scenario where the primitive benefits from LLM inference (e.g. auto-generating escalation triggers from natural-language descriptions), that work uses Claude via Max.
6. **No personas.** pOS core ships zero persona content; this is framework code.
7. **No assumed downstream consumer (A1 correction).** The primitive emits OTel observability; no consumer is assumed to exist. Consumption is future work.
8. **Halt-on-deviation.** If any constraint here cannot be honoured, or the proposal's direction becomes untenable in the course of building, stop immediately, write what you found up to the halt, name the specific constraint or criterion, and return. Silent deviation is forbidden.
9. **Bundled documentation per v1.1 R4.** Ships alongside the code; prose, diagrams, relationship map.

## Three decisions the owner made at proposal approval (hard-coded into this brief)

- **Exhaustion policy default: request-extension** across all three budget axes (time / tokens / money). On budget exhaustion, the scope pauses in a `pending-extension-request` state, surfaces the request (event log entry + OTel event), and waits indefinitely for a response. The response API accepts `extend(scope_id, axis, amount)` or `reject(scope_id)`. Per-scope authors may override to halt-and-signal or throttle per axis at scope creation.
- **Parent-close policy default: TERMINATE.** Cancelling a parent immediately terminates active children. Per-scope authors may override to ABANDON or REQUEST_CANCEL.
- **Internal design priorities (cross-process cascade latency, trigger-eval cost, refund semantics) are folded into the full build** rather than prototyped separately. The builder detects problems mid-build and halts cleanly rather than running a separate prototyping round.

---

## Deliverables

Eight deliverables D1–D8 as named in the proposal. Each has an objective and acceptance criteria in objective terms. None prescribe implementation method, file layout, module names, or class structure.

### D1. Core scope primitive

**Objective:** the seven-field primitive exists in Python, Pydantic-validated at construction, with the lifecycle FSM and event-log persistence working in-process.
**Acceptance:**
- Creating a scope with any missing field raises.
- Creating with all seven fields succeeds.
- State transitions produce events in the event log.
- Replaying the event log reconstructs state identically.
- Lifecycle states: `proposed → active → {paused ↔ active}* → {completed | failed | cancelled | escalated}`.
- **Query surface for future background-work monitoring:** `list(filter)` supports filtering by state (e.g. return all scopes currently in `active | paused | escalated | pending-extension-request`); `get(scope_id)` returns current state including last-transition timestamp. This is the data surface a future background-work-monitor component will poll or subscribe to in order to keep the primary persona aware of in-flight work. The monitor itself is out of scope for this primitive; the query surface must be sufficient for it.

### D2. Budget ledger with extension-request default

**Objective:** three-axis budget (time / tokens / money) tracked via the event log; per-LLM-call token debit works; refund semantics land; extension-request default triggers on exhaustion.
**Acceptance:**
- Ingesting a synthetic LLM-call sequence produces accurate budget-remaining at any point.
- A refund event corrects a prior debit.
- The per-prompt-name SQL view returns per-prompt costs matching a hand-calculated ground truth.
- Exceeding any budget axis (with default policy) transitions the scope to `paused` with reason `pending-extension-request`, emits an extension-request event, and waits for response.
- `extend()` with a valid amount resumes the scope with the new budget; `reject()` transitions to `completed` (or `cancelled` if the scope had not produced a result).
- Per-scope override to halt-and-signal or throttle at scope creation works correctly per axis.

### D3. Observer and trigger system

**Objective:** observer subscription via `pyee.AsyncIOEventEmitter` and declarative escalation triggers via Pydantic discriminated-union predicates both work; observer-add and observer-remove are themselves events in the audit log.
**Acceptance:**
- An observer subscribed to a scope receives events on state transitions and debits.
- A declared `BudgetThreshold` trigger fires an `escalated` event when its threshold is crossed.
- A declared `TimeElapsed` trigger fires when wall-clock elapsed crosses its value.
- Trigger predicates `EventType`, `SuccessCriterion`, and `Reversibility` similarly fire on their declared conditions.
- Observer-add and observer-remove operations write events to the log.

### D4. Parent-child hierarchy with TERMINATE default

**Objective:** scopes can spawn child scopes; parent-close policies (TERMINATE / ABANDON / REQUEST_CANCEL) are honoured; cancellation cascades correctly.
**Acceptance:**
- Creating a child scope under a parent links them in the event log.
- Cancelling the parent under TERMINATE policy (default) cascades to active children within a bounded time.
- Under ABANDON, children continue; under REQUEST_CANCEL, children receive a cancel request they can honour or reject.
- `asyncio.TaskGroup` handles in-process children; event-log polling handles cross-process coordination.

### D5. OTel observability emission

**Objective:** scope lifecycle produces OTel spans and events using the GenAI semantic conventions (`gen_ai.agent.*`, `gen_ai.usage.*`) plus a `pos.scope.*` namespace for scope-specific attributes.
**Acceptance:**
- Starting a scope produces an `invoke_scope` INTERNAL span covering active duration.
- LLM calls (recorded via debit API) produce child `chat {model}` spans following GenAI convention.
- State transitions produce span events on the scope's span.
- Budget remaining, reversibility class, and escalation reason appear as `pos.scope.*` attributes.
- Extension-request events appear as OTel events; no consumer is required for emission to succeed.

### D6. Memory-mock retirement

**Objective:** the memory system's `MockScopeSource` is replaced by a real adapter against the primitive; memory continues to function without modification beyond the single wiring line.
**Acceptance:**
- A `RealScopeSourceAdapter` wraps the primitive to match memory's existing `ScopeSource` protocol (at `pos-v2/memory-system/src/scope.py`).
- `MemoryAPI` constructor accepts the adapter via a one-line change.
- An integration test creates a scope via the primitive, ingests memory under that scope_id, searches memory and finds the entry, and rejects an unknown scope_id with a clear error.
- No memory-side rewrite beyond the one wiring line.

### D7. Upgrade-fidelity test harness

**Objective:** the primitive's event log passes a semantic round-trip test across an upgrade (v1.1 R1).
**Acceptance:**
- A probe set of scope creations, transitions, and queries is captured pre-upgrade.
- The same probes are replayed post-upgrade.
- Output-equivalence is asserted; drift above a declared threshold fails the upgrade.
- Sqlite database snapshot preserves physical reversibility alongside the semantic test.

### D8. Bundled documentation

**Objective:** v1.1 R4 — human-readable documentation bundled with the primitive.
**Acceptance:**
- Prose explanation of what the primitive is and why.
- Architecture diagram (event-sourced FSM + event log + projection cache).
- Data-flow diagram for a representative scope lifecycle including LLM-call debits, an extension request, and an escalation.
- Relationship map showing what subscribes (memory now; future components: objective tracker, primary persona loader, observability aggregator, cost governance, safety layer, reversibility primitive, self-correction loop).
- One-page API reference covering the public surface.
- A non-technical reader can answer "what does this primitive do and how does it fit with the others" from the bundled docs alone.

---

## Dependencies carried forward

- **Hard dependencies:** none. The primitive is foundational.
- **Soft dependencies (emission, not required to ship):** observability aggregator, cost governance, safety layer, reversibility primitive, self-correction loop, objective tracker, primary persona loader. The primitive names its emission shape; consumers subscribe later.
- **Permitted dependencies:** Python stdlib, `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`. Any additional third-party dependency requires halt-and-signal.

---

## Halt conditions

Halt and return with a named failure signal if:

- Any hard constraint cannot be honoured.
- A spec acceptance criterion is discovered to be unsatisfiable under the approved direction — do not silently drop it.
- An additional third-party dependency appears necessary — surface it, do not add it unilaterally.
- Any ambiguity in this brief that would require inventing a constraint the owner has not specified.
- One of the three folded-in design priorities (cross-process cascade latency, trigger-eval cost, refund semantics) reveals the approved design is untenable.

Halts return control to the primary persona, who reviews with the owner; the proposal is adjusted as needed and execution resumes against the revised version.

---

## Return format

When the brief's scope is complete, return with:

1. A summary (≤600 words) covering: which deliverables D1–D8 completed, which halted (if any), which spec acceptance criteria now pass on the primitive (cite each by v1.0 behaviour or v1.1 revision number).
2. The bundled documentation at `scope-of-work/docs/`.
3. Confirmation that memory's `MockScopeSource` has been retired and the integration test passes.
4. Complexity outcome — AI-time actually taken vs. the proposal's 265–440-minute estimate.
5. Commits on `pos-v2`.
6. Any halt signals raised.
7. Recommended next action: declare scope-of-work component complete / flag remaining gaps for follow-up.

---

## What this brief is NOT

- Not a specification of file layout, module structure, package organisation, class hierarchy, or function signatures beyond the API surface sketched in the proposal.
- Not a step-by-step execution plan.
- Not a commitment to designing the adjacent primitives (objective tracker, primary persona loader, safety layer, etc.) — those have their own components and briefs.

---

## inferences recorded in this brief (flagged so the builder can challenge)

Three items below come from the primary persona's interpretation rather than verbatim from the owner. Marked here so the builder can surface objections:

- *Default extension-request timeout: indefinite.* the owner chose request-extension as the default but did not specify a timeout. inference recorded: the scope stays paused until answered, with per-scope override available for hard timeouts. If this reads wrong to the builder on encountering the detail, halt and flag.
- *Extension-request surfacing: event log + OTel event + pending-extension log file.* The proposal says the primitive "needs a user-notification channel" but no specific channel is designated, since the primary persona loader is not built. inference recorded: emit to event log, OTel events, and a local human-readable log file until the persona loader exists; the persona loader will subscribe to the file or event log when it lands.
- *Synthetic test fixtures may extend the memory-system Aldermere world* (same fabricated entities, same consultancy framing). the primary persona's inclination — reduces fixture-authoring overhead and keeps test data internally consistent across new-pOS components. If the builder thinks a separate synthetic world makes testing cleaner, halt and flag.
