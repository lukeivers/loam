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
    ObjectiveStatus,
    ParentClosePolicy,
    ParentCloseEventKind,
    TimeBound,
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


# ---- discriminated union ---------------------------------------------


ObjectiveEvent = Annotated[
    Union[
        ObjectiveCreated,
        StatusTransitioned,
        CriterionEvaluated,
        ScopeBound,
        ParentClosed,
    ],
    Field(discriminator="kind"),
]


_EVENT_CLASSES = [
    ObjectiveCreated,
    StatusTransitioned,
    CriterionEvaluated,
    ScopeBound,
    ParentClosed,
]


def event_from_row(row_kind: str, payload: dict[str, Any]) -> Any:
    """Reconstruct a typed event from (kind, payload) — used on replay."""
    for cls in _EVENT_CLASSES:
        if cls.model_fields["kind"].default == row_kind:
            return cls(**payload)
    raise ValueError(f"Unknown event kind: {row_kind!r}")
