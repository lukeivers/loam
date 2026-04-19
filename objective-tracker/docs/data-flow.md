# Data flow

A worked example. The user decides to ship a beta release. One persona (Mara) decomposes that into a child objective. A scope-of-work is activated under the child. The child's predicate later fails; the parent is re-opened; a new objective is authored to catch the negative case.

---

## Step 1 — create the user-authored root

```python
from objective_tracker import (
    ObjectiveTracker, ObjectiveSpec, TimeBound, ProseCriterion,
)

tracker = ObjectiveTracker(db_path="objectives.db")

root = await tracker.create(
    ObjectiveSpec(
        goal="ship beta release",
        parent_id=None,                   # root
        acceptance_criteria=(
            ProseCriterion(criterion_id="rc", prose="beta shipped"),
        ),
        time_bound=TimeBound(evergreen=True, review_cadence="weekly"),
        authored_by="user",               # THIS is the enforcement anchor
    )
)
```

Events written: `objective_created`.
Projection row: `status=proposed`, `authored_by="user"`.

---

## Step 2 — a persona decomposes into a child objective

```python
child = await tracker.create(
    ObjectiveSpec(
        goal="check download link works",
        parent_id=root.objective_id,
        acceptance_criteria=(
            ExternalPredicateCriterion(
                criterion_id="dp", predicate_id="download_works"
            ),
        ),
        time_bound=TimeBound(deadline=datetime(2026, 5, 1, tzinfo=timezone.utc)),
        authored_by="mara",               # persona handle, arbitrary string
    )
)
```

Events written: `objective_created`.
Projection row: `status=proposed`, `authored_by="mara"`, parent_id points at root.

---

## Step 3 — dispatch layer binds a scope to the child objective

```python
# Called by the workspace dispatcher before it activates a scope.
await tracker.bind_scope(scope.scope_id, child.objective_id)
```

`bind_scope` walks `trace_to_root(child.objective_id)` → `[child, root]`. The terminal root's `authored_by == "user"` → binding succeeds.

Events written on the child's stream: `scope_bound`.
Sidecar row: `(scope_id, objective_id=child, bound_event_id, bound_at)`.

If the root had been `authored_by="mara"` (orphan), `bind_scope` would raise `OrphanRootError` and the dispatcher would refuse to activate the scope.

---

## Step 4 — scope runs, and its state-transition auto-evaluates a scope_success criterion

```python
# Earlier: tracker.subscribe_scope_emitter(scope_runtime.emitter)
# If a different objective carries a ScopeSuccessCriterion pointing at
# this scope, the tracker observes scope_runtime's `state_transitioned`
# event with to_state="completed" and writes:
#   criterion_evaluated(source="scope_success_auto", result="met")
```

---

## Step 5 — an ODD harness walks unchecked criteria

```python
unchecked = tracker.list_by_root(
    root.objective_id, with_unchecked_criteria=True
)
for p in unchecked:
    for c in p.unchecked_criteria():
        if c.kind == "external_predicate":
            result = registered_predicates[c.predicate_id]()
            await tracker.evaluate_criterion(
                p.objective_id,
                criterion_id=c.criterion_id,
                result="met" if result else "not_met",
                source="odd_harness",
            )
```

For the child's `download_works` predicate, suppose the predicate returns False. Events written: `criterion_evaluated` with result=`not_met`.

---

## Step 6 — re-open the parent and re-extend

The harness sees the not-met evaluation. It re-opens the parent and authors a new sibling objective that would have caught the gap.

```python
await tracker.re_open(
    root.objective_id,
    rationale="child predicate failed — re-extend"
)

new_child = await tracker.create(
    ObjectiveSpec(
        goal="add CDN-backed fallback for downloads",
        parent_id=root.objective_id,
        acceptance_criteria=(
            ExternalPredicateCriterion(
                criterion_id="fb", predicate_id="cdn_download_works"
            ),
        ),
        time_bound=TimeBound(deadline=future),
        authored_by="mara",
    )
)
```

Events written: `status_transitioned (achieved → active)` on the root with mandatory rationale, then `objective_created` for the new child.

`list_by_root(root.objective_id)` now includes the new child. `trace_to_root(new_child.objective_id)` still terminates at the user-authored root.

---

## Upgrade replay (D8)

Before an upgrade:

```python
captured = capture_pre_upgrade(tracker.store, snapshot_to="snap.db")
# captured: { probes: [...], bindings: [...], snapshot_db_path: ... }
```

After the upgrade (same DB, potentially new projector code):

```python
report = replay_post_upgrade(tracker.store, captured)
assert_no_drift(report, threshold=0)    # or ≥0 for forward-compatible changes
```

`report.total_drift > 0` fails the upgrade. The physical snapshot at `snap.db` is the escape hatch — copy it over the live DB to revert.
