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

"""AC.SFC.6 — ${LOAM_REPO} resolution.

``${LOAM_REPO}`` in a fragment's commands is resolved to the synced
workspace's repo root (the dir containing ``framework/``) in the
composed settings.json — no literal placeholder survives. A composed
``${LOAM_REPO}/framework/...`` command therefore points at the synced
framework tree.
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
                            "${LOAM_REPO}/.venv/bin/python "
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


def test_AC_SFC_6_placeholder_resolved_to_workspace_root(tmp_path):
    ws = tmp_path / "ws"
    frag = (
        ws / "framework" / "frame-kernel" / "hooks"
        / "settings.fragment.json"
    )
    frag.parent.mkdir(parents=True)
    frag.write_text(json.dumps(FRAGMENT))

    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads((ws / ".claude" / "settings.json").read_text())
    command = settings["hooks"]["SubagentStart"][0]["hooks"][0]["command"]

    # No literal placeholder survives.
    assert "${LOAM_REPO}" not in command
    # Resolved to the workspace root (the dir containing framework/),
    # so the framework path lands at <ws>/framework/...
    assert str(ws) in command
    assert str(ws / "framework" / "frame-kernel") in command
