# Objective Tracker — Proposal

**Component:** Objective Tracker (third and final Phase 1 primitive)

**Status:** DRAFT — awaiting owner's review and approval before a handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 addendum + v1.2 addendum
**Informed by:** `research-plan.md`, `research.md` (returned 19:09 CDT, 17 sections). the owner's two halt-signal rulings 2026-04-18 19:15 CDT are baked in.

---

## Summary

Build the objective tracker as a standalone Phase 1 primitive that persists a forest of objective trees, enforces scope-to-objective traceability via a sidecar binding table (no amendment to scope-of-work), and supports ODD test-harness integration. Every `Objective` carries a `goal`, `parent_id` (or root marker), a testable criterion (discriminated-union variants), a time-bound or evergreen mark, and an `authored_by` provenance field that names either `"user"` or a specific persona handle — so when a persona authors a sub-objective that turns out wrong, we can trace who authored it and why. Persistence is a separate SQLite WAL database, event-sourced, so v1.1 R1 semantic round-trip upgrade-fidelity works the same way as scope-of-work. Enforcement of "every scope traces to a user-authored root" is a deterministic check at scope-objective binding time, performed by a `tracker.bind_scope(scope_id, objective_id)` call that the dispatch layer makes before scope-of-work activates any scope.

## Direction

### Primitive schema

`ObjectiveSpec` (Pydantic-validated at construction):

- `id` — UUID
- `goal` — string, the plain-language objective statement
- `parent_id` — UUID of parent objective, or `None` for root
- `acceptance_criteria` — list of `Criterion` discriminated-union variants
- `time_bound` — either an ISO datetime deadline or the literal `"evergreen"` with an optional review cadence
- `authored_by` — string carrying the authoring actor's identity. Either the literal `"user"` or a persona handle (e.g. `"mara"`). Populated at creation based on which API path authored the objective.
- `status` — enum `proposed | active | achieved | abandoned` (event-sourced, not mutable state)
- `created_at`, `updated_at`, `owner` — optional metadata

### Criterion discriminated union

Four variants of `Criterion`:

- `prose` — free-text descriptive criterion (evaluated manually or by LLM)
- `scope_success` — points at a scope-of-work whose completion-without-failure is the acceptance
- `child_closure` — acceptance is N-of-M child objectives reaching `achieved` status
- `external_predicate` — names a registered predicate (entry-point pattern from hypothesis) that callers dispatch

The tracker records criteria but does **not** execute them. Evaluation is caller-dispatched — ODD harnesses, the self-correction loop, the persona authoring pipeline, or user-initiated checks register predicates and push results back via `evaluate_criterion(criterion_id, result, rationale)`. The tracker stores the evaluation as an event.

### Hierarchy

Strict forest of trees. DAG rejected — shared-parent ambiguity breaks "every scope traces to a *the* top-level objective." Every objective has at most one parent. Roots are objectives with `parent_id: None`.

**`authored_by` carries debuggable provenance.** The root of every trace must have `authored_by == "user"` (the enforcement invariant). Sub-objectives may be authored by personas — the field records the specific persona handle. A query `list(authored_by="mara")` returns all objectives a financial-advisor specialist authored, across all trees; useful for debugging a persona whose authoring produced wrong sub-objectives.

### Parent-close policy

Default `notify` (not `TERMINATE`). When a parent objective is marked abandoned or achieved, children receive a notification event but are not automatically terminated — "parent objective abandoned" is semantically distinct from "parent scope cancelled." Per-objective override available (`parent_close_policy: terminate | abandon | notify`).

### Persistence

Separate SQLite WAL database from scope-of-work, event-sourced mirror of scope-of-work's pattern:

- `objective_events` append-only table — source of truth
- `objective_state` projection cache — rebuildable from events
- `scope_objective_binding` sidecar table — maps scope IDs to objective IDs, with binding events
- Semantic round-trip upgrade test follows v1.1 R1 + scope-of-work D7 pattern

### Scope-to-objective enforcement (the sidecar mechanism)

Scope-of-work is **not amended.** The enforcement happens at the dispatch-layer boundary — before a scope is activated, the dispatch layer calls `tracker.bind_scope(scope_id, objective_id)`:

- If the objective id is unknown → raises `UnresolvedObjectiveError`
- If the objective's ancestry does not terminate at a user-authored root → raises `OrphanRootError`
- If both checks pass → writes a `ScopeBound` event and returns

The dispatch layer refuses to activate a scope that has not been bound. Scope-of-work itself remains agnostic of the tracker — no field change, no runtime change, no test change. The binding table is a sidecar that the tracker owns.

### ODD integration

The tracker supplies the runtime ODD needs. Flow:

1. ODD harness walks `tracker.list_by_root(root_id, states=[active], with_unchecked_criteria=True)`.
2. For each objective with external-predicate criteria, harness runs the registered predicate.
3. Results pushed back via `evaluate_criterion(criterion_id, result, rationale)` — tracker stores as events.
4. Negative cases found during evaluation re-extend up the chain: harness (or a persona, LLM-assisted via Claude via Max) authors a new `ObjectiveSpec` with `authored_by` set to the authoring actor, `parent_id` pointing at the relevant ancestor, and criteria that would have caught the negative case.
5. Optionally, `tracker.re_open(objective_id)` returns an affected ancestor from `achieved` back to `active` with an audit event.

The tracker is the passive data surface; harnesses and authors are active callers. This keeps the primitive cohesive.

### API surface

Thin async Python, mirroring scope-of-work's posture:

- `create(spec: ObjectiveSpec) → Objective` — Pydantic-validated at construction
- `get(objective_id) → Objective`
- `list(parent_id=?, root_id=?, status=?, authored_by=?, with_unchecked_criteria=?) → list[Objective]`
- `mark_achieved(objective_id, evidence)`
- `mark_abandoned(objective_id, reason)`
- `re_open(objective_id, reason)`
- `decompose_into_children(parent_id, child_specs)` — atomic multi-create
- `trace_to_root(objective_id) → list[Objective]` — ordered ancestor chain
- `bind_scope(scope_id, objective_id) → ScopeBinding` — enforcement entry point
- `evaluate_criterion(criterion_id, result, rationale)` — records evaluation events
- Observer subscription via `pyee` emitter
- OTel span emission per operation (v1.1 R11)

## Deliverables

Nine deliverables D1–D9.

### D1. Objective primitive (schema + persistence)

**Objective:** `ObjectiveSpec` exists with Pydantic validation; event-sourced persistence lands; state projection rebuildable from events.
**Acceptance:** creating an objective with any missing mandatory field raises; valid objectives persist; replaying the event log reconstructs state identically; per v1.1 R1 semantic round-trip passes.

### D2. Hierarchy and traceability

**Objective:** forest-of-trees structure works; `trace_to_root` returns the ordered ancestor chain; orphan detection identifies objectives whose chain does not terminate at a user-authored root.
**Acceptance:** a deliberately-orphaned chain is detected as orphan; a user-authored-root chain validates cleanly; DAG attempts (two parents) are rejected at construction.

### D3. Criterion discriminated union

**Objective:** all four variants (`prose`, `scope_success`, `child_closure`, `external_predicate`) validate, persist, and support `evaluate_criterion` for the two that can be automated (`scope_success`, `external_predicate`).
**Acceptance:** each variant passes its own validation test; `evaluate_criterion` events are stored and queryable; re-evaluations update the latest-result view.

### D4. Scope-to-objective enforcement (sidecar)

**Objective:** `bind_scope` deterministically resolves the objective id and ancestry chain; rejects unresolved ids and orphan roots; records `ScopeBound` events; the workspace dispatch layer refuses to activate unbound scopes.
**Acceptance:**
- Valid binding succeeds and emits an event.
- Unknown objective id → `UnresolvedObjectiveError`.
- Chain-not-terminating-at-user-authored-root → `OrphanRootError`.
- An integration test against the sealed scope-of-work confirms: scope activation succeeds after binding, fails without, and scope-of-work's own code is untouched.

### D5. `authored_by` provenance

**Objective:** every objective carries `authored_by` populated at creation; `list(authored_by=...)` returns all objectives authored by that actor across all trees.
**Acceptance:**
- Objectives created via the user API path carry `authored_by == "user"`.
- Objectives created via a persona API path carry `authored_by == <persona-handle>`.
- `list(authored_by="<handle>")` returns exactly the set of objectives authored by that handle.
- The root-user-authored check reads `authored_by` rather than an `is_user`-shaped flag.

### D6. ODD integration surface

**Objective:** the query surface ODD test harnesses need exists; `evaluate_criterion` works for external predicates; re-open + re-extension flow is supported.
**Acceptance:**
- `list_by_root(root_id, states=?, with_unchecked_criteria=?)` returns the exact set of objectives matching.
- An external-predicate criterion can be evaluated from an external harness and the result is stored.
- `re_open(objective_id)` transitions `achieved` → `active` with an audit event.
- A representative ODD cycle (register predicate → list → evaluate → record → re-extend on failure) runs end-to-end in a test.

### D7. OTel observability emission

**Objective:** every operation emits OTel spans/events per v1.1 R11.
**Acceptance:** create, mark, bind, evaluate, re-open all produce spans with relevant attributes (objective_id, authored_by, status); emission succeeds with no consumer (A1 correction).

### D8. Upgrade-fidelity test harness

**Objective:** the tracker passes a v1.1 R1 semantic round-trip test across an upgrade.
**Acceptance:** pre-upgrade probe set runs; post-upgrade replay compares output; drift above declared threshold fails the upgrade; SQLite snapshot preserves physical reversibility.

### D9. Bundled documentation

**Objective:** v1.1 R4 — human-readable documentation bundled with the component.
**Acceptance:** prose explanation; architecture diagram (objective event log + projection + sidecar binding table); data-flow diagram (objective create → decompose → bind-to-scope → evaluate → re-extend); relationship map (consumes nothing hard; consumed by scope-of-work via binding, by future self-correction loop, by ODD harnesses); one-page API reference.

---

## Spec coverage

| Criterion | Delivered by |
|---|---|
| v1.0 Objective — parent-or-root, testable criterion, time-bound-or-evergreen | D1 |
| v1.0 Architectural — no workflow, task, or scope without objective trace | D4 |
| v1.0 Observability — every action auditable | D7 |
| v1.1 R1 — semantic round-trip upgrade | D8 |
| v1.1 R4 — bundled documentation | D9 |
| v1.1 R11 — OTel observability | D7 |
| ODD methodology — tests authored against objectives, negative-case re-extension | D3 + D6 |
| the owner's `authored_by` refinement — debuggable provenance | D5 |

---

## Dependencies

### Hard dependencies

- **None.** The tracker is foundational. It does not depend on any other pOS component to ship.

### Soft dependencies (consumers, not requirements)

- Scope-of-work (consumed via `bind_scope` from the dispatch layer — no scope-of-work change required).
- Primary-persona layer's authoring pipeline (personas author objectives; the tracker records the handle in `authored_by`).
- Self-correction loop (future) — will subscribe to objective-abandonment events.
- Future observability aggregator — subscribes to OTel emissions.

### Permitted runtime dependencies

- Python stdlib (including `sqlite3`, `asyncio`, `uuid`, `dataclasses`)
- `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk` (already in scope)
- No additional third-party runtime libraries without halt-and-signal.

---

## Assumptions (inference recorded — flagged so the builder can challenge)

1. **`authored_by` is an unvalidated free string.** The tracker accepts either `"user"` or any string (treated as a persona handle). It does NOT cross-check handle strings against the persona loader's registry. Rationale: keeps the tracker decoupled; the workspace dispatch layer or audit reports can cross-check if needed. If the builder thinks the tracker should validate handles, halt and flag.
2. **Criterion evaluation is always external.** The tracker records criteria and stores evaluation events but never runs predicates itself. If the builder finds a simple variant (e.g. `child_closure` — "N of M children achieved") that's cheap enough to auto-evaluate on child state-change events, that's an additive improvement worth flagging, but the default is caller-dispatched.
3. **Objectives have at most one parent.** Firm — DAG ruled out in the research for traceability reasons.

---

## Open questions for the owner

Three minor decisions sharpen the handoff brief. the primary persona has a lean on each.

1. **Default `time_bound` when an author omits it.** Options: reject on omission (mandatory), default to `"evergreen"`, default to a stub "3 months from creation." recommendation: **reject on omission** — matches the spec's "every objective is time-bound or evergreen" language, and forces the author to make the call consciously.
2. **`scope_success` criterion auto-evaluation — should the tracker auto-evaluate when the referenced scope's state changes, or require explicit `evaluate_criterion` calls?** recommendation: **auto-evaluate** on scope events for the `scope_success` variant specifically. It's a cheap subscription and matches the caller's intent.
3. **`re_open` audit event — does it require a rationale string (mandatory field), or is rationale optional?** recommendation: **mandatory**. Re-opening an achieved objective is a meaningful action; the rationale is the audit trail's value. Empty strings rejected.

Default to leans unless any reads wrong.

---

## What happens on approval

1. I draft the handoff brief for your review. Eleven the owner decisions baked in: sidecar enforcement, `authored_by`-as-provenance (not binary), `notify` default parent-close, declared the primary persona leans on the three open questions, scope-of-work-untouched constraint.
2. On your review, a general-purpose agent is dispatched.
3. Halt-on-deviation applies. The builder stops and signals if any constraint cannot be honoured or if any design question reveals the approved direction is untenable.
