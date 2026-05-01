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

"""Always-ask list workspace extensibility.

Workspaces may ADD categories above the floor; they cannot remove.
This covers the "open string set" side of clause (g): the gate matches
the UNION (floor ∪ workspace), and any matching constraint fires the
gate even if the class isn't in the framework enum.
"""

from __future__ import annotations

import pytest

from loam.orchestrator.ipc import ApplicationError

from loam.safety_layer import (
    AlwaysAskList,
    AskListEntry,
    DEFAULT_DANGEROUS_OP_SUBSET,
    DEFAULT_FRAMEWORK_FLOOR,
    SafetyConfig,
    SafetyController,
    SafetyNotifier,
)
from loam.safety_layer.controller import IPC_ASK_GATE_PENDING

from .conftest import make_spec
from .fakes import FakeOrchestrator, make_fake_channel


@pytest.mark.asyncio
async def test_workspace_addition_fires_gate(
    scope_runtime, safety_store
):
    # Add a workspace-specific category.
    extended = AlwaysAskList(
        version=1,
        framework_floor=DEFAULT_FRAMEWORK_FLOOR,
        workspace_additions=(
            AskListEntry(
                action_class="send_telegram_to_allowlisted_close_associate",
                timeout="1h",
                description="Tier-D close-associate message.",
            ),
        ),
        dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
    )
    ch, _ = make_fake_channel(active=True)
    controller = SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=FakeOrchestrator(),
        store=safety_store,
        ask_list=extended,
        config=SafetyConfig(),
        notifier=SafetyNotifier(channels=[ch]),
    )

    spec = make_spec(
        constraints=("action_class=send_telegram_to_allowlisted_close_associate",),
    )
    with pytest.raises(ApplicationError) as exc:
        await controller.check_gates(spec, scope_id="s-1")
    assert exc.value.code == IPC_ASK_GATE_PENDING
