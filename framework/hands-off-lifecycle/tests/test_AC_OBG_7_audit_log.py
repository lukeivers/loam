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

"""AC.OBG.7 — Every gate fire is observable through a deterministic
audit surface.

Per the locked plan-doc §4 AC.OBG.7: each PreToolUse fire (allow +
deny + no-op) is recorded in a workspace-local audit surface that a
downstream consumer can read deterministically without re-running
the gate. Recorded fields are sufficient to reconstruct: when the
fire happened, which tool/path/mode it observed, the sentinel state,
the bound ``(component, ac_id)`` pairs (when present), the gate's
decision, and (on deny) the same reason text the model received.
The surface is append-only in A2; concurrent fires across processes
do not corrupt each other (atomicity guarantee).

This test exercises the byte-content read of the on-disk NDJSON log
per ODD §8.2.14 (the build dispatch's explicit requirement).
"""

from __future__ import annotations

import io
import json
import sys
import types
from pathlib import Path



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


def _stub_modules(monkeypatch, *, mode: str, sentinel):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: sentinel
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


def test_AC_OBG_7_audit_log_at_workspace_state_path(
    tmp_path, monkeypatch
) -> None:
    """The audit log lives at ``<workspace>/workspace/.pos/
    objective-binding-gate.log`` per locked plan §6 D-A2.8 + hard
    constraint 15."""
    import objective_binding_gate as gate

    expected = (
        tmp_path / "workspace" / ".pos" / "objective-binding-gate.log"
    )
    assert gate._audit_log_path(tmp_path) == expected


def test_AC_OBG_7_deny_writes_one_ndjson_line(tmp_path, monkeypatch) -> None:
    """A deny decision invoked through ``main`` appends one JSON
    object line to the audit log. Read it back; assert schema."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)

    import objective_binding_gate as gate

    # Invoke main with a synthetic stdin envelope; rebind sys.stdin
    # to a StringIO so the CLI reads our payload.
    target_path = tmp_path / "framework" / "orchestrator" / "src" / "x.py"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.touch()
    envelope = {
        "session_id": "S",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(target_path)},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    monkeypatch.setattr(sys, "stdout", io.StringIO())

    rc = gate.main()
    assert rc == 0

    log_path = (
        tmp_path / "workspace" / ".pos" / "objective-binding-gate.log"
    )
    assert log_path.exists(), "audit log was not written"
    raw = log_path.read_text(encoding="utf-8")
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    assert len(lines) == 1, f"expected exactly one NDJSON line, got {lines}"

    row = json.loads(lines[0])
    # Schema: timestamp, tool, path, rel_path, mode, sentinel_state,
    # bound_acs (list), decision, failure_class (nullable), reason
    # (nullable on allow / no-op, str on deny).
    assert isinstance(row.get("ts"), str)
    assert row.get("tool") == "Edit"
    assert row.get("path") == str(target_path)
    assert row.get("rel_path") == "framework/orchestrator/src/x.py"
    assert row.get("mode") == "dev-mode"
    assert row.get("sentinel_state") == "absent"
    assert row.get("decision") == "deny"
    assert row.get("failure_class") == "missing-sentinel"
    assert isinstance(row.get("reason"), str)
    assert isinstance(row.get("bound_acs"), list)


def test_AC_OBG_7_no_op_writes_audit_line_too(tmp_path, monkeypatch) -> None:
    """No-op fire (NORMAL USE) also lands an audit line — every fire
    is observable per AC.OBG.7."""
    _stub_modules(monkeypatch, mode="normal-use", sentinel=None)

    import objective_binding_gate as gate

    envelope = {
        "session_id": "S",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "x.py"
            )
        },
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    gate.main()

    log_path = (
        tmp_path / "workspace" / ".pos" / "objective-binding-gate.log"
    )
    raw = log_path.read_text(encoding="utf-8")
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["decision"] == "no-op"
    assert row["mode"] == "normal-use"


def test_AC_OBG_7_audit_log_is_append_only(tmp_path, monkeypatch) -> None:
    """Multiple fires append; earlier lines are preserved."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)

    import objective_binding_gate as gate

    target_path = tmp_path / "framework" / "orchestrator" / "src" / "x.py"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.touch()
    for tool in ("Edit", "Write", "MultiEdit"):
        envelope = {
            "session_id": "S",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": {"file_path": str(target_path)},
        }
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
        monkeypatch.setattr(sys, "stdout", io.StringIO())
        gate.main()

    log_path = (
        tmp_path / "workspace" / ".pos" / "objective-binding-gate.log"
    )
    lines = [
        ln for ln in log_path.read_text("utf-8").splitlines() if ln.strip()
    ]
    assert len(lines) == 3
    tools_recorded = [json.loads(ln)["tool"] for ln in lines]
    assert tools_recorded == ["Edit", "Write", "MultiEdit"]


def test_AC_OBG_7_main_emits_deny_envelope_to_stdout(
    tmp_path, monkeypatch
) -> None:
    """On deny the CLI emits the structured PreToolUse JSON envelope
    Claude Code consumes."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)

    import objective_binding_gate as gate

    target_path = tmp_path / "framework" / "orchestrator" / "src" / "x.py"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.touch()
    envelope = {
        "session_id": "S",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(target_path)},
    }
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    monkeypatch.setattr(sys, "stdout", out)
    gate.main()

    response = json.loads(out.getvalue())
    assert response["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    assert (
        response["hookSpecificOutput"]["permissionDecision"] == "deny"
    )
    assert response["hookSpecificOutput"]["permissionDecisionReason"]
