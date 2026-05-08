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

"""AC.OSS-M5.6 — Adapter short-circuits cleanly when memory sidecar absent.

Per amendment #86 (M5 wire-dormancy). When ``host.memory_sidecar_url``
is None (the ``memory_system`` adapter's ``launch: False`` config
skipped the sidecar entirely), the dormancy adapter:

  - Constructs ``DegradationComponent`` (Claude-API detection path
    stays active).
  - Skips ``MemorySupervisor`` construction.
  - Sets ``host.memory_supervisor = None``.
  - Registers no ``memory_supervisor`` shutdown hook.

Programme: OSS v0.1.0 publish — M5 — wire-dormancy.
Plan: docs/plans/oss-v0-1-0-publish-dormancy-constructor.md.
AC family: AC.OSS-M5.6.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fake_host_no_sidecar(tmp_path: Path):
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
    # memory_sidecar_url stays None (default).
    assert host.memory_sidecar_url is None

    yield host

    try:
        host.scope_runtime.close()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_AC_OSS_M5_6_component_built_supervisor_skipped(
    fake_host_no_sidecar,
) -> None:
    """``host.dormancy`` is a ``DegradationComponent`` instance,
    ``host.memory_supervisor`` is None."""
    from loam.dormancy.component import DegradationComponent
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host_no_sidecar)

    assert isinstance(fake_host_no_sidecar.dormancy, DegradationComponent)
    assert fake_host_no_sidecar.memory_supervisor is None


@pytest.mark.asyncio
async def test_AC_OSS_M5_6_no_supervisor_shutdown_hook(
    fake_host_no_sidecar,
) -> None:
    """No shutdown hook named ``memory_supervisor`` is registered when
    the sidecar URL is absent."""
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host_no_sidecar)

    hook_names = [
        name for name, _ in fake_host_no_sidecar._shutdown_hooks
    ]
    assert "memory_supervisor" not in hook_names
