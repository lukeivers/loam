"""Safety-wins-collision test — A20 (added per brief §5).

Rationale (commit-message-worthy): the proposal §5 states "Safety always
wins on collision" with graceful-degradation. The A-criteria list does
not explicitly name this as a testable objective, but the proposal
promises it and failure here would be a contract violation. Promoting
the promise to an acceptance criterion (A20) is the ODD "re-extend
negative cases up as positive objectives" pattern.
"""

from __future__ import annotations

import pytest

from loam.safety_layer import KillEngine


@pytest.mark.asyncio
async def test_A20_system_kill_supersedes_degradation_pause(
    scope_runtime, safety_store, fake_orchestrator
):
    """Graceful-degradation pauses activation with reason "degradation:down".
    A user-initiated system kill then fires — safety's pause reason
    overwrites degradation's; safety proceeds; the audit row shows
    safety's reason.
    """
    # Degradation pauses first.
    fake_orchestrator.pause_activation("degradation:down")
    assert fake_orchestrator.is_paused
    assert "degradation:down" in fake_orchestrator.pause_log

    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )

    nonce = engine.request_system_kill_nonce()
    await engine.kill_system(
        reason="user requested shutdown",
        source="cli",
        nonce=nonce,
    )

    # Safety's pause reason is now present in the log — distinct
    # reason-string so the audit is unambiguous (research §8).
    assert any(
        "safety:system_kill" in r for r in fake_orchestrator.pause_log
    )
    # Safety's request_stop was honoured.
    assert fake_orchestrator.stop_requested
    # Active system-kill row is written.
    active = safety_store.active_system_kill()
    assert active is not None
    assert active.reason == "user requested shutdown"


@pytest.mark.asyncio
async def test_A20_session_kill_supersedes_degradation_pause(
    scope_runtime, safety_store, fake_orchestrator
):
    fake_orchestrator.pause_activation("degradation:down")
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    await engine.kill_session(reason="user halt", source="cli")
    assert any(
        "safety:session_kill" in r for r in fake_orchestrator.pause_log
    )
