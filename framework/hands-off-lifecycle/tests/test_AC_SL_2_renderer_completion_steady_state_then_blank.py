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

"""AC.SL.2 — completion steady-state for 60 s, then blank.

Outcome (per locked plan §4 / D2 ruling 2026-04-26): when the worker
has just completed (``status=completed``, ``updated_at`` within the
last 60 s) the renderer produces a "ready"-shaped steady-state line
≤ 200 chars, exit 0. When the worker completed more than 60 s ago,
the renderer produces empty stdout, exit 0.

Two fixtures: now-30s (inside window) and now-3600s (outside window).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_state import FirstRunState, write_state  # noqa: E402
from statusline import _MAX_LINE, render  # noqa: E402


def _completed_state(workspace: Path, *, age_s: float) -> None:
    now = time.time()
    state = FirstRunState(
        status="completed",
        pid=0,
        started_at=now - 600.0,
        updated_at=now - age_s,
        phase="complete",
        detail="first-run finished; supervisor stanza active",
        workspace_root=str(workspace.resolve()),
        progress_pct=100,
    )
    write_state(state, workspace)
    # ``write_state`` rewrites updated_at to time.time(); restore.
    state.updated_at = now - age_s
    workspace_state = workspace / "workspace" / ".pos" / "first-run.state"
    workspace_state.write_text(state.to_json())


def test_AC_SL_2_recent_completion_renders_steady_state(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    _completed_state(workspace, age_s=30.0)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line, "expected steady-state line within the 60s window"
    assert "ready" in line.lower()
    assert len(line) <= _MAX_LINE


def test_AC_SL_2_old_completion_renders_blank(tmp_path: Path) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    _completed_state(workspace, age_s=3600.0)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line == "", (
        f"expected empty stdout outside the 60s window; got {line!r}"
    )
