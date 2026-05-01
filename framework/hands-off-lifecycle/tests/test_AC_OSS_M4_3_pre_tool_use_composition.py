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

"""AC.OSS-M4.3 — Composition with A2/A3/A4 + multi-contributor
PreToolUse stanza.

Per the locked plan-doc §4 AC.OSS-M4.3: post-M4 the multi-contributor
PreToolUse outer list carries five inner-hook envelopes —
objective_binding_gate (A2), tdd_guard (A3), bash_guard (A4_bash),
agent_guard (A4_task), dispatch_setup_hook (M4). A4_task and M4 share
the ``Task`` matcher and run sequentially per Claude Code's
deterministic-order semantics — A4_task runs first (refusal gate),
M4 runs second (always allows).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


from first_run_settings import merge_pre_tool_use  # noqa: E402
from first_run_helper import (  # noqa: E402
    _agent_guard_stanza,
    _bash_guard_stanza,
    _dispatch_setup_hook_stanza,
    _objective_binding_gate_stanza,
    _tdd_guard_stanza,
)


def test_AC_OSS_M4_3_dispatch_setup_hook_stanza_builder_present(
    tmp_path: Path,
) -> None:
    """``first_run_helper.py`` exposes the M4 stanza builder."""
    stanza = _dispatch_setup_hook_stanza(tmp_path)
    assert stanza["matcher"] == "Task"
    assert "dispatch_setup_hook.py" in stanza["hooks"][0]["command"]


def test_AC_OSS_M4_3_marker_tuple_includes_dispatch_setup_hook() -> None:
    """The pos-v2-owned marker tuple admits dispatch_setup_hook.py
    so re-merge over a five-element pos-v2 list does NOT back up."""
    from first_run_settings import _LOAM_PRE_TOOL_USE_COMMAND_MARKERS

    assert "dispatch_setup_hook.py" in _LOAM_PRE_TOOL_USE_COMMAND_MARKERS


def test_AC_OSS_M4_3_first_write_five_stanzas(tmp_path: Path) -> None:
    """First write with all five stanzas produces the five-element
    outer list under ``hooks.PreToolUse`` in the expected order."""
    settings_path = tmp_path / "settings.json"
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _objective_binding_gate_stanza(tmp_path),
            _tdd_guard_stanza(tmp_path),
            _bash_guard_stanza(tmp_path),
            _agent_guard_stanza(tmp_path),
            _dispatch_setup_hook_stanza(tmp_path),
        ],
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 5
    assert "objective_binding_gate.py" in pte[0]["hooks"][0]["command"]
    assert "tdd_guard.py" in pte[1]["hooks"][0]["command"]
    assert "bash_guard.py" in pte[2]["hooks"][0]["command"]
    assert "agent_guard.py" in pte[3]["hooks"][0]["command"]
    assert "dispatch_setup_hook.py" in pte[4]["hooks"][0]["command"]
    # A4_task and M4 share the Task matcher; entries run sequentially.
    assert pte[3]["matcher"] == "Task"
    assert pte[4]["matcher"] == "Task"
    # M4 is APPENDED 5th — A4 runs first per the established order.
    assert pte.index(pte[3]) < pte.index(pte[4])


def test_AC_OSS_M4_3_re_merge_no_backup_over_five_stanzas(
    tmp_path: Path,
) -> None:
    """Re-merge over a five-element pos-v2 list (every inner-hook
    command matches a recognised marker) does NOT create a backup."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _objective_binding_gate_stanza(tmp_path),
            _tdd_guard_stanza(tmp_path),
            _bash_guard_stanza(tmp_path),
            _agent_guard_stanza(tmp_path),
            _dispatch_setup_hook_stanza(tmp_path),
        ],
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _objective_binding_gate_stanza(tmp_path),
            _tdd_guard_stanza(tmp_path),
            _bash_guard_stanza(tmp_path),
            _agent_guard_stanza(tmp_path),
            _dispatch_setup_hook_stanza(tmp_path),
        ],
    )
    assert result.wrote is True
    assert result.backup_path is None


def test_AC_OSS_M4_3_re_merge_over_legacy_four_stanzas_no_backup(
    tmp_path: Path,
) -> None:
    """A pre-M4 settings.json carries 4 stanzas (A2 + A3 + A4_bash +
    A4_task). Re-merging with all 5 does NOT trigger backup (the
    legacy four markers stay in the recognised set)."""
    settings_path = tmp_path / "settings.json"
    merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _objective_binding_gate_stanza(tmp_path),
            _tdd_guard_stanza(tmp_path),
            _bash_guard_stanza(tmp_path),
            _agent_guard_stanza(tmp_path),
        ],
    )
    result = merge_pre_tool_use(
        settings_path=settings_path,
        new_entries=[
            _objective_binding_gate_stanza(tmp_path),
            _tdd_guard_stanza(tmp_path),
            _bash_guard_stanza(tmp_path),
            _agent_guard_stanza(tmp_path),
            _dispatch_setup_hook_stanza(tmp_path),
        ],
    )
    assert result.wrote is True
    assert result.backup_path is None
    data = json.loads(settings_path.read_text())
    pte = data["hooks"]["PreToolUse"]
    assert len(pte) == 5
