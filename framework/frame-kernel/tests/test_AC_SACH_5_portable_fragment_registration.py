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

"""AC.SACH.5 — the hook is registered for SubagentStart via a portable
settings-fragment any loam workspace can compose, with no per-workspace
hand-authoring of the registration.

The test parses ``settings.fragment.json`` and asserts it declares a
SubagentStart matcher block whose command invokes the hook under the
workspace venv Python with the ``${LOAM_REPO}`` placeholder (the
portable-declaration outcome — RF-1: the fragment is portable; the live
merge into a workspace's .claude/settings.json is the same gated
hand-merge keep-pace uses, out-of-scope per plan §7-4).
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


def test_fragment_exists_and_is_valid_json() -> None:
    """The portable fragment exists + parses (a malformed fragment could
    not be composed by any workspace)."""
    assert FRAGMENT.exists()
    data = _load_fragment()
    assert isinstance(data, dict)


def test_fragment_declares_subagent_start_event() -> None:
    """The fragment registers the SubagentStart event (the lifted
    primitive)."""
    data = _load_fragment()
    hooks = data.get("hooks")
    assert isinstance(hooks, dict)
    assert "SubagentStart" in hooks, (
        "fragment must declare a SubagentStart matcher block"
    )
    blocks = hooks["SubagentStart"]
    assert isinstance(blocks, list) and blocks


def test_fragment_command_targets_the_hook_with_loam_repo_placeholder() -> None:
    """The matcher block's command invokes the frame-kernel hook under the
    workspace venv Python with the ${LOAM_REPO} portable placeholder (the
    no-hand-authoring-of-registration outcome)."""
    data = _load_fragment()
    block = data["hooks"]["SubagentStart"][0]
    inner = block["hooks"]
    assert isinstance(inner, list) and inner
    cmd = inner[0]["command"]
    assert "${LOAM_REPO}" in cmd, (
        "command must use the portable ${LOAM_REPO} placeholder, not a "
        "per-workspace absolute path"
    )
    assert ".venv/bin/python" in cmd, "must run under the workspace venv Python"
    assert "framework/frame-kernel/hooks/subagent_start_context.py" in cmd, (
        "command must target the frame-kernel SubagentStart hook"
    )
    assert inner[0]["type"] == "command"


def test_fragment_documents_gated_activation() -> None:
    """The fragment carries the gated-activation comment (RF-1 / plan
    §7-4): it is a PORTABLE declaration, NOT an auto-merge into a live
    .claude/settings.json."""
    data = _load_fragment()
    comment = data.get("_comment", "")
    assert "NOT" in comment and "automatically" in comment.lower(), (
        "fragment must document that live activation is a gated, "
        "non-automatic merge (portable-declaration scope per RF-1)"
    )
