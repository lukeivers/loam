# API reference

One-page reference for the public surface. All async methods marked `(async)`; all others are synchronous queries.

---

## Construction

```python
from objective_tracker import ObjectiveTracker

tracker = ObjectiveTracker(db_path="path/to/objectives.db")
tracker.close()   # close connection; no async context manager
```

The SQLite file is created if it does not exist. WAL mode is enabled automatically.

---

## Specs

```python
from objective_tracker import (
    ObjectiveSpec, TimeBound, ParentClosePolicy,
    ProseCriterion, ScopeSuccessCriterion,
    ChildClosureCriterion, ExternalPredicateCriterion,
)
```

### `ObjectiveSpec`

| Field | Type | Required | Default |
|---|---|---|---|
| `goal` | `str` (non-empty) | yes | — |
| `parent_id` | `str \| None` | yes | `None` (root) |
| `acceptance_criteria` | `tuple[Criterion, ...]` | yes | — |
| `time_bound` | `TimeBound` | yes | — |
| `authored_by` | `str` (non-empty) | yes | — |
| `owner` | `str \| None` | no | `None` |
| `parent_close_policy` | `ParentClosePolicy` | no | `notify` |

Criterion ids must be unique within one ObjectiveSpec.

### `TimeBound`

| Field | Type | Required |
|---|---|---|
| `deadline` | `datetime \| None` | mutually exclusive with `evergreen` |
| `evergreen` | `bool` | mutually exclusive with `deadline` |
| `review_cadence` | `str \| None` | only permitted when `evergreen=True` |

Exactly one of `deadline` or `evergreen=True` must be set.

### Criterion variants (discriminated union, `kind` field)

- `ProseCriterion(criterion_id, prose, description="")` — `kind="prose"`
- `ScopeSuccessCriterion(criterion_id, scope_id, success_states=frozenset({"completed"}))` — `kind="scope_success"`
- `ChildClosureCriterion(criterion_id, required_count)` — `kind="child_closure"`
- `ExternalPredicateCriterion(criterion_id, predicate_id)` — `kind="external_predicate"`

---

## Lifecycle API

```python
# (async) create a new objective
proj = await tracker.create(spec, objective_id=None)

# (async) atomic multi-create of children under parent_id
projs = await tracker.decompose_into_children(parent_id, child_specs)

# (async) transitions
await tracker.start(objective_id, rationale=None)
await tracker.mark_achieved(objective_id, evidence=None)
await tracker.mark_abandoned(objective_id, rationale="...")   # rationale required
await tracker.re_open(objective_id, rationale="...")          # rationale required
```

Legal status transitions:

```
proposed → active, abandoned
active   → achieved, abandoned
achieved → active   (re_open — mandatory rationale)
abandoned → active  (re_open — mandatory rationale)
```

---

## Criterion evaluation

```python
# (async) record a met/not_met evaluation
proj = await tracker.evaluate_criterion(
    objective_id,
    criterion_id="p",
    result="met" | "not_met",
    rationale=None,
    source="caller",
)

# (sync) compute a child_closure on demand
achieved, required, is_met = tracker.child_closure_status(objective_id, criterion_id)
```

`scope_success` criteria auto-evaluate via `subscribe_scope_emitter` (see below). Other variants are caller-dispatched.

---

## Scope-to-objective binding (sidecar)

```python
# (async) bind a scope; raises UnresolvedObjectiveError or OrphanRootError
binding = await tracker.bind_scope(scope_id, objective_id)

# sync queries
binding_row = tracker.get_binding(scope_id)              # dict | None
is_bound     = tracker.is_scope_bound(scope_id)          # bool
```

`bind_scope` enforces that the objective's ancestry terminates at `authored_by == "user"`.

---

## Queries

```python
proj = tracker.get(objective_id)                         # ObjectiveProjection | None

projs = tracker.list(
    parent_id=None,          # str | None
    status=None,             # Sequence[ObjectiveStatus] | None
    authored_by=None,        # str | None
    is_root=None,            # bool | None
    with_unchecked_criteria=None,  # bool | None
)

descendants = tracker.list_by_root(
    root_id,
    states=None,
    with_unchecked_criteria=None,
)

chain = tracker.trace_to_root(objective_id)   # [self, parent, ..., root]
```

---

## Observation (pyee fan-out)

```python
tracker.subscribe(objective_id, callback)   # callback(event)
tracker.subscribe_all(callback)

# Optional scope-of-work integration for ScopeSuccessCriterion auto-eval:
tracker.subscribe_scope_emitter(scope_runtime.emitter)
```

Callbacks receive typed events from `objective_tracker.events` — `ObjectiveCreated`, `StatusTransitioned`, `CriterionEvaluated`, `ScopeBound`, `ParentClosed`.

---

## Upgrade-fidelity harness (D8)

```python
from objective_tracker.upgrade import (
    capture_pre_upgrade, replay_post_upgrade, assert_no_drift,
    captured_to_json, captured_from_json,
)

# pre-upgrade
captured = capture_pre_upgrade(tracker.store, snapshot_to="pre.db")
json_str = captured_to_json(captured)  # persist between runs

# post-upgrade
report = replay_post_upgrade(tracker.store, captured_from_json(json_str))
assert_no_drift(report, threshold=0)
```

---

## Errors

```python
from objective_tracker import (
    UnresolvedObjectiveError, OrphanRootError,
    IllegalTransitionError, MissingRationaleError, DAGRejected,
)
```

All inherit from `ObjectiveTrackerError`.
