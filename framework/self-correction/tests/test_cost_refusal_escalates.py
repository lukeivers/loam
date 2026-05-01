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

"""CR19 — cost-ceiling refusal caught, episode refused, notification fired.

Silent drop is structurally forbidden. Cost codes -32060..-32062 are
caught; all others propagate (see CR18).
"""

from __future__ import annotations

import pytest
from loam.orchestrator.ipc import ApplicationError

from loam.self_correction import (
    EpisodeState,
    SelfCorrectionController,
    build_trigger_from_user_report,
)


@pytest.mark.parametrize("code", [-32060, -32061, -32062])
async def test_CR19_cost_refusal_caught_and_escalated(
    controller: SelfCorrectionController, channel_and_inbox, code: int
) -> None:
    _, inbox = channel_and_inbox

    async def create_scope(spec, scope_id):
        return None

    async def register_comp(params):
        return None

    async def activate(params):
        raise ApplicationError(
            code,
            f"cost ceiling exceeded (code {code})",
            data={"scope_id": params["scope_id"]},
        )

    controller.create_scope_fn = create_scope
    controller.register_compensation_fn = register_comp
    controller.activate_fn = activate

    tr = build_trigger_from_user_report(
        description=f"cost test {code}",
        related_scope_id=None,
        reporter="eve",
    )
    # Must NOT raise — cost refusal is caught.
    result = await controller.intake(tr)
    assert result is not None
    assert result.state == EpisodeState.refused
    assert str(code) in (result.refusal_reason or "")

    # Episode persisted in refused state.
    ep = controller.store.get_episode(result.episode_id)
    assert ep is not None
    assert ep.state == EpisodeState.refused

    # One-on-one channel notification fired.
    assert len(inbox) == 1
    assert f"code {code}" in inbox[0] or str(code) in inbox[0]
    assert "Correction has NOT been attempted" in inbox[0]


async def test_CR19_non_cost_code_not_silently_dropped(
    controller: SelfCorrectionController, channel_and_inbox
) -> None:
    _, inbox = channel_and_inbox

    async def create_scope(spec, scope_id):
        return None

    async def register_comp(params):
        return None

    async def activate(params):
        # -32040 is safety's kill-switch code (not a cost code).
        raise ApplicationError(-32040, "kill switch active")

    controller.create_scope_fn = create_scope
    controller.register_compensation_fn = register_comp
    controller.activate_fn = activate

    tr = build_trigger_from_user_report(
        description="kill test", related_scope_id=None, reporter="eve"
    )
    # Non-cost refusals propagate (CR18).
    with pytest.raises(ApplicationError):
        await controller.intake(tr)
