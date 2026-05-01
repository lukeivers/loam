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

"""AC.OBG.1 — Refuse Edit on sealed-component source with no active-
scope sentinel (DEV MODE).

Per the locked plan-doc §4 AC.OBG.1: given workspace-mode = ``dev-
mode``, given ``tool_input.file_path`` is under a sealed-component
source path, given ``read_active_scope_sentinel(workspace_root)``
returns ``None``, given the path is not in the dev-discipline carve-
out list (AC.OBG.5): the hook returns ``hookSpecificOutput.
permissionDecision: "deny"`` with a ``permissionDecisionReason`` that
names (a) the path, (b) the missing sentinel, (c) at least one
repair direction.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
# Post-M6b.0: gate-hook source files MOVED to plugins/dev-sdlc/hooks/.
# Add plugin's hooks dir to sys.path so the test imports resolve to
# the moved gate modules. _gate_helpers.py STAYS at canonical
# (HOOKS_DIR above) and remains importable.
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
if PLUGIN_HOOKS_DIR.exists():
    sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


@pytest.fixture
def gate_with_dev_mode_no_sentinel(monkeypatch):
    """Stub workspace_mode + read_active_scope_sentinel for the test
    case (DEV MODE, sentinel absent)."""
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "dev-mode"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: None
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


def test_AC_OBG_1_dev_mode_no_sentinel_denies(
    tmp_path, gate_with_dev_mode_no_sentinel
) -> None:
    """Dev-mode workspace, no active-scope sentinel, sealed source path
    → deny with reason naming path + missing sentinel + repair."""
    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "x.py"
            )
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-sentinel"
    assert decision.reason is not None
    assert "x.py" in decision.reason
    assert "active-scope sentinel" in decision.reason
    # Repair directions per the locked plan §6 D-A2.3 are at least one
    # of: carve-out alternative, dispatcher-side write, halt-and-surface.
    assert (
        "carve-out" in decision.reason
        or "dispatcher" in decision.reason
        or "halt" in decision.reason
    )


def test_AC_OBG_1_write_tool_also_denies(
    tmp_path, gate_with_dev_mode_no_sentinel
) -> None:
    """Same condition but tool_name = Write — also denies."""
    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Write",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "y.py"
            )
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-sentinel"


def test_AC_OBG_1_multiedit_tool_also_denies(
    tmp_path, gate_with_dev_mode_no_sentinel
) -> None:
    """Same condition but tool_name = MultiEdit — also denies.
    Per Q1 empirical answer in §14: MultiEdit operates on ONE
    file_path at tool_input top-level (with multiple edits in
    ``edits[]``); per-call deny applies to that single path."""
    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="MultiEdit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "z.py"
            ),
            "edits": [
                {"old_string": "a", "new_string": "b"},
                {"old_string": "c", "new_string": "d"},
            ],
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-sentinel"
