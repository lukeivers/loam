# Research Plan — Reversibility Primitive

**Component:** Reversibility Primitive — promotes `ScopeSpec.reversibility_class` from a passive declaration to an active structural contract with compensation paths, rollback records, and telemetry for reversible-vs-irreversible path choice.
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for the reversibility primitive such that:

- A scope declared `irreversible` cannot activate without (a) a declared compensation path, or (b) an explicit dangerous-op approval from the safety layer. The refusal is deterministic.
- A scope with a compensation path persistently records the path, and on rollback, the path is invokable with access to the scope's committed state.
- `compensatable` is distinct from `fully_reversible` — compensatable means "we can compensate after the fact" (e.g. sent email then sent a correction); fully_reversible means "we can undo outright as if it hadn't happened."
- When the system has a choice between a reversible and irreversible path to the same declared objective, telemetry records which was chosen and why, and the default preference is reversible unless explicitly overridden.
- Integration with the sealed safety layer is clean: the reversibility primitive owns the compensation-path contract; the safety layer consumes the presence/absence of the contract as a gate signal.

## Starting position

- **Safety layer sealed** at `pos-v2/safety-layer/` (commit `45a15b9`). Reads `ScopeSpec.reversibility_class` from scope-of-work for the dangerous-op gate. Does not own the reversibility contract.
- **Scope-of-work exposes `ReversibilityClass` enum** with three values (`fully_reversible`, `compensatable`, `irreversible`). The field is present on `ScopeSpec`. What it does NOT currently have: a compensation-path declaration, a rollback-invocation surface, or a preference-signal for reversible-over-irreversible path choice.
- **Nine sealed components on `pos-v2`** (seven foundational + self-upgrade + safety). No amendments.
- **Python 3.13, `pos-v2` branch.** Permitted runtime deps: stdlib + pydantic + pyee + opentelemetry + PyYAML + duckdb. Test-only: pytest, pytest-asyncio.

## Questions the research must answer

### 1. Compensation path — the contract

1. What is a compensation path concretely? Candidates: (a) a named function symbol the workspace registers (string key in a framework registry → callable); (b) a full scope spec that activates on rollback; (c) a declarative YAML/pydantic record of actions to undo; (d) all three shapes supported.
2. Where is the compensation path declared? On the `ScopeSpec` at construction? In a sidecar table (like `ScopeObjectiveBinding` for objective tracker)? In the workspace's scope-authoring surface?
3. When the `irreversible` class is declared without a compensation path, what exactly happens at activation — does the safety layer's existing dangerous-op gate cover it, or does the reversibility primitive add its own pre-activation check?
4. How does the compensation path reference the scope's committed state? The scope-of-work event log preserves everything; the compensation path needs read access to the relevant subset.
5. What happens if the compensation path itself fails? Retry? Surface to user? Fall through to a degraded state?

### 2. Rollback invocation

6. What triggers rollback? Candidates: (a) scope explicitly calls `rollback()` during its own runtime (author-decided); (b) parent scope's cascade policy invokes it on child failure; (c) user issues `pos rollback scope <id>`; (d) system detects an error and invokes as part of self-correction.
7. Is rollback idempotent? If invoked twice, does it double-compensate or no-op on the second call?
8. What's the state machine around rollback? Does a rolled-back scope transition to a new terminal state (e.g. `rolled_back`), or does it stay `cancelled` with a `rollback_invoked` event appended?
9. Does rollback have its own budget / time limit? A compensation path that takes hours to run is a different class of problem than one that runs in milliseconds.

### 3. `compensatable` vs `fully_reversible` semantic distinction

10. What's the concrete difference in declaration? A `fully_reversible` scope might need no compensation path (the system can undo via the event log alone). A `compensatable` scope requires a compensation path because the forward action is externally visible (email sent, DNS changed) and cannot be "un-done" in the physical world.
11. Should the primitive enforce this distinction? E.g. `fully_reversible` + declared compensation path is allowed but redundant; `compensatable` + no compensation path is structurally refused.
12. Does the system's preference ordering (reversible > irreversible) treat `fully_reversible` and `compensatable` as a combined "reversible" bucket, or rank them separately (fully > compensatable > irreversible)?

### 4. Path-choice preference and telemetry

13. Where in the workflow does "choose between a reversible and irreversible path" actually happen? Candidates: (a) scope authoring — the LLM that generates the scope spec picks; (b) planning — a multi-scope plan selects between alternative sub-scopes; (c) dispatch — the orchestrator routes to one of several registered scope implementations.
14. What does "the same declared outcome" mean operationally? Two scopes with identical objective text and constraint set but different `reversibility_class` values? Or a broader notion (e.g. same high-level goal, different method)?
15. What telemetry signal records the choice? `pos.reversibility.path_chosen` span with `chosen_class`, `alternatives`, `reason`? Or an event on the scope itself?
16. How does the system *know* an alternative exists to choose between? The framework either (a) maintains a registry of scope-implementation alternatives per objective, (b) expects the LLM author to surface alternatives explicitly, or (c) both.

### 5. Integration with sealed components

17. Scope-of-work: the primitive consumes `ReversibilityClass` and `ScopeSpec` read-only. Default assumption (per §7 precedent): no amendment; the compensation-path declaration lives in a sidecar table owned by the reversibility primitive. Confirm the sidecar pattern delivers; halt-and-signal only if it genuinely cannot.
18. Safety layer: the dangerous-op gate currently reads reversibility class. Does the safety layer need to also read the compensation-path presence? Either (a) yes, via a new reversibility-primitive surface that says "has compensation?" or (b) no, the reversibility primitive refuses activation before safety ever sees the spec.
19. Orchestrator: rollback-on-failure needs orchestrator awareness. Is this a new orchestrator surface (likely halt-and-signal), or does the reversibility primitive compose via the existing cascade + cancel machinery?
20. Observability aggregator: `pos.reversibility.*` spans — standard emission pattern.
21. Memory system: should compensation-path registration and rollback events write to the memory system for durability beyond scope-of-work's event log, or is the event log sufficient?

### 6. State and storage

22. Does the primitive own its own SQLite (pattern: safety, degradation, observability)? Candidates: yes at `~/.pos/reversibility/reversibility.sqlite`; or no — compensation paths live in scope-of-work's event log as typed events and the primitive is stateless beyond that.
23. What's emitted to OTel? Path choice, compensation-path registration, rollback invocation, rollback completion, rollback failure — each as a span with scope_id, reversibility_class, compensation_path_id.

### 7. Deterministic enforcement — sidecar/wrap per precedent

The established pattern on `pos-v2` is that higher layers hold their own relationships and computations without amending sealed primitives:

- **Objective-tracker** uses a sidecar `ScopeObjectiveBinding` table to link scopes to objectives rather than amending `ScopeSpec` with an `objective_id` field.
- **Safety layer** uses a standalone `structural_hash(spec)` helper over `spec.model_dump_json()` rather than amending `ScopeSpec` with a `structural_hash()` method.
- **Safety layer** uses IPC-handler wrapping of `activate_scope` rather than amending the orchestrator with a pre-activation hook.

**Default assumption for this component: same pattern.** The reversibility primitive owns a sidecar `CompensationPathBinding` table (scope_id → compensation-path registration) and the structural enforcement lives in a reversibility-primitive activation wrap — layered with or alongside safety's wrap — that reads `ScopeSpec.reversibility_class` read-only and consults the sidecar for "is a compensation path registered?"

24. Confirm or rebut that default: does the activation wrap + sidecar combination fully deliver "irreversible cannot activate without a compensation path" without any `ScopeSpec` change? Specify how the wrap composes with safety's existing wrap (ordering, short-circuit semantics, error code disambiguation).
25. What's the Pydantic shape of the `CompensationPathBinding` record, and what's the registration surface the workspace uses to declare it (IPC method, CLI, YAML, all three)? The Pydantic enum/model_validator pattern (clause-g precedent) still applies — the binding record must structurally refuse invalid declarations (e.g. a binding with an empty path, or a binding pointing at a non-existent scope).
26. **If and only if** the sidecar/wrap pattern genuinely cannot deliver the acceptance criterion — halt and signal with the named constraint. Do not improvise an amendment. Amendment is the last resort, not the first question.

### 8. Testing discipline

26. How are compensation paths tested without actually performing the irreversible action? Mock scope adapter; inject stubbed compensation; verify invocation order + state access.
27. What's the ODD pattern for path-choice tests? Construct two scopes with the same objective, different reversibility classes; run the chooser; verify the reversible one was picked; verify telemetry recorded the choice.

## Constraints the research must respect

- **Python-native.** Permitted runtime as enumerated.
- **No amendments to sealed components.** If reversibility-primitive enforcement genuinely requires amending `ScopeSpec` (e.g. a new required field), halt and signal — do not improvise around it.
- **Max-first.** Reversibility-primitive internals should not require LLM inference; path choice may be LLM-surface (workspace-layer) but the primitive's contract enforcement is deterministic.
- **Zero carryover from current pOS.** Ruby compensation patterns are not a reference.
- **A1 correction held.** Emit OTel via aggregator's registered provider.
- **One-on-one notification channel only** for any user-facing rollback prompts.
- **Halt-on-deviation.**
- **Deterministic-layer enforcement** for the irreversibility refusal.
- **Composes with safety, does not duplicate.** The safety layer's dangerous-op gate already refuses irreversible scopes without approval. The reversibility primitive's refusal is for "irreversible declared without a compensation path" — a different structural shape.

## Deliverable — what the research document must contain

A markdown document at `components/reversibility-primitive/research.md` with:

1. **Survey of existing patterns** — database transactions (saga pattern, 2PC), undo/redo systems, SOA compensation patterns, functional programming's effect handlers, git revert vs reset semantics.
2. **Recommended design shape** — for each of the eight question groups, options considered, recommended option, rationale.
3. **Clause-by-clause spec coverage** — mapping each acceptance criterion to the piece of the design.
4. **Compensation-path contract specification** — concrete Pydantic shape; registration mechanism; state access pattern.
5. **Rollback state-machine** — transitions, idempotence, terminal states.
6. **Path-choice telemetry specification** — span schema, workflow integration points.
7. **Integration sequence diagrams** — compensation-path registration; rollback-on-failure; path-choice at scope authoring.
8. **Relationship to safety layer** — precise boundary. Which refusals belong to which component. Ordering of gates at activation.
9. **Dependency map** — consumed by: cost governance, self-correction loop. Depends on: scope-of-work, safety layer, orchestrator, observability aggregator.
10. **Complexity estimate** — AI-time calibrated against safety layer (~35 min) and graceful-degradation (~20 min). Reversibility's scope is comparable to safety's; anchor 30–45 AI-min wall-clock.
11. **Prototyping priorities** — questions only a prototype can answer. The sidecar/wrap pattern is the default; prototyping priority is confirming it covers the edge cases (e.g. compensation path invoked after orchestrator restart; rollback during an active dangerous-op gate).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies. The sidecar/activation-wrap pattern is the established precedent on `pos-v2` (objective-tracker's `ScopeObjectiveBinding`; safety-layer's `structural_hash` helper + IPC wrap). The researcher should take that as the default and only flag an amendment case if the sidecar/wrap genuinely cannot deliver — with a named failure mode, not a hypothetical.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
