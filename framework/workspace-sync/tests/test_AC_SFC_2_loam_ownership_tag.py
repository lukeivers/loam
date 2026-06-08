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

"""AC.SFC.2 — loam-ownership tag (clean ownership boundary).

Every composed hook entry is identifiable as loam-owned and traceable
to its source fragment; a user/workspace-authored hook entry carries no
such tag.

Build-time empirical note: the unknown ``_loam`` sibling field on a
matcher-group was VERIFIED tolerated by Claude Code (2.1.168) — a hook
carrying it fires normally (plan §8 trigger-1 / RF-2 resolved). The
unknown-field marker is the shipped mechanism; no fallback was needed.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_sync.fragment_composer import (
    LOAM_TAG_KEY,
    compose_settings_fragments,
)

FRAGMENT = {
    "_comment": "c",
    "hooks": {
        "SubagentStart": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "${LOAM_REPO}/framework/frame-kernel/hooks/"
                            "subagent_start_context.py"
                        ),
                        "timeout": 10,
                    }
                ],
            }
        ]
    },
}


def _ws_with_user_hook(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    frag = (
        ws / "framework" / "frame-kernel" / "hooks"
        / "settings.fragment.json"
    )
    frag.parent.mkdir(parents=True)
    frag.write_text(json.dumps(FRAGMENT))
    # Seed a user-authored hook (no _loam tag).
    claude = ws / ".claude"
    claude.mkdir(parents=True)
    (claude / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "Stop": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "echo user-stop",
                                }
                            ],
                        }
                    ]
                }
            }
        )
    )
    return ws


def test_AC_SFC_2_composed_group_tagged_and_traceable(tmp_path):
    ws = _ws_with_user_hook(tmp_path)
    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads((ws / ".claude" / "settings.json").read_text())
    composed = settings["hooks"]["SubagentStart"]
    assert len(composed) == 1
    tag = composed[0][LOAM_TAG_KEY]
    # Traceable to its source fragment + component.
    assert tag["component"] == "frame-kernel"
    assert tag["source_fragment"] == (
        "frame-kernel/hooks/settings.fragment.json"
    )


def test_AC_SFC_2_user_group_not_marked_loam_owned(tmp_path):
    ws = _ws_with_user_hook(tmp_path)
    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads((ws / ".claude" / "settings.json").read_text())
    user_groups = settings["hooks"]["Stop"]
    assert len(user_groups) == 1
    assert LOAM_TAG_KEY not in user_groups[0], (
        "a user-authored group must NOT carry the loam-ownership tag"
    )
