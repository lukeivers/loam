"""AC.A8.4 — `BudgetDebited` / `BudgetRefunded` emission.

The wrapper drives `record_dispatch_close` with the agent-reported
total_tokens after a successful dispatch. The IPC method then emits
BudgetDebited via the orchestrator-side scope-runtime path.
"""

from __future__ import annotations

import pytest

from loam.primary_persona import (
    DispatchOutcome,
    DispatchShape,
    dispatch_with_scope,
)

from ._helpers_a8 import (
    StubIPCClient,
    build_stub_ipc_client_factory,
    make_workspace,
    stub_agent_runner_no_tokens,
    stub_agent_runner_ok,
)


@pytest.mark.asyncio
async def test_AC_A8_4_record_dispatch_close_carries_agent_tokens(
    monkeypatch, tmp_path
):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
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
    outcome = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(outcome, DispatchOutcome)
    assert outcome.debited_tokens == 1234

    # Find the record_dispatch_close call.
    close_calls = [
        params for m, params in client.calls if m == "record_dispatch_close"
    ]
    assert len(close_calls) == 1
    assert close_calls[0]["debited_tokens"] == 1234
    assert close_calls[0]["terminal_state"] == "completed"


@pytest.mark.asyncio
async def test_AC_A8_4_zero_tokens_when_agent_omits(monkeypatch, tmp_path):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
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
    outcome = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_no_tokens,
        workspace_root=workspace,
    )
    assert isinstance(outcome, DispatchOutcome)
    assert outcome.debited_tokens == 0
    close_calls = [
        params for m, params in client.calls if m == "record_dispatch_close"
    ]
    assert close_calls[0]["debited_tokens"] == 0
