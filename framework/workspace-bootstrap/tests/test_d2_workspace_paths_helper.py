"""D.2 — workspace_paths helper unit tests (amendment #63).

Pure unit tests for ``workspace_bootstrap.workspace_paths``. Covers
the constant + helper-function surface every framework reader
imports.

Backing AC: support tests for AC.D.2.4 + AC.D.2.5 (the helper is the
substrate the structural-guard runs on).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workspace_bootstrap.workspace_paths import (
    CLAUDE_SUBDIR,
    DATA_SUBDIR,
    MCP_JSON_FILENAME,
    MEMORY_WORKER_ERR_LOG,
    MEMORY_WORKER_OUT_LOG,
    ORCHESTRATOR_ERR_LOG,
    ORCHESTRATOR_OUT_LOG,
    PERSONAS_SUBDIR,
    POS_SUBDIR,
    SCRATCH_SUBDIR,
    TRACKER_DB_FILENAME,
    WORKSPACE_STATE_SUBDIR,
    WorkspaceLayout,
    claude_dir,
    data_subdir,
    mcp_json_path,
    memory_worker_log_paths,
    orchestrator_log_paths,
    personas_dir,
    pos_subdir,
    scratch_dir,
    tracker_db_path,
    workspace_state_dir,
)


def test_d2_constants_match_locked_values() -> None:
    """Constants are part of the contract every reader imports.

    Changing one is a fence-wide ripple — the test pins them.
    """
    assert WORKSPACE_STATE_SUBDIR == "workspace"
    assert POS_SUBDIR == ".pos"
    assert PERSONAS_SUBDIR == "personas"
    assert DATA_SUBDIR == "data"
    assert SCRATCH_SUBDIR == ".scratch"
    assert MCP_JSON_FILENAME == ".mcp.json"
    assert TRACKER_DB_FILENAME == "objective_tracker.sqlite"
    assert ORCHESTRATOR_OUT_LOG == "orchestrator.out.log"
    assert ORCHESTRATOR_ERR_LOG == "orchestrator.err.log"
    assert MEMORY_WORKER_OUT_LOG == "memory-write-worker.out.log"
    assert MEMORY_WORKER_ERR_LOG == "memory-write-worker.err.log"
    assert CLAUDE_SUBDIR == ".claude"


def test_d2_helpers_root_under_workspace_state_subdir(tmp_path: Path) -> None:
    """Every workspace-state helper returns a path under
    ``<ws>/workspace/`` — the WORKSPACE_STATE_SUBDIR contract.
    """
    ws = tmp_path / "ws"
    ws.mkdir()

    expected_state_root = ws / WORKSPACE_STATE_SUBDIR

    assert workspace_state_dir(ws) == expected_state_root
    assert pos_subdir(ws) == expected_state_root / POS_SUBDIR
    assert personas_dir(ws) == expected_state_root / PERSONAS_SUBDIR
    assert data_subdir(ws) == expected_state_root / DATA_SUBDIR
    assert scratch_dir(ws) == expected_state_root / SCRATCH_SUBDIR
    assert mcp_json_path(ws) == expected_state_root / MCP_JSON_FILENAME
    assert tracker_db_path(ws) == expected_state_root / TRACKER_DB_FILENAME

    out, err = orchestrator_log_paths(ws)
    assert out == expected_state_root / ORCHESTRATOR_OUT_LOG
    assert err == expected_state_root / ORCHESTRATOR_ERR_LOG

    out, err = memory_worker_log_paths(ws)
    assert out == expected_state_root / MEMORY_WORKER_OUT_LOG
    assert err == expected_state_root / MEMORY_WORKER_ERR_LOG


def test_d2_claude_dir_at_workspace_root_not_under_state_subdir(
    tmp_path: Path,
) -> None:
    """D-Q.A4 lock: ``.claude/`` lives at workspace root, NOT under
    ``workspace/``. Claude Code's MCP-discovery + agents discovery
    looks at ``<ws>/.claude/``.
    """
    ws = tmp_path / "ws"
    ws.mkdir()

    assert claude_dir(ws) == ws / CLAUDE_SUBDIR
    # Defence: ensure claude_dir is NOT inside workspace_state_dir.
    state_root = workspace_state_dir(ws)
    assert CLAUDE_SUBDIR not in state_root.parts


def test_d2_layout_construction_returns_pydantic_model(tmp_path: Path) -> None:
    """``WorkspaceLayout`` is the schema; helpers wrap it. Direct
    construction yields a Pydantic-validated model with computed-
    attribute access.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    layout = WorkspaceLayout(workspace_root=ws)
    assert layout.workspace_root == ws
    assert layout.workspace_state_dir == ws / WORKSPACE_STATE_SUBDIR
    assert layout.pos_dir == ws / WORKSPACE_STATE_SUBDIR / POS_SUBDIR


def test_d2_helpers_accept_str_or_path(tmp_path: Path) -> None:
    """Helpers normalise ``str`` to ``Path`` internally."""
    ws = tmp_path / "ws"
    ws.mkdir()

    expected = ws / WORKSPACE_STATE_SUBDIR / POS_SUBDIR
    assert pos_subdir(str(ws)) == expected
    assert pos_subdir(ws) == expected


def test_d2_two_workspaces_resolve_to_distinct_paths(tmp_path: Path) -> None:
    """Cross-workspace bleed defence: two workspace_root values yield
    two distinct workspace-state trees.
    """
    ws_a = tmp_path / "alpha"
    ws_b = tmp_path / "beta"
    ws_a.mkdir()
    ws_b.mkdir()

    assert pos_subdir(ws_a) != pos_subdir(ws_b)
    assert tracker_db_path(ws_a) != tracker_db_path(ws_b)
    assert mcp_json_path(ws_a) != mcp_json_path(ws_b)
