"""AC.A8.5 — Scope state transitions to a terminal state on dispatch close.

Every dispatch issued through the wrapper transitions its scope to
exactly one of `completed | failed | cancelled` before the wrapper
returns. The wrapper drives this via `record_dispatch_close`'s
`terminal_state` parameter.
"""

from __future__ import annotations

import pytest

from primary_persona import (
    DispatchOutcome,
    DispatchShape,
    dispatch_with_scope,
)

from ._helpers_a8 import (
    StubIPCClient,
    build_stub_ipc_client_factory,
    make_agent_runner_raising,
    make_workspace,
    stub_agent_runner_ok,
)


@pytest.mark.asyncio
async def test_AC_A8_5_completed_on_agent_success(monkeypatch, tmp_path):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    monkeypatch.setattr(
        "pos_orchestrator.ipc.IPCClient",
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
    assert outcome.terminal_state == "completed"
    close_calls = [
        params for m, params in client.calls if m == "record_dispatch_close"
    ]
    assert close_calls[0]["terminal_state"] == "completed"


@pytest.mark.asyncio
async def test_AC_A8_5_failed_when_agent_raises(monkeypatch, tmp_path):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    monkeypatch.setattr(
        "pos_orchestrator.ipc.IPCClient",
        build_stub_ipc_client_factory(client),
    )

    shape = DispatchShape(
        objective="x",
        halt_conditions=("y",),
        expected_duration_seconds=1.0,
        task_shape_category="trivial",
    )
    runner = make_agent_runner_raising(RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        await dispatch_with_scope(
            shape, agent_runner=runner, workspace_root=workspace
        )
    # record_dispatch_close was called with terminal_state="failed"
    # before the wrapper re-raised.
    close_calls = [
        params for m, params in client.calls if m == "record_dispatch_close"
    ]
    assert close_calls
    assert close_calls[-1]["terminal_state"] == "failed"
    assert close_calls[-1]["debited_tokens"] == 0
