"""AC.J.5 — Workspace-bootstrap installs the memory-write-worker
launchd plist.

Outcome (per locked plan §4): the first-run scaffold provisions a
launchd plist named
``com.pos-v2.<slug>.memory-write-worker.plist`` carrying
``KeepAlive=true``, ``RunAtLoad=true``, ``ThrottleInterval=10``
(matching the memory-graphiti shape per amendment #29). The plist's
``ProgramArguments`` invokes the persona CLI's ``memory-worker``
subcommand under the workspace's ``.venv``.

The worker module + drain loop live under ``primary-persona/`` and
are tested in
``primary-persona/tests/test_AC_J_5_worker_drain_loop.py``; this
test exercises the workspace-bootstrap-side plist provisioning only.
"""

from __future__ import annotations

from pathlib import Path

from workspace_bootstrap.adapters.first_run_scaffold import (
    WORKER_CONFIG_FILENAME,
    WORKSPACE_POS_DIR,
    run_first_run_scaffold,
    service_label,
)


def test_AC_J_5_scaffold_installs_memory_write_worker_plist(tmp_path: Path) -> None:
    """The scaffold writes a memory-write-worker plist alongside the
    memory-graphiti and orchestrator plists; the new plist's contents
    match the supervised-launchd shape."""
    workspace = tmp_path / "test-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos"
    agents = tmp_path / "LaunchAgents"

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    label = service_label("memory-write-worker", "test-ws")
    plist_path = agents / f"{label}.plist"
    assert plist_path.exists(), f"worker plist missing: {plist_path}"
    text = plist_path.read_text()

    # Label + WorkingDirectory.
    assert f"<key>Label</key><string>{label}</string>" in text
    assert f"<key>WorkingDirectory</key><string>{workspace}</string>" in text

    # AC.J.5: supervised-launchd shape.
    assert "<key>KeepAlive</key><true/>" in text
    assert "<key>RunAtLoad</key><true/>" in text
    assert "<key>ThrottleInterval</key><integer>10</integer>" in text

    # AC.J.5: invokes the persona CLI's memory-worker subcommand.
    assert "<string>memory-worker</string>" in text
    assert "<string>--workspace</string>" in text
    # The .venv path inside the workspace is the runtime.
    assert f"<string>{workspace}/.venv/bin/python</string>" in text


def test_AC_J_5_distinct_workspaces_get_distinct_worker_labels(tmp_path: Path) -> None:
    """Per amendment #6 namespacing: two workspaces produce two
    differently-labelled worker plists."""
    ws_a = tmp_path / "alpha-ws"
    ws_a.mkdir()
    ws_b = tmp_path / "beta-ws"
    ws_b.mkdir()
    pos_a = tmp_path / "pos-a"
    pos_b = tmp_path / "pos-b"
    agents_a = tmp_path / "agents-a"
    agents_b = tmp_path / "agents-b"

    run_first_run_scaffold(
        pos_root=pos_a,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents_a,
        workspace_root=ws_a,
    )
    run_first_run_scaffold(
        pos_root=pos_b,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents_b,
        workspace_root=ws_b,
    )

    label_a = service_label("memory-write-worker", "alpha-ws")
    label_b = service_label("memory-write-worker", "beta-ws")
    assert label_a != label_b
    assert (agents_a / f"{label_a}.plist").exists()
    assert (agents_b / f"{label_b}.plist").exists()


def test_AC_J_5_scaffold_writes_worker_config_yaml(tmp_path: Path) -> None:
    """The scaffold writes a starter ``memory-worker.yaml`` under
    ``<workspace>/.pos/`` carrying the D-3 retry-curve defaults."""
    workspace = tmp_path / "test-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos"
    agents = tmp_path / "LaunchAgents"

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    cfg = workspace / WORKSPACE_POS_DIR / WORKER_CONFIG_FILENAME
    assert cfg.exists()
    text = cfg.read_text(encoding="utf-8")
    # D-3 lock: 5 retries, 2s→60s exp backoff.
    assert "max_retries: 5" in text
    assert "backoff_initial_s: 2.0" in text
    assert "backoff_max_s: 60.0" in text


def test_AC_J_5_worker_config_idempotent_re_run(tmp_path: Path) -> None:
    """Operator edits to ``memory-worker.yaml`` survive partial-
    recovery re-runs."""
    workspace = tmp_path / "test-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos"
    agents = tmp_path / "LaunchAgents"

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )

    cfg = workspace / WORKSPACE_POS_DIR / WORKER_CONFIG_FILENAME
    cfg.write_text("max_retries: 9\n# operator-tuned\n")

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        partial_recovery=True,
    )

    assert "max_retries: 9" in cfg.read_text(encoding="utf-8")
    assert "operator-tuned" in cfg.read_text(encoding="utf-8")
