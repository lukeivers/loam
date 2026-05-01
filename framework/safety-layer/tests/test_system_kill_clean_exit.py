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
