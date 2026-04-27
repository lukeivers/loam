"""AC.J.1 — Pre-warm advisory file written by workspace-bootstrap.

Outcome (per locked plan §4 + D-1 lock): the first-run scaffold
writes ``<workspace>/.pos/ollama-prewarm-recommended.txt`` carrying
the recommended ``OLLAMA_KEEP_ALIVE`` value (D-5 lock: 24h) and
operator instructions for setting it on the Ollama daemon.

Per Hard Constraint 12 (locked plan §6): pos-v2 does NOT touch the
operator's homebrew-installed Ollama plist. The advisory file is
the propagation surface only — the operator runs the named
commands themselves.
"""

from __future__ import annotations

from pathlib import Path

from workspace_bootstrap.adapters.first_run_scaffold import (
    PREWARM_ADVISORY_FILENAME,
    WORKSPACE_POS_DIR,
    run_first_run_scaffold,
)


def test_AC_J_1_fresh_scaffold_writes_advisory_file(tmp_path: Path) -> None:
    """Fresh-clone scaffold lands the advisory file under the
    workspace's ``.pos/`` dir."""
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

    advisory = workspace / "workspace" / WORKSPACE_POS_DIR / PREWARM_ADVISORY_FILENAME
    assert advisory.exists(), f"advisory file not written at {advisory}"
    text = advisory.read_text(encoding="utf-8")
    # AC.J.1 + D-5: 24h is the recommended value.
    assert "OLLAMA_KEEP_ALIVE=24h" in text
    # Hard Constraint 12 — operator-side commands named (not executed
    # by pos-v2):
    assert "launchctl setenv" in text
    assert "brew services restart ollama" in text


def test_AC_J_1_re_run_does_not_clobber_user_edits(tmp_path: Path) -> None:
    """Idempotent: a partial-recovery re-run respects existing edits
    (the operator may have customised the advisory or pinned a
    different keep-alive value)."""
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

    advisory = workspace / "workspace" / WORKSPACE_POS_DIR / PREWARM_ADVISORY_FILENAME
    # Operator edits the advisory.
    advisory.write_text("OLLAMA_KEEP_ALIVE=12h\n# operator-customised\n")

    # Partial-recovery re-run.
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        partial_recovery=True,
    )

    # User edits preserved.
    text = advisory.read_text(encoding="utf-8")
    assert "OLLAMA_KEEP_ALIVE=12h" in text
    assert "operator-customised" in text


def test_AC_J_1_advisory_under_workspace_pos_not_user_pos(tmp_path: Path) -> None:
    """The advisory file lives under ``<workspace>/.pos/`` (workspace-
    local), NOT under ``~/.pos/``. Hard Constraint 12 + plan §11 D-1
    lock — workspaces own their advisory state."""
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

    workspace_advisory = workspace / "workspace" / WORKSPACE_POS_DIR / PREWARM_ADVISORY_FILENAME
    user_advisory = pos_root / PREWARM_ADVISORY_FILENAME
    assert workspace_advisory.exists()
    assert not user_advisory.exists(), (
        f"advisory must live under <workspace>/.pos/, NOT ~/.pos/; "
        f"found {user_advisory}"
    )
