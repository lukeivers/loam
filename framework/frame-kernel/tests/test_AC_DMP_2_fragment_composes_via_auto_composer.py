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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.DMP.2 — the frame-kernel hooks fragment composes into a
workspace's ``.claude/settings.json`` through the sealed workspace-sync
auto-composer with no hand-editing, idempotently, preserving non-loam
entries — demonstrated against a fixture workspace. Live pos3
activation is dispatcher-timed (D3), not a build step.

Memory recall cycle, Slice 4.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from loam.workspace_sync.fragment_composer import (
    compose_settings_fragments,
)

# The REAL staged fragment — the artefact under test (no fixture copy
# drift: what composes here is byte-what ships).
_FRAGMENT = (
    Path(__file__).resolve().parents[1] / "hooks" / "settings.fragment.json"
)


def _fixture_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    target = ws / "framework" / "frame-kernel" / "hooks"
    target.mkdir(parents=True)
    shutil.copy(_FRAGMENT, target / "settings.fragment.json")
    # A pre-existing user settings.json with a NON-loam hook entry +
    # a non-hooks key — both must survive byte-untouched.
    claude_dir = ws / ".claude"
    claude_dir.mkdir(parents=True)
    (claude_dir / "settings.json").write_text(
        json.dumps(
            {
                "model": "sonnet",
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/usr/bin/true",
                                }
                            ],
                        }
                    ]
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ws


def test_AC_DMP_2_fragment_composes_idempotently_preserving_user_entries(
    tmp_path: Path,
) -> None:
    ws = _fixture_workspace(tmp_path)
    settings_path = ws / ".claude" / "settings.json"

    plan = compose_settings_fragments(ws, emit_summary=False)
    assert plan.added, "first compose must add the frame-kernel groups"

    composed = json.loads(settings_path.read_text(encoding="utf-8"))
    # Both frame-kernel hooks registered, ${LOAM_REPO} resolved away.
    text = settings_path.read_text(encoding="utf-8")
    assert "subagent_start_context.py" in text
    assert "subagent_stop_frame_check.py" in text
    assert "${LOAM_REPO}" not in text
    assert "SubagentStart" in composed["hooks"]
    assert "SubagentStop" in composed["hooks"]
    # Non-loam entries preserved.
    assert composed["model"] == "sonnet"
    assert composed["hooks"]["SessionStart"][0]["hooks"][0]["command"] == (
        "/usr/bin/true"
    )

    # Idempotent: a second compose changes nothing.
    before = settings_path.read_text(encoding="utf-8")
    plan2 = compose_settings_fragments(ws, emit_summary=False)
    assert not plan2.added, "second compose must add nothing"
    assert settings_path.read_text(encoding="utf-8") == before
