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

"""AC.M.11 (part 1) — ``merge_stop`` writes Stop hook into settings.json.

Outcome (per locked plan §5): invoking ``merge_stop`` with the
persona's stop envelope writes ``hooks.Stop = [envelope]`` to
settings.json, preserving every other top-level key.

Covers:
  - first-write path (no prior settings.json or no prior Stop stanza)
  - top-level key preservation
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


def test_AC_M_11_first_write_creates_stop_stanza(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    result = merge_stop(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    assert result.wrote is True
    data = json.loads(settings_path.read_text())
    assert "Stop" in data["hooks"]
    assert len(data["hooks"]["Stop"]) == 1
    cmd = data["hooks"]["Stop"][0]["hooks"][0]["command"]
    assert "primary_persona.cli stop" in cmd


def test_AC_M_11_merge_preserves_other_top_level_keys(
    tmp_path: Path,
) -> None:
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "agent": "eve",
                "user_key": "preserved",
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
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "x -m loam.primary_persona user-prompt-submit",
                                    "async": False,
                                    "timeout": 5,
                                }
                            ],
                        }
                    ],
                },
            },
            indent=2,
        )
    )
    merge_stop(
        settings_path=settings_path,
        new_entry=_persona_envelope(tmp_path),
    )
    data = json.loads(settings_path.read_text())
    assert data["agent"] == "eve"
    assert data["user_key"] == "preserved"
    # SessionStart preserved.
    assert "first-run.sh" in (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    )
    # UserPromptSubmit preserved.
    assert "user-prompt-submit" in (
        data["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
    )
    # Stop added.
    assert "primary_persona.cli stop" in (
        data["hooks"]["Stop"][0]["hooks"][0]["command"]
    )
