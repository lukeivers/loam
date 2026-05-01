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

"""AC.A8.7 — Refusal surfacing to the persona as a structured value.

The wrapper returns `DispatchRefusal` (Pydantic-shaped value) on
gate-chain refusal. NOT raised. Carries gate_code + rejecting_gate +
reason + scope_id.
"""

from __future__ import annotations

import pytest

from loam.primary_persona import (
    DispatchRefusal,
    DispatchShape,
    dispatch_with_scope,
)
from loam.orchestrator.ipc import ApplicationError

from ._helpers_a8 import (
    StubIPCClient,
    build_stub_ipc_client_factory,
    make_workspace,
    stub_agent_runner_ok,
)


@pytest.mark.asyncio
async def test_AC_A8_7_refusal_returned_not_raised(monkeypatch, tmp_path):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    client.set_exception(
        "activate_scope_with_spec",
        ApplicationError(-32061, "rolling 24h ceiling exhausted"),
    )
    monkeypatch.setattr(
        "loam.orchestrator.ipc.IPCClient",
        build_stub_ipc_client_factory(client),
    )
    shape = DispatchShape(
        objective="x",
        halt_conditions=("y",),
        expected_duration_seconds=1.0,
        task_shape_category="trivial",
    )
    # Must NOT raise.
    refusal = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(refusal, DispatchRefusal)
    assert refusal.gate_code == -32061
    assert refusal.rejecting_gate == "cost"
    assert "rolling 24h ceiling exhausted" in refusal.reason
    assert refusal.scope_id.startswith("scope-")


@pytest.mark.asyncio
async def test_AC_A8_7_unanticipated_error_bubbles(monkeypatch, tmp_path):
    """A non-gate-chain error (unmapped code) bubbles as exception —
    the wrapper does NOT swallow programmer errors."""
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    client.set_exception(
        "activate_scope_with_spec",
        ApplicationError(-32603, "internal server error"),
    )
    monkeypatch.setattr(
        "loam.orchestrator.ipc.IPCClient",
        build_stub_ipc_client_factory(client),
    )
    shape = DispatchShape(
        objective="x",
        halt_conditions=("y",),
        expected_duration_seconds=1.0,
        task_shape_category="trivial",
    )
    with pytest.raises(ApplicationError) as ei:
        await dispatch_with_scope(
            shape,
            agent_runner=stub_agent_runner_ok,
            workspace_root=workspace,
        )
    assert ei.value.code == -32603
