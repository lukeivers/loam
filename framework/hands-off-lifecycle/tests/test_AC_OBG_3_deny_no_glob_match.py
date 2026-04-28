"""AC.OBG.3 — Refuse Edit when no manifest-row glob matches the path.

Per the locked plan-doc §4 AC.OBG.3: given the sentinel is present,
given the sentinel's bindings have at least one manifest row each,
given no row's ``source_path_glob`` ``fnmatch.fnmatchcase``-matches
``tool_input.file_path``: hook returns ``permissionDecision: "deny"``
with a reason that names the path, the bound ``(component, ac_id)``
pairs, and the globs each binds to.
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


class _FakeTracker:
    """Stub ObjectiveTracker returning a single row whose glob does
    NOT match ``framework/cost-governance/src/wiring.py``."""

    def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
        return [
            {
                "component": component,
                "ac_id": ac_id,
                "source_path_glob": "framework/orchestrator/src/**",
            }
        ]


@pytest.fixture
def gate_dev_mode_sentinel_with_row_no_match(monkeypatch):
    sentinel = ActiveScopeSentinel(
        scope_id="test-scope",
        plan_path="docs/rebuild/plans/test.md",
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

    import objective_binding_gate as gate

    monkeypatch.setattr(gate, "_open_tracker", lambda _: _FakeTracker())


def test_AC_OBG_3_glob_does_not_match_path_denies(
    tmp_path, gate_dev_mode_sentinel_with_row_no_match
) -> None:
    """Sentinel binds (orchestrator, AC.O8.A1) → manifest row globs
    ``framework/orchestrator/src/**``. Edit attempts
    ``framework/cost-governance/src/wiring.py`` → no glob match →
    deny."""
    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "cost-governance" / "src" / "wiring.py"
            )
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "no-glob-matches-path"
    assert decision.reason is not None
    # Reason names the path + bound (component, ac_id) + bound globs.
    assert "wiring.py" in decision.reason
    assert "orchestrator" in decision.reason
    assert "AC.O8.A1" in decision.reason
    assert "framework/orchestrator/src/**" in decision.reason
