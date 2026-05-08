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

"""AC.TDG.8 — Helper-library extraction preserves A2's behaviour.

Per the locked plan-doc §4 AC.TDG.8: post-extraction, A2's existing
AC.OBG.1..AC.OBG.7 + AC.OBG.S + AC.OBG.settings_merge tests pass byte-
for-byte; A2's ``objective_binding_gate.py`` consumes symbols from
``_gate_helpers.py``; behaviour-equivalent at the hook-envelope-in /
JSON-out boundary on a parametrised harness covering A2's deny / allow
paths.

This test exercises the equivalence at the symbol level (the helper
module exposes the required symbols) and at the behavioural level
(parametrised allow/deny paths produce the same Decision shape).
"""

from __future__ import annotations

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


def test_AC_TDG_8_helper_module_exposes_required_symbols() -> None:
    """``_gate_helpers.py`` exposes the symbols A3 + A2 share."""
    import _gate_helpers as helpers

    # Constants
    assert helpers.WORKSPACE_STATE_SUBDIR == "workspace"
    assert helpers.POS_SUBDIR == ".pos"

    # Carve-out tuples / sets (private to helper, but used by A2 + A3
    # via shim re-exports — must still exist at the helper boundary).
    assert isinstance(helpers._CARVE_OUT_PREFIXES, tuple)
    assert "docs/" in helpers._CARVE_OUT_PREFIXES
    assert isinstance(helpers._CARVE_OUT_FILES, frozenset)
    assert "CLAUDE.md" in helpers._CARVE_OUT_FILES

    # Public helpers
    assert callable(helpers.is_carve_out_path)
    assert callable(helpers.workspace_relative)
    assert callable(helpers.read_workspace_mode_or_normal_use)
    assert callable(helpers.read_active_scope_sentinel_or_none)
    assert callable(helpers.open_tracker_or_none)
    assert callable(helpers.audit_log_path)
    assert callable(helpers.append_audit_line)


def test_AC_TDG_8_a2_module_re_exports_helpers_for_test_compat() -> None:
    """A2's ``objective_binding_gate`` keeps module-level shims so
    existing test imports (e.g. ``gate._audit_log_path(...)``) keep
    working byte-for-byte."""
    import objective_binding_gate as gate

    # The shims A2's test suite reaches for.
    assert callable(gate._workspace_relative)
    assert callable(gate._is_carve_out_path)
    assert callable(gate._open_tracker)
    assert callable(gate._audit_log_path)
    assert callable(gate._append_audit_line)
    assert isinstance(gate._CARVE_OUT_PREFIXES, tuple)
    assert isinstance(gate._CARVE_OUT_FILES, frozenset)
    assert gate.WORKSPACE_STATE_SUBDIR == "workspace"
    assert gate.POS_SUBDIR == ".pos"
    assert gate.AUDIT_LOG_FILENAME == "objective-binding-gate.log"


def test_AC_TDG_8_carve_out_predicate_byte_equivalent() -> None:
    """``_is_carve_out_path`` (A2 shim) and ``is_carve_out_path``
    (helper public) agree on every input."""
    import objective_binding_gate as gate
    import _gate_helpers as helpers

    cases = [
        "docs/foo.md",
        "tools/x.sh",
        ".scratch/y",
        "personas/p.md",
        "CLAUDE.md",
        "framework/CLAUDE.md",
        "framework/orchestrator/src/x.py",  # NOT a carve-out
        "framework/orchestrator/tests/test_x.py",  # NOT a carve-out (per A2)
        "docs/FUTURE_IDEAS.md",
        ".gitignore",
    ]
    for case in cases:
        assert gate._is_carve_out_path(case) == helpers.is_carve_out_path(
            case
        ), case


def test_AC_TDG_8_a2_evaluate_allow_path_unchanged(tmp_path, monkeypatch) -> None:
    """Parametrised behavioural equivalence: A2's allow path on a glob
    match produces a Decision with decision=allow, same as pre-
    extraction. (The full AC.OBG.x suite is the byte-for-byte
    regression contract; this test pins one canonical allow case
    explicitly.)"""
    sentinel = ActiveScopeSentinel(
        scope_id="test-scope",
        plan_path="docs/plans/test.md",
        bindings=(
            ScopeBinding(component="orchestrator", ac_id="AC.O8.A1"),
        ),
        created_at="2026-04-28T00:00:00Z",
        session_id=None,
    )
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "dev-mode"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: sentinel
    ass_mod.ActiveScopeSentinel = ActiveScopeSentinel
    ass_mod.ScopeBinding = ScopeBinding
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)

    class _T:
        def manifest_rows_for_ac(self, c, a):
            return [
                {
                    "component": c,
                    "ac_id": a,
                    "source_path_glob": "framework/orchestrator/src/**",
                }
            ]

    import objective_binding_gate as gate

    monkeypatch.setattr(gate, "_open_tracker", lambda _: _T())

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path
                / "framework"
                / "orchestrator"
                / "src"
                / "orchestrator.py"
            )
        },
    )
    assert decision.decision == "allow"


def test_AC_TDG_8_a2_evaluate_deny_path_unchanged(tmp_path, monkeypatch) -> None:
    """Parametrised behavioural equivalence: A2's deny path on missing
    sentinel produces decision=deny + failure_class=missing-sentinel,
    same as pre-extraction."""
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "dev-mode"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: None
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)

    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path
                / "framework"
                / "orchestrator"
                / "src"
                / "x.py"
            )
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-sentinel"
