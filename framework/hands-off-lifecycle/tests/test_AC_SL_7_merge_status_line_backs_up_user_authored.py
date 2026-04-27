"""AC.SL.7 — ``merge_status_line`` backs up user-authored statusLine.

Outcome (per locked plan §4): a workspace whose ``.claude/settings.json``
already carries a user-authored ``statusLine`` entry has that entry
preserved by writing the entire prior settings.json to a timestamped
backup before the merge replaces it; the new pos-v2 entry is in place
after the merge.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_status_line  # noqa: E402


def _pos_v2_envelope(pos_v2_root: Path) -> dict:
    return {
        "type": "command",
        "command": (
            f"{pos_v2_root}/.venv/bin/python "
            f"{pos_v2_root}/hands-off-lifecycle/hooks/statusline.py"
        ),
        "refreshInterval": 1,
    }


def test_AC_SL_7_first_write_no_backup(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    result = merge_status_line(
        settings_path=settings_path,
        new_entry=_pos_v2_envelope(tmp_path),
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    assert "hands-off-lifecycle/hooks/statusline.py" in (
        data["statusLine"]["command"]
    )


def test_AC_SL_7_user_authored_status_line_is_backed_up(
    tmp_path: Path,
) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "user_key": "preserved",
                "statusLine": {
                    "type": "command",
                    "command": "/usr/local/bin/my-statusline.sh",
                    "refreshInterval": 5,
                },
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/path/first-run.sh",
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

    result = merge_status_line(
        settings_path=settings_path,
        new_entry=_pos_v2_envelope(tmp_path),
        now_iso="20260426T120000Z",
    )

    # Backup was written.
    assert result.backup_path is not None, (
        "user-authored statusLine should trigger a backup"
    )
    assert result.prior_session_start_displaced is True
    assert result.backup_path.exists()
    backup = json.loads(result.backup_path.read_text())
    assert backup["statusLine"]["command"] == "/usr/local/bin/my-statusline.sh"
    assert backup["user_key"] == "preserved"
    assert "first-run.sh" in (
        backup["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    )

    # Settings now carry the pos-v2 statusLine and preserve the rest.
    data = json.loads(settings_path.read_text())
    assert "hands-off-lifecycle/hooks/statusline.py" in (
        data["statusLine"]["command"]
    )
    assert data["user_key"] == "preserved"
    assert "first-run.sh" in (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    )


def test_AC_SL_7_pos_v2_owned_status_line_re_merge_no_backup(
    tmp_path: Path,
) -> None:
    """Re-merging over a stanza we already wrote MUST NOT back up."""
    settings_path = tmp_path / "settings.json"
    # Prior write: pos-v2's own marker.
    merge_status_line(
        settings_path=settings_path,
        new_entry=_pos_v2_envelope(tmp_path),
    )

    # Re-merge — should be idempotent without a backup.
    result = merge_status_line(
        settings_path=settings_path,
        new_entry=_pos_v2_envelope(tmp_path),
    )
    assert result.backup_path is None
    assert result.prior_session_start_displaced is False
