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

"""AC.A8.3 — Wrapper calls `activate_scope_with_spec` and respects gate verdict.

On approval, the underlying agent is invoked. On gate-chain refusal,
the wrapper returns a structured `DispatchRefusal` per AC.A8.7
(tested separately) and the agent is NOT invoked.
"""

from __future__ import annotations


import pytest

from loam.primary_persona import (
    DispatchOutcome,
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
async def test_AC_A8_3_calls_activate_scope_with_spec_on_approval(
    monkeypatch, tmp_path
):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    monkeypatch.setattr(
        "loam.orchestrator.ipc.IPCClient",
        build_stub_ipc_client_factory(client),
    )

    shape = DispatchShape(
        objective="do the thing",
        halt_conditions=("done",),
        expected_duration_seconds=5.0,
        task_shape_category="simple",
    )
    outcome = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(outcome, DispatchOutcome)
    # The wrapper called activate_scope_with_spec.
    methods = [m for m, _ in client.calls]
    assert "activate_scope_with_spec" in methods
    # Then record_dispatch_close on success.
    assert "record_dispatch_close" in methods


@pytest.mark.asyncio
async def test_AC_A8_3_does_not_call_agent_on_cost_refusal(
    monkeypatch, tmp_path
):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    client.set_exception(
        "activate_scope_with_spec",
        ApplicationError(-32060, "session ceiling exceeded"),
    )
    monkeypatch.setattr(
        "loam.orchestrator.ipc.IPCClient",
        build_stub_ipc_client_factory(client),
    )

    agent_called = {"count": 0}

    async def agent_runner(payload):
        agent_called["count"] += 1
        return {"result": "ok", "total_tokens": 999}

    shape = DispatchShape(
        objective="x",
        halt_conditions=("y",),
        expected_duration_seconds=10.0,
        task_shape_category="simple",
    )
    refusal = await dispatch_with_scope(
        shape,
        agent_runner=agent_runner,
        workspace_root=workspace,
    )
    assert isinstance(refusal, DispatchRefusal)
    assert refusal.gate_code == -32060
    assert refusal.rejecting_gate == "cost"
    # Agent NOT invoked.
    assert agent_called["count"] == 0


@pytest.mark.asyncio
async def test_AC_A8_3_safety_refusal_classified_correctly(
    monkeypatch, tmp_path
):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    client.set_exception(
        "activate_scope_with_spec",
        ApplicationError(-32070, "kill switch active"),
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
    refusal = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(refusal, DispatchRefusal)
    assert refusal.rejecting_gate == "safety"


@pytest.mark.asyncio
async def test_AC_A8_3_reversibility_refusal_classified_correctly(
    monkeypatch, tmp_path
):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    client.set_exception(
        "activate_scope_with_spec",
        ApplicationError(-32082, "irreversible without approval"),
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
        reversibility_class="irreversible",
    )
    refusal = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(refusal, DispatchRefusal)
    assert refusal.rejecting_gate == "reversibility"


@pytest.mark.asyncio
async def test_AC_A8_3_orchestrator_bind_refused_classified_correctly(
    monkeypatch, tmp_path
):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    client.set_exception(
        "activate_scope_with_spec",
        ApplicationError(409, "bind refused"),
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
    refusal = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(refusal, DispatchRefusal)
    assert refusal.rejecting_gate == "orchestrator"
