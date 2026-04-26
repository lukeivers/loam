"""AC.SL.4 — empty render on absent or foreign-workspace state.

Outcome (per locked plan §4): when the state-file is absent OR
contains a ``workspace_root`` that does not match the stdin envelope's
workspace path, the renderer produces empty stdout, exit 0.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_state import FirstRunState, write_state  # noqa: E402
from statusline import render  # noqa: E402


def test_AC_SL_4_absent_state_file_renders_empty(tmp_path: Path) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    # No write_state call — state file does not exist.

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line == "", (
        f"absent state file should produce empty render; got {line!r}"
    )


def test_AC_SL_4_foreign_workspace_state_renders_empty(
    tmp_path: Path,
) -> None:
    """Defence-in-depth mirror of dispatcher's _state_belongs_to."""
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    other_workspace = tmp_path / "some-other-workspace"
    other_workspace.mkdir()
    # Write a state whose recorded workspace_root names the OTHER
    # workspace; the renderer should refuse to surface it.
    state = FirstRunState(
        status="running",
        pid=os.getpid(),
        started_at=time.time() - 10.0,
        updated_at=time.time(),
        phase="phase-3b-shared-deps",
        workspace_root=str(other_workspace.resolve()),
    )
    write_state(state, workspace)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line == "", (
        f"foreign-workspace state should produce empty render; got {line!r}"
    )


def test_AC_SL_4_envelope_without_project_dir_renders_empty(
    tmp_path: Path,
) -> None:
    """Malformed envelope (no workspace.project_dir) → empty render."""
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    state = FirstRunState(
        status="running",
        pid=os.getpid(),
        started_at=time.time() - 10.0,
        updated_at=time.time(),
        phase="phase-3b-shared-deps",
        workspace_root=str(workspace.resolve()),
    )
    write_state(state, workspace)

    # Envelope missing workspace.project_dir.
    envelope = {"workspace": {}}
    assert render(envelope) == ""

    # Envelope missing workspace key entirely.
    assert render({}) == ""
