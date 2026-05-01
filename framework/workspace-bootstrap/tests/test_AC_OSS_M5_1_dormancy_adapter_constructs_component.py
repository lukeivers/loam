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

"""AC.OSS-M5.1 — DormancyContribution constructs DegradationComponent in production.

Per amendment #86 (M5 wire-dormancy). The dormancy adapter previously
returned None from ``contribute()``; this test asserts the promoted
adapter actually constructs a ``DegradationComponent`` and assigns it
to ``host.dormancy``.

Programme: OSS v0.1.0 publish — M5 — wire-dormancy.
Plan: docs/rebuild/plans/oss-v0-1-0-publish-dormancy-constructor.md.
AC family: AC.OSS-M5.1.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fake_host(tmp_path: Path):
    """Build a synthesised BootstrapHost with a real orchestrator
    + scope-runtime so the adapter can complete construction."""
    from loam.orchestrator import Orchestrator
    from loam.orchestrator.config import OrchestratorConfig
    from loam.workspace_bootstrap.host import BootstrapHost

    cfg_dir = tmp_path / ".loam"
    cfg_dir.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    manifest = workspace / "bootstrap.yaml"

    # Orchestrator under a tmp root_dir so its sqlite + sockets are
    # per-test.
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

    # We don't need the full _startup() pipeline; just a ScopeRuntime
    # so the adapter's subscribe_all call finds a real emitter.
    from loam.scope_of_work import ScopeRuntime

    host.scope_runtime = ScopeRuntime(
        orch_cfg.scope_of_work_db,
        pending_extension_dir=orch_cfg.pending_extension_dir,
    )

    yield host

    # Cleanup: close any sockets / sqlite handles.
    try:
        host.scope_runtime.close()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_AC_OSS_M5_1_adapter_assigns_dormancy_to_host(fake_host) -> None:
    """The adapter's ``contribute(host)`` produces a
    ``DegradationComponent`` on ``host.dormancy``."""
    from loam.dormancy.component import DegradationComponent
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    contribution = DormancyContribution()
    await contribution.contribute(fake_host)

    assert isinstance(fake_host.dormancy, DegradationComponent)


@pytest.mark.asyncio
async def test_AC_OSS_M5_1_metadata_runs_after_primary_persona(
    fake_host,
) -> None:
    """The contribution's metadata declares ``after=('primary_persona',)``
    so the topo-sort schedules it after primary-persona populates
    ``host.orchestrator``."""
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )
    from loam.workspace_bootstrap.spec import Phase

    md = DormancyContribution.metadata
    assert md.phase == Phase.before_orchestrator_start
    assert md.after == ("primary_persona",)


@pytest.mark.asyncio
async def test_AC_OSS_M5_1_component_has_dispatcher_with_orchestrator_hook(
    fake_host,
) -> None:
    """The constructed component's dispatcher carries a reference to
    ``host.orchestrator`` — that's the binding AC.OSS-M5.2 verifies in
    detail; here we just confirm the wiring exists at construction."""
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    await DormancyContribution().contribute(fake_host)
    assert fake_host.dormancy.dispatcher.orchestrator is fake_host.orchestrator
