"""AC.M.11 (part 3) — re-merge over a user-authored Stop stanza.

Outcome (per locked plan §5): when ``hooks.Stop`` is already populated
with a user-authored entry whose inner-hook commands don't match the
persona's command markers, ``merge_stop`` writes a timestamped backup
of the prior settings.json before replacing the stanza.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_stop  # noqa: E402


def _persona_envelope(loam_root: Path) -> dict:
    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": (
                    f"{loam_root}/.venv/bin/python "
                    "-m loam.primary_persona.cli stop"
                ),
                "async": False,
                "timeout": 5,
            }
        ],
    }


def test_AC_M_11_re_merge_over_user_authored_creates_backup(
    tmp_path: Path,
) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "Stop": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/usr/local/bin/my-custom-stop",
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
    result = merge_stop(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
        now_iso="20260426T000000Z",
    )
    assert result.wrote is True
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.prior_session_start_displaced is True
    # User-authored other keys preserved.
    data = json.loads(settings_path.read_text())
    assert data["user_key"] == "preserved"
    cmd = data["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert "primary_persona.cli stop" in cmd
