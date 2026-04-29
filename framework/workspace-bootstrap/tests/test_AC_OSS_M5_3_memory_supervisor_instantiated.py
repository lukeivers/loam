"""AC.OSS-M5.3 — MemorySupervisor instantiated in production.

Per amendment #86 (M5 wire-dormancy). When ``host.memory_sidecar_url``
is populated by the ``memory_system`` adapter, the dormancy adapter
constructs a ``MemorySupervisor`` against a stdlib-urlopen probe + an
``on_transition`` bridge into dormancy's
``record_supervisor_signal`` surface, then awaits ``supervisor.start()``
and registers a shutdown hook. This test asserts:

  - ``host.memory_supervisor`` is a ``MemorySupervisor`` instance.
  - The supervisor's initial state is ``normal``.
  - A shutdown hook named ``"memory_supervisor"`` is registered.

The probe path is mocked (no real HTTP) by patching the adapter's
internal ``_build_probe`` helper.

Programme: OSS v0.1.0 publish — M5 — wire-dormancy.
Plan: docs/rebuild/plans/oss-v0-1-0-publish-dormancy-constructor.md.
AC family: AC.OSS-M5.3.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fake_host_with_sidecar(tmp_path: Path):
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
    # Populate memory_sidecar_url to drive the supervisor branch.
    host.memory_sidecar_url = "http://127.0.0.1:65535/health"

    yield host

    try:
        host.scope_runtime.close()
    except Exception:
        pass


@pytest.mark.asyncio
async def test_AC_OSS_M5_3_supervisor_instantiated_when_sidecar_url_set(
    fake_host_with_sidecar, monkeypatch
) -> None:
    """When ``host.memory_sidecar_url`` is populated, the adapter
    constructs a ``MemorySupervisor`` and assigns it to
    ``host.memory_supervisor``."""
    from loam.orchestrator.supervisor import (
        MemorySupervisor,
        ProbeResult,
        SupervisorState,
    )
    from loam.workspace_bootstrap.adapters import dormancy as dormancy_adapter
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    # Patch the probe builder so no real HTTP fires during start().
    async def _stub_probe() -> ProbeResult:
        return ProbeResult(ok=True, latency_ms=1.0)

    monkeypatch.setattr(
        dormancy_adapter, "_build_probe", lambda url: _stub_probe
    )

    await DormancyContribution().contribute(fake_host_with_sidecar)

    assert isinstance(
        fake_host_with_sidecar.memory_supervisor, MemorySupervisor
    )
    assert (
        fake_host_with_sidecar.memory_supervisor.state
        == SupervisorState.normal
    )

    # Stop the supervisor so the background loop doesn't outlive the test.
    await fake_host_with_sidecar.memory_supervisor.stop()


@pytest.mark.asyncio
async def test_AC_OSS_M5_3_shutdown_hook_registered(
    fake_host_with_sidecar, monkeypatch
) -> None:
    """A shutdown hook named ``memory_supervisor`` is registered on
    the host."""
    from loam.orchestrator.supervisor import ProbeResult
    from loam.workspace_bootstrap.adapters import dormancy as dormancy_adapter
    from loam.workspace_bootstrap.adapters.dormancy import (
        DormancyContribution,
    )

    async def _stub_probe() -> ProbeResult:
        return ProbeResult(ok=True, latency_ms=1.0)

    monkeypatch.setattr(
        dormancy_adapter, "_build_probe", lambda url: _stub_probe
    )

    await DormancyContribution().contribute(fake_host_with_sidecar)

    hooks = fake_host_with_sidecar._shutdown_hooks
    names = [name for name, _ in hooks]
    assert "memory_supervisor" in names

    await fake_host_with_sidecar.memory_supervisor.stop()
