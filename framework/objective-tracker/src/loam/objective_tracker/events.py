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

"""Typed event schema for the objective tracker.

Events are the source of truth (event-sourcing; proposal §Persistence).
Every creation, state change, criterion evaluation, scope binding, and
re-open is recorded as one typed event in an append-only log. The
projection cache is rebuildable from the events alone — that is the
round-trip fidelity test in D8.

The discriminated union below is what Pydantic uses to deserialise
rows from `objective_events`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from .spec import (
    Criterion,
    LiftedFrom,
    ObjectiveStatus,
    ParentClosePolicy,
    ParentCloseEventKind,
    TimeBound,
    WorkEdgeKind,
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- event base -------------------------------------------------------


class _EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Every event carries an envelope pointing at its subject. For
    # objective events the subject is the objective; for scope-bound
    # events the scope id is the primary key (see ScopeBound below).
    objective_id: str
    event_id: int = 0  # assigned by the store on append.
    created_at: str = Field(default_factory=_utcnow_iso)

    otel_span_id: str | None = None
    otel_trace_id: str | None = None


# ---- lifecycle --------------------------------------------------------


class ObjectiveCreated(_EventBase):
    """The spec payload is persisted so a cold restart reconstructs the
    full projection with no runtime help."""

    kind: Literal["objective_created"] = "objective_created"
    goal: str
    parent_id: str | None = None
    acceptance_criteria: tuple[Criterion, ...]
    time_bound: TimeBound
    authored_by: str
    owner: str | None = None
    parent_close_policy: ParentClosePolicy
    lifted_from: LiftedFrom | None = None
    """Amendment #38: optional source-document provenance pointer.
    Pre-widening events deserialise with `None` (additive default)."""

    # ---- WMS increment 2 — the work-item field-groups (AC.WI.1) -------
    #
    # Additive optional payload fields mirroring the `ObjectiveSpec`
    # additions. The defaults preserve the pre-increment-2 event shape:
    # a pre-widening `ObjectiveCreated` row deserialises with
    # `belongs_to_project=None`, `tagged_streams=()`, `priority=None`
    # (the D8 round-trip).
    belongs_to_project: str | None = None
    tagged_streams: tuple[str, ...] = ()
    priority: str | None = None


class StatusTransitioned(_EventBase):
    kind: Literal["status_transitioned"] = "status_transitioned"
    from_status: ObjectiveStatus
    to_status: ObjectiveStatus
    evidence: str | None = None
    rationale: str | None = None
    """Used for re_open — mandatory non-empty string (D6)."""


# ---- criterion evaluation --------------------------------------------


class CriterionEvaluated(_EventBase):
    """A criterion's met/not_met result plus optional rationale.

    The tracker records evaluations; callers decide when to dispatch.
    `scope_success` criteria auto-evaluate via the scope-of-work
    emitter subscription (brief §Luke's decisions) — the tracker writes
    a CriterionEvaluated event with `source="scope_success_auto"`.
    """

    kind: Literal["criterion_evaluated"] = "criterion_evaluated"
    criterion_id: str
    result: Literal["met", "not_met"]
    rationale: str | None = None
    source: str = "caller"
    """Who dispatched the evaluation. "caller" for external calls;
    "scope_success_auto" for tracker-internal scope-subscription hits."""


# ---- scope binding (sidecar) -----------------------------------------


class ScopeBound(_EventBase):
    """Binds a scope id to an objective id in the sidecar table.

    This event lives in the objective's event stream (its `objective_id`
    envelope). The sidecar projection `scope_objective_binding` is
    rebuildable from these events alone.
    """

    kind: Literal["scope_bound"] = "scope_bound"
    scope_id: str


# ---- parent-close notifications --------------------------------------


class ParentClosed(_EventBase):
    """A child receives this when its parent transitions to
    achieved | abandoned.

    The child's own state is NOT automatically changed (default policy
    `notify`). Per-child override to `terminate` or `abandon` is
    honoured by the runtime, which writes its own status-transition
    event in addition to this notification.
    """

    kind: Literal["parent_closed"] = "parent_closed"
    parent_id: str
    parent_event: ParentCloseEventKind
    applied_policy: ParentClosePolicy


# ---- WMS increment 2 — the relational graph (WorkEdge events) --------
#
# D-WMS2.2: a non-tree relational edge is a typed event in THIS
# append-only log (a new kind alongside `ObjectiveCreated`), NOT a side
# table and NOT an in-spec field-list. The event envelope's
# `objective_id` is the edge's `from_id` (the edge lives in the `from`
# item's stream); `to_id`, `edge_kind`, and the optional external
# `party` carry the relationship. A `WorkEdge` records an edge; a
# matching `WorkEdgeCleared` (same `from_id`/`to_id`/`edge_kind`)
# retracts it. The projection folds the pair so a cleared edge no longer
# surfaces (AC.WI.EDGE.1) — and the whole graph rebuilds from the events
# alone (AC.WI.2 / the D8 round-trip). An edge as a mutable spec field
# would contradict the frozen spec; an edge in a side table would break
# "projection rebuilds from events alone."


class WorkEdge(_EventBase):
    """Record a non-tree relational edge `from_id --kind--> to_id`.

    The event envelope `objective_id` is the edge's `from_id`. A
    `waits_on` edge may name an external `party` (e.g. "Eric") with
    `to_id` left empty — "the launch waits on an external party". For an
    item-to-item edge `to_id` names the other work item and `party` is
    None (AC.WI.EDGE.1).
    """

    kind: Literal["work_edge"] = "work_edge"
    to_id: str | None = None
    edge_kind: WorkEdgeKind
    party: str | None = None
    """Optional external party a `waits_on` edge names (the work item is
    waiting on someone/something outside the work graph). When set,
    `to_id` is typically None — the wait is on the party, not an item."""


class WorkEdgeCleared(_EventBase):
    """Retract a previously-recorded `WorkEdge` (AC.WI.EDGE.1).

    Matches on `from_id` (the envelope `objective_id`) + `to_id` +
    `edge_kind` + `party`; after clearing, the edge no longer surfaces on
    either endpoint's projection. The append-only retraction (rather than
    a row delete) keeps the event log the single source of truth and
    gives increment 4's edge self-heal a clean mutation path."""

    kind: Literal["work_edge_cleared"] = "work_edge_cleared"
    to_id: str | None = None
    edge_kind: WorkEdgeKind
    party: str | None = None


# ---- discriminated union ---------------------------------------------


ObjectiveEvent = Annotated[
    Union[
        ObjectiveCreated,
        StatusTransitioned,
        CriterionEvaluated,
        ScopeBound,
        ParentClosed,
        WorkEdge,
        WorkEdgeCleared,
    ],
    Field(discriminator="kind"),
]


_EVENT_CLASSES = [
    ObjectiveCreated,
    StatusTransitioned,
    CriterionEvaluated,
    ScopeBound,
    ParentClosed,
    WorkEdge,
    WorkEdgeCleared,
]


def event_from_row(row_kind: str, payload: dict[str, Any]) -> Any:
    """Reconstruct a typed event from (kind, payload) — used on replay."""
    for cls in _EVENT_CLASSES:
        if cls.model_fields["kind"].default == row_kind:
            return cls(**payload)
    raise ValueError(f"Unknown event kind: {row_kind!r}")
