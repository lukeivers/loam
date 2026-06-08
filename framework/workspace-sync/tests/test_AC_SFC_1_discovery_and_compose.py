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

"""AC.SFC.1 — discovery + compose at both glob depths.

After a compose, every loam component that ships a
``settings.fragment.json`` under its ``hooks/`` tree has its hook
entries present in ``<workspace>/.claude/settings.json``; a component
that ships no fragment contributes nothing. Discovery catches fragments
at BOTH ``hooks/`` (frame-kernel-shaped) and ``hooks/<subdir>/``
(keep_pace-shaped) depths.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_sync.fragment_composer import (
    LOAM_TAG_KEY,
    compose_settings_fragments,
    discover_fragments,
)

FRAME_KERNEL_FRAGMENT = {
    "_comment": "frame-kernel fragment",
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
        ],
        "SubagentStop": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "${LOAM_REPO}/.venv/bin/python "
                            "${LOAM_REPO}/framework/frame-kernel/hooks/"
                            "subagent_stop_frame_check.py"
                        ),
                        "timeout": 120,
                    }
                ],
            }
        ],
    },
}

NESTED_FRAGMENT = {
    "_comment": "keep_pace-shaped deeper-nested fragment",
    "hooks": {
        "UserPromptSubmit": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "${LOAM_REPO}/framework/hands-off-lifecycle/"
                            "hooks/keep_pace/user_prompt_submit.py"
                        ),
                        "timeout": 5,
                    }
                ],
            }
        ]
    },
}


def _build_ws(tmp_path: Path) -> Path:
    """A minimal workspace: framework/ + two fragment-shipping
    components at differing depths + one component with no fragment."""
    ws = tmp_path / "ws"
    fw = ws / "framework"
    # frame-kernel: hooks/settings.fragment.json (shallow depth).
    fk = fw / "frame-kernel" / "hooks" / "settings.fragment.json"
    fk.parent.mkdir(parents=True)
    fk.write_text(json.dumps(FRAME_KERNEL_FRAGMENT))
    # hands-off-lifecycle: hooks/keep_pace/settings.fragment.json (deep).
    nested = (
        fw
        / "hands-off-lifecycle"
        / "hooks"
        / "keep_pace"
        / "settings.fragment.json"
    )
    nested.parent.mkdir(parents=True)
    nested.write_text(json.dumps(NESTED_FRAGMENT))
    # A component with NO fragment.
    nofrag = fw / "some-other-component" / "src" / "thing.py"
    nofrag.parent.mkdir(parents=True)
    nofrag.write_text("x = 1\n")
    return ws


def test_AC_SFC_1_discovery_catches_both_glob_depths(tmp_path):
    ws = _build_ws(tmp_path)
    fragments = discover_fragments(ws / "framework")
    rels = sorted(
        str(p.relative_to(ws / "framework")) for p in fragments
    )
    assert rels == [
        "frame-kernel/hooks/settings.fragment.json",
        "hands-off-lifecycle/hooks/keep_pace/settings.fragment.json",
    ], "glob must catch fragments at BOTH hooks/ and hooks/<subdir>/ depths"


def test_AC_SFC_1_compose_places_all_fragment_hook_entries(tmp_path):
    ws = _build_ws(tmp_path)
    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads(
        (ws / ".claude" / "settings.json").read_text()
    )
    hooks = settings["hooks"]
    # frame-kernel contributes SubagentStart + SubagentStop.
    assert "SubagentStart" in hooks
    assert "SubagentStop" in hooks
    # keep_pace-shaped fragment contributes UserPromptSubmit.
    assert "UserPromptSubmit" in hooks
    # Every composed group is loam-tagged.
    for event, groups in hooks.items():
        for group in groups:
            assert LOAM_TAG_KEY in group, (
                f"composed group under {event} must be loam-tagged"
            )


def test_AC_SFC_1_fragmentless_component_contributes_nothing(tmp_path):
    ws = _build_ws(tmp_path)
    compose_settings_fragments(ws, emit_summary=False)

    settings = json.loads(
        (ws / ".claude" / "settings.json").read_text()
    )
    # Only the three events the two fragments declare are present;
    # the fragment-less component added nothing.
    assert set(settings["hooks"].keys()) == {
        "SubagentStart",
        "SubagentStop",
        "UserPromptSubmit",
    }
