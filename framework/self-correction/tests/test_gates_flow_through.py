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

"""CR13, CR14 — compensation binding registered; three-gate chain runs.

We use injected fakes for create_scope_fn, activate_fn, and
register_compensation_fn to assert the controller calls them in the
required order with the required parameters. This is the structural
contract; the real IPC wiring (`register_cost_governance_ipc` +
`register_reversibility_ipc` + `register_safety_ipc`) composes
independently and is tested by the sealed-component wrap-composition
tests.
"""

from __future__ import annotations

from typing import Any


from loam.self_correction import (
    SelfCorrectionController,
    build_trigger_from_user_report,
)


async def test_CR13_CR14_calls_create_register_activate_in_order(
    controller: SelfCorrectionController,
) -> None:
    calls: list[tuple[str, Any]] = []

    async def create_scope(spec, scope_id):
        calls.append(("create", (spec, scope_id)))

    async def register_comp(params):
        calls.append(("register", params))

    async def activate(params):
        calls.append(("activate", params))

    controller.create_scope_fn = create_scope
    controller.register_compensation_fn = register_comp
    controller.activate_fn = activate

    tr = build_trigger_from_user_report(
        description="integration", related_scope_id=None, reporter="eve"
    )
    result = await controller.intake(tr)
    assert result is not None
    assert result.correction_scope_id is not None

    assert [c[0] for c in calls] == ["create", "register", "activate"]

    # Registered compensation carries handle + scope_id.
    _, (reg_params,) = "register", (calls[1][1],)
    reg_params = calls[1][1]
    assert reg_params["scope_id"] == result.correction_scope_id
    assert reg_params["handle"] == "self_correction.revert_structural_remedy"

    # Activate was called with the same scope_id — the three-gate
    # chain (safety → reversibility → cost → orig_activate) fires
    # against this one call.
    act_params = calls[2][1]
    assert act_params["scope_id"] == result.correction_scope_id


async def test_CR14_spec_is_compensatable_when_activate_sees_it(
    controller: SelfCorrectionController,
) -> None:
    seen_specs: list = []

    async def create_scope(spec, scope_id):
        seen_specs.append(spec)

    async def register_comp(params):
        return None

    async def activate(params):
        return {"ok": True}

    controller.create_scope_fn = create_scope
    controller.register_compensation_fn = register_comp
    controller.activate_fn = activate

    tr = build_trigger_from_user_report(
        description="test compensatable", related_scope_id=None, reporter="eve"
    )
    await controller.intake(tr)
    assert len(seen_specs) == 1
    spec = seen_specs[0]
    assert spec.reversibility_class.value == "compensatable"
