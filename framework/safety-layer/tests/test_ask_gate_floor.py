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

"""Always-ask list — A6, A7, A8.

A6. Loading a YAML that omits any framework-floor category raises a
    Pydantic ValidationError at load time.
A7. A scope declaring action_class=commit_external_funds with no
    matching approval fires the gate; `check_gates` raises
    ApplicationError with the pending-code. Scope stays `proposed`.
A8. User replying "approve" via record_ask_decision writes a row and a
    subsequent check_gates call for the same spec hash passes.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.orchestrator.ipc import ApplicationError
from loam.scope_of_work import ReversibilityClass

from loam.safety_layer import (
    AlwaysAskList,
    DEFAULT_DANGEROUS_OP_SUBSET,
    DEFAULT_FRAMEWORK_FLOOR,
    FrameworkFloorCategory,
)
from loam.safety_layer.controller import IPC_ASK_GATE_PENDING, structural_hash

from .conftest import make_spec


def test_A6_floor_omission_is_rejected():
    # Drop two floor entries.
    short_floor = DEFAULT_FRAMEWORK_FLOOR[:5]
    with pytest.raises(ValidationError) as exc:
        AlwaysAskList(
            version=1,
            framework_floor=short_floor,
            workspace_additions=(),
            dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
        )
    assert "missing required categories" in str(exc.value)


def test_A6_empty_floor_is_rejected():
    with pytest.raises(ValidationError):
        AlwaysAskList(
            version=1,
            framework_floor=(),
            workspace_additions=(),
            dangerous_op_subset=(),
        )


@pytest.mark.asyncio
async def test_A7_ask_gate_fires_on_matching_action_class(controller):
    spec = make_spec(
        constraints=("action_class=commit_external_funds",),
    )

    with pytest.raises(ApplicationError) as exc:
        await controller.check_gates(spec, scope_id="s-new")

    assert exc.value.code == IPC_ASK_GATE_PENDING
    data = exc.value.data
    assert data["reason"] == "ask_gate_pending"
    assert "commit_external_funds" in data["action_classes"]


@pytest.mark.asyncio
async def test_A8_approved_decision_unblocks_subsequent_check(controller):
    spec = make_spec(
        constraints=("action_class=commit_external_funds",),
    )
    spec_hash = structural_hash(spec)

    # First call blocks.
    with pytest.raises(ApplicationError):
        await controller.check_gates(spec, scope_id="s-2")

    # User approves.
    record = controller.record_ask_decision(
        scope_spec_hash=spec_hash,
        decision="approved",
        action_classes=["commit_external_funds"],
        scope_id="s-2",
    )
    assert record.state == "approved"
    assert record.expires_at is not None

    # Now it passes.
    await controller.check_gates(spec, scope_id="s-2")


@pytest.mark.asyncio
async def test_A7_non_matching_scope_passes_gate(controller):
    spec = make_spec(constraints=("routine_constraint=ok",))
    # No action_class constraint, no money budget, no irreversibility
    # → gate passes.
    await controller.check_gates(spec, scope_id="s-clean")
