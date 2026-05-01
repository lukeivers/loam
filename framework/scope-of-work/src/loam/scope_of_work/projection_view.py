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

"""ScopeProjection — the public read-model exposed by `get()` / `list()`.

Decoupled from runtime.py to keep its size in check and let callers
import the dataclass without pulling the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .projection import ScopeProjectionData
from .spec import (
    BudgetAxis,
    ParentClosePolicy,
    ReversibilityClass,
    ScopeState,
)
from .triggers import (
    active_seconds_elapsed,
    is_stuck,
    remaining_for_axis,
    seconds_since_first_activation,
)


@dataclass
class ScopeProjection:
    """Read-only projection — what every public API call returns."""

    scope_id: str
    state: ScopeState
    goal: str
    constraints: tuple[str, ...]
    reversibility_class: ReversibilityClass
    owner_persona: str | None
    parent_scope_id: str | None
    parent_close_policy: ParentClosePolicy
    last_event_id: int
    last_transition_at: str | None
    pause_reason: str | None
    pending_extension_axis: BudgetAxis | None
    children: tuple[str, ...]
    budget_tokens_remaining: int | None
    budget_money_cents_remaining: int | None
    budget_time_seconds_remaining: int | None
    budget_tokens_consumed: int
    budget_money_cents_consumed: int
    budget_time_seconds_elapsed: int
    success_criteria_met: tuple[str, ...]
    success_criteria_not_met: tuple[str, ...]
    fired_trigger_ids: tuple[str, ...]
    # D0 amendment (primary-persona D3 stuck-detection support).
    expected_duration_seconds: float | None
    first_activated_at: str | None
    seconds_since_first_activation: float | None
    state_events_since_start: int
    is_stuck: bool


def public_projection(proj: ScopeProjectionData) -> ScopeProjection:
    now = datetime.now(timezone.utc)
    time_elapsed = active_seconds_elapsed(proj, now=now)
    return ScopeProjection(
        scope_id=proj.scope_id,
        state=proj.state,
        goal=proj.goal,
        constraints=proj.constraints,
        reversibility_class=proj.reversibility_class,
        owner_persona=proj.owner_persona,
        parent_scope_id=proj.parent_scope_id,
        parent_close_policy=ParentClosePolicy(proj.parent_close_policy),
        last_event_id=proj.last_event_id,
        last_transition_at=proj.last_transition_at,
        pause_reason=proj.pause_reason,
        pending_extension_axis=proj.pending_extension_axis,
        children=tuple(proj.children),
        budget_tokens_remaining=remaining_for_axis(proj, BudgetAxis.tokens, now=now),
        budget_money_cents_remaining=remaining_for_axis(proj, BudgetAxis.money, now=now),
        budget_time_seconds_remaining=remaining_for_axis(proj, BudgetAxis.time, now=now),
        budget_tokens_consumed=proj.ledger.tokens_consumed,
        budget_money_cents_consumed=proj.ledger.money_cents_consumed,
        budget_time_seconds_elapsed=time_elapsed,
        success_criteria_met=tuple(sorted(proj.success_criteria_met)),
        success_criteria_not_met=tuple(sorted(proj.success_criteria_not_met)),
        fired_trigger_ids=tuple(sorted(proj.fired_triggers)),
        expected_duration_seconds=proj.expected_duration_seconds,
        first_activated_at=proj.first_activated_at,
        seconds_since_first_activation=seconds_since_first_activation(proj, now=now),
        state_events_since_start=proj.state_events_since_start,
        is_stuck=is_stuck(proj, now=now),
    )
