# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    WorkEdge,
    WorkEdgeCleared,
)
from .spec import (
    Criterion,
    LiftedFrom,
    ObjectiveStatus,
    ParentClosePolicy,
    TimeBound,
    WorkEdgeKind,
)


@dataclass
class CriterionEvalRecord:
    """One evaluation entry — latest result plus full history."""

    criterion_id: str
    result: str
    rationale: str | None
    source: str
    event_id: int


@dataclass(frozen=True)
class WorkEdgeRecord:
    """A folded, currently-active non-tree edge (WMS increment 2).

    `from_id --kind--> to_id` (or, for a `waits_on` on an external
    `party`, `from_id --waits_on--> party` with `to_id is None`). Only
    edges that have NOT been cleared appear in a projection's edge set
    (AC.WI.EDGE.1). Frozen + hashable so a `WorkEdge`/`WorkEdgeCleared`
    pair cancels by set membership during the fold.
    """

    from_id: str
    to_id: str | None
    edge_kind: WorkEdgeKind
    party: str | None = None


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
    # ---- WMS increment 2 — work-item field-groups (AC.WI.1) ----------
    belongs_to_project: str | None = None
    tagged_streams: tuple[str, ...] = ()
    priority: str | None = None
    # The OUTGOING edges this item has recorded and not cleared, folded
    # from its own stream's WorkEdge/WorkEdgeCleared events (AC.WI.EDGE.1).
    # Incoming edges (where this item is the `to`) are resolved at the
    # runtime layer by scanning all items' streams — they are NOT in this
    # per-stream projection. Order-preserving; a cleared edge is removed.
    edges_out: list[WorkEdgeRecord] = field(default_factory=list)


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
        proj.belongs_to_project = event.belongs_to_project
        proj.tagged_streams = tuple(event.tagged_streams)
        proj.priority = event.priority
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
    elif isinstance(event, WorkEdge):
        rec = WorkEdgeRecord(
            from_id=event.objective_id,
            to_id=event.to_id,
            edge_kind=event.edge_kind,
            party=event.party,
        )
        # Re-recording an already-active edge is idempotent (no dup).
        if rec not in proj.edges_out:
            proj.edges_out.append(rec)
        proj.last_event_id = event.event_id
    elif isinstance(event, WorkEdgeCleared):
        rec = WorkEdgeRecord(
            from_id=event.objective_id,
            to_id=event.to_id,
            edge_kind=event.edge_kind,
            party=event.party,
        )
        # Clearing retracts the matching active edge; clearing an absent
        # edge is a no-op (idempotent — no edge fabrication, AC.WI.EDGE.3).
        proj.edges_out = [e for e in proj.edges_out if e != rec]
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
        # ---- WMS increment 2 — work-item field-groups (AC.WI.1) ------
        # The state-cache row carries the new fields so a list_states
        # filter (the projects-lens query) can read them without a full
        # per-objective event replay. All are additive columns with a
        # default-preserving sentinel; the event log stays the source of
        # truth (the cache rebuilds from events alone — AC.WI.2).
        "belongs_to_project": proj.belongs_to_project,
        "tagged_streams_json": json.dumps(list(proj.tagged_streams)),
        "priority": proj.priority,
    }
