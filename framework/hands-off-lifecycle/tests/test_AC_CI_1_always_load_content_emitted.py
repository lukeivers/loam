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

"""AC.CI.1 — always-load corpus content reaches additionalContext (DEV MODE).

Per the locked plan-doc §4 AC.CI.1: on a SessionStart fan-out in a
DEV MODE workspace, the new hook emits to stdout an additionalContext-
shaped payload that contains the literal byte content of every
always-load corpus file. Per-file delimiters disambiguate one file
from another. Files absent from disk are emitted with a structured
``[missing]`` marker; their content is omitted.
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


def _make_dev_mode_workspace(tmp_path: Path) -> Path:
    """Set up a DEV-MODE workspace with the always-load tier present.

    Per A1's `workspace_mode` contract, the dev_intent answer lives at
    `<workspace>/workspace/personas/<handle>/contract.yaml` (post-D.2,
    amendment #63). Build the minimum shape that loam-mode's
    `read_dev_intent_safe` recognises.
    """
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    (tmp_path / "CLAUDE.md").write_text(
        "# Workspace CLAUDE\n\nClaude is the model.\n",
        encoding="utf-8",
    )
    rebuild_dir = tmp_path / "docs"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text(
        "# VALUE_PROPOSITION\n\nPrime objective text here.\n",
        encoding="utf-8",
    )
    (rebuild_dir / "STATE.md").write_text(
        "# STATE\n\nCurrent cycle status.\n",
        encoding="utf-8",
    )
    return tmp_path


def _run_hook(workspace: Path, session_id: str = "sess-1") -> tuple[str, int]:
    envelope = json.dumps(
        {
            "session_id": session_id,
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


def test_AC_CI_1_emits_always_load_content_in_dev_mode(
    tmp_path: Path,
) -> None:
    """DEV MODE workspace; all always-load files present → stdout
    contains every file's content under per-file delimiters."""
    workspace = _make_dev_mode_workspace(tmp_path)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    assert "=== pos-v2 always-loaded corpus (DEV MODE) ===" in stdout
    # Per-file delimiters
    assert "--- CLAUDE.md ---" in stdout
    assert "--- docs/VALUE_PROPOSITION.md ---" in stdout
    assert "--- docs/STATE.md ---" in stdout
    # File contents present (literal bytes from the workspace files).
    assert "Claude is the model." in stdout
    assert "Prime objective text here." in stdout
    assert "Current cycle status." in stdout


def test_AC_CI_1_emits_missing_marker_for_absent_files(
    tmp_path: Path,
) -> None:
    """DEV MODE workspace; STATE.md absent → stdout contains
    ``[missing]`` marker for that slot; other files emitted as
    content."""
    workspace = _make_dev_mode_workspace(tmp_path)
    # Remove STATE.md to force the missing path.
    (workspace / "docs" / "STATE.md").unlink()
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    # Content of the present files is still emitted.
    assert "Claude is the model." in stdout
    assert "Prime objective text here." in stdout
    # Missing-file marker present in the STATE.md slot.
    # The marker must follow the STATE.md delimiter.
    state_idx = stdout.index("--- docs/STATE.md ---")
    rest = stdout[state_idx:]
    # The first non-blank section after the STATE.md delimiter is
    # the [missing] slot.
    assert "[missing]" in rest


def test_AC_CI_1_per_file_delimiters_disambiguate_files(
    tmp_path: Path,
) -> None:
    """Files are disambiguatable from one another in the emitted
    text via the ``--- <path> ---`` delimiter shape."""
    workspace = _make_dev_mode_workspace(tmp_path)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    delimiters = [
        line for line in stdout.splitlines()
        if line.startswith("--- ") and line.endswith(" ---")
    ]
    # All three always-load files emit their delimiter.
    rels = {
        line.removeprefix("--- ").removesuffix(" ---")
        for line in delimiters
    }
    assert "CLAUDE.md" in rels
    assert "docs/VALUE_PROPOSITION.md" in rels
    assert "docs/STATE.md" in rels
