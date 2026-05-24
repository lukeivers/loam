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

"""AC.SECHK.3 — config-write guard blocks Edit/Write/MultiEdit
against .eslintrc / biome.json / .pre-commit-config.yaml / .git/config
+ top-level .gitignore.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "safety-layer" / "hooks"
HOOK_SCRIPT = HOOKS_DIR / "config_write_guard.py"


def _envelope(
    *,
    cwd: Path,
    tool_name: str,
    file_path: str,
    extra_input: dict | None = None,
) -> str:
    tool_input: dict = {"file_path": file_path}
    if extra_input:
        tool_input.update(extra_input)
    return json.dumps(
        {
            "session_id": "test-session",
            "cwd": str(cwd),
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": tool_input,
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


@pytest.mark.parametrize(
    "name",
    [
        ".eslintrc",
        ".eslintrc.json",
        ".eslintrc.js",
        ".eslintrc.yaml",
        ".eslintrc.cjs",
    ],
)
def test_AC_SECHK_3_eslintrc_variants_denied(tmp_path, name: str) -> None:
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path,
            tool_name="Write",
            file_path=str(tmp_path / name),
            extra_input={"content": "{}"},
        )
    )
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "eslintrc" in payload["hookSpecificOutput"][
        "permissionDecisionReason"
    ].lower()


def test_AC_SECHK_3_biome_json_denied(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path,
            tool_name="Write",
            file_path=str(tmp_path / "biome.json"),
            extra_input={"content": "{}"},
        )
    )
    assert code == 0
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_3_pre_commit_config_denied(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path,
            tool_name="Edit",
            file_path=str(tmp_path / ".pre-commit-config.yaml"),
            extra_input={"old_string": "a", "new_string": "b"},
        )
    )
    assert code == 0
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_3_git_config_denied(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path,
            tool_name="Edit",
            file_path=str(tmp_path / ".git" / "config"),
            extra_input={"old_string": "a", "new_string": "b"},
        )
    )
    assert code == 0
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_3_root_gitignore_denied(tmp_path) -> None:
    """Top-level .gitignore fires; the file path matches workspace
    root."""
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path,
            tool_name="Write",
            file_path=str(tmp_path / ".gitignore"),
            extra_input={"content": "node_modules\n"},
        )
    )
    assert code == 0
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_3_subdir_gitignore_passes(tmp_path) -> None:
    """A .gitignore in a subdirectory passes — subdir gitignores are
    typically intentional."""
    subdir = tmp_path / "src"
    subdir.mkdir()
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path,
            tool_name="Write",
            file_path=str(subdir / ".gitignore"),
            extra_input={"content": "*.pyc\n"},
        )
    )
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_3_normal_file_passes(tmp_path) -> None:
    code, stdout = _invoke(
        _envelope(
            cwd=tmp_path,
            tool_name="Write",
            file_path=str(tmp_path / "normal.py"),
            extra_input={"content": "print(1)"},
        )
    )
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_3_bash_command_no_op(tmp_path) -> None:
    """Bash tool input is NOT in CONTENT_TOOLS for this hook."""
    envelope = json.dumps(
        {
            "session_id": "test-session",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "vim .eslintrc.json"},
        }
    )
    code, stdout = _invoke(envelope)
    assert code == 0
    assert stdout == ""
