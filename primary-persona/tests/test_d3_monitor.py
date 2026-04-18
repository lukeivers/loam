"""D3 — background-work monitor.

Acceptance (brief D3):
- Monitor starts with the session.
- Handles pyee events in real time.
- Handles 30-sec tick deterministically.
- Awareness block ≤ 1,000 tokens, structured JSON-like, six
  categories, ≤ 5 rows per category.
- Stuck detection fires via the D0 rule (elapsed > 2 × expected,
  no state events).
- Stuck-reason optional second pass populates `detail`.
- Injection is structural (hook fires every UserPromptSubmit).
- Monitor survives per-tick failures.
- Monitor emits its own health via OTel.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scope_of_work.runtime import ScopeRuntime
from scope_of_work.spec import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
)

from src.monitor import (
    AwarenessBlock,
    AwarenessCategory,
    AwarenessRow,
    BackgroundWorkMonitor,
)


def _spec(
    *,
    goal: str = "test scope",
    expected_duration_seconds: float | None = None,
    owner_persona: str | None = None,
) -> ScopeSpec:
    return ScopeSpec(
        goal=goal,
        constraints=(),
        budget=Budget(tokens=1000, money_cents=1000, time_seconds=3600),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="done"),),
        observers=(),
        escalation_triggers=(),
        owner_persona=owner_persona,
        expected_duration_seconds=expected_duration_seconds,
    )


@pytest.fixture
async def runtime(tmp_path: Path):
    rt = ScopeRuntime(db_path=tmp_path / "scope.db")
    yield rt
    rt.close()


# ---- snapshot / block generation ------------------------------------


async def test_block_has_six_categories(runtime):
    mon = BackgroundWorkMonitor(runtime)
    block = mon.on_user_prompt("t1")
    d = block.to_dict()
    for cat in [
        "active",
        "pending_decision",
        "stuck",
        "recently_finished",
        "escalated",
        "failed",
    ]:
        assert cat in d


async def test_block_lists_active_scopes(runtime):
    await runtime.create(_spec(goal="active work"), scope_id="s1")
    await runtime.start("s1")
    mon = BackgroundWorkMonitor(runtime)
    block = mon.on_user_prompt("t1")
    assert len(block.active) == 1
    assert block.active[0].scope_id == "s1"
    assert block.active[0].state == "active"


async def test_block_respects_five_rows_per_category(runtime):
    for i in range(8):
        sid = f"s{i}"
        await runtime.create(_spec(goal=f"scope {i}"), scope_id=sid)
        await runtime.start(sid)
    mon = BackgroundWorkMonitor(runtime)
    block = mon.on_user_prompt("t1")
    assert len(block.active) == 5  # capped


async def test_block_under_token_cap(runtime):
    # Create many scopes; after trimming the block must stay under cap.
    for i in range(20):
        sid = f"big-{i}"
        await runtime.create(_spec(goal="x" * 120), scope_id=sid)
        await runtime.start(sid)
    mon = BackgroundWorkMonitor(runtime)
    block = mon.on_user_prompt("t1")
    assert block.token_estimate() <= AwarenessBlock.MAX_TOKENS


async def test_block_is_json_serialisable(runtime):
    await runtime.create(_spec(), scope_id="s1")
    await runtime.start("s1")
    mon = BackgroundWorkMonitor(runtime)
    s = mon.on_user_prompt("t").to_json()
    json.loads(s)  # must parse cleanly


# ---- stuck detection via D0 rule ------------------------------------


async def test_stuck_scope_appears_in_stuck_category(runtime, monkeypatch):
    await runtime.create(
        _spec(expected_duration_seconds=0.1, goal="stuck-work"), scope_id="s-stuck"
    )
    await runtime.start("s-stuck")

    # Simulate wall-clock elapsed past 2× expected.
    import src.monitor as monitor_mod
    import scope_of_work.triggers as sow_triggers
    import scope_of_work.projection_view as sow_view

    future = datetime.now(timezone.utc) + timedelta(seconds=5)

    class _FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return future if tz is None else future.astimezone(tz)

    monkeypatch.setattr(sow_triggers, "datetime", _FakeDT)
    monkeypatch.setattr(sow_view, "datetime", _FakeDT)

    mon = BackgroundWorkMonitor(runtime)
    block = mon.on_user_prompt("t")
    stuck_ids = {r.scope_id for r in block.stuck}
    assert "s-stuck" in stuck_ids
    # Stuck scope should NOT also appear in active.
    active_ids = {r.scope_id for r in block.active}
    assert "s-stuck" not in active_ids


async def test_stuck_reason_second_pass_populates_detail(runtime, monkeypatch):
    await runtime.create(
        _spec(expected_duration_seconds=0.1, goal="stuck-work"), scope_id="s2"
    )
    await runtime.start("s2")

    # Force stuck-detection to fire.
    import scope_of_work.triggers as sow_triggers
    import scope_of_work.projection_view as sow_view

    future = datetime.now(timezone.utc) + timedelta(seconds=5)

    class _FakeDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return future if tz is None else future.astimezone(tz)

    monkeypatch.setattr(sow_triggers, "datetime", _FakeDT)
    monkeypatch.setattr(sow_view, "datetime", _FakeDT)

    async def reason_fn(scope):
        return f"waiting on a network call for {scope.scope_id}"

    mon = BackgroundWorkMonitor(
        runtime, stuck_reason_fn=reason_fn, stuck_reason_budget=5
    )
    # Run one tick to populate reasons.
    await mon._tick()
    block = mon.on_user_prompt("t")
    assert block.stuck
    assert block.stuck[0].detail is not None
    assert "network" in block.stuck[0].detail


# ---- pending-decision category --------------------------------------


async def test_pending_extension_surfaces_in_pending_category(runtime):
    # Create a scope with a tiny token budget and debit past it to
    # trigger a pending extension.
    spec = ScopeSpec(
        goal="tiny",
        constraints=(),
        budget=Budget(tokens=10),  # intentionally small
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="done"),),
        observers=(),
        escalation_triggers=(),
    )
    await runtime.create(spec, scope_id="pend")
    await runtime.start("pend")
    await runtime.debit("pend", input_tokens=100, output_tokens=0)

    mon = BackgroundWorkMonitor(runtime)
    block = mon.on_user_prompt("t")
    pending_ids = {r.scope_id for r in block.pending_decision}
    assert "pend" in pending_ids


# ---- terminal transitions and recently_finished --------------------


async def test_recently_finished_tracked_via_pyee(runtime):
    mon = BackgroundWorkMonitor(runtime)
    await mon.start()
    try:
        await runtime.create(_spec(), scope_id="ff")
        await runtime.start("ff")
        await runtime.complete("ff", evaluations=[("c1", "met", None)])
        # Give pyee callbacks a chance.
        await asyncio.sleep(0.05)
    finally:
        await mon.stop()
    block = mon.on_user_prompt("t")
    finished_ids = {r.scope_id for r in block.recently_finished}
    assert "ff" in finished_ids


# ---- lifecycle + failure resilience --------------------------------


async def test_monitor_start_and_stop(runtime):
    mon = BackgroundWorkMonitor(runtime, tick_interval_seconds=0.1)
    await mon.start()
    await asyncio.sleep(0.05)
    await mon.stop()
    assert mon._task is None


async def test_monitor_survives_tick_exception(runtime, monkeypatch):
    mon = BackgroundWorkMonitor(runtime, tick_interval_seconds=0.05)

    # Patch _tick to throw once, then succeed.
    call_count = {"n": 0}

    original_tick = mon._tick

    async def flaky_tick():
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("simulated failure")
        await original_tick()

    monkeypatch.setattr(mon, "_tick", flaky_tick)
    await mon.start()
    # Wait for at least 2 ticks.
    await asyncio.sleep(0.25)
    await mon.stop()
    assert call_count["n"] >= 2  # survived the first failure


# ---- structural injection (STATE.md rule #7) -----------------------


async def test_every_userpromptsubmit_produces_a_block(runtime):
    """The injection is structural — the monitor produces a block on
    every call without the persona opting in. This tests the shape of
    the guarantee; the actual hook-level wiring is session-layer code.
    """
    mon = BackgroundWorkMonitor(runtime)
    for i in range(3):
        b = mon.on_user_prompt(f"turn-{i}")
        assert b is not None
        assert isinstance(b, AwarenessBlock)
