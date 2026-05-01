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

"""AC.DSA.7 — setup precedes activate_scope_with_spec.

In the wrapper's execution sequence, the setup phase (sentinel +
manifest + stubs) runs strictly before the IPC call to
``activate_scope_with_spec`` (amendment #52 AC.A8.A1). On gate-chain
refusal at activate_scope_with_spec, the setup artefacts persist on
disk. Subsequent dispatches benefit from idempotency (AC.DSA.4); the
operator observes the gate refusal and the audit-trail of attempted-
setup via the diagnostic log.
"""

from __future__ import annotations

import pytest

from loam.primary_persona import DispatchRefusal, DispatchShape, dispatch_with_scope
from loam.primary_persona.dispatch_wrapper import NewACSpec

from ._helpers_a8 import (
    StubIPCClient,
    build_stub_ipc_client_factory,
    make_workspace,
    stub_agent_runner_ok,
)
from ._helpers_dsa import (
    RecordingTracker,
    install_stub_active_scope_sentinel,
    install_stub_tracker,
    stub_workspace_dev_mode,
    disable_iso_second_wait,
)


@pytest.mark.asyncio
async def test_AC_DSA_7_setup_calls_precede_activate_scope(
    tmp_path, monkeypatch
) -> None:
    """Both the sentinel-write and the tracker-register call land
    BEFORE the IPC client's first ``activate_scope_with_spec`` call."""
    workspace = make_workspace(tmp_path, ambient_objective="obj")
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)

    event_log: list[str] = []

    # Recording sentinel writer.
    import sys
    import types
    from pathlib import Path

    ass_mod = types.ModuleType("active_scope_sentinel")

    class _ScopeBinding:
        def __init__(self, *, component, ac_id):
            self.component = component
            self.ac_id = ac_id

    class _Result:
        def __init__(self, *, wrote, reason, path):
            self.wrote = wrote
            self.reason = reason
            self.path = path
            self.error_detail = ""

    def _write(workspace_root, *, scope_id, plan_path, bindings, session_id=None):
        event_log.append("sentinel")
        target = Path(workspace_root) / "workspace" / ".pos" / "active-scope.json"
        return _Result(wrote=True, reason="written", path=target)

    ass_mod.ScopeBinding = _ScopeBinding
    ass_mod.write_active_scope_sentinel = _write
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)

    # Recording tracker.
    tracker = RecordingTracker()
    original = tracker.register_source_binding

    def wrapped(**kw):
        event_log.append("manifest")
        return original(**kw)

    tracker.register_source_binding = wrapped  # type: ignore[method-assign]
    install_stub_tracker(monkeypatch, tracker)

    # IPC client that records its calls.
    client = StubIPCClient()

    async def _record_call(method, params=None, *, timeout=None):
        event_log.append(f"ipc:{method}")
        return {}

    client.call = _record_call  # type: ignore[method-assign]

    import loam.orchestrator.ipc as _ipc_mod

    monkeypatch.setattr(
        _ipc_mod, "IPCClient", build_stub_ipc_client_factory(client)
    )

    shape = DispatchShape(
        objective="o",
        new_acs=(NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),),
    )
    await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )

    # Assert ordering: sentinel + manifest BEFORE
    # ipc:activate_scope_with_spec.
    assert "sentinel" in event_log
    assert "manifest" in event_log
    assert "ipc:activate_scope_with_spec" in event_log
    activate_idx = event_log.index("ipc:activate_scope_with_spec")
    assert event_log.index("sentinel") < activate_idx
    assert event_log.index("manifest") < activate_idx


@pytest.mark.asyncio
async def test_AC_DSA_7_setup_artefacts_persist_on_gate_refusal(
    tmp_path, monkeypatch
) -> None:
    """When activate_scope_with_spec raises a cost-gate refusal, the
    sentinel + manifest registrations + stub already on disk persist
    (idempotent on retry)."""
    from loam.orchestrator.ipc import ApplicationError

    workspace = make_workspace(tmp_path, ambient_objective="obj")
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    sentinel_recorder = install_stub_active_scope_sentinel(monkeypatch)
    tracker = RecordingTracker()
    install_stub_tracker(monkeypatch, tracker)

    client = StubIPCClient()
    client.set_exception(
        "activate_scope_with_spec",
        ApplicationError(-32060, "cost-gate refusal", None),
    )

    import loam.orchestrator.ipc as _ipc_mod

    monkeypatch.setattr(
        _ipc_mod, "IPCClient", build_stub_ipc_client_factory(client)
    )

    shape = DispatchShape(
        objective="o",
        new_acs=(NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),),
    )
    result = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(result, DispatchRefusal)
    # Setup artefacts ran before the refusal — they're on disk.
    assert len(sentinel_recorder["writes"]) == 1
    assert len(tracker.calls) == 1
    expected_stub = (
        workspace
        / "framework"
        / "c"
        / "tests"
        / "test_AC_X_1_placeholder.py"
    )
    assert expected_stub.exists()
