"""AC.A8.6 — Orchestrator unreachable: documented fallback path.

Given the orchestrator socket is missing / connection refused / no
ambient objective seed, the wrapper:
  - Emits a structured NDJSON diagnostic to
    `<workspace>/.pos/dispatch-wrapper.log`.
  - Proceeds with the underlying Agent tool unwrapped.
  - Returns a `DispatchOutcome(fallback=True)`.
"""

from __future__ import annotations

import json

import pytest

from primary_persona import (
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


def _read_log(workspace):
    log = workspace / "workspace" / ".pos" / "dispatch-wrapper.log"
    if not log.exists():
        return []
    return [json.loads(ln) for ln in log.read_text().splitlines() if ln.strip()]


@pytest.mark.asyncio
async def test_AC_A8_6_socket_missing_takes_fallback(tmp_path):
    workspace = make_workspace(tmp_path, socket_present=False)
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
    assert outcome.fallback is True
    # Diagnostic recorded.
    log = _read_log(workspace)
    assert log
    assert log[-1]["event"] == "fallback"


@pytest.mark.asyncio
async def test_AC_A8_6_no_ambient_objective_takes_fallback(tmp_path):
    workspace = make_workspace(
        tmp_path, socket_present=True, ambient_objective=None
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
    assert outcome.fallback is True
    log = _read_log(workspace)
    assert log[-1]["reason"] == "no_ambient_objective"


@pytest.mark.asyncio
async def test_AC_A8_6_connect_failure_takes_fallback(monkeypatch, tmp_path):
    workspace = make_workspace(tmp_path)
    client = StubIPCClient()
    client.set_connect_exception(ConnectionRefusedError("nope"))
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
    assert outcome.fallback is True
    log = _read_log(workspace)
    assert any(rec.get("reason", "").startswith("connect_failed") for rec in log)


@pytest.mark.asyncio
async def test_AC_A8_6_diagnostic_log_is_ndjson(tmp_path):
    """One JSON object per line (NDJSON shape per D1 / amendment-#48
    sibling pattern)."""
    workspace = make_workspace(tmp_path, socket_present=False)
    shape = DispatchShape(
        objective="ndjson check",
        halt_conditions=("y",),
        expected_duration_seconds=1.0,
        task_shape_category="trivial",
    )
    await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    log = _read_log(workspace)
    assert log
    rec = log[-1]
    assert "ts" in rec
    assert "scope_id" in rec
    assert "event" in rec
