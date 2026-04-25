"""Projection: fold events into current state.

The projection is deterministic — replay the events in order and you
get back the current state. This is the upgrade-fidelity guarantee
(D8 / v1.1 R1): capture a projection pre-upgrade, replay post-upgrade,
assert equivalence.

Public read-model: `ObjectiveProjection` in projection_view.py.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Sequence

from .events import (
    CriterionEvaluated,
    ObjectiveCreated,
    ParentClosed,
    ScopeBound,
    StatusTransitioned,
)
from .spec import (
    Criterion,
    LiftedFrom,
    ObjectiveStatus,
    ParentClosePolicy,
    TimeBound,
)


@dataclass
class CriterionEvalRecord:
    """One evaluation entry — latest result plus full history."""

    criterion_id: str
    result: str
    rationale: str | None
    source: str
    event_id: int


@dataclass
class ObjectiveProjectionData:
    """Folded projection of one objective.

    This is the internal representation. The public read-model
    (`ObjectiveProjection`) is a pared-down projection of this.
    """

    objective_id: str
    goal: str = ""
    parent_id: str | None = None
    authored_by: str = ""
    owner: str | None = None
    status: ObjectiveStatus = ObjectiveStatus.proposed
    time_bound: TimeBound | None = None
    criteria: tuple[Criterion, ...] = ()
    parent_close_policy: ParentClosePolicy = ParentClosePolicy.notify
    lifted_from: LiftedFrom | None = None
    last_event_id: int = 0
    last_transition_at: str = ""
    # criterion_id -> latest evaluation record
    criteria_latest: dict[str, CriterionEvalRecord] = field(default_factory=dict)
    # full history list (event-order) of evaluation records
    criteria_history: list[CriterionEvalRecord] = field(default_factory=list)
    scope_bindings: list[str] = field(default_factory=list)
    parent_close_notifications: list[dict[str, Any]] = field(default_factory=list)


def apply_event(proj: ObjectiveProjectionData, event: Any) -> ObjectiveProjectionData:
    """Apply one event to the projection. Pure — returns a new object."""
    if isinstance(event, ObjectiveCreated):
        proj.goal = event.goal
        proj.parent_id = event.parent_id
        proj.authored_by = event.authored_by
        proj.owner = event.owner
        proj.time_bound = event.time_bound
        proj.criteria = event.acceptance_criteria
        proj.parent_close_policy = event.parent_close_policy
        proj.lifted_from = event.lifted_from
        proj.status = ObjectiveStatus.proposed
        proj.last_event_id = event.event_id
        proj.last_transition_at = event.created_at
    elif isinstance(event, StatusTransitioned):
        proj.status = event.to_status
        proj.last_event_id = event.event_id
        proj.last_transition_at = event.created_at
    elif isinstance(event, CriterionEvaluated):
        rec = CriterionEvalRecord(
            criterion_id=event.criterion_id,
            result=event.result,
            rationale=event.rationale,
            source=event.source,
            event_id=event.event_id,
        )
        proj.criteria_latest[event.criterion_id] = rec
        proj.criteria_history.append(rec)
        proj.last_event_id = event.event_id
    elif isinstance(event, ScopeBound):
        if event.scope_id not in proj.scope_bindings:
            proj.scope_bindings.append(event.scope_id)
        proj.last_event_id = event.event_id
    elif isinstance(event, ParentClosed):
        proj.parent_close_notifications.append(
            {
                "parent_id": event.parent_id,
                "parent_event": event.parent_event.value,
                "applied_policy": event.applied_policy.value,
                "event_id": event.event_id,
                "at": event.created_at,
            }
        )
        proj.last_event_id = event.event_id
    else:
        raise ValueError(f"Unknown event type on apply: {type(event)!r}")
    return proj


def project(objective_id: str, events: Sequence[Any]) -> ObjectiveProjectionData:
    """Fold events into a fresh projection."""
    proj = ObjectiveProjectionData(objective_id=objective_id)
    for ev in events:
        apply_event(proj, ev)
    return proj


def projection_to_state_row(proj: ObjectiveProjectionData) -> dict[str, Any]:
    """Flatten the projection into the objective_state cache row."""
    latest = {
        k: {
            "result": v.result,
            "rationale": v.rationale,
            "source": v.source,
            "event_id": v.event_id,
        }
        for k, v in proj.criteria_latest.items()
    }
    return {
        "objective_id": proj.objective_id,
        "goal": proj.goal,
        "parent_id": proj.parent_id,
        "authored_by": proj.authored_by,
        "owner": proj.owner,
        "status": proj.status.value,
        "time_bound_json": proj.time_bound.model_dump_json() if proj.time_bound else "{}",
        "criteria_json": json.dumps(
            [c.model_dump(mode="json") for c in proj.criteria], default=str
        ),
        "parent_close_policy": proj.parent_close_policy.value,
        "last_event_id": proj.last_event_id,
        "last_transition_at": proj.last_transition_at,
        "criteria_latest_json": json.dumps(latest, default=str),
        "lifted_from_json": (
            proj.lifted_from.model_dump_json() if proj.lifted_from else "null"
        ),
    }
