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

"""AC.SECHK.2 — dangerous-flag guard blocks git push --no-verify,
git commit --no-verify, git push --force on protected branches.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "safety-layer" / "hooks"
HOOK_SCRIPT = HOOKS_DIR / "dangerous_flag_guard.py"


def _envelope(*, cwd: Path, command: str) -> str:
    return json.dumps(
        {
            "session_id": "test-session",
            "cwd": str(cwd),
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        },
        ensure_ascii=False,
    )


def _invoke(envelope: str) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return (result.returncode, result.stdout)


def test_AC_SECHK_2_git_push_no_verify_denied(tmp_path) -> None:
    code, stdout = _invoke(_envelope(cwd=tmp_path, command="git push --no-verify"))
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "git push --no-verify" in hso["permissionDecisionReason"]


def test_AC_SECHK_2_git_commit_no_verify_denied(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(cwd=tmp_path, command="git commit --no-verify -m 'fix'")
    )
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_2_git_push_force_protected_main_denied(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(cwd=tmp_path, command="git push --force origin main")
    )
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "main" in hso["permissionDecisionReason"]


def test_AC_SECHK_2_git_push_force_protected_pos_v2_denied(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(cwd=tmp_path, command="git push --force origin pos-v2")
    )
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_2_git_push_force_with_lease_protected_denied(
    tmp_path,
) -> None:
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path, command="git push --force-with-lease origin master"
        )
    )
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_2_git_push_force_unprotected_branch_passes(
    tmp_path,
) -> None:
    """git push --force origin feature-branch → pass (unprotected)."""
    code, stdout = _invoke(
        _envelope(cwd=tmp_path, command="git push --force origin feature-x")
    )
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_2_git_push_no_flag_passes(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(cwd=tmp_path, command="git push origin main")
    )
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_2_non_git_command_passes(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(cwd=tmp_path, command="ls -la")
    )
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_2_workspace_protected_addition(tmp_path) -> None:
    """A workspace-local protected-branches.yaml extends the floor."""
    additions_dir = tmp_path / ".loam"
    additions_dir.mkdir(parents=True, exist_ok=True)
    (additions_dir / "protected-branches.yaml").write_text(
        "branches:\n  - release-train\n",
        encoding="utf-8",
    )
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path, command="git push --force origin release-train"
        )
    )
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "release-train" in payload["hookSpecificOutput"][
        "permissionDecisionReason"
    ]
