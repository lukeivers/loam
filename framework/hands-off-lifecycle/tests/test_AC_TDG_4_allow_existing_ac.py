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

"""AC.TDG.4 — Allow Edit when AC is NOT new (existing AC, in-AC mod).

Per the locked plan-doc §4 AC.TDG.4: given the sentinel binds
``(X, Y)``, given every manifest row for ``(X, Y)`` has
``created_at`` strictly BEFORE the sentinel's ``created_at`` (no row
was registered after the sentinel was authored): hook returns no
``permissionDecision``. Per D2 lock, A3 does not gate in-AC
modifications.
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


class _ExistingAcTracker:
    """Stub returning a manifest row whose created_at is strictly
    BEFORE the sentinel's created_at (i.e. the AC pre-existed)."""

    def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
        return [
            {
                "component": component,
                "ac_id": ac_id,
                "source_path_glob": "framework/orchestrator/src/**",
                # Sentinel created_at fixture below is 2026-04-28T12...;
                # this row pre-dates by a day.
                "created_at": "2026-04-27T00:00:00+00:00",
            }
        ]


@pytest.fixture
def gate_dev_mode_existing_ac(monkeypatch):
    sentinel = ActiveScopeSentinel(
        scope_id="test-scope",
        plan_path="docs/plans/test.md",
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

    monkeypatch.setattr(gate, "_open_tracker", lambda _: _ExistingAcTracker())


def test_AC_TDG_4_existing_ac_allows(
    tmp_path, gate_dev_mode_existing_ac
) -> None:
    """Sentinel created_at is 2026-04-28; manifest row created_at is
    2026-04-27 — strictly before. AC is NOT new in this diff. A3
    allows regardless of whether a test exists."""
    import tdd_guard as gate

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


def test_AC_TDG_4_existing_ac_allows_even_without_test(
    tmp_path, gate_dev_mode_existing_ac
) -> None:
    """Even when no test file exists for the existing AC, A3 allows —
    in-AC modifications are out of A3's scope per D2."""
    import tdd_guard as gate

    # No tests directory exists at all in tmp_path; gate must still
    # allow because the AC isn't new.
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
    assert decision.decision == "allow"
