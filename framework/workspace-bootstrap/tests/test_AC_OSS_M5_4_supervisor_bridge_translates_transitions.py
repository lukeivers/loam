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

"""AC.OSS-M5.4 — Supervisor outage transitions reach DormancyComponent.

Per amendment #86 (M5 wire-dormancy). The adapter authors a small
bridge that maps ``SupervisorTransition.to_state`` to dormancy detector
signals via ``record_supervisor_signal``:

  to_state == degraded   → memory_sidecar_down
  to_state == escalated  → memory_sidecar_down (idempotent)
  to_state == recovering → no-op (intermediate state)
  to_state == normal     → memory_sidecar_recovered

This test exercises the bridge against synthetic ``SupervisorTransition``
events for each ``to_state`` value and asserts the resulting dormancy
``memory_sidecar`` FSM state.

Programme: OSS v0.1.0 publish — M5 — wire-dormancy.
Plan: docs/plans/oss-v0-1-0-publish-dormancy-constructor.md.
AC family: AC.OSS-M5.4.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fake_host(tmp_path: Path):
    from loam.orchestrator import Orchestrator
    from loam.orchestrator.config import OrchestratorConfig
    from loam.scope_of_work import ScopeRuntime
    from loam.workspace_bootstrap.host import BootstrapHost

    cfg_dir = tmp_path / ".loam"
    cfg_dir.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    manifest = workspace / "bootstrap.yaml"

    pos_root = tmp_path / "pos-root"
    pos_root.mkdir()
    orch_cfg = OrchestratorConfig(root_dir=pos_root)
    orch_cfg.ensure_dirs()
    orch = Orchestrator(orch_cfg)

    host = BootstrapHost(
        config_dir=cfg_dir,
        workspace_root=workspace,
        manifest_path=manifest,
    )
    host.orchestrator = orch
    host.scope_runtime = ScopeRuntime(
        orch_cfg.scope_of_work_db,
        pending_extension_dir=orch_cfg.pending_extension_dir,
    )

    yield host

    try:
        host.scope_runtime.close()
    except Exception:
        pass


def _make_transition(to_state):
    """Minimal SupervisorTransition factory for bridge testing."""
    from loam.orchestrator.supervisor import (
        SupervisorState,
        SupervisorTransition,
    )

    return SupervisorTransition(
        from_state=SupervisorState.normal,
        to_state=to_state,
        trigger="test",
        at=0.0,
    )


@pytest.mark.asyncio
async def test_AC_OSS_M5_4_bridge_degraded_trips_memory_sidecar_fsm(
    fake_host,
) -> None:
    """``to_state == degraded`` fires
    ``record_supervisor_signal(memory_sidecar_down)``; the dormancy
    detector's memory_sidecar FSM transitions to open."""
    from loam.dormancy.fsm import DegradationMode, FSMState
    from loam.orchestrator.supervisor import SupervisorState
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
        _build_supervisor_bridge,
    )

    await DormancyContribution().contribute(fake_host)
    comp = fake_host.dormancy
    bridge = _build_supervisor_bridge(comp)

    await bridge(_make_transition(SupervisorState.degraded))

    fsm = comp.detector.fsms[DegradationMode.memory_sidecar]
    assert fsm.state == FSMState.open


@pytest.mark.asyncio
async def test_AC_OSS_M5_4_bridge_escalated_idempotent(fake_host) -> None:
    """``to_state == escalated`` after ``degraded`` is idempotent —
    the FSM stays open."""
    from loam.dormancy.fsm import DegradationMode, FSMState
    from loam.orchestrator.supervisor import SupervisorState
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
        _build_supervisor_bridge,
    )

    await DormancyContribution().contribute(fake_host)
    comp = fake_host.dormancy
    bridge = _build_supervisor_bridge(comp)

    await bridge(_make_transition(SupervisorState.degraded))
    await bridge(_make_transition(SupervisorState.escalated))

    fsm = comp.detector.fsms[DegradationMode.memory_sidecar]
    assert fsm.state == FSMState.open


@pytest.mark.asyncio
async def test_AC_OSS_M5_4_bridge_normal_recovers(fake_host) -> None:
    """``to_state == normal`` fires
    ``record_supervisor_signal(memory_sidecar_recovered)``; the FSM
    closes from half_open.

    Per the FSM contract (fsm.py:111-126) ``record_success`` only
    transitions out of half_open — the recovery short-path requires
    the FSM to first reach half_open via dwell expiry. This test
    forces half_open (mirroring the existing dormancy test pattern at
    framework/dormancy/tests/test_memory_sidecar_mode.py:59) so the
    bridge's recovered-signal effect is observable directly.
    """
    from loam.dormancy.fsm import DegradationMode, FSMState
    from loam.orchestrator.supervisor import SupervisorState
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
        _build_supervisor_bridge,
    )

    await DormancyContribution().contribute(fake_host)
    comp = fake_host.dormancy
    bridge = _build_supervisor_bridge(comp)

    await bridge(_make_transition(SupervisorState.degraded))
    fsm = comp.detector.fsms[DegradationMode.memory_sidecar]
    assert fsm.state == FSMState.open

    # Force half_open (would normally happen after dwell expiry) so the
    # recovery signal can close it via record_success.
    fsm.state = FSMState.half_open

    await bridge(_make_transition(SupervisorState.normal))

    assert fsm.state == FSMState.closed


@pytest.mark.asyncio
async def test_AC_OSS_M5_4_bridge_recovering_is_noop(fake_host) -> None:
    """``to_state == recovering`` is an intermediate supervisor state;
    the bridge emits no dormancy signal."""
    from loam.dormancy.fsm import DegradationMode, FSMState
    from loam.orchestrator.supervisor import SupervisorState
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
        _build_supervisor_bridge,
    )

    await DormancyContribution().contribute(fake_host)
    comp = fake_host.dormancy
    bridge = _build_supervisor_bridge(comp)

    fsm = comp.detector.fsms[DegradationMode.memory_sidecar]
    state_before = fsm.state

    await bridge(_make_transition(SupervisorState.recovering))

    # No transition fired — FSM unchanged.
    assert fsm.state == state_before
    assert fsm.state == FSMState.closed
