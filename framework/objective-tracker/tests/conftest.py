"""Shared pytest fixtures for the objective-tracker test suite."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loam.objective_tracker.runtime import ObjectiveTracker  # noqa: E402
from loam.objective_tracker.spec import (  # noqa: E402
    ObjectiveSpec,
    ParentClosePolicy,
    ProseCriterion,
    TimeBound,
)


@pytest.fixture
async def tracker(tmp_path):
    db = tmp_path / "objectives.db"
    rt = ObjectiveTracker(db_path=db)
    yield rt
    rt.close()


def future_deadline(days: int = 7) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days)


def make_user_root_spec(
    *,
    goal: str = "root goal",
    criteria=None,
    evergreen: bool = True,
    review_cadence: str | None = "weekly",
    parent_close_policy: ParentClosePolicy = ParentClosePolicy.notify,
    owner: str | None = None,
) -> ObjectiveSpec:
    """User-authored root objective with a prose criterion by default."""
    tb = (
        TimeBound(evergreen=True, review_cadence=review_cadence)
        if evergreen
        else TimeBound(deadline=future_deadline())
    )
    if criteria is None:
        criteria = (ProseCriterion(criterion_id="root-c1", prose="root is done"),)
    return ObjectiveSpec(
        goal=goal,
        parent_id=None,
        acceptance_criteria=tuple(criteria),
        time_bound=tb,
        authored_by="user",
        owner=owner,
        parent_close_policy=parent_close_policy,
    )


def make_child_spec(
    *,
    parent_id: str,
    goal: str = "child goal",
    criteria=None,
    authored_by: str = "user",
    parent_close_policy: ParentClosePolicy = ParentClosePolicy.notify,
    evergreen: bool = False,
) -> ObjectiveSpec:
    tb = (
        TimeBound(evergreen=True)
        if evergreen
        else TimeBound(deadline=future_deadline())
    )
    if criteria is None:
        criteria = (ProseCriterion(criterion_id="child-c1", prose="child is done"),)
    return ObjectiveSpec(
        goal=goal,
        parent_id=parent_id,
        acceptance_criteria=tuple(criteria),
        time_bound=tb,
        authored_by=authored_by,
        parent_close_policy=parent_close_policy,
    )
