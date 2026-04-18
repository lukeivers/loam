"""Declarative trigger evaluation.

Triggers are Pydantic discriminated-union predicates (see `spec.py`).
This module owns the evaluation logic: given a current projection and
a single event, does a trigger fire?

Design note (proposal §2.5, §6): evaluation is O(events × triggers) per
scope. For the personal-OS cardinality (single-user, typically <10
triggers per scope) this is trivial; the evaluator short-circuits on
event kind so most triggers return False immediately.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .events import BudgetDebited, StateTransitioned, SuccessCriterionEvaluated
from .projection import ScopeProjectionData
from .spec import (
    BudgetAxis,
    BudgetThreshold,
    EventTypeTrigger,
    ReversibilityTrigger,
    ScopeState,
    SuccessCriterionTrigger,
    TimeElapsed,
    Trigger,
)


def remaining_for_axis(
    proj: ScopeProjectionData, axis: BudgetAxis, *, now: datetime | None = None
) -> int | None:
    """Remaining budget on an axis. None if no cap declared."""
    if axis == BudgetAxis.tokens:
        cap = proj.budget_cap_tokens
        if cap is None:
            return None
        return cap + proj.ledger.tokens_extended - proj.ledger.tokens_consumed
    if axis == BudgetAxis.money:
        cap = proj.budget_cap_money_cents
        if cap is None:
            return None
        return cap + proj.ledger.money_cents_extended - proj.ledger.money_cents_consumed
    if axis == BudgetAxis.time:
        cap = proj.budget_cap_time_seconds
        if cap is None:
            return None
        elapsed = active_seconds_elapsed(proj, now=now)
        return cap + proj.ledger.time_seconds_extended - elapsed
    raise ValueError(f"unknown axis {axis}")


def active_seconds_elapsed(
    proj: ScopeProjectionData, *, now: datetime | None = None
) -> int:
    """Cumulative active-seconds including the current active span."""
    elapsed = proj.active_cumulative_seconds
    if proj.state == ScopeState.active and proj.active_started_at:
        try:
            started = datetime.fromisoformat(proj.active_started_at)
            current = now or datetime.now(tz=started.tzinfo)
            elapsed += max(0, int((current - started).total_seconds()))
        except Exception:
            pass
    return elapsed


def seconds_since_first_activation(
    proj: ScopeProjectionData, *, now: datetime | None = None
) -> float | None:
    """Wall-clock seconds since the scope first became active.

    Returns None if the scope has never been activated. Unlike
    `active_seconds_elapsed`, this includes time spent paused. It is
    the clock stuck-detection measures against.
    """
    if proj.first_activated_at is None:
        return None
    try:
        started = datetime.fromisoformat(proj.first_activated_at)
    except Exception:
        return None
    current = now or datetime.now(tz=started.tzinfo)
    return max(0.0, (current - started).total_seconds())


def is_stuck(
    proj: ScopeProjectionData,
    *,
    multiplier: float = 2.0,
    now: datetime | None = None,
) -> bool:
    """Deterministic stuck-detection (brief D0 + D3).

    A scope is stuck when:
      1. It declared `expected_duration_seconds` (opt-in).
      2. It is currently in a non-terminal state.
      3. It has had no state_transitioned events after the initial
         `proposed → active` transition.
      4. Wall-clock elapsed since first activation exceeds
         `multiplier × expected_duration_seconds`.

    Default multiplier is 2.0 (Luke's decision, brief §"Luke's
    decisions"). Scopes without `expected_duration_seconds` are never
    stuck (the field is opt-in).
    """
    from .policies import is_terminal

    if proj.expected_duration_seconds is None:
        return False
    if is_terminal(proj.state):
        return False
    if proj.first_activated_at is None:
        return False
    if proj.state_events_since_start > 0:
        return False
    elapsed = seconds_since_first_activation(proj, now=now)
    if elapsed is None:
        return False
    return elapsed > multiplier * proj.expected_duration_seconds


def evaluate_trigger(
    trigger: Trigger, proj: ScopeProjectionData, event: Any, *, now: datetime | None = None
) -> tuple[bool, Any]:
    """Return (fires, triggering_value) for the given trigger/event pair.

    `triggering_value` is a small serialisable summary of why the
    trigger fired — recorded on the `trigger_fired` event for audit.
    """
    # Short-circuit: a trigger already fired on this scope is not
    # re-evaluated. (Triggers are single-shot; re-arming is a future
    # extension that would require an explicit reset event.)
    if trigger.trigger_id in proj.fired_triggers:
        return False, None

    if isinstance(trigger, BudgetThreshold):
        # Evaluate on debit events (tokens/money) and any state change
        # (time axis).
        remaining = remaining_for_axis(proj, trigger.axis, now=now)
        if remaining is None:
            return False, None
        if remaining < trigger.threshold:
            return True, {"axis": trigger.axis.value, "remaining": remaining}
        return False, None

    if isinstance(trigger, TimeElapsed):
        elapsed = active_seconds_elapsed(proj, now=now)
        if elapsed >= trigger.seconds:
            return True, {"elapsed_seconds": elapsed}
        return False, None

    if isinstance(trigger, EventTypeTrigger):
        # Fires the first time an event of the declared kind appears.
        if getattr(event, "kind", None) == trigger.event_type:
            return True, {"event_kind": trigger.event_type}
        return False, None

    if isinstance(trigger, SuccessCriterionTrigger):
        if isinstance(event, SuccessCriterionEvaluated):
            if event.criterion_id == trigger.criterion_id and event.result == trigger.fire_on:
                return True, {
                    "criterion_id": event.criterion_id,
                    "result": event.result,
                }
        return False, None

    if isinstance(trigger, ReversibilityTrigger):
        # Evaluate on state transitions INTO active (so the safety layer
        # can escalate irreversible actions before they execute).
        if isinstance(event, StateTransitioned) and event.to_state == ScopeState.active:
            if proj.reversibility_class == trigger.match_class:
                return True, {"class": trigger.match_class.value}
        return False, None

    return False, None
