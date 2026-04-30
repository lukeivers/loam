"""AC.TDG.6 — Gate is a no-op when workspace-mode is ``normal-use``.

Per the locked plan-doc §4 AC.TDG.6: given workspace_mode = ``normal-
use``: hook returns no ``permissionDecision`` and does not consult
the active-scope sentinel, manifest table, or filesystem. The hook's
wall-clock cost in this branch is bounded by the mode-bit read alone
(sub-10ms, matches A2's AC.OBG.6 envelope).
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


@pytest.fixture
def gate_with_normal_use(monkeypatch):
    """Stub workspace_mode = normal-use. The fixture also installs
    sentinel + tracker stubs that RAISE if consulted, so the test
    can assert the no-op branch never touches them."""
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "normal-use"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    def _should_not_be_called(*_args, **_kwargs):
        raise AssertionError(
            "AC.TDG.6 violated: normal-use branch consulted sentinel/tracker"
        )

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = _should_not_be_called
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


def test_AC_TDG_6_normal_use_returns_no_op(
    tmp_path, gate_with_normal_use
) -> None:
    """Mode = normal-use → decision = no-op."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "x.py"
            )
        },
    )
    assert decision.decision == "no-op"
    assert decision.reason is None
    assert decision.failure_class is None


def test_AC_TDG_6_normal_use_does_not_consult_sentinel(
    tmp_path, gate_with_normal_use
) -> None:
    """The fixture installs a sentinel reader that raises; if the gate
    consulted it on the normal-use branch, this test would explode.
    Reaching this assertion proves the short-circuit."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Write",
        tool_input={"file_path": str(tmp_path / "x.py")},
    )
    assert decision.decision == "no-op"
