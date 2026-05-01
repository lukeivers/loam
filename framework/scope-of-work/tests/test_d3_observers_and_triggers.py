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

"""D3 — observers + declarative escalation triggers.

Acceptance (brief D3):
- An observer subscribed to a scope receives events on state transitions
  and debits.
- A declared `BudgetThreshold` trigger fires an `escalated` event when
  its threshold is crossed.
- A declared `TimeElapsed` trigger fires when wall-clock elapsed
  crosses its value.
- Trigger predicates `EventType`, `SuccessCriterion`, and
  `Reversibility` similarly fire on their declared conditions.
- Observer-add and observer-remove operations write events to the log.
"""

from __future__ import annotations

import asyncio

import pytest

from loam.scope_of_work.events import (
    BudgetDebited,
    ObserverAdded,
    ObserverRemoved,
    StateTransitioned,
    TriggerFired,
)
from loam.scope_of_work.spec import (
    Budget,
    BudgetAxis,
    BudgetThreshold,
    EventTypeTrigger,
    Observer,
    ReversibilityClass,
    ReversibilityTrigger,
    ScopeState,
    SuccessCriterion,
    SuccessCriterionTrigger,
    TimeElapsed,
)
from tests.conftest import make_spec


# ---- observer subscription ------------------------------------------


async def test_observer_receives_state_transitions(runtime):
    proj = await runtime.create(make_spec())
    received: list[str] = []

    def cb(ev):
        received.append(ev.kind)

    runtime.subscribe(proj.scope_id, cb)
    await runtime.start(proj.scope_id)
    await runtime.pause(proj.scope_id)
    await asyncio.sleep(0)  # let pyee flush
    assert "state_transitioned" in received


async def test_observer_receives_debits(runtime):
    proj = await runtime.create(make_spec())
    received: list[str] = []

    def cb(ev):
        received.append(ev.kind)

    runtime.subscribe(proj.scope_id, cb)
    await runtime.start(proj.scope_id)
    await runtime.debit(proj.scope_id, input_tokens=10, output_tokens=5)
    await asyncio.sleep(0)
    assert "budget_debited" in received


async def test_observer_added_event_in_log(runtime):
    proj = await runtime.create(make_spec())
    obs = Observer(observer_id="late-add")
    await runtime.add_observer(proj.scope_id, obs)
    events = runtime.store.events_for(proj.scope_id)
    assert any(isinstance(e, ObserverAdded) and e.observer.observer_id == "late-add" for e in events)


async def test_observer_removed_event_in_log(runtime):
    proj = await runtime.create(make_spec(observers=(Observer(observer_id="o1"),)))
    await runtime.remove_observer(proj.scope_id, "o1")
    events = runtime.store.events_for(proj.scope_id)
    assert any(isinstance(e, ObserverRemoved) and e.observer_id == "o1" for e in events)


# ---- triggers --------------------------------------------------------


async def test_budget_threshold_trigger_fires_and_escalates(runtime):
    spec = make_spec(
        budget=Budget(tokens=100),
        triggers=(
            BudgetThreshold(
                trigger_id="t-low-tokens",
                axis=BudgetAxis.tokens,
                threshold=50,
                reason_on_fire="tokens running low",
            ),
        ),
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    # 60 < threshold of 50 remaining? remaining = 100 - 60 = 40 < 50 → fires.
    p = await runtime.debit(sid, input_tokens=60)
    assert p.state == ScopeState.escalated
    assert "t-low-tokens" in p.fired_trigger_ids
    events = runtime.store.events_for(sid)
    fired = [e for e in events if isinstance(e, TriggerFired)]
    assert any(f.trigger_id == "t-low-tokens" for f in fired)


async def test_time_elapsed_trigger_fires(runtime):
    """We back-date the active_started_at via a manual debit/transition pair."""
    spec = make_spec(
        budget=Budget(tokens=10000, time_seconds=10000),
        triggers=(
            TimeElapsed(trigger_id="t-time", seconds=0),
        ),
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    # TimeElapsed fires on any debit/transition where elapsed >= seconds.
    # With seconds=0, any movement after start triggers.
    p = await runtime.debit(sid, input_tokens=1)
    assert "t-time" in p.fired_trigger_ids


async def test_event_type_trigger_fires_on_named_kind(runtime):
    spec = make_spec(
        triggers=(
            EventTypeTrigger(trigger_id="t-debit", event_type="budget_debited"),
        ),
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    p = await runtime.debit(sid, input_tokens=1)
    assert "t-debit" in p.fired_trigger_ids
    assert p.state == ScopeState.escalated


async def test_success_criterion_trigger_fires_on_not_met(runtime):
    spec = make_spec(
        triggers=(
            SuccessCriterionTrigger(
                trigger_id="t-fail-c1", criterion_id="c1", fire_on="not_met"
            ),
        ),
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    p = await runtime.evaluate_success_criterion(
        sid, criterion_id="c1", result="not_met", note="alignment failed"
    )
    assert "t-fail-c1" in p.fired_trigger_ids
    assert p.state == ScopeState.escalated


async def test_reversibility_trigger_fires_on_irreversible_activation(runtime):
    spec = make_spec(
        reversibility=ReversibilityClass.irreversible,
        triggers=(
            ReversibilityTrigger(trigger_id="t-rev"),
        ),
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    p = await runtime.start(sid)
    # Trigger fires on the active transition; scope ends up escalated.
    assert "t-rev" in p.fired_trigger_ids
    assert p.state == ScopeState.escalated


async def test_trigger_does_not_re_fire_after_escalation(runtime):
    """Triggers are single-shot per scope (proposal §2.5)."""
    spec = make_spec(
        budget=Budget(tokens=100),
        triggers=(
            BudgetThreshold(trigger_id="t1", axis=BudgetAxis.tokens, threshold=50),
        ),
    )
    proj = await runtime.create(spec)
    sid = proj.scope_id
    await runtime.start(sid)
    await runtime.debit(sid, input_tokens=60)  # fires
    # Reactivate after escalation and debit more.
    await runtime.resume(sid)
    p = await runtime.debit(sid, input_tokens=10)  # should NOT re-fire
    fired_count = [
        e for e in runtime.store.events_for(sid)
        if isinstance(e, TriggerFired) and e.trigger_id == "t1"
    ]
    assert len(fired_count) == 1
