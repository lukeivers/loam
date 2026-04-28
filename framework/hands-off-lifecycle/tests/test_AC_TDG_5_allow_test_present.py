"""AC.TDG.5 — Allow Edit when new AC has matching test (file +
function).

Per the locked plan-doc §4 AC.TDG.5: given the sentinel binds
``(X, Y)``, given at least one ``(X, Y)`` manifest row's
``created_at`` is after the sentinel's, given a file matching
``framework/<X>/tests/test_AC_<Y-normalised>_*.py`` exists AND
contains at least one function whose name starts with
``test_AC_<Y-normalised>_``: hook returns no ``permissionDecision``.
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


def test_AC_TDG_5_test_present_allows(
    tmp_path, gate_dev_mode_new_ac
) -> None:
    """File ``test_AC_O8_A1_*.py`` exists with matching function →
    allow. Sentinel binds (orchestrator, AC.O8.A1); manifest row's
    created_at is after sentinel's; AC is new in this diff."""
    import tdd_guard as gate

    tests_dir = tmp_path / "framework" / "orchestrator" / "tests"
    tests_dir.mkdir(parents=True)
    test_file = tests_dir / "test_AC_O8_A1_some_behaviour.py"
    test_file.write_text(
        "def test_AC_O8_A1_first_behaviour():\n    assert True\n"
        "def test_AC_O8_A1_second_behaviour():\n    assert True\n",
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
    assert decision.reason is None
    assert decision.failure_class is None


def test_AC_TDG_5_test_present_with_other_glob_suffix_allows(
    tmp_path, gate_dev_mode_new_ac
) -> None:
    """Multiple test files matching the glob; ANY match suffices.
    Pattern is ``test_AC_O8_A1_*.py`` — both ``..._first.py`` and
    ``..._second.py`` qualify."""
    import tdd_guard as gate

    tests_dir = tmp_path / "framework" / "orchestrator" / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_AC_O8_A1_one_thing.py").write_text(
        "def test_AC_O8_A1_one():\n    pass\n", encoding="utf-8"
    )
    (tests_dir / "test_AC_O8_A1_other_thing.py").write_text(
        "def test_AC_O8_A1_other():\n    pass\n", encoding="utf-8"
    )

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Write",
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
    assert decision.decision == "allow"
