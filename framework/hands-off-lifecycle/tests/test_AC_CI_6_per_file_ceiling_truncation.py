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

"""AC.CI.6 — per-file size ceiling and truncation marker.

Per the locked plan-doc §4 AC.CI.6: a per-file ceiling (50_000 chars
per D-build.3) caps the inlined content per file. Files exceeding
the ceiling have their content truncated at the ceiling boundary
and a structured ``[truncated at N chars; full file at <path>]``
marker is emitted. The hook does not refuse to emit other files
when one truncates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SCRIPT = (
    REPO_ROOT
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
    / "corpus_inline_session_start.py"
)


def _make_dev_mode_workspace(
    tmp_path: Path, *, oversized_state: bool = False
) -> Path:
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text(
        "# C — small file (under ceiling)\n", encoding="utf-8"
    )
    rebuild_dir = tmp_path / "docs"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text(
        "# V — small file\n", encoding="utf-8"
    )
    if oversized_state:
        # 60_000 chars > 50_000 ceiling.
        big = "X" * 60_000
        (rebuild_dir / "STATE.md").write_text(big, encoding="utf-8")
    else:
        (rebuild_dir / "STATE.md").write_text(
            "# S — small file\n", encoding="utf-8"
        )
    return tmp_path


def _run_hook(workspace: Path) -> tuple[str, int]:
    envelope = json.dumps(
        {
            "session_id": "sess-truncate",
            "workspace": {"project_dir": str(workspace)},
        }
    )
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout, result.returncode


def test_AC_CI_6_no_truncation_marker_for_small_files(
    tmp_path: Path,
) -> None:
    """No file exceeds the ceiling → no truncation marker emitted."""
    workspace = _make_dev_mode_workspace(tmp_path, oversized_state=False)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    assert "[truncated at" not in stdout


def test_AC_CI_6_emits_truncation_marker_when_ceiling_exceeded(
    tmp_path: Path,
) -> None:
    """STATE.md exceeds the ceiling → emits ``[truncated at 50000
    chars; full file at docs/STATE.md]`` marker; the
    truncated content is bounded by the ceiling."""
    workspace = _make_dev_mode_workspace(tmp_path, oversized_state=True)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    # The marker MUST mention the ceiling literal value AND the
    # workspace-relative path.
    expected_marker = (
        "[truncated at 50000 chars; full file at docs/STATE.md]"
    )
    assert expected_marker in stdout


def test_AC_CI_6_other_files_unaffected_by_truncation(
    tmp_path: Path,
) -> None:
    """When STATE.md truncates, CLAUDE.md and VALUE_PROPOSITION.md
    still emit their full content."""
    workspace = _make_dev_mode_workspace(tmp_path, oversized_state=True)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    # Other files untouched.
    assert "# C — small file (under ceiling)" in stdout
    assert "# V — small file" in stdout


def test_AC_CI_6_truncated_content_bounded_by_ceiling(
    tmp_path: Path,
) -> None:
    """The truncated file's emitted content must be at most the
    ceiling number of chars before the marker."""
    workspace = _make_dev_mode_workspace(tmp_path, oversized_state=True)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    # Find the STATE.md slot.
    state_idx = stdout.index("--- docs/STATE.md ---")
    state_block = stdout[state_idx:]
    # Locate the next delimiter or pointer-block boundary.
    next_delim = state_block.find("\n---", 1)
    next_block = state_block.find("\n===", 1)
    end = min(x for x in (next_delim, next_block, len(state_block)) if x > 0)
    state_segment = state_block[:end]
    # The X-content portion should not exceed 50_000 chars (the
    # marker adds some bytes after — the ceiling caps the file
    # CONTENT, not the marker text).
    x_count = state_segment.count("X")
    assert x_count <= 50_000, (
        f"Truncated content exceeded 50_000-char ceiling: "
        f"got {x_count} X's"
    )
