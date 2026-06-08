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

"""AC.SSFC.6 — the hook is registered for SubagentStop via the portable
settings-fragment any loam workspace can compose, with no per-workspace
hand-authoring of the registration.

The test parses ``settings.fragment.json`` and asserts it declares a
SubagentStop matcher block invoking the hook with the ``${LOAM_REPO}``
placeholder + venv-python command shape (alongside the existing
SubagentStart block, which must be preserved — §15 backwards-compat).
Live merge into a workspace's .claude/settings.json is the same gated
hand-merge step, out-of-scope per plan §7-4.
"""

from __future__ import annotations

import json
from pathlib import Path

from conftest import REPO_ROOT

FRAGMENT = (
    REPO_ROOT / "framework" / "frame-kernel" / "hooks" / "settings.fragment.json"
)


def _load_fragment() -> dict:
    return json.loads(FRAGMENT.read_text(encoding="utf-8"))


def test_fragment_declares_subagent_stop_event() -> None:
    """The fragment registers the SubagentStop event (the lifted
    previously-unused primitive)."""
    data = _load_fragment()
    hooks = data.get("hooks")
    assert isinstance(hooks, dict)
    assert "SubagentStop" in hooks, (
        "fragment must declare a SubagentStop matcher block"
    )
    blocks = hooks["SubagentStop"]
    assert isinstance(blocks, list) and blocks


def test_subagent_stop_command_targets_the_hook_with_placeholder() -> None:
    """The SubagentStop matcher block invokes the frame-check hook under
    the workspace venv Python with the ${LOAM_REPO} portable
    placeholder."""
    data = _load_fragment()
    block = data["hooks"]["SubagentStop"][0]
    inner = block["hooks"]
    assert isinstance(inner, list) and inner
    cmd = inner[0]["command"]
    assert "${LOAM_REPO}" in cmd, (
        "command must use the portable ${LOAM_REPO} placeholder"
    )
    assert ".venv/bin/python" in cmd, "must run under the workspace venv Python"
    assert "framework/frame-kernel/hooks/subagent_stop_frame_check.py" in cmd, (
        "command must target the frame-kernel SubagentStop hook"
    )
    assert inner[0]["type"] == "command"


def test_subagent_start_block_preserved() -> None:
    """§15 backwards-compat: the 1a SubagentStart block is preserved
    beside the new SubagentStop block (the EXTEND does not drop it)."""
    data = _load_fragment()
    hooks = data["hooks"]
    assert "SubagentStart" in hooks, "the 1a SubagentStart block must survive"
    start_cmd = hooks["SubagentStart"][0]["hooks"][0]["command"]
    assert "subagent_start_context.py" in start_cmd


def test_fragment_documents_gated_activation() -> None:
    """The fragment carries the gated-activation comment (RF-1 / plan
    §7-4): a PORTABLE declaration, NOT an auto-merge into a live
    .claude/settings.json."""
    data = _load_fragment()
    comment = data.get("_comment", "")
    assert "NOT" in comment and "automatically" in comment.lower(), (
        "fragment must document that live activation is a gated, "
        "non-automatic merge"
    )
