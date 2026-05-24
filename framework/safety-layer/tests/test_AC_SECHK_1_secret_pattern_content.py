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

"""AC.SECHK.1 — secret-pattern guard fires on Bash command args +
Edit/Write/MultiEdit content; blocks the 14-pattern floor; emits
structured permissionDecisionReason.

Direct module-level tests against the hook's classification helpers
+ a small subprocess-driven envelope test for the deny shape.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "safety-layer" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


HOOK_SCRIPT = HOOKS_DIR / "secret_pattern_guard.py"


def _envelope(
    *,
    tool_name: str,
    tool_input: dict,
    cwd: Path,
) -> str:
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


def _invoke_hook(envelope: str) -> tuple[int, str, str]:
    """Invoke the hook script as a subprocess. Returns
    (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return (result.returncode, result.stdout, result.stderr)


# ---------------------------------------------------------------------
# CONTENT pattern matches — module-level helper coverage
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "literal,expected_pattern",
    [
        ("sk-ant-abcdefghijklmnopqrstuvwxyz", "anthropic-api-key"),
        (
            "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890",
            "openai-project-key",
        ),
        (
            "ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "github-pat",
        ),
        ("AKIAIOSFODNN7EXAMPLE", "aws-access-key"),
        ("AIzaSyBVS5test_key_for_test_use_xxxxxxx", "google-api-key"),
        (
            "xoxb-1234567890-1234567890-abcdef",
            "slack-token",
        ),
        (
            "sk_live_abcdefghijklmnopqrstuvwxyz",
            "stripe-live-secret",
        ),
        (
            "-----BEGIN PRIVATE KEY-----",
            "private-key-pem",
        ),
    ],
)
def test_AC_SECHK_1_content_pattern_match_bash_command(
    tmp_path, literal: str, expected_pattern: str
) -> None:
    """Each 14-pattern-floor literal fires deny when embedded in a
    Bash command argument."""
    envelope = _envelope(
        tool_name="Bash",
        tool_input={"command": f"echo '{literal}' > /tmp/leak"},
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    assert stdout, f"no deny emitted for {expected_pattern}"
    payload = json.loads(stdout)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert expected_pattern in hso["permissionDecisionReason"]


def test_AC_SECHK_1_content_pattern_match_edit_tool(tmp_path) -> None:
    """Edit tool's new_string carrying a secret-content literal
    fires deny."""
    envelope = _envelope(
        tool_name="Edit",
        tool_input={
            "file_path": str(tmp_path / "any.py"),
            "old_string": "old",
            "new_string": "key = 'sk-ant-XXXXXXXXXXXXXXXXXXXXXX'",
        },
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_1_content_pattern_write_tool(tmp_path) -> None:
    """Write tool's content carrying a secret literal fires deny."""
    envelope = _envelope(
        tool_name="Write",
        tool_input={
            "file_path": str(tmp_path / "any.py"),
            "content": "API_KEY = 'ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'",
        },
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_1_content_pattern_multiedit(tmp_path) -> None:
    """MultiEdit's edits[*].new_string carrying secret fires deny."""
    envelope = _envelope(
        tool_name="MultiEdit",
        tool_input={
            "file_path": str(tmp_path / "any.py"),
            "edits": [
                {"old_string": "a", "new_string": "b"},
                {
                    "old_string": "c",
                    "new_string": "token = 'sk_live_abcdef1234567890abcdef12'",
                },
            ],
        },
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    assert stdout
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_AC_SECHK_1_random_string_passes(tmp_path) -> None:
    """English prose / random non-credential strings pass through."""
    envelope = _envelope(
        tool_name="Bash",
        tool_input={"command": "echo 'hello world, this is a test'"},
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_1_reason_redacts_token(tmp_path) -> None:
    """The permissionDecisionReason includes a redacted view of the
    matched token (not the full literal — avoid logging the secret
    in the diagnostic itself)."""
    full_token = "sk-ant-aaaabbbbccccddddeeeeffffgggghhhh"
    envelope = _envelope(
        tool_name="Bash",
        tool_input={"command": f"echo '{full_token}'"},
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    payload = json.loads(stdout)
    reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
    # Full literal should NOT appear verbatim in the diagnostic.
    assert full_token not in reason
    # Redacted form should include some recognizable prefix.
    assert "sk-ant" in reason or "..." in reason


def test_AC_SECHK_1_workspace_additions_extend_floor(tmp_path) -> None:
    """A workspace-additions entry adds a new pattern alongside the
    floor; the additive pattern fires deny."""
    additions_dir = tmp_path / ".loam"
    additions_dir.mkdir(parents=True, exist_ok=True)
    (additions_dir / "secret-patterns.yaml").write_text(
        "patterns:\n"
        '  - name: workspace-token\n'
        '    regex: "INTERNAL-[A-Z0-9]{12}"\n',
        encoding="utf-8",
    )
    envelope = _envelope(
        tool_name="Bash",
        tool_input={"command": "echo INTERNAL-AAAABBBBCCCC"},
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    payload = json.loads(stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "workspace-token" in (
        payload["hookSpecificOutput"]["permissionDecisionReason"]
    )


def test_AC_SECHK_1_non_content_tool_passes(tmp_path) -> None:
    """Tools not in {Bash, Edit, Write, MultiEdit} → no-op."""
    envelope = _envelope(
        tool_name="Read",
        tool_input={"file_path": "/tmp/x"},
        cwd=tmp_path,
    )
    code, stdout, _ = _invoke_hook(envelope)
    assert code == 0
    assert stdout == ""
