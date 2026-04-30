"""AC.OBG.6 — Gate is a no-op when workspace-mode is ``normal-use``.

Per the locked plan-doc §4 AC.OBG.6: given
``workspace_mode(workspace_root) == "normal-use"``: hook returns no
``permissionDecision`` and does not consult the active-scope sentinel
or the manifest table. The hook's wall-clock cost in this branch is
bounded by the mode-bit read alone (sub-10ms, matches A1's mode-bit
p95 envelope).
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
def gate_normal_use_with_tracking_calls(monkeypatch):
    """NORMAL USE: workspace_mode returns 'normal-use'. Track whether
    the sentinel reader or tracker open are called — they must NOT be."""
    sentinel_calls: list[Path] = []
    tracker_calls: list[Path] = []

    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "normal-use"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    def _track_sentinel(workspace_root):
        sentinel_calls.append(workspace_root)
        return None

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = _track_sentinel
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)

    import objective_binding_gate as gate

    def _track_tracker(workspace_root):
        tracker_calls.append(workspace_root)
        return None

    monkeypatch.setattr(gate, "_open_tracker", _track_tracker)
    return sentinel_calls, tracker_calls


def test_AC_OBG_6_normal_use_returns_no_op_without_consulting_substrate(
    tmp_path, gate_normal_use_with_tracking_calls
) -> None:
    """NORMAL USE → no-op. Sentinel + tracker NOT consulted in
    ``evaluate``."""
    import objective_binding_gate as gate

    sentinel_calls, tracker_calls = gate_normal_use_with_tracking_calls

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
    # Inside ``evaluate`` the mode-bit short circuit fires before
    # sentinel-read or tracker-open. (The audit-log path in ``main``
    # may consult the sentinel post-evaluate for logging shape; that
    # is the audit branch — AC.OBG.6 names ``evaluate``'s contract.)
    assert sentinel_calls == []
    assert tracker_calls == []


def test_AC_OBG_6_normal_use_non_carve_out_path_still_no_op(
    tmp_path, gate_normal_use_with_tracking_calls
) -> None:
    """NORMAL USE no-ops every path, regardless of whether it would
    have been carved out under DEV MODE."""
    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(tmp_path / "anywhere" / "really" / "x.py")
        },
    )
    assert decision.decision == "no-op"
