"""D1 — core scope primitive (seven-field validation, FSM, replay, query surface).

Acceptance (brief D1):
- Creating a scope with any missing field raises.
- Creating with all seven fields succeeds.
- State transitions produce events in the event log.
- Replaying the event log reconstructs state identically.
- Lifecycle states proposed → active → {paused ↔ active}* → terminal.
- list(filter) supports filtering by state; get(scope_id) returns
  current state including last-transition timestamp.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.scope_of_work.events import ScopeCreated, StateTransitioned
from loam.scope_of_work.projection import project, projection_to_state_row
from loam.scope_of_work.spec import (
    Budget,
    Observer,
    ReversibilityClass,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
)
from tests.conftest import make_spec


# ---- spec validation -------------------------------------------------


def test_missing_goal_field_rejects():
    with pytest.raises(ValidationError):
        ScopeSpec(  # type: ignore[call-arg]
            constraints=(),
            budget=Budget(tokens=1),
            reversibility_class=ReversibilityClass.fully_reversible,
            success_criteria=(),
            observers=(),
            escalation_triggers=(),
        )


def test_missing_constraints_field_rejects():
    with pytest.raises(ValidationError):
        ScopeSpec(  # type: ignore[call-arg]
            goal="x",
            budget=Budget(tokens=1),
            reversibility_class=ReversibilityClass.fully_reversible,
            success_criteria=(),
            observers=(),
            escalation_triggers=(),
        )


def test_missing_budget_field_rejects():
    with pytest.raises(ValidationError):
        ScopeSpec(  # type: ignore[call-arg]
            goal="x",
            constraints=(),
            reversibility_class=ReversibilityClass.fully_reversible,
            success_criteria=(),
            observers=(),
            escalation_triggers=(),
        )


def test_missing_reversibility_class_field_rejects():
    with pytest.raises(ValidationError):
        ScopeSpec(  # type: ignore[call-arg]
            goal="x",
            constraints=(),
            budget=Budget(tokens=1),
            success_criteria=(),
            observers=(),
            escalation_triggers=(),
        )


def test_missing_success_criteria_field_rejects():
    with pytest.raises(ValidationError):
        ScopeSpec(  # type: ignore[call-arg]
            goal="x",
            constraints=(),
            budget=Budget(tokens=1),
            reversibility_class=ReversibilityClass.fully_reversible,
            observers=(),
            escalation_triggers=(),
        )


def test_missing_observers_field_rejects():
    with pytest.raises(ValidationError):
        ScopeSpec(  # type: ignore[call-arg]
            goal="x",
            constraints=(),
            budget=Budget(tokens=1),
            reversibility_class=ReversibilityClass.fully_reversible,
            success_criteria=(),
            escalation_triggers=(),
        )


def test_missing_escalation_triggers_field_rejects():
    with pytest.raises(ValidationError):
        ScopeSpec(  # type: ignore[call-arg]
            goal="x",
            constraints=(),
            budget=Budget(tokens=1),
            reversibility_class=ReversibilityClass.fully_reversible,
            success_criteria=(),
            observers=(),
        )


def test_all_seven_fields_succeeds():
    spec = ScopeSpec(
        goal="ship the primitive",
        constraints=("python only",),
        budget=Budget(tokens=1000),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="done"),),
        observers=(Observer(observer_id="eve"),),
        escalation_triggers=(),
    )
    assert spec.goal == "ship the primitive"
    assert spec.budget.tokens == 1000


def test_budget_with_no_axes_rejects():
    with pytest.raises(ValueError):
        Budget()


# ---- runtime construction --------------------------------------------


async def test_create_records_scope_created_event(runtime):
    proj = await runtime.create(make_spec(goal="alpha"))
    events = runtime.store.events_for(proj.scope_id)
    assert len(events) == 1
    assert isinstance(events[0], ScopeCreated)
    assert events[0].goal == "alpha"


async def test_get_returns_projection_with_last_transition_at(runtime):
    proj = await runtime.create(make_spec())
    fetched = runtime.get(proj.scope_id)
    assert fetched is not None
    assert fetched.last_transition_at  # non-empty timestamp


async def test_get_unknown_scope_returns_none(runtime):
    assert runtime.get("does-not-exist") is None


# ---- FSM lifecycle ---------------------------------------------------


async def test_lifecycle_states_succeed_in_order(runtime):
    proj = await runtime.create(make_spec())
    sid = proj.scope_id
    assert (await runtime.start(sid)).state == ScopeState.active
    assert (await runtime.pause(sid, "rest")).state == ScopeState.paused
    assert (await runtime.resume(sid)).state == ScopeState.active
    p = await runtime.complete(sid, evaluations=[("c1", "met", "ok")])
    assert p.state == ScopeState.completed


async def test_illegal_transition_from_terminal_raises(runtime):
    proj = await runtime.create(make_spec())
    await runtime.start(proj.scope_id)
    await runtime.complete(proj.scope_id, evaluations=[("c1", "met", "ok")])
    with pytest.raises(RuntimeError):
        await runtime.start(proj.scope_id)


async def test_state_transitions_produce_state_transitioned_events(runtime):
    proj = await runtime.create(make_spec())
    await runtime.start(proj.scope_id)
    await runtime.pause(proj.scope_id)
    await runtime.resume(proj.scope_id)
    transitions = [
        e for e in runtime.store.events_for(proj.scope_id)
        if isinstance(e, StateTransitioned)
    ]
    assert [t.to_state for t in transitions] == [
        ScopeState.active,
        ScopeState.paused,
        ScopeState.active,
    ]


# ---- replay determinism ----------------------------------------------


async def test_replay_event_log_reconstructs_state_identically(runtime):
    proj = await runtime.create(make_spec(goal="replay test"))
    sid = proj.scope_id
    await runtime.start(sid)
    await runtime.debit(sid, input_tokens=50, output_tokens=20, prompt_name="p1")
    await runtime.pause(sid, "midway")
    await runtime.resume(sid)
    await runtime.complete(sid, evaluations=[("c1", "met", None)])

    # Capture live state row (cached projection).
    live_row = runtime.store.read_state(sid)
    assert live_row is not None

    # Replay events through projector from scratch.
    events = runtime.store.events_for(sid)
    replayed = project(sid, events)
    replayed_row = projection_to_state_row(replayed)

    # The two rows should be identical except for one bookkeeping field
    # — `active_started_at` is None on completion in both, so this
    # equality is strict.
    for k in replayed_row:
        assert live_row.get(k) == replayed_row[k], f"drift on {k}"


# ---- query surface (D1 monitor-feeder) -------------------------------


async def test_list_filter_by_state(runtime):
    a = await runtime.create(make_spec(goal="a"))
    b = await runtime.create(make_spec(goal="b"))
    c = await runtime.create(make_spec(goal="c"))
    await runtime.start(a.scope_id)
    await runtime.start(b.scope_id)
    await runtime.pause(b.scope_id, "wait")
    # c stays proposed.

    actives = runtime.list(states=[ScopeState.active])
    assert {p.scope_id for p in actives} == {a.scope_id}

    paused = runtime.list(states=[ScopeState.paused])
    assert {p.scope_id for p in paused} == {b.scope_id}

    multi = runtime.list(states=[ScopeState.active, ScopeState.paused])
    assert {p.scope_id for p in multi} == {a.scope_id, b.scope_id}


async def test_list_filter_by_owner_persona(runtime):
    eve = await runtime.create(make_spec(owner_persona="eve"))
    cal = await runtime.create(make_spec(owner_persona="cal"))
    eves = runtime.list(owner_persona="eve")
    assert [p.scope_id for p in eves] == [eve.scope_id]


async def test_list_filter_pending_extension(runtime):
    """Monitor needs to find scopes awaiting extension responses."""
    spec = make_spec(budget=Budget(tokens=10))
    proj = await runtime.create(spec)
    await runtime.start(proj.scope_id)
    # Burn the budget — request_extension default fires.
    await runtime.debit(proj.scope_id, input_tokens=20)
    pending = runtime.list(include_pending_extension=True)
    assert len(pending) == 1
    assert pending[0].scope_id == proj.scope_id
    assert pending[0].pending_extension_axis is not None
