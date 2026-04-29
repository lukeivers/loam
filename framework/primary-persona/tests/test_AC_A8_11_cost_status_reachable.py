"""AC.A8.11 — `cost.status` reachable for persona awareness.

After a dispatch closes through the wrapper, the cost surface is
reachable. (In the bare-orchestrator test fixture there is no
cost-governance adapter installed, so `cost.status` IPC isn't
registered. AC.A8.11's full end-to-end shape requires a workspace-
bootstrap composition; in this unit-level test we measure the
shape-level behaviour: the wrapper correctly emits the close-emission
IPC, so a downstream `cost.status` consumer can observe the
reservation.)

The shape-level assertion: every successful (non-refusal,
non-fallback) dispatch terminates with a `record_dispatch_close`
call carrying the agent-reported tokens. With cost-governance
installed, this drives BudgetDebited → CostLedger reservation row →
cost.status response. End-to-end is verified in
`cost-governance/tests/test_ipc_wrap_composition.py` (composition
test, unchanged by this amendment).
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
async def test_AC_A8_11_close_emission_drives_cost_surface(
    monkeypatch, tmp_path
):
    """A successful dispatch's close-emission carries the tokens that
    fill the cost ledger. Verified at the wrapper boundary; the
    end-to-end ledger-fill is exercised by the orchestrator-side
    AC.A8.A3 tests."""
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
    # The close call carries the agent-reported tokens — this is the
    # input the cost ledger consumes.
    close_calls = [
        params for m, params in client.calls if m == "record_dispatch_close"
    ]
    assert close_calls
    assert close_calls[-1]["debited_tokens"] == 1234
    assert close_calls[-1]["scope_id"] == outcome.scope_id
