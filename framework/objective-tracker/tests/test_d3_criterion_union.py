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

"""D3 — Criterion discriminated union.

Acceptance (brief §D3):
- Each variant has its own Pydantic validation rules and round-trips
  through the event log.
- evaluate_criterion(criterion_id, result, rationale) stores an
  evaluation event; later retrievals return the latest result plus
  full history.
- child_closure is computed by querying the current state of referenced
  children (callers decide when to query).
- scope_success auto-evaluates on scope-state-change events.
"""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError
from pyee.asyncio import AsyncIOEventEmitter

from loam.objective_tracker.spec import (
    ChildClosureCriterion,
    ExternalPredicateCriterion,
    ObjectiveSpec,
    ObjectiveStatus,
    ProseCriterion,
    ScopeSuccessCriterion,
    TimeBound,
)
from tests.conftest import make_child_spec, make_user_root_spec


# ---- Pydantic validation per-variant --------------------------------


def test_prose_criterion_requires_non_empty_prose():
    with pytest.raises(ValidationError):
        ProseCriterion(criterion_id="c", prose="")


def test_scope_success_requires_scope_id():
    with pytest.raises(ValidationError):
        ScopeSuccessCriterion(criterion_id="c", scope_id="")


def test_child_closure_requires_positive_count():
    with pytest.raises(ValidationError):
        ChildClosureCriterion(criterion_id="c", required_count=0)


def test_external_predicate_requires_predicate_id():
    with pytest.raises(ValidationError):
        ExternalPredicateCriterion(criterion_id="c", predicate_id="")


def test_discriminator_picks_correct_variant():
    c = ProseCriterion(criterion_id="c", prose="x")
    assert c.kind == "prose"
    c2 = ScopeSuccessCriterion(criterion_id="c", scope_id="scope-1")
    assert c2.kind == "scope_success"


# ---- Round-trip through the event log -------------------------------


async def test_all_four_variants_persist_and_round_trip(tracker):
    criteria = (
        ProseCriterion(criterion_id="p1", prose="write it"),
        ScopeSuccessCriterion(criterion_id="s1", scope_id="scope-alpha"),
        ChildClosureCriterion(criterion_id="cc1", required_count=2),
        ExternalPredicateCriterion(criterion_id="ep1", predicate_id="my_pred"),
    )
    proj = await tracker.create(
        make_user_root_spec(goal="all variants", criteria=criteria)
    )
    rehydrated = tracker.get(proj.objective_id)
    kinds = [c.kind for c in rehydrated.acceptance_criteria]
    assert kinds == ["prose", "scope_success", "child_closure", "external_predicate"]


# ---- evaluate_criterion ---------------------------------------------


async def test_evaluate_stores_event_and_latest_result(tracker):
    proj = await tracker.create(
        make_user_root_spec(
            criteria=(ProseCriterion(criterion_id="p", prose="x"),)
        )
    )
    after = await tracker.evaluate_criterion(
        proj.objective_id,
        criterion_id="p",
        result="met",
        rationale="looks good",
    )
    assert after.criteria_latest["p"].result == "met"
    assert after.criteria_latest["p"].rationale == "looks good"


async def test_evaluate_keeps_full_history(tracker):
    proj = await tracker.create(
        make_user_root_spec(
            criteria=(ProseCriterion(criterion_id="p", prose="x"),)
        )
    )
    await tracker.evaluate_criterion(
        proj.objective_id, criterion_id="p", result="not_met", rationale="a"
    )
    await tracker.evaluate_criterion(
        proj.objective_id, criterion_id="p", result="met", rationale="b"
    )
    final = tracker.get(proj.objective_id)
    results = [e.result for e in final.criteria_history]
    assert results == ["not_met", "met"]
    assert final.criteria_latest["p"].result == "met"


async def test_evaluate_unknown_criterion_raises(tracker):
    proj = await tracker.create(make_user_root_spec())
    with pytest.raises(ValueError):
        await tracker.evaluate_criterion(
            proj.objective_id, criterion_id="nope", result="met"
        )


async def test_evaluate_invalid_result_raises(tracker):
    proj = await tracker.create(
        make_user_root_spec(
            criteria=(ProseCriterion(criterion_id="p", prose="x"),)
        )
    )
    with pytest.raises(ValueError):
        await tracker.evaluate_criterion(
            proj.objective_id, criterion_id="p", result="maybe"
        )


# ---- child_closure computation on demand ---------------------------


async def test_child_closure_computed_on_demand(tracker):
    root = await tracker.create(
        make_user_root_spec(
            goal="parent",
            criteria=(ChildClosureCriterion(criterion_id="cc", required_count=2),),
        )
    )
    c1 = await tracker.create(make_child_spec(parent_id=root.objective_id, goal="c1"))
    c2 = await tracker.create(make_child_spec(parent_id=root.objective_id, goal="c2"))
    c3 = await tracker.create(make_child_spec(parent_id=root.objective_id, goal="c3"))

    achieved, required, is_met = tracker.child_closure_status(root.objective_id, "cc")
    assert (achieved, required, is_met) == (0, 2, False)

    await tracker.start(c1.objective_id)
    await tracker.mark_achieved(c1.objective_id)
    achieved, required, is_met = tracker.child_closure_status(root.objective_id, "cc")
    assert (achieved, required, is_met) == (1, 2, False)

    await tracker.start(c2.objective_id)
    await tracker.mark_achieved(c2.objective_id)
    achieved, required, is_met = tracker.child_closure_status(root.objective_id, "cc")
    assert (achieved, required, is_met) == (2, 2, True)


# ---- scope_success auto-evaluation ---------------------------------


class _FakeState:
    def __init__(self, value):
        self.value = value


class _FakeEvent:
    def __init__(self, scope_id, to_state_value):
        self.scope_id = scope_id
        self.to_state = _FakeState(to_state_value)
        self.kind = "state_transitioned"


async def test_scope_success_auto_evaluates_on_scope_terminal_event(tracker):
    emitter = AsyncIOEventEmitter()
    scope_id = "scope-auto-1"
    proj = await tracker.create(
        make_user_root_spec(
            goal="wraps scope",
            criteria=(
                ScopeSuccessCriterion(criterion_id="s", scope_id=scope_id),
            ),
        )
    )
    tracker.subscribe_scope_emitter(emitter)

    # Emit a scope "completed" state transition.
    emitter.emit(f"scope:{scope_id}", _FakeEvent(scope_id, "completed"))
    # Give the async listener a tick.
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    latest = tracker.get(proj.objective_id).criteria_latest["s"]
    assert latest.result == "met"
    assert latest.source == "scope_success_auto"


async def test_scope_success_auto_evaluates_not_met_on_failed(tracker):
    emitter = AsyncIOEventEmitter()
    scope_id = "scope-auto-2"
    proj = await tracker.create(
        make_user_root_spec(
            goal="wraps scope",
            criteria=(
                ScopeSuccessCriterion(criterion_id="s", scope_id=scope_id),
            ),
        )
    )
    tracker.subscribe_scope_emitter(emitter)
    emitter.emit(f"scope:{scope_id}", _FakeEvent(scope_id, "failed"))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    latest = tracker.get(proj.objective_id).criteria_latest["s"]
    assert latest.result == "not_met"
    assert "failed" in latest.rationale


async def test_non_scope_success_variants_stay_caller_dispatched(tracker):
    """Only scope_success auto-evaluates. Prose / child_closure /
    external_predicate do NOT auto-fire on any event.
    """
    emitter = AsyncIOEventEmitter()
    proj = await tracker.create(
        make_user_root_spec(
            goal="prose only",
            criteria=(ProseCriterion(criterion_id="p", prose="x"),),
        )
    )
    tracker.subscribe_scope_emitter(emitter)
    emitter.emit("scope:anything", _FakeEvent("anything", "completed"))
    await asyncio.sleep(0)
    # No evaluation recorded.
    assert tracker.get(proj.objective_id).criteria_latest == {}
