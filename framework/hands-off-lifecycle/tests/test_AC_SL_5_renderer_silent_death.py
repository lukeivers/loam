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

"""AC.SL.5 — stale-live state (silent worker death) glanceable summary.

Outcome (per locked plan §4): when the state-file's ``status`` is
``running`` or ``starting`` and the recorded pid is not alive AND
the most-recent ``updated_at`` is older than the dispatcher's
``is_stale_live_state`` grace window, the renderer produces a
one-line stalled-summary instructing the user to reopen Claude
(≤ 200 chars), exit 0.
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


def _find_dead_pid() -> int:
    """Return a pid that is guaranteed not to exist.

    Scans candidate pids 99000 upward and returns the first one
    ``os.kill(pid, 0)`` reports as not-running. Robust across hosts.
    """
    import os

    for candidate in range(99000, 99500):
        try:
            os.kill(candidate, 0)
        except ProcessLookupError:
            return candidate
        except PermissionError:
            continue
    # Fallback — vanishingly unlikely to be alive on a fresh host.
    return 99999


def test_AC_SL_5_stale_live_state_renders_stalled_summary(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    state = FirstRunState(
        status="running",
        pid=_find_dead_pid(),
        started_at=time.time() - 600.0,
        updated_at=time.time() - 600.0,
        phase="phase-3b-shared-deps",
        workspace_root=str(workspace.resolve()),
    )
    write_state(state, workspace)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line, "stale-live state should produce a stalled summary"
    assert "stalled" in line.lower()
    assert "reopen" in line.lower(), (
        f"stalled summary missing reopen instruction: {line!r}"
    )
    assert len(line) <= _MAX_LINE
