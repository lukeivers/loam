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

"""AC.SFC.5 — clean removal (loam removes only loam).

When a previously-composed component's fragment is gone from the synced
tree, its loam-owned entry is removed on the next compose; a co-present
user entry and any still-shipping loam entry remain.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_sync.fragment_composer import (
    LOAM_TAG_KEY,
    compose_settings_fragments,
)


def _frag(component: str, event: str, script: str) -> dict:
    return {
        "_comment": "c",
        "hooks": {
            event: [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                f"${{LOAM_REPO}}/framework/{component}/"
                                f"hooks/{script}"
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


def test_AC_SFC_5_vanished_fragment_entry_removed(tmp_path):
    ws = tmp_path / "ws"
    fw = ws / "framework"
    # Two fragment-shipping components: A and B.
    frag_a = fw / "comp-a" / "hooks" / "settings.fragment.json"
    frag_a.parent.mkdir(parents=True)
    frag_a.write_text(
        json.dumps(_frag("comp-a", "SubagentStart", "a.py"))
    )
    frag_b = fw / "comp-b" / "hooks" / "settings.fragment.json"
    frag_b.parent.mkdir(parents=True)
    frag_b.write_text(
        json.dumps(_frag("comp-b", "SubagentStop", "b.py"))
    )
    # Seed a user hook.
    claude = ws / ".claude"
    claude.mkdir(parents=True)
    (claude / "settings.json").write_text(
        json.dumps({"hooks": {"Stop": [USER_STOP_GROUP]}})
    )

    # First compose: both A + B present.
    compose_settings_fragments(ws, emit_summary=False)
    settings = json.loads((claude / "settings.json").read_text())
    assert "SubagentStart" in settings["hooks"]
    assert "SubagentStop" in settings["hooks"]

    # A's fragment vanishes from the synced tree.
    frag_a.unlink()

    # Second compose: A's loam entry removed; B + user entry remain.
    plan = compose_settings_fragments(ws, emit_summary=False)
    assert any(
        sf == "comp-a/hooks/settings.fragment.json"
        for _, sf in plan.removed
    ), "the vanished fragment's loam entry must be in the removal plan"

    settings = json.loads((claude / "settings.json").read_text())
    # A's loam event is gone.
    assert "SubagentStart" not in settings["hooks"]
    # B's loam entry still present + tagged.
    assert "SubagentStop" in settings["hooks"]
    assert LOAM_TAG_KEY in settings["hooks"]["SubagentStop"][0]
    # The user entry is never removed.
    assert settings["hooks"]["Stop"] == [USER_STOP_GROUP]
