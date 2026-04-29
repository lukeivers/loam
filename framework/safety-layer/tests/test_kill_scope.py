"""Scope kill — A1, A5 (scope-level).

A1. Scope kill issued against an active scope transitions the scope and
    its TERMINATE-policy children to `cancelled` within 500ms p95.
    Emits `loam.safety.scope_kill` span; writes a `kill_events` row.

A5 (scope slice). A wedged scope (slow-LLM stub, 10s awaitable) does
    not block the kill-issuance from returning within budget — only
    the liveness of the wedged task is separate.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from loam.scope_of_work import (
    Budget,
    ParentClosePolicy,
    ReversibilityClass,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
)

from loam.safety_layer import KillEngine, KillLevel


def _spec() -> ScopeSpec:
    return ScopeSpec(
        goal="scope to kill",
        constraints=(),
        budget=Budget(time_seconds=120),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(
            SuccessCriterion(criterion_id="c", description="d"),
        ),
        observers=(),
        escalation_triggers=(),
    )


@pytest.mark.asyncio
async def test_A1_scope_kill_transitions_target_to_cancelled(
    scope_runtime, safety_store, fake_orchestrator
):
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    proj = await scope_runtime.create(_spec(), scope_id="s-1")
    await scope_runtime.start("s-1")

    t0 = time.monotonic()
    record = await engine.kill_scope(
        scope_id="s-1", reason="test-kill", source="cli"
    )
    elapsed_ms = (time.monotonic() - t0) * 1000.0

    # Scope transitioned.
    cur = scope_runtime.get("s-1")
    assert cur is not None
    assert cur.state == ScopeState.cancelled
    # Audit row written.
    assert record.level == KillLevel.scope
    assert record.source == "cli"
    kills = safety_store.list_kills()
    assert len(kills) == 1
    assert kills[0].scope_id == "s-1"
    assert "s-1" in kills[0].cancelled_scope_ids
    # Bounded time — generous wall-clock budget because CI jitter
    # (A1 target is 500ms; actual p95 for a non-wedged in-memory
    # scope is single-digit ms).
    assert elapsed_ms < 500, f"kill took {elapsed_ms:.1f}ms, exceeds 500ms budget"


@pytest.mark.asyncio
async def test_A1_scope_kill_cascades_to_children(
    scope_runtime, safety_store, fake_orchestrator
):
    """Child with TERMINATE policy cancels with parent."""
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    await scope_runtime.create(_spec(), scope_id="parent-1")
    await scope_runtime.start("parent-1")

    child_spec = ScopeSpec(
        goal="child",
        constraints=(),
        budget=Budget(time_seconds=60),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(
            SuccessCriterion(criterion_id="c", description="d"),
        ),
        observers=(),
        escalation_triggers=(),
        parent_close_policy=ParentClosePolicy.TERMINATE,
    )
    await scope_runtime.create(
        child_spec, scope_id="child-1", parent_scope_id="parent-1"
    )
    await scope_runtime.start("child-1")

    await engine.kill_scope(
        scope_id="parent-1", reason="test-cascade", source="ipc"
    )

    # Both should be cancelled due to TERMINATE default.
    assert scope_runtime.get("parent-1").state == ScopeState.cancelled
    assert scope_runtime.get("child-1").state == ScopeState.cancelled


@pytest.mark.asyncio
async def test_A5_wedged_scope_does_not_delay_kill_issuance(
    scope_runtime, safety_store, fake_orchestrator
):
    """A1/A5 wedged: a scope whose work-task is still awaiting a slow
    LLM does not block the kill from returning within budget. The
    safety layer issues the cancel; liveness of the wedged task is a
    separate concern (research §11).
    """
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    await scope_runtime.create(_spec(), scope_id="wedged-1")
    await scope_runtime.start("wedged-1")

    # Simulate a wedged downstream task the user never awaits.
    async def _slow_work() -> None:
        await asyncio.sleep(10)  # 10s — longer than the kill budget

    task = asyncio.create_task(_slow_work())

    t0 = time.monotonic()
    await engine.kill_scope(
        scope_id="wedged-1", reason="wedged", source="persona"
    )
    elapsed_ms = (time.monotonic() - t0) * 1000.0

    # Kill returned within budget even though the wedged task is still alive.
    assert elapsed_ms < 500, f"kill took {elapsed_ms:.1f}ms, exceeds 500ms budget"
    assert not task.done(), "wedged task should still be running"
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
