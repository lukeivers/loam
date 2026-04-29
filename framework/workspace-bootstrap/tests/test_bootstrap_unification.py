"""Amendment #7 — orchestrator-bootstrap-unification (framework side).

Each test maps 1:1 to an acceptance criterion in
``docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md``.

Covered here (framework/adapter-owned behaviours):
  * AC3 — missing ``bootstrap.yaml`` is the new fail-closed trigger.
  * AC4 — the adapter still loads ``bootstrap.py`` when present.
  * AC5 — the adapter is a successful no-op when ``bootstrap.py`` is
    missing and ``required`` is unset (default False).
  * AC6 — the adapter fails closed (AdapterRaisedError / -32086) when
    ``required: True`` and ``bootstrap.py`` is missing.

AC1/AC2/AC7/AC8 live in orchestrator/tests/test_bootstrap_unification.py
because they exercise orchestrator-owned surfaces.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import pytest
import yaml

from loam.workspace_bootstrap import AdapterRaisedError, Bootstrapper, load_manifest
from loam.workspace_bootstrap.errors import MissingConfigError


def _short_socket_path() -> Path:
    return Path(tempfile.gettempdir()) / f"pos-{uuid.uuid4().hex[:12]}.sock"


def _write_orchestrator_yaml(workspace: Path) -> None:
    (workspace / "config").mkdir(parents=True, exist_ok=True)
    root = workspace / ".pos"
    root.mkdir(parents=True, exist_ok=True)
    cfg = {
        "root_dir": str(root),
        "socket_path": str(_short_socket_path()),
        "heartbeat_interval_seconds": 0.05,
        "sigterm_grace_seconds": 1.0,
    }
    (workspace / "config" / "orchestrator.yaml").write_text(yaml.safe_dump(cfg))


_CORE_CONTRIBUTIONS = [
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


def _write_minimal_workspace(
    tmp_path: Path,
    *,
    wbp_config: dict | None = None,
) -> Path:
    """Build a manifest + config tree under tmp_path and return the
    manifest path. ``wbp_config`` is written to
    ``config/workspace_bootstrap_py.yaml`` when provided."""
    _write_orchestrator_yaml(tmp_path)
    (tmp_path / "config" / "memory.yaml").write_text(
        yaml.safe_dump({"launch": False})
    )
    (tmp_path / "config" / "self_upgrade.yaml").write_text(
        yaml.safe_dump({"required": False})
    )
    if wbp_config is not None:
        (tmp_path / "config" / "workspace_bootstrap_py.yaml").write_text(
            yaml.safe_dump(wbp_config)
        )
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": _CORE_CONTRIBUTIONS,
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))
    return manifest_path


def test_AC3_missing_bootstrap_yaml_fails_closed_in_framework(
    tmp_path: Path,
) -> None:
    """With no ``bootstrap.yaml`` at the expected path, the framework's
    ``load_manifest`` refuses fail-closed before any contribution runs.

    ``MissingConfigError`` carries code ``-32080`` (the framework's
    reserved band for missing configuration). No orchestrator process
    is constructed, no ``workspace_bootstrap_py`` adapter is invoked —
    the new fail-closed trigger fires upstream of everything.

    This replaces the orchestrator-internal exit-code-2 branch the
    proposal removed; see AC2 for the positive-space inverse.
    """
    missing_path = tmp_path / "does-not-exist" / "bootstrap.yaml"
    with pytest.raises(MissingConfigError) as excinfo:
        load_manifest(missing_path)
    # Code is in the framework's MISSING_CONFIG band (not introducing a
    # new top-level code, per proposal §5 ruling #4).
    assert excinfo.value.code == -32080, (
        f"expected MissingConfigError code -32080, got {excinfo.value.code}"
    )
    assert "not found" in str(excinfo.value).lower() or "manifest" in str(excinfo.value).lower()


@pytest.mark.asyncio
async def test_AC4_adapter_loads_bootstrap_py_when_present(
    tmp_path: Path,
) -> None:
    """Regression: with ``bootstrap.yaml`` listing
    ``workspace_bootstrap_py`` and a real ``bootstrap.py`` exposing
    ``def register(orch)`` that mutates orchestrator state, the
    framework run-through results in the orchestrator reflecting that
    mutation.

    Confirms the adapter honours orchestrator's
    ``load_and_register`` contract end-to-end. Amendment #7 moved the
    loader call-site from ``_startup`` to the adapter; this test pins
    the happy path after the move.
    """
    pos_root = tmp_path / ".pos"
    pos_root.mkdir(exist_ok=True)
    bootstrap_py = pos_root / "bootstrap.py"
    bootstrap_py.write_text(
        "def register(orchestrator):\n"
        "    orchestrator.marker = 42\n"
    )
    manifest_path = _write_minimal_workspace(
        tmp_path,
        wbp_config={
            "bootstrap_path": str(bootstrap_py),
            "required": True,
        },
    )
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        assert bs.host.orchestrator is not None
        assert getattr(bs.host.orchestrator, "marker", None) == 42, (
            "bootstrap.py's register() did not mutate the orchestrator; "
            "the adapter is no longer honouring load_and_register."
        )
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_AC5_adapter_noops_when_bootstrap_py_missing_and_not_required(
    tmp_path: Path,
) -> None:
    """Regression: with ``bootstrap.yaml`` listing
    ``workspace_bootstrap_py``, no ``bootstrap.py``, and no
    ``workspace_bootstrap_py.yaml`` (so ``required`` defaults to False),
    framework composition succeeds and ``host.orchestrator`` is
    populated. No exception reaches the user.

    Pins the new default: most workspaces don't ship a bootstrap.py,
    and they should boot cleanly anyway.
    """
    manifest_path = _write_minimal_workspace(tmp_path, wbp_config=None)
    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        assert bs.host.orchestrator is not None
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_AC6_adapter_fails_closed_when_required_true_and_missing(
    tmp_path: Path,
) -> None:
    """With ``bootstrap.yaml`` listing ``workspace_bootstrap_py``, a
    ``workspace_bootstrap_py.yaml`` declaring ``required: True``, and
    no ``bootstrap.py`` on disk, the framework raises
    ``AdapterRaisedError`` (code ``-32086``).

    Confirms the opt-in fail-closed path for production workspaces. The
    orchestrator-internal branch was removed; this is the sole surface
    that still refuses startup on a missing Python stub.
    """
    manifest_path = _write_minimal_workspace(
        tmp_path,
        wbp_config={
            "bootstrap_path": str(tmp_path / ".pos" / "bootstrap.py"),
            "required": True,
        },
    )
    # Ensure the target does not exist.
    bp = tmp_path / ".pos" / "bootstrap.py"
    if bp.exists():
        bp.unlink()

    bs = Bootstrapper(load_manifest(manifest_path))
    with pytest.raises(AdapterRaisedError) as excinfo:
        await bs.start()
    assert excinfo.value.code == -32086, (
        f"expected AdapterRaisedError code -32086, got {excinfo.value.code}"
    )
    await bs.shutdown()
