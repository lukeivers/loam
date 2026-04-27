"""D1 — Objective primitive (schema + persistence).

Acceptance (brief §D1):
- Creating with any missing mandatory field raises at construction.
- Valid objectives persist via event log.
- Replay of the event log reconstructs projection state identically.
- SQLite WAL mode enabled.
- Mandatory fields present: id, goal, parent_id-or-root-marker,
  acceptance_criteria, time_bound, authored_by, status.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.projection import project, projection_to_state_row
from src.runtime import ObjectiveTracker
from src.spec import (
    ObjectiveSpec,
    ObjectiveStatus,
    ProseCriterion,
    TimeBound,
)
from tests.conftest import make_user_root_spec


# ---- Pydantic-level construction gates -------------------------------


def test_missing_goal_rejects_at_construction():
    with pytest.raises(ValidationError):
        ObjectiveSpec(
            parent_id=None,
            acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
            time_bound=TimeBound(evergreen=True),
            authored_by="user",
        )


def test_empty_goal_rejects():
    with pytest.raises(ValidationError):
        ObjectiveSpec(
            goal="",
            parent_id=None,
            acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
            time_bound=TimeBound(evergreen=True),
            authored_by="user",
        )


def test_missing_acceptance_criteria_rejects():
    with pytest.raises(ValidationError):
        ObjectiveSpec(
            goal="x",
            parent_id=None,
            time_bound=TimeBound(evergreen=True),
            authored_by="user",
        )


def test_missing_time_bound_rejects():
    """Luke's decision: time_bound is mandatory; omission rejects."""
    with pytest.raises(ValidationError):
        ObjectiveSpec(
            goal="x",
            parent_id=None,
            acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
            authored_by="user",
        )


def test_missing_authored_by_rejects():
    with pytest.raises(ValidationError):
        ObjectiveSpec(
            goal="x",
            parent_id=None,
            acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
            time_bound=TimeBound(evergreen=True),
        )


def test_empty_authored_by_rejects():
    with pytest.raises(ValidationError):
        ObjectiveSpec(
            goal="x",
            parent_id=None,
            acceptance_criteria=(ProseCriterion(criterion_id="c", prose="x"),),
            time_bound=TimeBound(evergreen=True),
            authored_by="",
        )


def test_time_bound_requires_deadline_or_evergreen():
    """Luke's decision: no silent default."""
    with pytest.raises(ValidationError):
        TimeBound()


def test_time_bound_rejects_both_deadline_and_evergreen():
    from tests.conftest import future_deadline

    # deadline-only is valid
    TimeBound(deadline=future_deadline())
    # evergreen-only is valid
    TimeBound(evergreen=True)
    # both at once is rejected
    with pytest.raises(ValidationError):
        TimeBound(deadline=future_deadline(), evergreen=True)


def test_review_cadence_requires_evergreen():
    from tests.conftest import future_deadline

    with pytest.raises(ValidationError):
        TimeBound(deadline=future_deadline(), review_cadence="weekly")


def test_duplicate_criterion_ids_rejected():
    with pytest.raises(ValidationError):
        ObjectiveSpec(
            goal="x",
            parent_id=None,
            acceptance_criteria=(
                ProseCriterion(criterion_id="c", prose="a"),
                ProseCriterion(criterion_id="c", prose="b"),
            ),
            time_bound=TimeBound(evergreen=True),
            authored_by="user",
        )


# ---- Persistence and event sourcing ---------------------------------


async def test_valid_objective_persists(tracker):
    spec = make_user_root_spec(goal="ship a book")
    proj = await tracker.create(spec)
    assert proj.goal == "ship a book"
    assert proj.status == ObjectiveStatus.proposed
    assert proj.authored_by == "user"
    # Event exists in the log.
    events = tracker.store.events_for(proj.objective_id)
    assert len(events) == 1
    assert events[0].kind == "objective_created"


async def test_event_log_replay_reconstructs_projection(tracker):
    spec = make_user_root_spec(goal="replay-me")
    proj = await tracker.create(spec)
    await tracker.start(proj.objective_id)
    await tracker.mark_achieved(proj.objective_id, evidence="done")

    events = tracker.store.events_for(proj.objective_id)
    # Independently project from events only.
    rebuilt = project(proj.objective_id, events)
    rebuilt_row = projection_to_state_row(rebuilt)
    live_row = tracker.store.read_state(proj.objective_id)
    assert rebuilt_row == live_row


async def test_sqlite_wal_mode_enabled(tracker):
    with tracker.store._lock:  # noqa: SLF001 (direct access ok for tests)
        cur = tracker.store._conn.execute("PRAGMA journal_mode")  # noqa: SLF001
        mode = cur.fetchone()[0]
    assert mode.lower() == "wal"


async def test_create_assigns_id_if_not_given(tracker):
    spec = make_user_root_spec()
    proj = await tracker.create(spec)
    assert proj.objective_id.startswith("obj-")


async def test_create_respects_caller_id(tracker):
    spec = make_user_root_spec()
    proj = await tracker.create(spec, objective_id="obj-fixed")
    assert proj.objective_id == "obj-fixed"


async def test_mandatory_fields_present_on_projection(tracker):
    spec = make_user_root_spec(goal="seven-field check")
    proj = await tracker.create(spec)
    # id, goal, parent_id-or-root, acceptance_criteria, time_bound,
    # authored_by, status — all present on the public projection.
    assert proj.objective_id
    assert proj.goal == "seven-field check"
    assert proj.parent_id is None
    assert proj.acceptance_criteria
    assert proj.time_bound is not None
    assert proj.authored_by == "user"
    assert proj.status == ObjectiveStatus.proposed


async def test_get_returns_none_for_unknown_id(tracker):
    assert tracker.get("nonexistent") is None


async def test_create_fans_out_via_pyee(tracker):
    received = []
    tracker.subscribe_all(lambda ev: received.append(ev))
    spec = make_user_root_spec()
    proj = await tracker.create(spec)
    # pyee callbacks run in the same event loop.
    # Give asyncio a tick.
    import asyncio

    await asyncio.sleep(0)
    assert any(getattr(ev, "objective_id", None) == proj.objective_id for ev in received)
