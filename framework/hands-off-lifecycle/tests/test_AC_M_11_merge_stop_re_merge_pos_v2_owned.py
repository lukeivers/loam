"""AC.M.11 (part 2) — re-merge over a pos-v2-owned Stop stanza.

Outcome (per locked plan §5): re-running ``merge_stop`` over a
settings.json whose existing ``hooks.Stop`` is pos-v2-owned (matches
the persona's command markers) replaces it without backup.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import merge_stop  # noqa: E402


def _persona_envelope(pos_v2_root: Path) -> dict:
    return {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": (
                    f"{pos_v2_root}/.venv/bin/python "
                    "-m primary_persona.cli stop"
                ),
                "async": False,
                "timeout": 5,
            }
        ],
    }


def test_AC_M_11_re_merge_over_pos_v2_owned_no_backup(
    tmp_path: Path,
) -> None:
    settings_path = tmp_path / "settings.json"
    # Seed with pos-v2-owned Stop stanza.
    merge_stop(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    result = merge_stop(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    assert result.wrote is True
    assert result.backup_path is None
    assert result.prior_session_start_displaced is False
    # Stanza still in place.
    data = json.loads(settings_path.read_text())
    assert "primary_persona.cli stop" in (
        data["hooks"]["Stop"][0]["hooks"][0]["command"]
    )
