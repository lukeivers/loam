"""System kill — A3, A4, A5 (system slice), ruling #2 (clean exit).

A3. System kill requires the two-step confirm (IPC nonce). On commit:
    pause + cancel all scopes + write system_kill_state + call
    request_stop. Within 5s p95.
A4. Next orchestrator bootstrap reads system_kill_state and refuses to
    activate any scope until `clear-system-kill` runs (records
    `system_kill_cleared` row).
Ruling #2. Orchestrator exits 0 via request_stop.
"""

from __future__ import annotations

import time

import pytest

from scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
)

from safety_layer import KillEngine, KillLevel


def _spec() -> ScopeSpec:
    return ScopeSpec(
        goal="system test",
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
async def test_A3_system_kill_requires_nonce_on_ipc(
    scope_runtime, safety_store, fake_orchestrator
):
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )

    # No nonce → refused.
    with pytest.raises(ValueError, match="nonce"):
        await engine.kill_system(reason="no-nonce", source="ipc")

    # Wrong nonce → refused.
    with pytest.raises(ValueError, match="nonce"):
        await engine.kill_system(
            reason="bogus", source="ipc", nonce="not-a-real-nonce"
        )

    # Correct flow.
    nonce = engine.request_system_kill_nonce()
    assert isinstance(nonce, str) and len(nonce) > 0

    record = await engine.kill_system(
        reason="test-system-kill", source="ipc", nonce=nonce
    )
    assert record.level == KillLevel.system

    # Nonce is single-use — second call fails.
    with pytest.raises(ValueError, match="nonce"):
        await engine.kill_system(
            reason="retry", source="ipc", nonce=nonce
        )


@pytest.mark.asyncio
async def test_A3_system_kill_cancels_all_and_calls_request_stop(
    scope_runtime, safety_store, fake_orchestrator
):
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    for i in range(2):
        await scope_runtime.create(_spec(), scope_id=f"s-{i}")
        await scope_runtime.start(f"s-{i}")

    nonce = engine.request_system_kill_nonce()
    t0 = time.monotonic()
    record = await engine.kill_system(
        reason="system-kill-test", source="ipc", nonce=nonce
    )
    elapsed_ms = (time.monotonic() - t0) * 1000.0

    # Ruling #2: clean exit via request_stop.
    assert fake_orchestrator.stop_requested
    # All scopes cancelled.
    for i in range(2):
        assert scope_runtime.get(f"s-{i}").state == ScopeState.cancelled
    # State row written.
    active = safety_store.active_system_kill()
    assert active is not None
    assert active.cleared_at is None
    assert active.reason == "system-kill-test"
    # Kill audit row.
    assert record.level == KillLevel.system
    # Bounded A3 = 5s p95.
    assert elapsed_ms < 5000


@pytest.mark.asyncio
async def test_A4_system_kill_blocks_future_activation_until_cleared(
    scope_runtime, safety_store, fake_orchestrator
):
    """A4. The store tracks system-kill state so the next bootstrap's
    activate_scope wrap refuses activation. We verify the store reads
    + the clear operation records a new row."""
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    nonce = engine.request_system_kill_nonce()
    await engine.kill_system(reason="r", source="ipc", nonce=nonce)

    # Active.
    assert safety_store.active_system_kill() is not None

    # Clear it.
    ok = safety_store.clear_system_kill(reason="manual clear")
    assert ok is True

    # Now active is None.
    assert safety_store.active_system_kill() is None
