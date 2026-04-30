"""AC.OBG.4 — Allow Edit when path matches at least one bound
manifest-row glob.

Per the locked plan-doc §4 AC.OBG.4: given the sentinel is present,
given at least one manifest row whose ``(component, ac_id)`` matches
a sentinel binding has a ``source_path_glob`` that
``fnmatch.fnmatchcase``-matches ``tool_input.file_path``: hook
returns no ``permissionDecision`` (default-allow) OR explicit
``permissionDecision: "allow"``. The model proceeds with the edit.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


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


class _FakeTracker:
    """Stub ObjectiveTracker returning a row whose glob matches."""

    def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
        return [
            {
                "component": component,
                "ac_id": ac_id,
                "source_path_glob": "framework/orchestrator/src/**",
            }
        ]


@pytest.fixture
def gate_dev_mode_sentinel_with_matching_row(monkeypatch):
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


def test_AC_OBG_4_glob_matches_path_allows(
    tmp_path, gate_dev_mode_sentinel_with_matching_row
) -> None:
    """Sentinel binds (orchestrator, AC.O8.A1) → manifest row glob
    ``framework/orchestrator/src/**``. Edit attempts
    ``framework/orchestrator/src/orchestrator.py`` → glob matches →
    allow."""
    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "orchestrator.py"
            )
        },
    )
    assert decision.decision == "allow"
    assert decision.reason is None
    assert decision.failure_class is None
