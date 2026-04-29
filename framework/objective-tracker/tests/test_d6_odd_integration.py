"""D6 — ODD integration surface.

Acceptance (brief §D6):
- list_by_root(root_id, states=?, with_unchecked_criteria=?) returns
  the exact set matching.
- External predicate registered by a harness can evaluate against an
  objective's criterion; result stores as event; queries return it.
- re_open(objective_id, rationale) transitions achieved back to active
  with audit event; empty/missing rationale raises.
- Representative ODD cycle end-to-end: register predicate → list with
  unchecked criteria → evaluate → record → re-open parent on failure
  → re-extend with a new objective → verify new objective is
  reachable in the tree.
"""

from __future__ import annotations

import pytest

from loam.objective_tracker.errors import MissingRationaleError
from loam.objective_tracker.spec import (
    ExternalPredicateCriterion,
    ObjectiveStatus,
    ProseCriterion,
)
from tests.conftest import make_child_spec, make_user_root_spec


# ---- list_by_root filters ------------------------------------------


async def test_list_by_root_with_states_filter(tracker):
    root = await tracker.create(make_user_root_spec(goal="r"))
    c1 = await tracker.create(make_child_spec(parent_id=root.objective_id))
    c2 = await tracker.create(make_child_spec(parent_id=root.objective_id))
    await tracker.start(c1.objective_id)
    await tracker.mark_achieved(c1.objective_id)
    # c2 stays proposed; root stays proposed.
    achieved = tracker.list_by_root(
        root.objective_id, states=[ObjectiveStatus.achieved]
    )
    assert {p.objective_id for p in achieved} == {c1.objective_id}
    proposed = tracker.list_by_root(
        root.objective_id, states=[ObjectiveStatus.proposed]
    )
    assert {p.objective_id for p in proposed} == {
        root.objective_id,
        c2.objective_id,
    }


async def test_list_by_root_with_unchecked_criteria_filter(tracker):
    root = await tracker.create(
        make_user_root_spec(
            goal="r",
            criteria=(ProseCriterion(criterion_id="rc", prose="x"),),
        )
    )
    c = await tracker.create(make_child_spec(parent_id=root.objective_id))
    # Evaluate the root's sole criterion as met.
    await tracker.evaluate_criterion(
        root.objective_id, criterion_id="rc", result="met", rationale="ok"
    )
    with_unchecked = tracker.list_by_root(
        root.objective_id, with_unchecked_criteria=True
    )
    assert {p.objective_id for p in with_unchecked} == {c.objective_id}


# ---- external predicates ------------------------------------------


async def test_external_predicate_evaluation_stores_result(tracker):
    """A registered predicate's result is pushed back via
    evaluate_criterion and is visible on queries."""
    proj = await tracker.create(
        make_user_root_spec(
            criteria=(
                ExternalPredicateCriterion(criterion_id="p", predicate_id="myp"),
            )
        )
    )
    after = await tracker.evaluate_criterion(
        proj.objective_id, criterion_id="p", result="met", rationale="harness ran"
    )
    assert after.criteria_latest["p"].result == "met"
    assert after.criteria_latest["p"].rationale == "harness ran"


# ---- re_open --------------------------------------------------------


async def test_re_open_transitions_achieved_to_active(tracker):
    proj = await tracker.create(make_user_root_spec())
    await tracker.start(proj.objective_id)
    await tracker.mark_achieved(proj.objective_id)
    reopened = await tracker.re_open(
        proj.objective_id, rationale="discovered a miss"
    )
    assert reopened.status == ObjectiveStatus.active


async def test_re_open_writes_audit_event_with_rationale(tracker):
    proj = await tracker.create(make_user_root_spec())
    await tracker.start(proj.objective_id)
    await tracker.mark_achieved(proj.objective_id)
    await tracker.re_open(proj.objective_id, rationale="why not")
    evs = tracker.store.events_for(proj.objective_id)
    kinds = [e.kind for e in evs]
    assert kinds == [
        "objective_created",
        "status_transitioned",  # proposed → active (start)
        "status_transitioned",  # active → achieved
        "status_transitioned",  # achieved → active (re_open)
    ]
    re_open_event = evs[-1]
    assert re_open_event.rationale == "why not"


async def test_re_open_empty_rationale_raises(tracker):
    proj = await tracker.create(make_user_root_spec())
    await tracker.start(proj.objective_id)
    await tracker.mark_achieved(proj.objective_id)
    with pytest.raises(MissingRationaleError):
        await tracker.re_open(proj.objective_id, rationale="")
    with pytest.raises(MissingRationaleError):
        await tracker.re_open(proj.objective_id, rationale="   ")


async def test_re_open_from_abandoned_also_permitted(tracker):
    proj = await tracker.create(make_user_root_spec())
    await tracker.mark_abandoned(proj.objective_id, rationale="dropped")
    reopened = await tracker.re_open(proj.objective_id, rationale="reconsidered")
    assert reopened.status == ObjectiveStatus.active


# ---- end-to-end ODD cycle -----------------------------------------


async def test_representative_odd_cycle_end_to_end(tracker):
    """Brief §D6: register predicate → list objectives with unchecked
    criteria → evaluate → record → re-open parent on failure → re-extend
    with a new objective → verify the new objective is reachable in
    the tree.

    The "harness" here is the test function itself; the "predicate
    registry" is a local dict of callables.
    """
    # 1. Create a tree with a predicate-based criterion on a child.
    root = await tracker.create(
        make_user_root_spec(
            goal="ship beta release",
            criteria=(ProseCriterion(criterion_id="rc", prose="beta shipped"),),
        )
    )
    child = await tracker.create(
        make_child_spec(
            parent_id=root.objective_id,
            goal="check download link works",
            criteria=(
                ExternalPredicateCriterion(
                    criterion_id="dp", predicate_id="download_works"
                ),
            ),
            authored_by="mara",
        )
    )

    # Mark root and child active, then root achieved.
    await tracker.start(root.objective_id)
    await tracker.start(child.objective_id)

    # Evaluate the root's prose criterion as met; root becomes achieved.
    await tracker.evaluate_criterion(
        root.objective_id, criterion_id="rc", result="met", rationale="beta went out"
    )
    await tracker.mark_achieved(root.objective_id, evidence="beta is up")

    # 2. Harness registers predicates and walks unchecked criteria.
    predicates = {
        "download_works": lambda: False,  # a negative case
    }
    unchecked_list = tracker.list_by_root(
        root.objective_id, with_unchecked_criteria=True
    )
    # The child has an unchecked predicate.
    assert child.objective_id in {p.objective_id for p in unchecked_list}

    # 3. Harness runs the predicate for each objective in unchecked.
    for p in unchecked_list:
        for c in p.unchecked_criteria():
            if c.kind == "external_predicate":
                result = predicates[c.predicate_id]()
                await tracker.evaluate_criterion(
                    p.objective_id,
                    criterion_id=c.criterion_id,
                    result="met" if result else "not_met",
                    rationale="harness: auto-evaluated",
                    source="odd_harness",
                )

    # Child now has a not_met evaluation on its predicate.
    child_proj = tracker.get(child.objective_id)
    assert child_proj.criteria_latest["dp"].result == "not_met"

    # 4. Negative case re-extends: re_open the root (its child's
    # predicate failed), then author a new child addressing the gap.
    await tracker.re_open(
        root.objective_id, rationale="child predicate failed — re-extend"
    )

    # 5. Author a new objective that will catch the negative case.
    from loam.objective_tracker.spec import ObjectiveSpec as _ObjectiveSpec
    from loam.objective_tracker.spec import TimeBound as _TimeBound
    from tests.conftest import future_deadline

    new_child_spec = _ObjectiveSpec(
        goal="add CDN-backed fallback for downloads",
        parent_id=root.objective_id,
        acceptance_criteria=(
            ExternalPredicateCriterion(
                criterion_id="fallback_ok", predicate_id="cdn_download_works"
            ),
        ),
        time_bound=_TimeBound(deadline=future_deadline()),
        authored_by="mara",
    )
    new_child = await tracker.create(new_child_spec)

    # 6. The new objective is reachable in the tree under the root.
    under_root = tracker.list_by_root(root.objective_id)
    assert new_child.objective_id in {p.objective_id for p in under_root}

    # And the tree walk now traces up to a user-authored root.
    chain = tracker.trace_to_root(new_child.objective_id)
    assert chain[-1].authored_by == "user"
    assert chain[-1].objective_id == root.objective_id


async def test_list_with_unchecked_criteria_filter_flat(tracker):
    """list (flat query) also honours with_unchecked_criteria."""
    a = await tracker.create(
        make_user_root_spec(
            goal="a",
            criteria=(ProseCriterion(criterion_id="c", prose="x"),),
        )
    )
    b = await tracker.create(
        make_user_root_spec(
            goal="b",
            criteria=(ProseCriterion(criterion_id="c", prose="x"),),
        )
    )
    await tracker.evaluate_criterion(
        a.objective_id, criterion_id="c", result="met"
    )
    unchecked = tracker.list(with_unchecked_criteria=True)
    assert {p.objective_id for p in unchecked} == {b.objective_id}
    checked = tracker.list(with_unchecked_criteria=False)
    assert {p.objective_id for p in checked} == {a.objective_id}
