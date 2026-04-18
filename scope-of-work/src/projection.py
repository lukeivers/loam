"""Event-log projector.

Given an ordered list of events for a single scope, produce a
`ScopeProjection` (the cached runtime state). The projector is
deterministic — running it twice on the same event sequence produces
the same output — which is the foundation for the upgrade-fidelity
semantic round-trip (v1.1 R1).

The projector lives separate from the runtime so tests and the upgrade
harness can replay event streams without spinning a runtime up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import TypeAdapter

from .events import (
    BudgetDebited,
    BudgetExtended,
    BudgetRefunded,
    ChildLinked,
    ExtensionRejected,
    ExtensionRequested,
    ObserverAdded,
    ObserverRemoved,
    ParentCloseRequested,
    ScopeCreated,
    StateTransitioned,
    SuccessCriterionEvaluated,
    TriggerFired,
)
from .spec import (
    BudgetAxis,
    Observer,
    ReversibilityClass,
    ScopeState,
    Trigger,
)


_OBSERVER_ADAPTER = TypeAdapter(Observer)
_TRIGGER_ADAPTER = TypeAdapter(Trigger)


@dataclass
class BudgetLedger:
    """Per-axis consumed / extended counters.

    `remaining(cap)` returns the budget remaining: cap + extended −
    consumed. When remaining ≤ 0, the axis is exhausted.

    Time is treated specially — `consumed` for the time axis is live
    wall-clock (active_cumulative_seconds at query time), not an event-
    sourced counter. That value is computed outside the ledger (the
    runtime tracks active_started_at and cumulative seconds).
    """

    tokens_consumed: int = 0
    tokens_extended: int = 0
    money_cents_consumed: int = 0
    money_cents_extended: int = 0
    time_seconds_extended: int = 0


@dataclass
class ScopeProjectionData:
    """Internal dataclass used by the projector."""

    scope_id: str
    state: ScopeState = ScopeState.proposed
    goal: str = ""
    constraints: tuple[str, ...] = ()
    reversibility_class: ReversibilityClass = ReversibilityClass.fully_reversible
    owner_persona: str | None = None
    parent_scope_id: str | None = None
    parent_close_policy: str = "TERMINATE"
    budget_cap_tokens: int | None = None
    budget_cap_money_cents: int | None = None
    budget_cap_time_seconds: int | None = None
    ledger: BudgetLedger = field(default_factory=BudgetLedger)
    observers: dict[str, Observer] = field(default_factory=dict)
    triggers: tuple[Trigger, ...] = ()
    success_criteria_ids: tuple[str, ...] = ()
    success_criteria_met: set[str] = field(default_factory=set)
    success_criteria_not_met: set[str] = field(default_factory=set)
    last_event_id: int = 0
    last_transition_at: str | None = None
    pause_reason: str | None = None
    pending_extension_axis: BudgetAxis | None = None
    active_started_at: str | None = None
    active_cumulative_seconds: int = 0
    fired_triggers: set[str] = field(default_factory=set)
    children: list[str] = field(default_factory=list)
    # Debits indexed by call_id for refund reconciliation.
    debits_by_call: dict[str, tuple[int, int, int]] = field(default_factory=dict)


def _as_dt(value: str) -> datetime:
    # ISO-8601 with timezone; fromisoformat handles it in 3.11+.
    return datetime.fromisoformat(value)


def apply_event(proj: ScopeProjectionData, event: Any) -> None:
    """Mutate `proj` in-place with `event`."""
    proj.last_event_id = max(proj.last_event_id, getattr(event, "event_id", 0) or 0)

    if isinstance(event, ScopeCreated):
        proj.state = ScopeState.proposed
        proj.goal = event.goal
        proj.constraints = event.constraints
        proj.reversibility_class = event.reversibility_class
        proj.owner_persona = event.owner_persona
        proj.parent_scope_id = event.parent_scope_id
        proj.parent_close_policy = event.parent_close_policy.value
        proj.budget_cap_tokens = event.budget.tokens
        proj.budget_cap_money_cents = event.budget.money_cents
        proj.budget_cap_time_seconds = event.budget.time_seconds
        proj.triggers = event.escalation_triggers
        proj.observers = {o.observer_id: o for o in event.observers}
        proj.success_criteria_ids = tuple(sc.criterion_id for sc in event.success_criteria)
        proj.last_transition_at = event.created_at
        return

    if isinstance(event, StateTransitioned):
        # Time accounting: when leaving active, accumulate seconds.
        if event.from_state == ScopeState.active and proj.active_started_at:
            try:
                started = _as_dt(proj.active_started_at)
                ended = _as_dt(event.created_at)
                delta = max(0, int((ended - started).total_seconds()))
                proj.active_cumulative_seconds += delta
            except Exception:
                pass
            proj.active_started_at = None
        if event.to_state == ScopeState.active:
            proj.active_started_at = event.created_at
        proj.state = event.to_state
        proj.last_transition_at = event.created_at
        proj.pause_reason = event.pause_reason
        return

    if isinstance(event, BudgetDebited):
        proj.ledger.tokens_consumed += (event.input_tokens + event.output_tokens)
        proj.ledger.money_cents_consumed += event.money_cents
        if event.call_id:
            proj.debits_by_call[event.call_id] = (
                event.input_tokens,
                event.output_tokens,
                event.money_cents,
            )
        return

    if isinstance(event, BudgetRefunded):
        proj.ledger.tokens_consumed -= (event.input_tokens + event.output_tokens)
        proj.ledger.money_cents_consumed -= event.money_cents
        # Clamp at zero — a refund larger than the original debit
        # shouldn't happen, but we never want a negative counter.
        if proj.ledger.tokens_consumed < 0:
            proj.ledger.tokens_consumed = 0
        if proj.ledger.money_cents_consumed < 0:
            proj.ledger.money_cents_consumed = 0
        return

    if isinstance(event, BudgetExtended):
        if event.axis == BudgetAxis.tokens:
            proj.ledger.tokens_extended += event.amount
        elif event.axis == BudgetAxis.money:
            proj.ledger.money_cents_extended += event.amount
        elif event.axis == BudgetAxis.time:
            proj.ledger.time_seconds_extended += event.amount
        if proj.pending_extension_axis == event.axis:
            proj.pending_extension_axis = None
        return

    if isinstance(event, ObserverAdded):
        proj.observers[event.observer.observer_id] = event.observer
        return

    if isinstance(event, ObserverRemoved):
        proj.observers.pop(event.observer_id, None)
        return

    if isinstance(event, TriggerFired):
        proj.fired_triggers.add(event.trigger_id)
        return

    if isinstance(event, ExtensionRequested):
        proj.pending_extension_axis = event.axis
        return

    if isinstance(event, ExtensionRejected):
        if proj.pending_extension_axis == event.axis:
            proj.pending_extension_axis = None
        return

    if isinstance(event, ChildLinked):
        if event.child_scope_id not in proj.children:
            proj.children.append(event.child_scope_id)
        return

    if isinstance(event, ParentCloseRequested):
        # Projection doesn't change — the child is just notified.
        return

    if isinstance(event, SuccessCriterionEvaluated):
        if event.result == "met":
            proj.success_criteria_met.add(event.criterion_id)
            proj.success_criteria_not_met.discard(event.criterion_id)
        else:
            proj.success_criteria_not_met.add(event.criterion_id)
            proj.success_criteria_met.discard(event.criterion_id)
        return

    # Unknown event types fall through harmlessly; forward-compatible
    # for upgrade scenarios where a new event shape is added but the
    # old projector is re-run on a historical stream.


def project(scope_id: str, events: list[Any]) -> ScopeProjectionData:
    proj = ScopeProjectionData(scope_id=scope_id)
    for ev in events:
        apply_event(proj, ev)
    return proj


def projection_to_state_row(proj: ScopeProjectionData) -> dict[str, Any]:
    """Translate the runtime dataclass to a scope_state row dict."""
    import json

    return {
        "scope_id": proj.scope_id,
        "state": proj.state.value,
        "parent_scope_id": proj.parent_scope_id,
        "owner_persona": proj.owner_persona,
        "last_event_id": proj.last_event_id,
        "last_transition_at": proj.last_transition_at or "",
        "pause_reason": proj.pause_reason,
        "goal": proj.goal,
        "reversibility_class": proj.reversibility_class.value,
        "parent_close_policy": proj.parent_close_policy,
        "budget_tokens_cap": proj.budget_cap_tokens,
        "budget_tokens_consumed": proj.ledger.tokens_consumed,
        "budget_tokens_extended": proj.ledger.tokens_extended,
        "budget_money_cents_cap": proj.budget_cap_money_cents,
        "budget_money_cents_consumed": proj.ledger.money_cents_consumed,
        "budget_money_cents_extended": proj.ledger.money_cents_extended,
        "budget_time_seconds_cap": proj.budget_cap_time_seconds,
        "budget_time_seconds_extended": proj.ledger.time_seconds_extended,
        "active_started_at": proj.active_started_at,
        "active_cumulative_seconds": proj.active_cumulative_seconds,
        "observers_json": json.dumps(
            [o.model_dump(mode="json") for o in proj.observers.values()]
        ),
        "triggers_json": json.dumps(
            [t.model_dump(mode="json") for t in proj.triggers]
        ),
        "pending_extension_axis": (
            proj.pending_extension_axis.value if proj.pending_extension_axis else None
        ),
    }
