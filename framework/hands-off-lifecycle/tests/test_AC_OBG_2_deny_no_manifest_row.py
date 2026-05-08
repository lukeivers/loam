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

"""AC.OBG.2 — Refuse Edit when sentinel binds an AC with no manifest row.

Per the locked plan-doc §4 AC.OBG.2: given the sentinel is present,
given ``manifest_rows_for_ac(component, ac_id)`` returns ``[]`` for
every binding in the sentinel: hook returns ``permissionDecision:
"deny"`` with a reason that names the unregistered binding and at
least one repair direction (register the row via
``tracker.register_source_binding(...)``, or correct the sentinel to
a registered binding).
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
    """Stub ObjectiveTracker that returns no rows for any AC."""

    def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
        return []


@pytest.fixture
def gate_dev_mode_sentinel_no_rows(monkeypatch):
    """DEV MODE + sentinel binding (orchestrator, AC.X.1) + tracker
    returns no manifest rows."""
    sentinel = ActiveScopeSentinel(
        scope_id="test-scope",
        plan_path="docs/plans/test.md",
        bindings=(ScopeBinding(component="orchestrator", ac_id="AC.X.1"),),
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


def test_AC_OBG_2_sentinel_present_no_manifest_row_denies(
    tmp_path, gate_dev_mode_sentinel_no_rows
) -> None:
    """Sentinel binds (orchestrator, AC.X.1) but no manifest rows
    exist for that pair → deny with reason naming the binding +
    register_source_binding repair direction."""
    import objective_binding_gate as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "x.py"
            )
        },
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "no-manifest-row-for-binding"
    assert decision.reason is not None
    # Reason names the unregistered (component, ac_id).
    assert "orchestrator" in decision.reason
    assert "AC.X.1" in decision.reason
    # Reason names register_source_binding repair direction.
    assert "register_source_binding" in decision.reason
    # bound_acs surfaces the binding.
    assert decision.bound_acs == (("orchestrator", "AC.X.1"),)
