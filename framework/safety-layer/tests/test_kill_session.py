"""Session kill — A2, A5 (session slice).

A2. Session kill calls `pause_activation("safety:session_kill")`,
    cancels every active scope, writes kill_events, emits OTel within
    2s p95.
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
async def test_A2_session_kill_pauses_activation_and_cancels_all(
    scope_runtime, safety_store, fake_orchestrator
):
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    # Three active + one terminal.
    for i in range(3):
        await scope_runtime.create(_spec(), scope_id=f"s-{i}")
        await scope_runtime.start(f"s-{i}")
    await scope_runtime.create(_spec(), scope_id="s-done")
    await scope_runtime.start("s-done")
    await scope_runtime.complete("s-done")

    t0 = time.monotonic()
    record = await engine.kill_session(
        reason="session-kill-test", source="cli"
    )
    elapsed_ms = (time.monotonic() - t0) * 1000.0

    # Orchestrator paused.
    assert fake_orchestrator.is_paused
    assert fake_orchestrator.pause_log
    assert "safety:session_kill" in fake_orchestrator.pause_log[0]
    # All three active scopes cancelled.
    for i in range(3):
        assert scope_runtime.get(f"s-{i}").state == ScopeState.cancelled
    # Terminal scope untouched.
    assert scope_runtime.get("s-done").state == ScopeState.completed
    # Audit row.
    assert record.level == KillLevel.session
    assert set(record.cancelled_scope_ids) == {"s-0", "s-1", "s-2"}
    # Bounded: A2 is 2s p95 — in-memory this is orders of magnitude faster.
    assert elapsed_ms < 2000, f"session kill took {elapsed_ms:.1f}ms"


@pytest.mark.asyncio
async def test_A2_session_kill_with_no_active_scopes(
    scope_runtime, safety_store, fake_orchestrator
):
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    record = await engine.kill_session(reason="empty", source="cli")
    assert fake_orchestrator.is_paused
    assert record.cancelled_scope_ids == ()
    assert safety_store.list_kills()[0].level == KillLevel.session


# ---- amendment #19 (site 1) -----------------------------------------


class _RaisingPauseOrchestrator:
    """FakeOrchestrator whose pause_activation raises — used to verify
    amendment #19's observable-surface fix. Cancellation must still
    run; the failure must be surfaced in the audit record's reason."""

    def __init__(self) -> None:
        self._stop_requested = False

    def pause_activation(self, reason: str) -> None:
        raise RuntimeError("pause-activation-blew-up")

    def resume_activation(self) -> None:
        pass

    def request_stop(self) -> None:
        self._stop_requested = True


@pytest.mark.asyncio
async def test_amendment_19_session_kill_pause_failure_is_surfaced(
    scope_runtime, safety_store
):
    """S1 (amendment #19, site 1): a pause_activation failure must
    surface into the audit record's reason string (and the OTel span,
    not asserted here). Cancellation must still run — fail-safe
    direction preserved for user-issued session kills."""
    orch = _RaisingPauseOrchestrator()
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=orch,
    )
    # One active scope that should still be cancelled despite the
    # pause_activation failure.
    await scope_runtime.create(_spec(), scope_id="s-amend19")
    await scope_runtime.start("s-amend19")

    record = await engine.kill_session(
        reason="session-kill-pause-raises", source="cli"
    )

    # Pause failure is recorded in the audit reason.
    assert "pause_failed:RuntimeError" in record.reason
    # Cancellation still ran — the scope is terminal.
    from loam.scope_of_work import ScopeState
    assert scope_runtime.get("s-amend19").state == ScopeState.cancelled
    assert record.cancelled_scope_ids == ("s-amend19",)
    # Kill audit row is persisted with the suffixed reason.
    stored = safety_store.list_kills()
    assert stored and "pause_failed:RuntimeError" in stored[0].reason
