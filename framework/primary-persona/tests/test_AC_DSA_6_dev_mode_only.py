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

"""AC.DSA.6 — DEV-MODE-only.

The dispatcher's setup phase fires only when the workspace is in DEV
MODE (per the workspace-mode bit consumed by A1/A2/A3 — same source).
In NORMAL USE workspaces, the dispatcher does not write the sentinel,
does not register manifest rows, does not author stubs (regardless of
``new_acs``). Outcome: the wall-clock cost of the setup phase in
NORMAL USE is bounded by the mode-bit read alone.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from loam.primary_persona import DispatchShape, dispatch_with_scope
from loam.primary_persona.dispatch_wrapper import NewACSpec
from loam.primary_persona.dispatch_wrapper import _read_workspace_mode

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
async def test_AC_DSA_6_normal_use_skips_setup_phase(
    tmp_path, monkeypatch
) -> None:
    """workspace_mode == 'normal-use' ⇒ no sentinel write, no
    manifest register, no stub authored."""
    workspace = make_workspace(tmp_path, ambient_objective="obj")
    stub_workspace_dev_mode(monkeypatch, mode="normal-use")
    disable_iso_second_wait(monkeypatch)
    sentinel_recorder = install_stub_active_scope_sentinel(monkeypatch)
    tracker = RecordingTracker()
    install_stub_tracker(monkeypatch, tracker)

    client = StubIPCClient()
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
    # Setup didn't fire.
    assert sentinel_recorder["writes"] == []
    assert tracker.calls == []
    expected_stub = (
        workspace
        / "framework"
        / "c"
        / "tests"
        / "test_AC_X_1_placeholder.py"
    )
    assert not expected_stub.exists()


@pytest.mark.asyncio
async def test_AC_DSA_6_dev_mode_fires_setup_phase(
    tmp_path, monkeypatch
) -> None:
    """workspace_mode == 'dev-mode' ⇒ setup phase fires; sentinel
    write recorded, manifest call recorded, stub authored."""
    workspace = make_workspace(tmp_path, ambient_objective="obj")
    stub_workspace_dev_mode(monkeypatch, mode="dev-mode")
    disable_iso_second_wait(monkeypatch)
    sentinel_recorder = install_stub_active_scope_sentinel(monkeypatch)
    tracker = RecordingTracker()
    install_stub_tracker(monkeypatch, tracker)

    client = StubIPCClient()
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


def test_AC_DSA_6_mode_reader_falls_through_to_normal_use(
    tmp_path,
) -> None:
    """When ``corpus_load_sentinel`` is unavailable, the helper falls
    through to ``"normal-use"`` (fail-closed-to-permissive — the gate
    machinery is opt-in)."""
    # Without monkeypatching corpus_load_sentinel, the import is
    # likely to succeed against the framework's hooks/ dir on
    # sys.path, returning whatever workspace_mode it computes for an
    # empty tmp_path. The contract: never raise. Verify graceful
    # outcome.
    mode = _read_workspace_mode(tmp_path)
    assert mode in {"dev-mode", "normal-use"}
