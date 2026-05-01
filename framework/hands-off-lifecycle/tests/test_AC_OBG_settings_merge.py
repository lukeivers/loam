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

"""``merge_pre_tool_use`` writes a PreToolUse hook entry into
settings.json — settings-merge contract for the structural-
enforcement A2 amendment.

Mirrors the AC46.5 ``test_AC46_5_settings_json_carries_user_prompt_
submit_hook.py`` pattern byte-for-byte: first-write, re-merge over
pos-v2-owned, re-merge over user-authored (backup created),
preservation of orthogonal stanzas (SessionStart, UserPromptSubmit,
Stop, statusLine).

This is the empirical answer to the dispatch's Q3 (existing user-
authored PreToolUse hook preservation): a workspace whose
settings.json carries a user-authored PreToolUse hook is preserved
via the timestamped backup convention; the new entry replaces the
prior stanza but the prior stanza is recoverable byte-equal from the
backup.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_pre_tool_use  # noqa: E402


def _gate_envelope(loam_root: Path) -> dict:
    script = (
        loam_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "objective_binding_gate.py"
    )
    return {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
            {
                "type": "command",
                "command": f"{sys.executable} {script}",
                "async": False,
                "timeout": 5,
            }
        ],
    }


def test_first_write_creates_pre_tool_use_stanza(tmp_path: Path) -> None:
    """No prior settings.json → write produces a settings.json with
    hooks.PreToolUse set to [envelope]."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_gate_envelope(tmp_path),
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    assert "hooks" in data
    assert "PreToolUse" in data["hooks"]
    assert len(data["hooks"]["PreToolUse"]) == 1
    cmd = data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "objective_binding_gate.py" in cmd
    assert data["hooks"]["PreToolUse"][0]["matcher"] == "Edit|Write|MultiEdit"


def test_re_merge_over_pos_v2_owned_no_backup(tmp_path: Path) -> None:
    """Re-merge over a pos-v2-owned PreToolUse stanza (gate command
    marker present) does NOT create a backup."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_gate_envelope(tmp_path),
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_gate_envelope(tmp_path),
    )
    assert result.wrote is True
    assert result.backup_path is None
    assert result.prior_session_start_displaced is False


def test_re_merge_over_user_authored_creates_backup(
    tmp_path: Path,
) -> None:
    """Re-merge over a user-authored PreToolUse stanza (whose inner-
    hook commands don't match pos-v2 markers) creates a timestamped
    backup AND preserves the prior stanza inside the backup. Q3
    empirical answer: existing user PreToolUse hooks are preserved."""
    settings_path = tmp_path / "settings.json"
    user_authored_payload = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "/usr/local/bin/my-bash-guard",
                            "async": False,
                            "timeout": 30,
                        }
                    ],
                }
            ],
        },
        "user_key": "preserved",
    }
    settings_path.write_text(
        json.dumps(user_authored_payload, indent=2)
    )

    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_gate_envelope(tmp_path),
        now_iso="20260428T120000Z",
    )
    assert result.wrote is True
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.prior_session_start_displaced is True

    # The backup carries the user's prior stanza byte-equal.
    backup_data = json.loads(result.backup_path.read_text())
    assert (
        backup_data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        == "/usr/local/bin/my-bash-guard"
    )

    # User-authored other top-level keys are preserved on the live
    # settings.json (only the PreToolUse stanza is replaced).
    data = json.loads(settings_path.read_text())
    assert data.get("user_key") == "preserved"
    cmd = data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert "objective_binding_gate.py" in cmd


def test_pre_tool_use_merge_preserves_orthogonal_stanzas(
    tmp_path: Path,
) -> None:
    """Merging a PreToolUse stanza does NOT touch a pre-existing
    SessionStart / UserPromptSubmit / Stop / statusLine entry."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/path/to/first-run.sh",
                                    "async": False,
                                    "timeout": 60,
                                }
                            ],
                        }
                    ],
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "X -m loam.primary_persona Y",
                                    "async": False,
                                    "timeout": 5,
                                }
                            ],
                        }
                    ],
                },
                "statusLine": {
                    "type": "command",
                    "command": "X hands-off-lifecycle/hooks/statusline.py",
                    "refreshInterval": 1,
                },
            },
            indent=2,
        )
    )

    merge_pre_tool_use(
        settings_path=settings_path,
        new_entry=_gate_envelope(tmp_path),
    )

    data = json.loads(settings_path.read_text())
    # SessionStart preserved.
    assert (
        "first-run.sh"
        in data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    )
    # UserPromptSubmit preserved.
    assert (
        "primary_persona"
        in data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    )
    # statusLine preserved.
    assert "statusline.py" in data["statusLine"]["command"]
    # PreToolUse newly written.
    assert (
        "objective_binding_gate.py"
        in data["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    )
