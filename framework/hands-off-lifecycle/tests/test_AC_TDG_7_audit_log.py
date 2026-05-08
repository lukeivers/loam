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

"""AC.TDG.7 — Every gate fire is observable through a deterministic
audit surface.

Per the locked plan-doc §4 AC.TDG.7: each PreToolUse fire (allow +
deny + no-op) is recorded in a workspace-local audit surface that a
downstream consumer can read deterministically without re-running
the gate. Surface is append-only; concurrent fires across processes
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


from active_scope_sentinel import ActiveScopeSentinel, ScopeBinding  # noqa: E402


def _stub_modules(monkeypatch, *, mode: str, sentinel):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: sentinel
    ass_mod.ActiveScopeSentinel = ActiveScopeSentinel
    ass_mod.ScopeBinding = ScopeBinding
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


def test_AC_TDG_7_audit_log_at_workspace_state_path(tmp_path) -> None:
    """The audit log lives at ``<workspace>/workspace/.pos/
    tdd-guard.log`` per locked plan §6 D-A3.10 + hard constraint 17."""
    import tdd_guard as gate

    expected = tmp_path / "workspace" / ".pos" / "tdd-guard.log"
    assert gate._audit_log_path(tmp_path) == expected


def test_AC_TDG_7_deny_writes_one_ndjson_line(tmp_path, monkeypatch) -> None:
    """A deny decision invoked through ``main`` appends one JSON object
    line to the audit log. Read it back; assert schema (byte-content
    verification per ODD §8.2.14)."""
    import tdd_guard as gate

    sentinel = ActiveScopeSentinel(
        scope_id="test-scope",
        plan_path="docs/plans/test.md",
        bindings=(
            ScopeBinding(component="orchestrator", ac_id="AC.O8.A1"),
        ),
        created_at="2026-04-28T12:00:00+00:00",
        session_id=None,
    )
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=sentinel)

    class _NewAcTracker:
        def manifest_rows_for_ac(self, component, ac_id):
            return [
                {
                    "component": component,
                    "ac_id": ac_id,
                    "source_path_glob": "framework/orchestrator/src/**",
                    "created_at": "2026-04-28T13:00:00+00:00",
                }
            ]

    monkeypatch.setattr(gate, "_open_tracker", lambda _: _NewAcTracker())

    raw_path = str(
        tmp_path / "framework" / "orchestrator" / "src" / "orchestrator.py"
    )
    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": raw_path},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    rc = gate.main([])
    assert rc == 0

    log_path = tmp_path / "workspace" / ".pos" / "tdd-guard.log"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])

    # Schema: required fields per locked plan §6 D-A3.10.
    for field in (
        "ts",
        "tool",
        "path",
        "rel_path",
        "mode",
        "sentinel_state",
        "bound_acs",
        "new_acs_in_scope",
        "tests_present",
        "tests_missing",
        "decision",
        "failure_class",
        "reason",
    ):
        assert field in payload, f"missing field {field!r}"

    assert payload["tool"] == "Edit"
    assert payload["path"] == raw_path
    assert payload["mode"] == "dev-mode"
    assert payload["sentinel_state"] == "present"
    assert payload["decision"] == "deny"
    assert payload["failure_class"] == "missing-test-file"
    # On deny the reason text is non-empty and matches the deny envelope.
    assert isinstance(payload["reason"], str) and payload["reason"]
    # bound_acs reflects the sentinel's bindings.
    assert {
        "component": "orchestrator",
        "ac_id": "AC.O8.A1",
    } in payload["bound_acs"]
    # new_acs_in_scope contains the (orchestrator, AC.O8.A1) binding.
    assert {
        "component": "orchestrator",
        "ac_id": "AC.O8.A1",
    } in payload["new_acs_in_scope"]
    # tests_missing names the expected test glob.
    assert any(
        entry.get("ac_id") == "AC.O8.A1"
        and "test_AC_O8_A1_" in entry.get("expected_test_glob", "")
        for entry in payload["tests_missing"]
    )


def test_AC_TDG_7_no_op_writes_one_line(tmp_path, monkeypatch) -> None:
    """Mode = normal-use → no-op decision still appends one audit line
    with decision=no-op + sentinel_state field."""
    import tdd_guard as gate

    _stub_modules(monkeypatch, mode="normal-use", sentinel=None)

    raw_path = str(tmp_path / "framework" / "x" / "y.py")
    envelope = {
        "session_id": "s1",
        "cwd": str(tmp_path),
        "hook_event_name": "PreToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": raw_path},
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    rc = gate.main([])
    assert rc == 0

    log_path = tmp_path / "workspace" / ".pos" / "tdd-guard.log"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["decision"] == "no-op"
    assert payload["mode"] == "normal-use"


def test_AC_TDG_7_two_fires_append_atomically(tmp_path, monkeypatch) -> None:
    """Two sequential fires append two NDJSON lines (atomic append; no
    overwrite, no corruption)."""
    import tdd_guard as gate

    _stub_modules(monkeypatch, mode="normal-use", sentinel=None)

    log_path = tmp_path / "workspace" / ".pos" / "tdd-guard.log"

    for i in range(2):
        envelope = {
            "session_id": f"s{i}",
            "cwd": str(tmp_path),
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": str(tmp_path / f"file{i}.py")},
        }
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)
        gate.main([])

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payloads = [json.loads(line) for line in lines]
    assert payloads[0]["path"].endswith("file0.py")
    assert payloads[1]["path"].endswith("file1.py")
