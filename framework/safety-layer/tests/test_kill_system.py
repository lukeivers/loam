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

from loam.scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    ScopeState,
    SuccessCriterion,
)

from loam.safety_layer import KillEngine, KillLevel


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


# ---- amendment #19 (sites 2, 3, 4) ----------------------------------


class _RaisingPauseSystemOrchestrator:
    """pause_activation raises; request_stop is a no-op."""

    def __init__(self) -> None:
        self._stop_requested = False

    def pause_activation(self, reason: str) -> None:
        raise RuntimeError("pause-system-boom")

    def resume_activation(self) -> None:
        pass

    def request_stop(self) -> None:
        self._stop_requested = True

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested


class _RaisingStopSystemOrchestrator:
    """pause_activation works; request_stop raises."""

    def __init__(self) -> None:
        self._paused = False
        self._paused_reason: str | None = None
        self._stop_requested = False

    def pause_activation(self, reason: str) -> None:
        self._paused = True
        self._paused_reason = reason

    def resume_activation(self) -> None:
        self._paused = False
        self._paused_reason = None

    def request_stop(self) -> None:
        raise RuntimeError("request-stop-blew-up")

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def stop_requested(self) -> bool:
        return self._stop_requested


@pytest.mark.asyncio
async def test_amendment_19_system_kill_pause_failure_is_surfaced(
    scope_runtime, safety_store
):
    """S1 (amendment #19, site 2): pause failure surfaces in audit
    reason; system-kill state row + kill audit still land."""
    orch = _RaisingPauseSystemOrchestrator()
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=orch,
    )
    nonce = engine.request_system_kill_nonce()
    record = await engine.kill_system(
        reason="system-kill-pause-raises", source="ipc", nonce=nonce
    )
    assert "pause_failed:RuntimeError" in record.reason
    # State row still persisted — the next bootstrap contract (A4) is
    # not broken by the pause failure.
    active = safety_store.active_system_kill()
    assert active is not None


@pytest.mark.asyncio
async def test_amendment_19_system_kill_cancel_failure_records_failed_ids(
    scope_runtime, safety_store, fake_orchestrator
):
    """S1 (amendment #19, site 3): a per-scope cancel failure must be
    recorded in the new KillEventRecord.failed_scope_ids field so
    callers can distinguish "nothing to cancel" from "cancel raised."
    cancelled_scope_ids preserves its prior meaning (only successful
    cancellations)."""
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    # Create three active scopes. Monkey-patch scope_runtime.cancel so
    # one id always fails; the other two cancel normally.
    for sid in ("s-ok-a", "s-bad", "s-ok-b"):
        await scope_runtime.create(_spec(), scope_id=sid)
        await scope_runtime.start(sid)

    real_cancel = scope_runtime.cancel

    async def flaky_cancel(scope_id: str, reason: str):
        if scope_id == "s-bad":
            raise RuntimeError("cancel-blew-up")
        return await real_cancel(scope_id, reason=reason)

    scope_runtime.cancel = flaky_cancel  # type: ignore[assignment]

    nonce = engine.request_system_kill_nonce()
    record = await engine.kill_system(
        reason="cancel-failure-surface", source="ipc", nonce=nonce
    )

    assert "s-bad" in record.failed_scope_ids
    assert "s-bad" not in record.cancelled_scope_ids
    assert set(record.cancelled_scope_ids) == {"s-ok-a", "s-ok-b"}


@pytest.mark.asyncio
async def test_amendment_19_system_kill_request_stop_failure_record_returned(
    scope_runtime, safety_store
):
    """S1 (amendment #19, site 4): when request_stop raises, the
    KillEventRecord must still be returned, the state row must still be
    persisted, and the OTel emitter must surface the failure. Contract
    "kill_system returns a KillEventRecord on issued system-kill" is
    preserved."""
    orch = _RaisingStopSystemOrchestrator()
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=orch,
    )
    nonce = engine.request_system_kill_nonce()
    record = await engine.kill_system(
        reason="stop-raises", source="ipc", nonce=nonce
    )
    # Record returned, state row present.
    assert record.level == KillLevel.system
    assert safety_store.active_system_kill() is not None
    # The fake's stop_requested flag stays False because request_stop
    # raised before setting it (by construction above).
    assert orch.stop_requested is False


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
