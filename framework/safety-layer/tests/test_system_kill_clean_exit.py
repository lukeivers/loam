"""System kill clean exit — ruling #2, A4.

A4. Next orchestrator bootstrap refuses to activate until
    `clear-system-kill` is run.
Ruling #2. Orchestrator exits 0 via `request_stop`.
"""

from __future__ import annotations

import pytest

from loam.orchestrator.ipc import ApplicationError

from loam.safety_layer import KillEngine
from loam.safety_layer.controller import IPC_SYSTEM_KILL_ACTIVE


@pytest.mark.asyncio
async def test_ruling2_request_stop_called_on_system_kill(
    scope_runtime, safety_store, fake_orchestrator
):
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )
    nonce = engine.request_system_kill_nonce()
    await engine.kill_system(reason="r", source="ipc", nonce=nonce)
    assert fake_orchestrator.stop_requested is True


@pytest.mark.asyncio
async def test_A4_refuse_if_system_killed_raises(controller):
    # Seed a system-kill row without going through the engine.
    controller.store.record_system_kill(reason="unit", source="ipc")

    with pytest.raises(ApplicationError) as exc:
        controller.refuse_if_system_killed(scope_id="s-post-kill")
    assert exc.value.code == IPC_SYSTEM_KILL_ACTIVE


@pytest.mark.asyncio
async def test_A4_clear_system_kill_unblocks(controller):
    controller.store.record_system_kill(reason="unit", source="ipc")
    # Clear.
    ok = controller.store.clear_system_kill(reason="clear-it")
    assert ok is True
    # Now no refusal.
    controller.refuse_if_system_killed(scope_id="s-after")
