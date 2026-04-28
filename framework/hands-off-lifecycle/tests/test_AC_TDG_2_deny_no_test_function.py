"""AC.TDG.2 — Refuse Edit when test file exists but matching function
is absent.

Per the locked plan-doc §4 AC.TDG.2: given a file matching
``framework/<X>/tests/test_AC_<Y-normalised>_*.py`` exists, given no
function whose name starts with ``test_AC_<Y-normalised>_`` is
defined in any such file: hook returns ``permissionDecision:
"deny"`` with a reason that names the file path(s) found, the
expected function-name pattern, and at least one repair direction.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


from active_scope_sentinel import ActiveScopeSentinel, ScopeBinding  # noqa: E402


class _NewAcTracker:
    def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
        return [
            {
                "component": component,
                "ac_id": ac_id,
                "source_path_glob": "framework/orchestrator/src/**",
                "created_at": "2026-04-28T13:00:00+00:00",
            }
        ]


@pytest.fixture
def gate_dev_mode_new_ac(monkeypatch):
    sentinel = ActiveScopeSentinel(
        scope_id="test-scope",
        plan_path="docs/rebuild/plans/test.md",
        bindings=(
            ScopeBinding(component="orchestrator", ac_id="AC.O8.A1"),
        ),
        created_at="2026-04-28T12:00:00+00:00",
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

    import tdd_guard as gate

    monkeypatch.setattr(gate, "_open_tracker", lambda _: _NewAcTracker())


def test_AC_TDG_2_test_file_present_no_function_denies(
    tmp_path, gate_dev_mode_new_ac
) -> None:
    """File ``test_AC_O8_A1_anything.py`` exists but contains no
    function whose name starts with ``test_AC_O8_A1_`` → deny with
    missing-test-function failure-class."""
    import tdd_guard as gate

    tests_dir = tmp_path / "framework" / "orchestrator" / "tests"
    tests_dir.mkdir(parents=True)
    test_file = tests_dir / "test_AC_O8_A1_renamed.py"
    # File present, but the function inside has the WRONG name —
    # someone renamed it after copy-pasting from another AC's test.
    test_file.write_text(
        "def test_O8_A1_no_AC_prefix():\n    pass\n"
        "def test_AC_OBG_3_unrelated():\n    pass\n",
        encoding="utf-8",
    )

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
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-test-function"
    assert decision.reason is not None
    # Reason names the file found + expected function-name pattern +
    # at least one repair direction.
    assert "test_AC_O8_A1_renamed.py" in decision.reason
    assert "test_AC_O8_A1_" in decision.reason
    assert (
        "rename" in decision.reason.lower()
        or "add a function" in decision.reason.lower()
        or "add" in decision.reason.lower()
    )


def test_AC_TDG_2_test_file_with_matching_function_allows(
    tmp_path, gate_dev_mode_new_ac
) -> None:
    """File present AND contains a matching function → allow.
    (Consistency cross-check; AC.TDG.5 covers this directly but keeping
    it here to assert the deny path is the only failure direction in
    AC.TDG.2's surface.)"""
    import tdd_guard as gate

    tests_dir = tmp_path / "framework" / "orchestrator" / "tests"
    tests_dir.mkdir(parents=True)
    test_file = tests_dir / "test_AC_O8_A1_normal.py"
    test_file.write_text(
        "def test_AC_O8_A1_does_something():\n    assert True\n",
        encoding="utf-8",
    )

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
