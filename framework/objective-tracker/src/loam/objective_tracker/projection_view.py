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

"""Public read-model for ObjectiveProjectionData.

External consumers receive `ObjectiveProjection` instances — frozen
Pydantic objects whose shape is stable across projection-cache schema
changes. Tests, ODD harnesses, and the scope-of-work dispatcher all
consume this type.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from .projection import CriterionEvalRecord, ObjectiveProjectionData, WorkEdgeRecord
from .spec import (
    Criterion,
    LiftedFrom,
    ObjectiveStatus,
    ParentClosePolicy,
    TimeBound,
    WorkEdgeKind,
)


class CriterionEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    criterion_id: str
    result: str
    rationale: str | None
    source: str
    event_id: int


class WorkEdgeView(BaseModel):
    """Public immutable view of one active non-tree edge (AC.WI.EDGE.1).

    `from_id --edge_kind--> to_id` (or `--waits_on--> party` with
    `to_id is None` for an external-party wait). Surfaced on the
    projection of BOTH endpoints: it appears in the `from` item's
    `edges_out` and the `to` item's `edges_in`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    from_id: str
    to_id: str | None
    edge_kind: WorkEdgeKind
    party: str | None = None


class ObjectiveProjection(BaseModel):
    """Public immutable view of one objective."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    objective_id: str
    goal: str
    parent_id: str | None
    authored_by: str
    owner: str | None
    status: ObjectiveStatus
    time_bound: TimeBound
    acceptance_criteria: tuple[Criterion, ...]
    parent_close_policy: ParentClosePolicy
    last_event_id: int
    last_transition_at: str
    criteria_latest: dict[str, CriterionEvaluation]
    criteria_history: tuple[CriterionEvaluation, ...]
    scope_bindings: tuple[str, ...]
    parent_close_notifications: tuple[dict[str, Any], ...]
    lifted_from: LiftedFrom | None = None
    """Amendment #38: optional source-document provenance pointer
    surfaced from `ObjectiveSpec.lifted_from`. `None` for records
    authored without provenance — preserves the pre-widening shape."""

    # ---- WMS increment 2 — work-item field-groups (AC.WI.1) ----------
    belongs_to_project: str | None = None
    """The project this work item is bound to (resolved at render time
    against the FBM registry by the projects lens). `None` for unbound
    records — preserves the pre-increment-2 shape."""

    tagged_streams: tuple[str, ...] = ()
    """The cross-cutting streams this item is tagged with (the streams
    lens reads this for membership — AC.REPOINT.1). Empty for untagged
    records."""

    priority: str | None = None
    """The priority signal the projects-lens sort reads (AC.PROJ.1).
    Populated this cycle from the `tracker_context` priority vocabulary
    (D-WMS2.5). `None` sorts last."""

    edges_out: tuple[WorkEdgeView, ...] = ()
    """Active non-tree edges where THIS item is the `from` (AC.WI.EDGE.1).
    Empty when no outgoing edge is recorded (no edge fabrication —
    AC.WI.EDGE.3)."""

    edges_in: tuple[WorkEdgeView, ...] = ()
    """Active non-tree edges where THIS item is the `to` (AC.WI.EDGE.1).
    Resolved at the runtime layer by scanning every item's stream; the
    same edge surfaces on both endpoints. Empty when nothing points at
    this item."""

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    def unchecked_criteria(self) -> tuple[Criterion, ...]:
        """Criteria with no 'met' result recorded.

        A criterion is 'unchecked' if it has no latest evaluation or
        its latest evaluation is `not_met`. Callers use this to drive
        ODD walks.
        """
        out: list[Criterion] = []
        for c in self.acceptance_criteria:
            latest = self.criteria_latest.get(c.criterion_id)
            if latest is None or latest.result != "met":
                out.append(c)
        return tuple(out)


def _eval_to_public(rec: CriterionEvalRecord) -> CriterionEvaluation:
    return CriterionEvaluation(
        criterion_id=rec.criterion_id,
        result=rec.result,
        rationale=rec.rationale,
        source=rec.source,
        event_id=rec.event_id,
    )


def _edge_to_public(rec: WorkEdgeRecord) -> WorkEdgeView:
    return WorkEdgeView(
        from_id=rec.from_id,
        to_id=rec.to_id,
        edge_kind=rec.edge_kind,
        party=rec.party,
    )


def public_projection(
    data: ObjectiveProjectionData,
    *,
    edges_in: tuple[WorkEdgeRecord, ...] = (),
) -> ObjectiveProjection:
    """Build the public read-model. `edges_in` is the set of active
    edges pointing AT this item, resolved by the runtime from other
    items' streams (a per-stream projection only sees its own outgoing
    edges — AC.WI.EDGE.1). Defaults to empty so every existing caller
    (which does not pass it) keeps the pre-increment-2 behaviour."""
    assert data.time_bound is not None, (
        "cannot build public projection before ObjectiveCreated has been applied"
    )
    return ObjectiveProjection(
        objective_id=data.objective_id,
        goal=data.goal,
        parent_id=data.parent_id,
        authored_by=data.authored_by,
        owner=data.owner,
        status=data.status,
        time_bound=data.time_bound,
        acceptance_criteria=data.criteria,
        parent_close_policy=data.parent_close_policy,
        last_event_id=data.last_event_id,
        last_transition_at=data.last_transition_at,
        criteria_latest={
            k: _eval_to_public(v) for k, v in data.criteria_latest.items()
        },
        criteria_history=tuple(_eval_to_public(r) for r in data.criteria_history),
        scope_bindings=tuple(data.scope_bindings),
        parent_close_notifications=tuple(data.parent_close_notifications),
        lifted_from=data.lifted_from,
        belongs_to_project=data.belongs_to_project,
        tagged_streams=tuple(data.tagged_streams),
        priority=data.priority,
        edges_out=tuple(_edge_to_public(e) for e in data.edges_out),
        edges_in=tuple(_edge_to_public(e) for e in edges_in),
    )
