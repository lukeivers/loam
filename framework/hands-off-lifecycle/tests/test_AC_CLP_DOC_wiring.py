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

"""Wiring leg of the claude-leverage DOCTRINE slice (D-DOC.2 / D-DOC.7).

The prefer-the-primitive PreToolUse guard reaches a bootstrapped
workspace ONLY via the first_run_settings marker + the first_run_helper
stanza builder (the single shipped wiring surface —
``_LOAM_PRE_TOOL_USE_COMMAND_MARKERS``). This test covers the
hands-off-lifecycle leg of the fence: the marker is present, the stanza
builder produces a Task-matcher envelope naming the guard, and a fresh
multi-contributor merge lands the guard as the sixth PreToolUse
contributor without backing up the pos-v2-owned stanza.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


from first_run_settings import (  # noqa: E402
    _LOAM_PRE_TOOL_USE_COMMAND_MARKERS,
    merge_pre_tool_use,
)
from first_run_helper import (  # noqa: E402
    _agent_guard_stanza,
    _bash_guard_stanza,
    _dispatch_setup_hook_stanza,
    _objective_binding_gate_stanza,
    _primitive_check_guard_stanza,
    _tdd_guard_stanza,
)


def test_marker_tuple_includes_primitive_check_guard() -> None:
    """The pos-v2-owned PreToolUse marker tuple admits
    primitive_check_guard.py so a re-merge over a six-element pos-v2
    list does NOT back up (treats it as user-authored)."""
    assert (
        "primitive_check_guard.py"
        in _LOAM_PRE_TOOL_USE_COMMAND_MARKERS
    )


def test_stanza_builder_is_task_scoped(tmp_path: Path) -> None:
    """The stanza builder produces a Task-matcher envelope naming the
    guard script (D-DOC.7 matcher-scoping; D-DOC.2 home)."""
    stanza = _primitive_check_guard_stanza(tmp_path)
    assert stanza["matcher"] == "Task"
    assert (
        "primitive_check_guard.py" in stanza["hooks"][0]["command"]
    )


def _all_six(tmp_path: Path) -> list[dict]:
    return [
        _objective_binding_gate_stanza(tmp_path),
        _tdd_guard_stanza(tmp_path),
        _bash_guard_stanza(tmp_path),
        _agent_guard_stanza(tmp_path),
        _dispatch_setup_hook_stanza(tmp_path),
        _primitive_check_guard_stanza(tmp_path),
    ]


def test_first_write_six_stanzas_in_order(tmp_path: Path) -> None:
    """First write with all six stanzas lands the primitive-check guard
    as the sixth PreToolUse contributor, in order."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path, new_entries=_all_six(tmp_path)
    )
    assert result.wrote is True
    assert result.backup_path is None
    pte = json.loads(settings_path.read_text())["hooks"]["PreToolUse"]
    assert len(pte) == 6
    assert (
        "primitive_check_guard.py" in pte[5]["hooks"][0]["command"]
    )
    assert pte[5]["matcher"] == "Task"


def test_re_merge_over_six_no_backup(tmp_path: Path) -> None:
    """Re-merge over a six-element pos-v2 list (every inner-hook command
    matches a recognised marker) does NOT create a backup."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path, new_entries=_all_six(tmp_path)
    )
    result = merge_pre_tool_use(
        settings_path=settings_path, new_entries=_all_six(tmp_path)
    )
    assert result.wrote is True
    assert result.backup_path is None
