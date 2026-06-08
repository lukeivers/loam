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

"""AC.SFC.3 — non-clobber (the safety keystone).

Composing never modifies/removes the user's/workspace's own hook
entries and never alters any non-``hooks`` settings key. Mirrors the
live settings shape (a ``statusLine`` key + a user ``Stop`` hook).
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_sync.fragment_composer import compose_settings_fragments

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

USER_STOP_GROUP = {
    "matcher": "",
    "hooks": [{"type": "command", "command": "echo user-stop-hook"}],
}

# A non-hooks key the user owns (mirrors live: statusLine).
STATUSLINE = {"type": "command", "command": "echo my-status"}


def _ws(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    frag = (
        ws / "framework" / "frame-kernel" / "hooks"
        / "settings.fragment.json"
    )
    frag.parent.mkdir(parents=True)
    frag.write_text(json.dumps(FRAGMENT))
    claude = ws / ".claude"
    claude.mkdir(parents=True)
    (claude / "settings.json").write_text(
        json.dumps(
            {
                "statusLine": STATUSLINE,
                "hooks": {"Stop": [USER_STOP_GROUP]},
            },
            indent=2,
        )
        + "\n"
    )
    return ws


def test_AC_SFC_3_user_stop_hook_survives_unchanged(tmp_path):
    ws = _ws(tmp_path)
    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads((ws / ".claude" / "settings.json").read_text())
    assert settings["hooks"]["Stop"] == [USER_STOP_GROUP], (
        "the user Stop group must be byte-equivalent + still present"
    )


def test_AC_SFC_3_non_hooks_key_byte_identical(tmp_path):
    ws = _ws(tmp_path)
    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads((ws / ".claude" / "settings.json").read_text())
    assert settings["statusLine"] == STATUSLINE, (
        "a non-hooks key must be copied through verbatim"
    )


def test_AC_SFC_3_only_loam_groups_added(tmp_path):
    ws = _ws(tmp_path)
    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads((ws / ".claude" / "settings.json").read_text())
    # Stop still has exactly the user group; SubagentStart is the only
    # newly-added event.
    assert settings["hooks"]["Stop"] == [USER_STOP_GROUP]
    assert "SubagentStart" in settings["hooks"]
    assert set(settings["hooks"].keys()) == {"Stop", "SubagentStart"}
