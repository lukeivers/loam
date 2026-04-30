"""AC.TDG.3 — Allow Edit when path is a test path (chicken-and-egg).

Per the locked plan-doc §4 AC.TDG.3: given ``tool_input.file_path``
matches ``framework/<comp>/tests/**``: hook returns no
``permissionDecision`` (allow). Test-tree edits bypass A3 regardless
of new-AC state — the test file IS the satisfaction surface, gating
its own creation creates a chicken-and-egg.
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


class _RaisingTracker:
    """Tracker stub that raises if consulted — proves the test-path
    short-circuit fires before the new-AC detection branch."""

    def manifest_rows_for_ac(self, *_args, **_kwargs):
        raise AssertionError(
            "AC.TDG.3 violated: test-path branch consulted tracker"
        )


@pytest.fixture
def gate_dev_mode_test_path(monkeypatch):
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

    import tdd_guard as gate

    monkeypatch.setattr(
        gate, "_open_tracker", lambda _: _RaisingTracker()
    )


def test_AC_TDG_3_test_tree_path_allows(
    tmp_path, gate_dev_mode_test_path
) -> None:
    """Edit on framework/<comp>/tests/<file> → allow.
    Tracker stub raises if consulted — reaching the allow proves the
    short-circuit."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Write",
        tool_input={
            "file_path": str(
                tmp_path
                / "framework"
                / "orchestrator"
                / "tests"
                / "test_AC_O8_A1_some_behaviour.py"
            )
        },
    )
    assert decision.decision == "allow"
    assert decision.reason is None
    assert decision.failure_class is None


def test_AC_TDG_3_test_tree_subdir_path_allows(
    tmp_path, gate_dev_mode_test_path
) -> None:
    """Tests can live in subdirectories under ``tests/`` (e.g.
    ``tests/integration/``); A3's carve-out admits the whole subtree."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path
                / "framework"
                / "orchestrator"
                / "tests"
                / "integration"
                / "test_something.py"
            )
        },
    )
    assert decision.decision == "allow"
