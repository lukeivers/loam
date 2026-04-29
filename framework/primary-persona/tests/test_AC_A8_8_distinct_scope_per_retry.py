"""AC.A8.8 — Idempotent re-dispatch produces distinct scope ids.

A retry of the same dispatch shape opens a new scope id; reservations
from prior attempts are not re-charged.
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
    stub_agent_runner_ok,
)


@pytest.mark.asyncio
async def test_AC_A8_8_two_dispatches_distinct_scope_ids(
    monkeypatch, tmp_path
):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    monkeypatch.setattr(
        "loam.orchestrator.ipc.IPCClient",
        build_stub_ipc_client_factory(client),
    )

    shape = DispatchShape(
        objective="repeated objective",
        halt_conditions=("done",),
        expected_duration_seconds=1.0,
        task_shape_category="trivial",
    )

    outcome_a = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    outcome_b = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(outcome_a, DispatchOutcome)
    assert isinstance(outcome_b, DispatchOutcome)
    assert outcome_a.scope_id != outcome_b.scope_id

    # Each activate_scope_with_spec call carries its own scope_id.
    activate_calls = [
        params for m, params in client.calls
        if m == "activate_scope_with_spec"
    ]
    assert len(activate_calls) == 2
    assert activate_calls[0]["scope_id"] != activate_calls[1]["scope_id"]
