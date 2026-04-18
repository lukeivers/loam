"""Scope-of-work primitive for pOS v2.

Public surface (see docs/api-reference.md for the one-page reference):

    from scope_of_work import ScopeRuntime, ScopeSpec
    from scope_of_work.spec import (
        Budget, Observer, Trigger, ReversibilityClass,
        BudgetThreshold, TimeElapsed, EventTypeTrigger,
        SuccessCriterionTrigger, ReversibilityTrigger,
        BudgetExhaustionPolicy, ParentClosePolicy,
    )
    from scope_of_work.adapter import RealScopeSourceAdapter

The runtime is constructed once per process (or per database file) and
exposes the full lifecycle API — create, start, pause, resume, complete,
fail, cancel, debit, extend, reject, get, list, subscribe.
"""

from __future__ import annotations

from .spec import (
    Budget,
    BudgetAxis,
    BudgetExhaustionPolicy,
    BudgetThreshold,
    EventTypeTrigger,
    Observer,
    ParentClosePolicy,
    ReversibilityClass,
    ReversibilityTrigger,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
    SuccessCriterionTrigger,
    TimeElapsed,
    Trigger,
)
from .projection_view import ScopeProjection
from .runtime import ScopeRuntime

__all__ = [
    "Budget",
    "BudgetAxis",
    "BudgetExhaustionPolicy",
    "BudgetThreshold",
    "EventTypeTrigger",
    "Observer",
    "ParentClosePolicy",
    "ReversibilityClass",
    "ReversibilityTrigger",
    "ScopeProjection",
    "ScopeRuntime",
    "ScopeSpec",
    "ScopeState",
    "SuccessCriterion",
    "SuccessCriterionTrigger",
    "TimeElapsed",
    "Trigger",
]
