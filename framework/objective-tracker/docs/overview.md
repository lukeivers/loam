# Objective Tracker — Overview

**Component:** Objective Tracker (pOS v2 Phase 1)
**Status:** D1–D9 complete; sealed primitive under `<workspace>/loam/objective-tracker/`.
**Depends on:** nothing. It is a foundational primitive — other components consume it.

---

## What this tracker does

The objective tracker is the answer to one question: **what is this piece of work actually trying to accomplish, and does it trace up to something the user wanted?**

A pOS agent (persona, harness, dispatcher) can invent plausible-looking sub-work out of thin air. Without a primitive that records the authoring actor, the parent goal, and the acceptance criteria, "the system did something" is indistinguishable from "the system chased its own hallucination." The objective tracker makes that distinction machine-checkable.

Concretely, the tracker:

1. **Persists a forest of objective trees.** Every objective has at most one parent; roots are top-level intentions. A forest, not a DAG — shared parenthood breaks the traceability guarantee.
2. **Records provenance.** Every objective carries `authored_by`: either the literal string `"user"` (the human), or any persona handle (e.g. `"mara"`). The tracker does not validate handle strings against any registry — it stores what the caller passes. When a persona authors a bad sub-objective, the trail is visible.
3. **Carries testable acceptance criteria.** Four variants: `prose` (plain-text, caller-dispatched), `scope_success` (ties the criterion to a scope-of-work's terminal state — auto-evaluates), `child_closure` (N-of-M children achieved — caller queries), `external_predicate` (a named predicate an ODD harness evaluates).
4. **Enforces traceability at the dispatch-layer boundary.** Via a **sidecar** binding table (`scope_objective_binding`). Before any scope-of-work is activated, the dispatcher calls `tracker.bind_scope(scope_id, objective_id)` — the call refuses to write the binding unless the objective's ancestry terminates at a root authored by `"user"`. Scope-of-work itself is unchanged. The enforcement is deterministic.
5. **Supports re-opening.** An `achieved` or `abandoned` objective can be returned to `active` via `re_open(objective_id, rationale)` — rationale is a **mandatory non-empty string** (Luke's decision). This is the closing move of the negative-case ODD loop: a test fails, the harness re-opens the parent, and re-extends with a new objective that would have caught the gap.
6. **Emits OpenTelemetry spans and events.** Every operation produces a span; state transitions are span events. No consumer is assumed — emission succeeds with the SDK's default no-op tracer (A1 correction).
7. **Supports semantic round-trip upgrade fidelity** (v1.1 R1). A pre-upgrade probe set of projections and bindings replays post-upgrade; drift above a declared threshold fails the upgrade.

---

## Why it looks the way it does

**Why event-sourcing?** Because the projection cache must be rebuildable from events alone. That is the upgrade-fidelity guarantee. A projection-first schema that couldn't be rebuilt from events would make any future pOS upgrade irreversible.

**Why a sidecar binding table instead of a column on scope-of-work?** Because scope-of-work is a sealed component. Adding a field would force a schema change and retest of a component that already passes 77 tests. The sidecar is additive: scope-of-work remains agnostic of the tracker; the dispatcher is the only code that knows about both.

**Why is `authored_by` a string, not an enum?** Because personas are configured per-workspace, not fixed by the framework. An enum would bake workspace assumptions into the core. The string is the minimum that supports the "debug a bad persona" use case (`list(authored_by="mara")` returns everything Mara authored; fix Mara and re-check).

**Why `notify` as the default parent-close?** Because "parent objective abandoned" is not the same as "parent scope cancelled." A scope cascades because its children cannot outlive the thing running them; an objective's children are separate intentions that may still matter. Callers opt in to cascade by setting `parent_close_policy=terminate | abandon`.

**Why is `time_bound` mandatory?** Because the spec says "every objective is time-bound or evergreen," and silent defaults smuggle in assumptions. Forcing the author to pick — a deadline, or `evergreen=True` — keeps the system honest.

**Why is `re_open` rationale mandatory?** Because re-opening a closed objective is a semantically-loaded action. The rationale is the audit trail's value. An empty rationale is an unaudited reversion.

---

## What this tracker is not

- **Not a workflow engine.** It doesn't dispatch tasks, schedule work, or run LLM calls. Those are consumers.
- **Not an evaluator.** Except for `scope_success` auto-evaluation, the tracker does not run predicates. It records criteria and evaluations — callers push results.
- **Not a DAG.** One parent per objective. If you need a shared dependency, model the shared thing as its own tree and let multiple trees reference it at the application layer.
- **Not coupled to any persona.** pOS core ships zero personas. The tracker records handle strings but never introspects them.

---

## Related documents in this bundle

- `architecture.md` — event log + projection + sidecar binding table diagram.
- `data-flow.md` — create → decompose → bind → evaluate → re-open → re-extend.
- `relationship-map.md` — who consumes the tracker and how.
- `api-reference.md` — one-page API reference.
