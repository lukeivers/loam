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

"""OUTCOME-ALTITUDE — the real secure-build PreToolUse hook entry-point.

Invoking the real hook as a SEPARATE PROCESS over a real stdin pipe
against a real on-disk git repository, with NO pre-arranged fixture/state
beyond the files on disk and no internal function stubbed:

* a ``git add -A`` in a project that has a ``.env`` (and no ``.gitignore``)
  returns a deny naming the offending path in non-technical vocabulary
  (AC.SBB.3 enforced end-to-end through the production entry-point); and
* the same broad-stage command in a project whose floor ``.gitignore`` is
  in place returns NO deny (the property the sweep guards).

``outcome-altitude: true``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Import the floor .gitignore content from the production module so the
# "clean" arm exercises the same template the guarantee ships.
from loam.secure_build_baseline.gitignore_template import render_gitignore


HOOK = (
    Path(__file__).resolve().parent.parent
    / "hooks"
    / "secure_build_baseline_guard.py"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")


def _run_hook(cwd: Path, command: str) -> tuple[int, str]:
    envelope = {
        "session_id": "sbb-oa",
        "cwd": str(cwd),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(envelope),
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def test_real_entrypoint_denies_broad_stage_of_unignored_secret(tmp_path: Path) -> None:
    """No pre-arranged state: a real ``git add -A`` in a project with an
    unignored ``.env`` returns a deny naming the path in plain words."""
    repo = tmp_path / "artifact"
    _init_repo(repo)
    (repo / ".env").write_text("API_TOKEN=shhh\n", encoding="utf-8")
    (repo / "main.py").write_text("print('x')\n", encoding="utf-8")

    rc, out = _run_hook(repo, "git add -A")
    assert rc == 0
    assert out.strip(), "the hook must emit a deny payload on stdout"
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    reason = hso["permissionDecisionReason"]
    assert "AC.SBB.3" in reason
    assert ".env" in reason
    # Plain words, not internal jargon.
    assert "shipped artifact" in reason


def test_real_entrypoint_allows_broad_stage_with_floor_gitignore(tmp_path: Path) -> None:
    """The same broad-stage command in a project carrying the floor
    ``.gitignore`` returns NO deny — git ignores the runtime state, so the
    sweep finds nothing offending."""
    repo = tmp_path / "clean-artifact"
    _init_repo(repo)
    (repo / ".gitignore").write_text(render_gitignore(), encoding="utf-8")
    (repo / ".env").write_text("API_TOKEN=shhh\n", encoding="utf-8")
    (repo / "main.py").write_text("print('x')\n", encoding="utf-8")

    rc, out = _run_hook(repo, "git add -A")
    assert rc == 0
    assert out.strip() == "", "a clean artifact must produce no deny payload"


def test_real_entrypoint_failsoft_in_non_repo_directory(tmp_path: Path) -> None:
    """A broad-stage command in a directory that is not a git repo must NOT
    block — the floor fails soft on its own read fault rather than walling
    off the build."""
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / ".env").write_text("X=1\n", encoding="utf-8")
    rc, out = _run_hook(plain, "git add -A")
    assert rc == 0
    assert out.strip() == "", "a non-repo read fault must fail soft (no deny)"
