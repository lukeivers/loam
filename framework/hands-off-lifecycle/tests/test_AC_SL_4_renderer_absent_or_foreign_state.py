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


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
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
