"""AC.A8.9 — Wrapper public surface is callable from the persona.

The wrapper exposes a single public callable
(`primary_persona.dispatch_with_scope`) that takes a dispatch shape
and returns the dispatch result or a structured refusal — no further
IPC plumbing in the caller.
"""

from __future__ import annotations

import pytest

import primary_persona
from primary_persona import DispatchOutcome, DispatchShape, dispatch_with_scope

from ._helpers_a8 import (
    StubIPCClient,
    build_stub_ipc_client_factory,
    make_workspace,
    stub_agent_runner_ok,
)


def test_AC_A8_9_dispatch_with_scope_in_public_surface():
    """`primary_persona.dispatch_with_scope` is callable + re-exported."""
    assert callable(dispatch_with_scope)
    assert hasattr(primary_persona, "dispatch_with_scope")
    assert primary_persona.dispatch_with_scope is dispatch_with_scope


def test_AC_A8_9_DispatchShape_DispatchOutcome_DispatchRefusal_re_exported():
    assert hasattr(primary_persona, "DispatchShape")
    assert hasattr(primary_persona, "DispatchOutcome")
    assert hasattr(primary_persona, "DispatchRefusal")


@pytest.mark.asyncio
async def test_AC_A8_9_persona_caller_no_ipc_plumbing_required(
    monkeypatch, tmp_path
):
    """A persona-shaped caller assembles a DispatchShape and calls
    `dispatch_with_scope` — no IPCClient assembly visible to the
    caller."""
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    monkeypatch.setattr(
        "pos_orchestrator.ipc.IPCClient",
        build_stub_ipc_client_factory(client),
    )

    # The caller's whole interaction:
    shape = DispatchShape(
        objective="caller-side objective",
        halt_conditions=("done",),
        expected_duration_seconds=1.0,
        task_shape_category="trivial",
    )
    outcome = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(outcome, DispatchOutcome)
    # Caller did not need to import IPCClient or scope_of_work.
