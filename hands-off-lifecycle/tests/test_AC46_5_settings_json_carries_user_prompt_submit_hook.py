"""AC46.5 (part 3) — ``merge_user_prompt_submit`` writes a
UserPromptSubmit hook entry into settings.json.

Outcome: invoking ``merge_user_prompt_submit`` with the persona's
user-prompt-submit envelope writes ``hooks.UserPromptSubmit = [envelope]``
to settings.json, preserving every other top-level key.

Includes:
  - first-write path (no prior settings.json or no prior
    UserPromptSubmit stanza)
  - re-merge over a pos-v2-owned UserPromptSubmit stanza (no backup)
  - re-merge over a user-authored UserPromptSubmit stanza (backup
    written, replaced)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_user_prompt_submit  # noqa: E402


def _persona_envelope(pos_v2_root: Path) -> dict:
    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": (
                    f"{pos_v2_root}/.venv/bin/python "
                    "-m primary_persona.cli user-prompt-submit"
                ),
                "async": False,
                "timeout": 5,
            }
        ],
    }


def test_AC46_5_first_write_creates_user_prompt_submit_stanza(
    tmp_path: Path,
) -> None:
    """No prior settings.json → write produces a settings.json with
    hooks.UserPromptSubmit set to [envelope]."""
    settings_path = tmp_path / "settings.json"
    result = merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    assert result.wrote is True
    data = json.loads(settings_path.read_text())
    assert "hooks" in data
    assert "UserPromptSubmit" in data["hooks"]
    assert len(data["hooks"]["UserPromptSubmit"]) == 1
    cmd = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert "primary_persona.cli user-prompt-submit" in cmd


def test_AC46_5_re_merge_over_pos_v2_owned_stanza_no_backup(
    tmp_path: Path,
) -> None:
    """Re-merging over a stanza we previously wrote (recognised via
    the persona-side command markers) does NOT create a backup."""
    settings_path = tmp_path / "settings.json"
    # Seed a pos-v2-owned stanza (same envelope shape).
    merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    # Re-merge.
    result = merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    assert result.wrote is True
    assert result.backup_path is None
    assert result.prior_session_start_displaced is False


def test_AC46_5_re_merge_over_user_authored_stanza_creates_backup(
    tmp_path: Path,
) -> None:
    """Re-merging over a user-authored UserPromptSubmit stanza (whose
    inner-hook commands don't match pos-v2 markers) creates a backup."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/usr/local/bin/my-custom-hook",
                                    "async": False,
                                    "timeout": 30,
                                }
                            ],
                        }
                    ],
                },
                "user_key": "preserved",
            },
            indent=2,
        )
    )
    result = merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
        now_iso="20260425T000000Z",
    )
    assert result.wrote is True
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.prior_session_start_displaced is True
    # User-authored other keys preserved.
    data = json.loads(settings_path.read_text())
    assert data.get("user_key") == "preserved"
    # New stanza in place.
    cmd = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert "primary_persona.cli user-prompt-submit" in cmd


def test_AC46_5_user_prompt_submit_merge_preserves_session_start_stanza(
    tmp_path: Path,
) -> None:
    """Merging a UserPromptSubmit stanza does NOT touch a pre-existing
    SessionStart stanza."""
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
                },
            },
            indent=2,
        )
    )
    result = merge_user_prompt_submit(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    assert result.wrote is True
    data = json.loads(settings_path.read_text())
    # SessionStart preserved.
    ss_cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "first-run.sh" in ss_cmd
    # UserPromptSubmit added.
    ups_cmd = data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    assert "primary_persona.cli user-prompt-submit" in ups_cmd
