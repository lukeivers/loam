"""Typed scope-event schema.

Events are the source of truth (proposal §2.3 event-sourcing). Every
state change, budget debit, observer mutation, extension request, and
trigger fire is recorded as one typed event in an append-only log.

The discriminated union below is what Pydantic uses to deserialise
rows from `scope_events`. Reconstruction-from-events is deterministic
— replay the events in order, and you get back the current state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from .spec import (
    Budget,
    BudgetAxis,
    Observer,
    ParentClosePolicy,
    ReversibilityClass,
    ScopeState,
    SuccessCriterion,
    Trigger,
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- event base -------------------------------------------------------


class _EventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Event envelope; every event carries these.
    scope_id: str
    event_id: int = 0  # assigned by the store on append.
    created_at: str = Field(default_factory=_utcnow_iso)
    # Span/trace cross-correlation (populated when the runtime's OTel
    # tracer is emitting a span at the moment of write).
    otel_span_id: str | None = None
    otel_trace_id: str | None = None


# ---- lifecycle events -------------------------------------------------


class ScopeCreated(_EventBase):
    kind: Literal["scope_created"] = "scope_created"
    # Persist the seven-field spec so a cold restart rebuilds projection
    # with no runtime help.
    goal: str
    constraints: tuple[str, ...]
    budget: Budget
    reversibility_class: ReversibilityClass
    success_criteria: tuple[SuccessCriterion, ...]
    observers: tuple[Observer, ...]
    escalation_triggers: tuple[Trigger, ...]
    owner_persona: str | None
    parent_close_policy: ParentClosePolicy
    parent_scope_id: str | None = None
    # D0 amendment: opt-in stuck-detection hint for the background-
    # work monitor (primary-persona layer D3). See ScopeSpec for
    # semantics.
    expected_duration_seconds: float | None = None


class StateTransitioned(_EventBase):
    kind: Literal["state_transitioned"] = "state_transitioned"
    from_state: ScopeState
    to_state: ScopeState
    reason: str | None = None
    pause_reason: str | None = None


# ---- budget events ----------------------------------------------------


class BudgetDebited(_EventBase):
    kind: Literal["budget_debited"] = "budget_debited"
    # Debits are recorded per-axis per-event; a single LLM call writes
    # one event with input/output tokens and (possibly) money delta.
    prompt_name: str | None = None
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    money_cents: int = 0
    call_id: str | None = None  # correlation id for refunds


class BudgetRefunded(_EventBase):
    """Reverses a prior BudgetDebited event.

    Used when an LLM call was debited but subsequently failed at the
    network layer or returned unusable output. The projector treats
    refund as a negative debit.
    """

    kind: Literal["budget_refunded"] = "budget_refunded"
    call_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    money_cents: int = 0
    reason: str | None = None


class BudgetExtended(_EventBase):
    """Grants additional budget on one axis (response to extension request)."""

    kind: Literal["budget_extended"] = "budget_extended"
    axis: BudgetAxis
    amount: int = Field(ge=0)


# ---- observer events --------------------------------------------------


class ObserverAdded(_EventBase):
    kind: Literal["observer_added"] = "observer_added"
    observer: Observer


class ObserverRemoved(_EventBase):
    kind: Literal["observer_removed"] = "observer_removed"
    observer_id: str


# ---- trigger events ---------------------------------------------------


class TriggerFired(_EventBase):
    kind: Literal["trigger_fired"] = "trigger_fired"
    trigger_id: str
    trigger_kind: str
    triggering_value: Any | None = None
    reason: str | None = None


# ---- extension-request events -----------------------------------------


class ExtensionRequested(_EventBase):
    """Emitted when a budget axis is exhausted and the default policy
    (request_extension) fires. The scope pauses and awaits a response
    via `extend(axis, amount)` or `reject()` — see runtime."""

    kind: Literal["extension_requested"] = "extension_requested"
    axis: BudgetAxis
    remaining: int
    cap: int
    reason: str


class ExtensionRejected(_EventBase):
    """Emitted when `reject()` is called on a pending extension request."""

    kind: Literal["extension_rejected"] = "extension_rejected"
    axis: BudgetAxis


# ---- hierarchy events -------------------------------------------------


class ChildLinked(_EventBase):
    """Emitted on the PARENT when a child scope is spawned.

    The child's own `scope_created` event also carries `parent_scope_id`;
    this event lives on the parent so queries for "list children of X"
    are a one-pass scan of the parent's event stream.
    """

    kind: Literal["child_linked"] = "child_linked"
    child_scope_id: str


class ParentCloseRequested(_EventBase):
    """A child receives this when its parent applied REQUEST_CANCEL.

    The child can then honour or reject; the runtime records the
    response as a subsequent state transition.
    """

    kind: Literal["parent_close_requested"] = "parent_close_requested"
    parent_scope_id: str


# ---- success-criterion evaluation -------------------------------------


class SuccessCriterionEvaluated(_EventBase):
    kind: Literal["success_criterion_evaluated"] = "success_criterion_evaluated"
    criterion_id: str
    result: Literal["met", "not_met"]
    note: str | None = None


# ---- discriminated union ---------------------------------------------


ScopeEvent = Annotated[
    Union[
        ScopeCreated,
        StateTransitioned,
        BudgetDebited,
        BudgetRefunded,
        BudgetExtended,
        ObserverAdded,
        ObserverRemoved,
        TriggerFired,
        ExtensionRequested,
        ExtensionRejected,
        ChildLinked,
        ParentCloseRequested,
        SuccessCriterionEvaluated,
    ],
    Field(discriminator="kind"),
]


_EVENT_CLASSES = [
    ScopeCreated,
    StateTransitioned,
    BudgetDebited,
    BudgetRefunded,
    BudgetExtended,
    ObserverAdded,
    ObserverRemoved,
    TriggerFired,
    ExtensionRequested,
    ExtensionRejected,
    ChildLinked,
    ParentCloseRequested,
    SuccessCriterionEvaluated,
]


def event_from_row(row_kind: str, payload: dict[str, Any]) -> Any:
    """Reconstruct a typed event from (kind, payload) — used on replay."""
    for cls in _EVENT_CLASSES:
        if cls.model_fields["kind"].default == row_kind:
            return cls(**payload)
    raise ValueError(f"Unknown event kind: {row_kind!r}")
