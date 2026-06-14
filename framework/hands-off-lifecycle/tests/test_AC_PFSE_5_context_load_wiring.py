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

"""Wiring leg of AC.PFSE.5 (principle-foundation-structural-enforcement,
Slice B) — the context-load gate reaches a bootstrapped workspace.

The gate reaches a bootstrapped workspace ONLY via the
first_run_settings marker + the first_run_helper stanza builder (the A4
precedent — the single shipped wiring surface). This test covers the
hands-off-lifecycle leg of the fence: the marker is present, the stanza
builder produces the two matcher envelopes (Task + Edit|Write|MultiEdit)
naming the gate, and a fresh multi-contributor merge lands them without
backing up the pos-v2-owned stanza.

This is the ONLY hands-off-lifecycle edit in this slice (wiring only,
per the manifest's admitted-for-wiring scope).
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
    _context_load_gate_stanzas,
    _dispatch_setup_hook_stanza,
    _objective_binding_gate_stanza,
    _primitive_check_guard_stanza,
    _tdd_guard_stanza,
)


def test_marker_tuple_includes_context_load_gate() -> None:
    """The pos-v2-owned PreToolUse marker tuple admits
    context_load_gate.py so a re-merge over the full pos-v2 list does
    NOT back up (treats it as user-authored)."""
    assert (
        "context_load_gate.py" in _LOAM_PRE_TOOL_USE_COMMAND_MARKERS
    )


def test_stanza_builder_emits_two_matchers(tmp_path: Path) -> None:
    """The builder produces two matcher envelopes (Task +
    Edit|Write|MultiEdit), each naming the gate script."""
    stanzas = _context_load_gate_stanzas(tmp_path)
    assert len(stanzas) == 2
    matchers = {s["matcher"] for s in stanzas}
    assert matchers == {"Task", "Edit|Write|MultiEdit"}
    for s in stanzas:
        assert (
            "context_load_gate.py" in s["hooks"][0]["command"]
        )


def _full_list(tmp_path: Path) -> list[dict]:
    return [
        _objective_binding_gate_stanza(tmp_path),
        _tdd_guard_stanza(tmp_path),
        _bash_guard_stanza(tmp_path),
        _agent_guard_stanza(tmp_path),
        _dispatch_setup_hook_stanza(tmp_path),
        _primitive_check_guard_stanza(tmp_path),
        *_context_load_gate_stanzas(tmp_path),
    ]


def test_first_write_lands_context_load_gate(tmp_path: Path) -> None:
    """First write with the full list lands the two context-load
    entries as the seventh + eighth PreToolUse contributors."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path, new_entries=_full_list(tmp_path)
    )
    assert result.wrote is True
    assert result.backup_path is None
    pte = json.loads(settings_path.read_text())["hooks"]["PreToolUse"]
    assert len(pte) == 8
    cmds = [e["hooks"][0]["command"] for e in pte]
    assert sum("context_load_gate.py" in c for c in cmds) == 2


def test_re_merge_over_full_list_no_backup(tmp_path: Path) -> None:
    """Re-merge over the full pos-v2 list (every inner-hook command
    matches a recognised marker, including context_load_gate.py) does
    NOT create a backup."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path, new_entries=_full_list(tmp_path)
    )
    result = merge_pre_tool_use(
        settings_path=settings_path, new_entries=_full_list(tmp_path)
    )
    assert result.wrote is True
    assert result.backup_path is None
