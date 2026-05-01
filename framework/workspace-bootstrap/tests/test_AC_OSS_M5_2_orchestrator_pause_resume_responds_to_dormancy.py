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

"""AC.OSS-M5.2 — Orchestrator pause/resume hooks bound via DormancyComponent.

Per amendment #86 (M5 wire-dormancy). The PolicyDispatcher's apply
already calls ``orchestrator.pause_activation(reason)``; the gap was
that the dispatcher was never constructed in production. With the
adapter promotion in AC.OSS-M5.1 the dispatcher now exists and binds
the orchestrator. This test exercises that wiring directly:
``dispatcher.apply(...)`` causes ``host.orchestrator.is_paused`` to
flip True; ``dispatcher.release(...)`` flips it False.

Programme: OSS v0.1.0 publish — M5 — wire-dormancy.
Plan: docs/rebuild/plans/oss-v0-1-0-publish-dormancy-constructor.md.
AC family: AC.OSS-M5.2.
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


@pytest.mark.asyncio
async def test_AC_OSS_M5_2_dispatcher_apply_pauses_orchestrator(
    fake_host,
) -> None:
    """``dispatcher.apply(...)`` calls ``orchestrator.pause_activation``;
    asserts ``is_paused`` flips True."""
    from loam.dormancy.fsm import DegradationMode
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host)
    comp = fake_host.dormancy

    assert fake_host.orchestrator.is_paused is False

    await comp.dispatcher.apply(
        mode=DegradationMode.memory_sidecar,
        episode_id="test-ep-1",
        signal="memory_sidecar_down",
    )

    assert fake_host.orchestrator.is_paused is True


@pytest.mark.asyncio
async def test_AC_OSS_M5_2_dispatcher_release_resumes_orchestrator(
    fake_host,
) -> None:
    """After apply→release, ``is_paused`` returns to False."""
    from loam.dormancy.fsm import DegradationMode
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host)
    comp = fake_host.dormancy

    app = await comp.dispatcher.apply(
        mode=DegradationMode.memory_sidecar,
        episode_id="test-ep-2",
        signal="memory_sidecar_down",
    )
    assert fake_host.orchestrator.is_paused is True

    await comp.dispatcher.release(
        mode=DegradationMode.memory_sidecar,
        episode_id="test-ep-2",
        paused_scope_ids=app.paused_scope_ids,
    )

    assert fake_host.orchestrator.is_paused is False


@pytest.mark.asyncio
async def test_AC_OSS_M5_2_pause_event_recorded_on_orchestrator(
    fake_host,
) -> None:
    """The orchestrator's local_state captures the pause_activation
    event with the dispatcher-supplied reason."""
    from loam.dormancy.fsm import DegradationMode
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host)
    comp = fake_host.dormancy

    await comp.dispatcher.apply(
        mode=DegradationMode.memory_sidecar,
        episode_id="reason-test",
        signal="memory_sidecar_down",
    )

    # The dispatcher emits the reason as
    # "claude_upstream_degraded:<mode>:<episode_id>" (per dormancy/policy.py).
    state = fake_host.orchestrator.local_state
    pauses = state.events_of_type("pause_activation")
    assert len(pauses) >= 1
    assert any(
        "memory_sidecar" in str(p.payload.get("reason", ""))
        for p in pauses
    )
