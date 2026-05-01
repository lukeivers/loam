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

"""Scope-of-work primitive for pOS v2.

Public surface (see docs/api-reference.md for the one-page reference):

    from loam.scope_of_work import ScopeRuntime, ScopeSpec
    from loam.scope_of_work.spec import (
        Budget, Observer, Trigger, ReversibilityClass,
        BudgetThreshold, TimeElapsed, EventTypeTrigger,
        SuccessCriterionTrigger, ReversibilityTrigger,
        BudgetExhaustionPolicy, ParentClosePolicy,
    )
    from loam.scope_of_work.adapter import RealScopeSourceAdapter

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
