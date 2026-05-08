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

"""D1 — orchestrator process skeleton.

Acceptance (from brief):
- Process starts and runs a main event loop.
- SIGTERM triggers a clean flush followed by exit code 0.
- Crash produces non-zero exit code.
- Heartbeat writes to the local SQLite on a configured interval.
"""

from __future__ import annotations

import asyncio

import pytest

from loam.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_starts_and_stops_cleanly(tmp_config):
    """Process starts, reaches the event loop, and shuts down cleanly."""
    orch = Orchestrator(tmp_config)
    async with orch.running():
        # Give at least one heartbeat tick a chance to fire.
        await asyncio.sleep(0.12)
        # Process started event written.
        started = orch.local_state.events_of_type("process_started")
        assert len(started) == 1
        assert started[0].payload["workspace"] == tmp_config.workspace_label

    # After shutdown, a process_stopped event exists.
    stopped = orch.local_state.events_of_type("process_stopped")
    assert len(stopped) == 1


@pytest.mark.asyncio
async def test_heartbeat_writes_on_interval(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running():
        await asyncio.sleep(0.18)  # ~3 ticks @ 0.05 interval
    beats = orch.local_state.events_of_type("heartbeat")
    assert len(beats) >= 2, f"expected >=2 heartbeats, got {len(beats)}"
    # Each heartbeat has tick_id and uptime_seconds.
    for b in beats:
        assert "tick_id" in b.payload
        assert "uptime_seconds" in b.payload


@pytest.mark.asyncio
async def test_sigterm_triggers_clean_flush(tmp_config):
    """request_stop() mirrors SIGTERM path; must yield clean shutdown."""
    orch = Orchestrator(tmp_config)

    async def _shutdown_soon():
        await asyncio.sleep(0.08)
        orch.request_stop()

    task = asyncio.create_task(orch.run())
    stopper = asyncio.create_task(_shutdown_soon())
    exit_code = await asyncio.wait_for(task, timeout=2.0)
    await stopper

    assert exit_code == 0
    assert orch.local_state.events_of_type("process_stopped")


@pytest.mark.asyncio
async def test_crash_during_startup_yields_non_zero(tmp_path, monkeypatch):
    """If _startup() raises an unexpected exception, exit code is non-zero."""
    from loam.orchestrator import Orchestrator as Orch
    from loam.orchestrator.config import OrchestratorConfig

    from .conftest import _short_socket_path

    root = tmp_path / "pos"
    root.mkdir(parents=True, exist_ok=True)
    cfg = OrchestratorConfig(
        root_dir=root,
        socket_path=_short_socket_path(),
        heartbeat_interval_seconds=0.05,
        sigterm_grace_seconds=1.0,
    )
    orch = Orch(cfg)

    async def boom(self):  # noqa: ARG001
        raise RuntimeError("synthetic crash")

    monkeypatch.setattr(Orch, "_startup", boom, raising=True)
    code = await asyncio.wait_for(orch.run(), timeout=2.0)
    assert code == 1
    crashes = orch.local_state.events_of_type("process_crashed")
    assert crashes and crashes[0].payload["type"] == "RuntimeError"


# Amendment #7 (orchestrator-bootstrap-unification, approved 2026-04-22)
# deleted the `test_missing_bootstrap_fails_closed` +
# `test_erroring_bootstrap_fails_closed` tests. They pinned a contract
# this amendment intentionally removes: the orchestrator's `_startup`
# no longer loads `~/.loam/bootstrap.py` directly, so no exit-code-2/3
# branch exists. The framework now refuses fail-closed on missing
# `~/.loam/bootstrap.yaml` (code -32080) and the adapter refuses when
# `required: True` is set. Positive-space coverage lives in:
#   * test_AC2_missing_bootstrap_py_is_not_a_fail_closed_condition (below)
#   * workspace-bootstrap/tests/test_integration_foundational.py
#     (AC3/AC4/AC5/AC6).
# See docs/archive/component-research/orchestrator-bootstrap-unification/proposal.md.


@pytest.mark.asyncio
async def test_core_purity_assertion():
    """Brief: a build-time check fails if any persona directory appears
    in the orchestrator's paths."""
    from loam.orchestrator.core_purity import assert_core_purity

    # Runs at import; explicit call re-verifies.
    assert_core_purity()
