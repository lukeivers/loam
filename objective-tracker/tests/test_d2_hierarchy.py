"""D2 — Hierarchy and traceability.

Acceptance (brief §D2):
- A deliberately-orphaned chain (root authored_by != "user") is detected
  as orphan by trace_to_root + ancestry check.
- A user-authored-root chain validates cleanly.
- DAG attempts (two parents) raise at construction — ONLY one parent
  permitted.
- trace_to_root(objective_id) returns the ordered ancestor list, with
  the user-authored root last.
"""

from __future__ import annotations

import pytest

from src.errors import DAGRejected, OrphanRootError, UnresolvedObjectiveError
from src.spec import ObjectiveSpec, ProseCriterion, TimeBound
from tests.conftest import make_child_spec, make_user_root_spec


async def test_trace_to_root_returns_ordered_chain(tracker):
    root = await tracker.create(make_user_root_spec(goal="root"))
    mid = await tracker.create(
        make_child_spec(parent_id=root.objective_id, goal="middle", authored_by="mara")
    )
    leaf = await tracker.create(
        make_child_spec(parent_id=mid.objective_id, goal="leaf", authored_by="mara")
    )
    chain = tracker.trace_to_root(leaf.objective_id)
    assert [p.objective_id for p in chain] == [
        leaf.objective_id,
        mid.objective_id,
        root.objective_id,
    ]
    assert chain[-1].authored_by == "user"


async def test_user_authored_root_chain_validates_cleanly(tracker):
    root = await tracker.create(make_user_root_spec())
    child = await tracker.create(make_child_spec(parent_id=root.objective_id))
    chain = tracker.trace_to_root(child.objective_id)
    # Non-raising; terminal root is authored_by="user".
    assert chain[-1].authored_by == "user"


async def test_orphaned_chain_detected_by_bind_scope(tracker):
    # Persona-authored root (NOT a user-authored root) — orphan.
    orphan_root_spec = make_user_root_spec(goal="orphan")
    orphan_root_spec = orphan_root_spec.model_copy(update={"authored_by": "mara"})
    root = await tracker.create(orphan_root_spec)
    child = await tracker.create(
        make_child_spec(parent_id=root.objective_id, authored_by="mara")
    )
    with pytest.raises(OrphanRootError) as excinfo:
        await tracker.bind_scope("scope-x", child.objective_id)
    assert excinfo.value.terminal_authored_by == "mara"


async def test_dag_self_parent_rejected(tracker):
    from tests.conftest import future_deadline

    # Cannot create an objective that names itself as parent.
    spec = ObjectiveSpec(
        goal="loopy",
        parent_id="obj-self",
        acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
        time_bound=TimeBound(deadline=future_deadline()),
        authored_by="user",
    )
    with pytest.raises(DAGRejected):
        await tracker.create(spec, objective_id="obj-self")


async def test_dag_unknown_parent_rejected(tracker):
    with pytest.raises(UnresolvedObjectiveError):
        await tracker.create(
            make_child_spec(parent_id="obj-nonexistent")
        )


async def test_forest_of_trees_multiple_roots(tracker):
    r1 = await tracker.create(make_user_root_spec(goal="tree-1"))
    r2 = await tracker.create(make_user_root_spec(goal="tree-2"))
    assert r1.is_root and r2.is_root
    roots = tracker.list(is_root=True)
    assert len(roots) == 2


async def test_trace_to_root_on_unknown_objective_raises(tracker):
    with pytest.raises(UnresolvedObjectiveError):
        tracker.trace_to_root("obj-does-not-exist")


async def test_only_one_parent_per_objective(tracker):
    """Every objective has at most one parent — DAGs rejected.

    Since ObjectiveSpec only carries a single `parent_id`, this is a
    structural guarantee. This test confirms the shape: you can't
    pass multiple parents at construction.
    """
    from tests.conftest import future_deadline

    # Type system already forbids a list of parents — this is a
    # smoke-test against the shape.
    spec = ObjectiveSpec(
        goal="x",
        parent_id="obj-A",  # string, not a list
        acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
        time_bound=TimeBound(deadline=future_deadline()),
        authored_by="user",
    )
    assert spec.parent_id == "obj-A"
    assert not isinstance(spec.parent_id, list)


async def test_list_by_root_walks_full_descendants(tracker):
    root = await tracker.create(make_user_root_spec(goal="r"))
    a = await tracker.create(
        make_child_spec(parent_id=root.objective_id, goal="a")
    )
    b = await tracker.create(
        make_child_spec(parent_id=root.objective_id, goal="b")
    )
    a1 = await tracker.create(
        make_child_spec(parent_id=a.objective_id, goal="a1")
    )
    descendants = tracker.list_by_root(root.objective_id)
    ids = {p.objective_id for p in descendants}
    assert ids == {
        root.objective_id,
        a.objective_id,
        b.objective_id,
        a1.objective_id,
    }


async def test_trace_stops_at_root(tracker):
    root = await tracker.create(make_user_root_spec(goal="r"))
    chain = tracker.trace_to_root(root.objective_id)
    assert len(chain) == 1
    assert chain[0].parent_id is None
