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

"""AC.SFC.4 — idempotency.

Re-running the composer (a second sync) with an unchanged fragment set
produces no duplicate entries and no change to the file's loam-owned
set; user entries remain untouched.
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
    "hooks": [{"type": "command", "command": "echo user"}],
}


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
        json.dumps({"hooks": {"Stop": [USER_STOP_GROUP]}})
    )
    return ws


def test_AC_SFC_4_second_compose_adds_no_duplicate(tmp_path):
    ws = _ws(tmp_path)

    plan1 = compose_settings_fragments(ws, emit_summary=False)
    assert len(plan1.added) == 1

    after_first = (ws / ".claude" / "settings.json").read_text()

    plan2 = compose_settings_fragments(ws, emit_summary=False)
    assert plan2.added == [], "second compose must add nothing"
    assert plan2.refreshed == []
    assert plan2.removed == []
    assert plan2.is_noop()

    after_second = (ws / ".claude" / "settings.json").read_text()
    # Idempotent: a no-op compose does not rewrite the file content.
    assert after_first == after_second

    settings = json.loads(after_second)
    # Exactly one composed SubagentStart group; user Stop untouched.
    assert len(settings["hooks"]["SubagentStart"]) == 1
    assert settings["hooks"]["Stop"] == [USER_STOP_GROUP]
