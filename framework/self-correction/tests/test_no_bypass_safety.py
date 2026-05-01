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

"""CR18 — safety gate fires on correction scopes; self-correction does not bypass.

Simulated via an injected activate_fn that raises safety's
`ApplicationError(-32041 DANGEROUS_OP_GATE_BLOCKED)`. The controller
must propagate the error (it is not a cost code; no special catch)
and mark the episode refused with a gate_refused reason.
"""

from __future__ import annotations

import pytest
from loam.orchestrator.ipc import ApplicationError

from loam.self_correction import (
    EpisodeState,
    SelfCorrectionController,
    build_trigger_from_user_report,
)


async def test_CR18_safety_refusal_propagates_and_marks_refused(
    controller: SelfCorrectionController,
) -> None:
    async def create_scope(spec, scope_id):
        return None

    async def register_comp(params):
        return None

    async def activate(params):
        raise ApplicationError(
            -32041,
            "dangerous_op_gate blocked: rm -rf target",
            data={"scope_id": params["scope_id"]},
        )

    controller.create_scope_fn = create_scope
    controller.register_compensation_fn = register_comp
    controller.activate_fn = activate

    tr = build_trigger_from_user_report(
        description="scope would erase ~/", related_scope_id=None, reporter="eve"
    )
    with pytest.raises(ApplicationError) as excinfo:
        await controller.intake(tr)
    assert excinfo.value.code == -32041

    # Episode exists and is marked refused with gate_refused reason.
    eps = controller.store.list_all_episodes()
    assert len(eps) == 1
    assert eps[0].state == EpisodeState.refused
    assert "gate_refused" in (eps[0].refusal_reason or "")
    assert "-32041" in (eps[0].refusal_reason or "")


async def test_CR18_reversibility_refusal_propagates(
    controller: SelfCorrectionController,
) -> None:
    async def create_scope(spec, scope_id):
        return None

    async def register_comp(params):
        return None

    async def activate(params):
        raise ApplicationError(
            -32050, "compensatable_no_binding"
        )

    controller.create_scope_fn = create_scope
    controller.register_compensation_fn = register_comp
    controller.activate_fn = activate

    tr = build_trigger_from_user_report(
        description="test rev gate", related_scope_id=None, reporter="eve"
    )
    with pytest.raises(ApplicationError) as excinfo:
        await controller.intake(tr)
    assert excinfo.value.code == -32050
