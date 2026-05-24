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

"""AC.SECHK.S1 / S2 / S3 — outcome-altitude tests per
`feedback_test_outcome_altitude_required.md`.

Each test invokes the production hook dispatch path with NO
pre-arranged state — no fakes, no module-level patches, no stubs on
the regex engine. A real `python <hook-script>` subprocess receives
the synthetic PreToolUse envelope on stdin; the test asserts the
production deny shape lands on stdout.

These tests are the cross-cycle confidence-builders alongside the
unit tests in the sibling AC.SECHK.{1,2,3} files (which use the same
subprocess shape but as their primary test surface).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "safety-layer" / "hooks"


def _invoke(script: Path, envelope: str) -> tuple[int, str, str]:
    """Real subprocess; production hook script; no monkeypatching."""
    result = subprocess.run(
        [sys.executable, str(script)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return (result.returncode, result.stdout, result.stderr)


def test_AC_SECHK_S1_secret_pattern_outcome_altitude(tmp_path) -> None:
    """Synthetic Claude Code session: secret-pattern hook blocks a
    pasted sk-... content via the production dispatch path.

    Production entry-point: `python secret_pattern_guard.py` with
    PreToolUse envelope on stdin. No pre-arranged state.
    """
    envelope = json.dumps(
        {
            "session_id": "outcome-altitude",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "echo sk-ant-aaaabbbbccccddddeeeeffffgggghhhh"
            },
        }
    )
    code, stdout, stderr = _invoke(
        HOOKS_DIR / "secret_pattern_guard.py", envelope
    )
    assert code == 0, stderr
    assert stdout
    payload = json.loads(stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    assert "anthropic-api-key" in hso["permissionDecisionReason"]


def test_AC_SECHK_S2_dangerous_flag_outcome_altitude(tmp_path) -> None:
    """Synthetic session: dangerous-flag hook blocks `git push
    --no-verify` via the production dispatch path."""
    envelope = json.dumps(
        {
            "session_id": "outcome-altitude",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "git push --no-verify origin pos-v2"},
        }
    )
    code, stdout, stderr = _invoke(
        HOOKS_DIR / "dangerous_flag_guard.py", envelope
    )
    assert code == 0, stderr
    assert stdout
    payload = json.loads(stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "no-verify" in hso["permissionDecisionReason"]


def test_AC_SECHK_S3_config_write_outcome_altitude(tmp_path) -> None:
    """Synthetic session: config-write hook blocks an Edit to
    `.eslintrc.json` via the production dispatch path."""
    target = tmp_path / ".eslintrc.json"
    envelope = json.dumps(
        {
            "session_id": "outcome-altitude",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "a",
                "new_string": "b",
            },
        }
    )
    code, stdout, stderr = _invoke(
        HOOKS_DIR / "config_write_guard.py", envelope
    )
    assert code == 0, stderr
    assert stdout
    payload = json.loads(stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "eslintrc" in hso["permissionDecisionReason"].lower()
