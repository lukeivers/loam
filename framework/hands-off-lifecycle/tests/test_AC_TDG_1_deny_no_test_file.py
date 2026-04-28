"""AC.TDG.1 — Refuse Edit on sealed-component non-test source for a
NEW AC with no matching test file (DEV MODE).

Per the locked plan-doc §4 AC.TDG.1: given workspace-mode = ``dev-
mode``, given A2's gate admitted the path, given
``tool_input.file_path`` is under ``framework/<X>/`` but NOT under
``framework/<X>/tests/``, given the active-scope sentinel binds
``(X, Y)``, given at least one manifest row for ``(X, Y)`` has
``created_at`` strictly after the sentinel's ``created_at`` (the AC
is "new in this diff"), given no file matching
``framework/<X>/tests/test_AC_<Y-normalised>_*.py`` exists: hook
returns ``hookSpecificOutput.permissionDecision: "deny"`` with a
``permissionDecisionReason`` that names (a) the source path,
(b) the new AC ``(X, Y)``, (c) the expected test path glob, (d) at
least one repair direction.
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
    """Stub returning a row whose created_at is AFTER the sentinel's —
    the AC is NEW in this diff."""

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
        # 1 hour BEFORE manifest row's created_at — AC is new.
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


def test_AC_TDG_1_no_test_file_denies(
    tmp_path, gate_dev_mode_new_ac
) -> None:
    """New AC bound by sentinel; no test file at expected glob → deny."""
    import tdd_guard as gate

    # No tests/ directory created — file does not exist.
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
    assert decision.failure_class == "missing-test-file"
    assert decision.reason is not None
    # Reason names (a) source path, (b) AC, (c) expected test glob,
    # (d) at least one repair direction.
    assert "orchestrator.py" in decision.reason
    assert "AC.O8.A1" in decision.reason or "O8_A1" in decision.reason
    assert "test_AC_O8_A1_" in decision.reason
    assert (
        "author the test" in decision.reason.lower()
        or "halt" in decision.reason.lower()
    )


def test_AC_TDG_1_write_tool_also_denies(
    tmp_path, gate_dev_mode_new_ac
) -> None:
    """Tool=Write, same condition → also denies."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Write",
        tool_input={
            "file_path": str(
                tmp_path
                / "framework"
                / "orchestrator"
                / "src"
                / "y.py"
            )
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-test-file"


def test_AC_TDG_1_multiedit_tool_also_denies(
    tmp_path, gate_dev_mode_new_ac
) -> None:
    """Tool=MultiEdit, same condition → also denies."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="MultiEdit",
        tool_input={
            "file_path": str(
                tmp_path
                / "framework"
                / "orchestrator"
                / "src"
                / "z.py"
            ),
            "edits": [
                {"old_string": "a", "new_string": "b"},
            ],
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-test-file"
