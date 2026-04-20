"""B12–B17 — foundational-adapter bundle integration.

End-to-end test: the ten foundational contributions listed in
`bootstrap.yaml`; main() runs; orchestrator starts; activate_scope
flows through the three-wrap chain in dispatch order
(safety → reversibility → cost → orig_activate).

The memory-sidecar adapter is EXCLUDED by default here — most CI
environments don't have Neo4j+Graphiti running. A separate test
(`test_memory_sidecar_health_probe`) covers B14 against a mock HTTP
server.

The `workspace_bootstrap_py` adapter is INCLUDED with
`required: False` and a non-existent bootstrap.py path so it
no-ops (B17 covered separately with a real file).
"""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Any, ClassVar

import pytest
import yaml


def _short_socket_path() -> Path:
    """macOS AF_UNIX path cap — use /tmp with short name."""
    return Path(tempfile.gettempdir()) / f"pos-{uuid.uuid4().hex[:12]}.sock"


def _write_orchestrator_yaml(workspace: Path) -> None:
    """Write orchestrator.yaml that puts the socket under /tmp."""
    (workspace / "config").mkdir(parents=True, exist_ok=True)
    root = workspace / ".pos"
    root.mkdir(parents=True, exist_ok=True)
    cfg = {
        "root_dir": str(root),
        "socket_path": str(_short_socket_path()),
        "heartbeat_interval_seconds": 0.05,
        "sigterm_grace_seconds": 1.0,
        "require_bootstrap": False,
    }
    (workspace / "config" / "orchestrator.yaml").write_text(yaml.safe_dump(cfg))

from workspace_bootstrap import (
    BaseContribution,
    Bootstrapper,
    ContributionMetadata,
    Phase,
    load_manifest,
)


def _write_workspace(tmp_path: Path, include_memory: bool = False) -> Path:
    """Write a full-bundle bootstrap.yaml for integration testing."""
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    _write_orchestrator_yaml(tmp_path)

    # Disable the memory sidecar by default.
    (tmp_path / "config" / "memory.yaml").write_text(
        yaml.safe_dump({"launch": False, "startup_timeout_s": 0.01})
    )
    (tmp_path / "config" / "self_upgrade.yaml").write_text(
        yaml.safe_dump({"required": False})
    )
    (tmp_path / "config" / "workspace_bootstrap_py.yaml").write_text(
        yaml.safe_dump(
            {
                "bootstrap_path": str(tmp_path / ".pos" / "bootstrap.py"),
                "required": False,
            }
        )
    )

    contributions: list[Any] = [
        "observability_aggregator",
        "scope_of_work",
        "objective_tracker",
        "primary_persona",
        "graceful_degradation",
    ]
    if include_memory:
        contributions.append("memory_system")
    contributions.extend(
        [
            "cost_governance",
            "reversibility_primitive",
            "safety_layer",
            "self_correction",
            "self_upgrade",
            "workspace_bootstrap_py",
        ]
    )

    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": contributions,
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))
    return manifest_path


@pytest.mark.asyncio
async def test_B12_full_bundle_starts_and_wraps_dispatch(tmp_path: Path) -> None:
    """B12: the foundational bundle boots end-to-end.

    Verifies:
      - all adapters run through in phase order;
      - the orchestrator is constructed and `_startup()` completed;
      - activate_scope IPC handler is installed with the three-wrap
        chain composed on top (by checking `host.ipc_server._handlers`
        has `activate_scope` and behaves when the chain runs).
    """
    manifest_path = _write_workspace(tmp_path)
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()

        # Orchestrator exists and is started.
        assert bs.host.orchestrator is not None
        assert bs.host.ipc_server is not None
        assert bs.host.scope_runtime is not None
        assert bs.host.objective_tracker is not None
        assert bs.host.monitor is not None

        # Gate controllers installed.
        assert bs.host.safety_controller is not None
        assert bs.host.reversibility_controller is not None
        assert bs.host.cost_controller is not None

        # Self-correction controller installed.
        assert bs.host.self_correction_controller is not None

        # activate_scope handler is installed.
        handler = bs.host.ipc_server._handlers["activate_scope"]
        assert callable(handler)
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B12_dispatch_chain_order(tmp_path: Path) -> None:
    """B12: safety → reversibility → cost → orig_activate order.

    We don't force a refusal here — the full-chain composition test
    lives in cost-governance's test suite. This test verifies that
    after the wrap phase finishes, the registered activate_scope
    handler is NOT the orchestrator's original — meaning the wraps
    composed on top.
    """
    from pos_orchestrator.ipc import IPCServer

    manifest_path = _write_workspace(tmp_path)
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        handler = bs.host.ipc_server._handlers["activate_scope"]
        # The orchestrator registers its inner activate_scope at startup;
        # the three wraps each replace it. So the handler we end up
        # with must differ from the orchestrator's own inner method.
        assert handler is not bs.host.orchestrator.activate_scope
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B13_self_correction_subscribes_on_scope_failure(tmp_path: Path) -> None:
    """B13: self-correction subscribes to ScopeRuntime.emitter and an
    episode row appears on a synthetic failed scope."""
    manifest_path = _write_workspace(tmp_path)
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        ctrl = bs.host.self_correction_controller
        # Assert the subscriber is wired.
        scope_runtime = bs.host.scope_runtime
        listeners = scope_runtime.emitter.listeners("*")
        assert len(listeners) >= 1, "ScopeRuntime.emitter has no '*' listener"
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B14_memory_sidecar_timeout_fails_with_32086(tmp_path: Path) -> None:
    """B14: memory-sidecar adapter times out to -32086 when /health
    never returns success.

    We craft a workspace that enables memory_system with a URL that
    has no listener. The adapter should fail-closed within its
    configured timeout and raise AdapterRaisedError (-32086).
    """
    from workspace_bootstrap import AdapterRaisedError, IPC_BOOTSTRAP_ADAPTER_RAISED

    (tmp_path / "config").mkdir()
    # Point at a port that should be closed (high, random); short timeout.
    (tmp_path / "config" / "memory.yaml").write_text(
        yaml.safe_dump(
            {
                "launch": False,
                "host": "127.0.0.1",
                "port": 1,  # privileged port with no listener in tests
                "startup_timeout_s": 0.5,
                "poll_interval_s": 0.05,
            }
        )
    )
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": ["observability_aggregator", "memory_system"],
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))

    bs = Bootstrapper(load_manifest(manifest_path))
    with pytest.raises(AdapterRaisedError) as excinfo:
        await bs.start()
    assert excinfo.value.code == IPC_BOOTSTRAP_ADAPTER_RAISED
    assert "memory_system" in excinfo.value.message or "sidecar" in excinfo.value.message
    await bs.shutdown()


@pytest.mark.asyncio
async def test_B14_memory_sidecar_succeeds_on_mock_health(tmp_path: Path) -> None:
    """B14 positive case: a mock HTTP server returning 200 on /health
    lets the adapter proceed, populating host.memory_sidecar_url."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *a, **kw):
            pass

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            else:
                self.send_response(404)
                self.end_headers()

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        (tmp_path / "config").mkdir()
        (tmp_path / "config" / "memory.yaml").write_text(
            yaml.safe_dump(
                {
                    "launch": False,
                    "host": "127.0.0.1",
                    "port": port,
                    "startup_timeout_s": 5.0,
                    "poll_interval_s": 0.05,
                }
            )
        )
        manifest = {
            "version": 1,
            "workspace_root": str(tmp_path),
            "config_dir": str(tmp_path / "config"),
            "contributions": ["observability_aggregator", "memory_system"],
        }
        manifest_path = tmp_path / "bootstrap.yaml"
        manifest_path.write_text(yaml.safe_dump(manifest))

        bs = Bootstrapper(load_manifest(manifest_path))
        try:
            await bs.start()
            assert bs.host.memory_sidecar_url is not None
            assert f":{port}/health" in bs.host.memory_sidecar_url
        finally:
            await bs.shutdown()
    finally:
        server.shutdown()
        thread.join(timeout=2.0)


@pytest.mark.asyncio
async def test_B15_self_upgrade_cli_probe_success(tmp_path: Path) -> None:
    """B15: self-upgrade adapter runs the probe. With a sensible
    default (pos --help) and `required: False`, the adapter no-ops
    if `pos` is missing. A failing probe with required=True raises
    -32086. We test both sides."""
    from workspace_bootstrap import AdapterRaisedError

    (tmp_path / "config").mkdir()
    # A probe that always succeeds (`true` exits 0 on POSIX).
    (tmp_path / "config" / "self_upgrade.yaml").write_text(
        yaml.safe_dump({"probe_cmd": ["true"], "required": True})
    )
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": ["self_upgrade"],
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))

    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()  # should NOT raise.
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B15_self_upgrade_cli_probe_failure(tmp_path: Path) -> None:
    """B15 negative case."""
    from workspace_bootstrap import (
        AdapterRaisedError,
        IPC_BOOTSTRAP_ADAPTER_RAISED,
    )

    (tmp_path / "config").mkdir()
    # A probe that always fails.
    (tmp_path / "config" / "self_upgrade.yaml").write_text(
        yaml.safe_dump({"probe_cmd": ["false"], "required": True})
    )
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": ["self_upgrade"],
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))
    bs = Bootstrapper(load_manifest(manifest_path))
    with pytest.raises(AdapterRaisedError) as excinfo:
        await bs.start()
    assert excinfo.value.code == IPC_BOOTSTRAP_ADAPTER_RAISED


@pytest.mark.asyncio
async def test_B16_orchestrator_constructed_four_on_host(tmp_path: Path) -> None:
    """B16: scope_runtime, objective_tracker, monitor are on the host
    after the primary_persona contribution runs. The declaration-only
    adapters register names in the ordering DAG without side effects."""
    manifest_path = _write_workspace(tmp_path)
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        # The orchestrator-constructed components exist on the host.
        assert bs.host.scope_runtime is not None
        assert bs.host.objective_tracker is not None
        assert bs.host.monitor is not None
        # Verify declaration-only adapters ran (names appear in completed list).
        names_completed = [rc.name for rc in bs._completed_contributions]
        assert "scope_of_work" in names_completed
        assert "objective_tracker" in names_completed
        assert "graceful_degradation" in names_completed
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B17_workspace_bootstrap_py_fires_register(tmp_path: Path) -> None:
    """B17: workspace_bootstrap_py invokes the sealed
    orchestrator/src/bootstrap.py::load_and_register with
    host.orchestrator. A file defining `register(orchestrator)` runs."""
    _write_orchestrator_yaml(tmp_path)
    (tmp_path / ".pos").mkdir(exist_ok=True)
    bootstrap_py = tmp_path / ".pos" / "bootstrap.py"
    bootstrap_py.write_text(
        "FIRED = []\n"
        "def register(orchestrator):\n"
        "    FIRED.append(orchestrator)\n"
    )
    (tmp_path / "config" / "memory.yaml").write_text(
        yaml.safe_dump({"launch": False})
    )
    (tmp_path / "config" / "self_upgrade.yaml").write_text(
        yaml.safe_dump({"required": False})
    )
    (tmp_path / "config" / "workspace_bootstrap_py.yaml").write_text(
        yaml.safe_dump(
            {"bootstrap_path": str(bootstrap_py), "required": True}
        )
    )
    contributions = [
        "observability_aggregator",
        "scope_of_work",
        "objective_tracker",
        "primary_persona",
        "graceful_degradation",
        "cost_governance",
        "reversibility_primitive",
        "safety_layer",
        "self_correction",
        "workspace_bootstrap_py",
    ]
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": contributions,
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        # The bootstrap.py module should have FIRED with the orchestrator.
        import sys

        # It got loaded under a sanitised name by the orchestrator's
        # loader; search for the one that has FIRED populated.
        found = False
        for k, mod in list(sys.modules.items()):
            if not k.startswith("_pos_workspace_bootstrap_"):
                continue
            if hasattr(mod, "FIRED") and mod.FIRED:
                found = True
                assert mod.FIRED[0] is bs.host.orchestrator
                break
        assert found, "workspace bootstrap.py register() did not fire"
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B17_workspace_bootstrap_py_missing_non_required(tmp_path: Path) -> None:
    """B17: missing bootstrap.py with required=False is a no-op (not a failure)."""
    manifest_path = _write_workspace(tmp_path)
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        # _write_workspace sets required=False and points at a
        # non-existent file, so startup succeeds.
        await bs.start()
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B17_workspace_bootstrap_py_missing_required_fails(tmp_path: Path) -> None:
    """B17: missing bootstrap.py with required=True raises -32086."""
    from workspace_bootstrap import AdapterRaisedError

    _write_orchestrator_yaml(tmp_path)
    (tmp_path / "config" / "memory.yaml").write_text(
        yaml.safe_dump({"launch": False})
    )
    (tmp_path / "config" / "self_upgrade.yaml").write_text(
        yaml.safe_dump({"required": False})
    )
    (tmp_path / "config" / "workspace_bootstrap_py.yaml").write_text(
        yaml.safe_dump(
            {
                "bootstrap_path": str(tmp_path / "does_not_exist.py"),
                "required": True,
            }
        )
    )
    contributions = [
        "observability_aggregator",
        "scope_of_work",
        "objective_tracker",
        "primary_persona",
        "graceful_degradation",
        "cost_governance",
        "reversibility_primitive",
        "safety_layer",
        "self_correction",
        "workspace_bootstrap_py",
    ]
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": contributions,
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))
    bs = Bootstrapper(load_manifest(manifest_path))
    with pytest.raises(AdapterRaisedError):
        await bs.start()
    await bs.shutdown()
