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

"""AC.SECHK.5 — Toggle-off env vars disable hooks at declared
granularity. LOAM_SAFETY_HOOKS=off disables all three;
LOAM_SAFETY_HOOKS_{SECRET,DANGEROUS_FLAG,CONFIG_WRITE}=off disable
individually. NDJSON log records the no-op for audit.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "safety-layer" / "hooks"

SECRET_HOOK = HOOKS_DIR / "secret_pattern_guard.py"
DANGER_HOOK = HOOKS_DIR / "dangerous_flag_guard.py"
CONFIG_HOOK = HOOKS_DIR / "config_write_guard.py"


def _invoke_with_env(
    script: Path, stdin: str, env_overrides: dict[str, str]
) -> tuple[int, str]:
    env = os.environ.copy()
    env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, str(script)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    return (result.returncode, result.stdout)


def _bash_envelope(cwd: Path, command: str) -> str:
    return json.dumps(
        {
            "cwd": str(cwd),
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "hook_event_name": "PreToolUse",
        }
    )


def _write_envelope(cwd: Path, file_path: str) -> str:
    return json.dumps(
        {
            "cwd": str(cwd),
            "tool_name": "Write",
            "tool_input": {"file_path": file_path, "content": "x"},
            "hook_event_name": "PreToolUse",
        }
    )


def _log_lines(workspace_root: Path) -> list[dict]:
    log = workspace_root / ".loam" / "safety-hooks.log"
    if not log.is_file():
        return []
    return [
        json.loads(line)
        for line in log.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_AC_SECHK_5_loam_safety_hooks_off_disables_secret(tmp_path) -> None:
    code, stdout = _invoke_with_env(
        SECRET_HOOK,
        _bash_envelope(
            tmp_path,
            "echo sk-ant-aaaabbbbccccddddeeeeffffgggghhhh",
        ),
        {"LOAM_SAFETY_HOOKS": "off"},
    )
    assert code == 0
    assert stdout == ""
    logs = _log_lines(tmp_path)
    assert any(
        e.get("decision") == "toggled-off"
        and e.get("hook") == "secret_pattern_guard"
        for e in logs
    )


def test_AC_SECHK_5_per_hook_secret_off_disables_only_secret(tmp_path) -> None:
    code, stdout = _invoke_with_env(
        SECRET_HOOK,
        _bash_envelope(
            tmp_path,
            "echo sk-ant-aaaabbbbccccddddeeeeffffgggghhhh",
        ),
        {"LOAM_SAFETY_HOOKS_SECRET": "off"},
    )
    assert code == 0
    assert stdout == ""

    # Dangerous-flag hook still fires (different env var).
    code_d, stdout_d = _invoke_with_env(
        DANGER_HOOK,
        _bash_envelope(tmp_path, "git push --no-verify"),
        {"LOAM_SAFETY_HOOKS_SECRET": "off"},
    )
    assert code_d == 0
    assert stdout_d
    payload = json.loads(stdout_d)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_5_per_hook_dangerous_off_disables_only_dangerous(
    tmp_path,
) -> None:
    code, stdout = _invoke_with_env(
        DANGER_HOOK,
        _bash_envelope(tmp_path, "git push --no-verify"),
        {"LOAM_SAFETY_HOOKS_DANGEROUS_FLAG": "off"},
    )
    assert code == 0
    assert stdout == ""

    # Secret hook still fires.
    code_s, stdout_s = _invoke_with_env(
        SECRET_HOOK,
        _bash_envelope(
            tmp_path,
            "echo sk-ant-aaaabbbbccccddddeeeeffffgggghhhh",
        ),
        {"LOAM_SAFETY_HOOKS_DANGEROUS_FLAG": "off"},
    )
    assert code_s == 0
    assert stdout_s


def test_AC_SECHK_5_per_hook_config_off_disables_only_config(
    tmp_path,
) -> None:
    code, stdout = _invoke_with_env(
        CONFIG_HOOK,
        _write_envelope(tmp_path, str(tmp_path / "biome.json")),
        {"LOAM_SAFETY_HOOKS_CONFIG_WRITE": "off"},
    )
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_5_logs_toggle_off(tmp_path) -> None:
    """The NDJSON log records the toggled-off no-op."""
    _invoke_with_env(
        SECRET_HOOK,
        _bash_envelope(tmp_path, "echo hi"),
        {"LOAM_SAFETY_HOOKS_SECRET": "off"},
    )
    logs = _log_lines(tmp_path)
    assert any(
        e.get("decision") == "toggled-off" for e in logs
    ), "expected a toggled-off log line, found: {}".format(logs)
