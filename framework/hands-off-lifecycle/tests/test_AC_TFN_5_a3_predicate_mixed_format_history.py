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

"""AC.TFN.5 — A3 predicate works on mixed-format manifest history.

Per the locked plan-doc §4 AC.TFN.5: when the manifest column
contains a mix of pre-fix β-format rows (microsecond ``+00:00``) and
post-fix γ-format rows (microsecond ``Z``), AND the active-scope
sentinel is post-fix γ-format, A3's
``manifest_row.created_at > sentinel.created_at`` lex-predicate
produces the correct verdict for every (row, sentinel) pair where
the sentinel was written AFTER the fix landed.

Outcome: workspaces upgrading across the fix boundary do not regress
A3.

Rationale (plan §9 Risk #2): post-fix sentinel γ has suffix ``Z``
(0x5A); pre-fix manifest β has suffix ``+`` (0x2B). γ > β at the
suffix byte, so any manifest row from BEFORE the fix lex-sorts
BEFORE a post-fix sentinel, regardless of wall-clock time. That is
the CORRECT verdict — the row was registered before the sentinel
was written, so the AC is not new in this diff (A3 allows).

A post-fix γ-format manifest row written AFTER the post-fix sentinel
lex-sorts AFTER the sentinel — the correct verdict for a new AC.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
# Post-M6b.0: gate-hook source files MOVED to plugins/dev-sdlc/hooks/.
# Add plugin's hooks dir to sys.path so test imports resolve to the
# moved gate modules. _gate_helpers.py STAYS at canonical HOOKS_DIR.
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))
if PLUGIN_HOOKS_DIR.exists() and str(PLUGIN_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


from active_scope_sentinel import ActiveScopeSentinel, ScopeBinding  # noqa: E402


class _MixedHistoryTracker:
    """Tracker carrying TWO rows: one pre-fix (β-format, registered
    before the sentinel was written) and one post-fix (γ-format,
    registered after). The post-fix row is the "new in this diff"
    signal; the pre-fix row is the "existing AC" signal."""

    def __init__(self, pre_fix_created_at: str, post_fix_created_at: str) -> None:
        self._rows = [
            {
                "component": "orchestrator",
                "ac_id": "AC.MIX.1",
                "source_path_glob": "framework/orchestrator/src/old.py",
                "created_at": pre_fix_created_at,
            },
            {
                "component": "orchestrator",
                "ac_id": "AC.MIX.1",
                "source_path_glob": "framework/orchestrator/src/new.py",
                "created_at": post_fix_created_at,
            },
        ]

    def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
        return [
            r for r in self._rows
            if r["component"] == component and r["ac_id"] == ac_id
        ]


@pytest.fixture
def gate_dev_mode_mixed_history(monkeypatch):
    """Wire A3 with: post-fix γ sentinel + a mixed-history tracker.
    The sentinel ``created_at`` falls BETWEEN the two manifest rows
    by wall-clock time, but the lex-compare needs to give the right
    verdict in both cases.
    """
    # Sentinel γ-format. Wall-clock instant ``T+5``.
    sentinel = ActiveScopeSentinel(
        scope_id="test-scope-mix",
        plan_path="docs/plans/test.md",
        bindings=(
            ScopeBinding(component="orchestrator", ac_id="AC.MIX.1"),
        ),
        created_at="2026-04-28T12:00:05.000000Z",  # γ-format
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

    # Pre-fix β-format row. Wall-clock instant ``T+0`` — earlier
    # than the sentinel.
    pre_fix = "2026-04-28T12:00:00.000000+00:00"
    # Post-fix γ-format row. Wall-clock instant ``T+10`` — later
    # than the sentinel.
    post_fix = "2026-04-28T12:00:10.000000Z"

    tracker = _MixedHistoryTracker(pre_fix, post_fix)
    import tdd_guard as gate

    monkeypatch.setattr(gate, "_open_tracker", lambda _: tracker)
    return tracker


def test_AC_TFN_5_post_fix_row_recognised_as_new_ac(
    tmp_path, gate_dev_mode_mixed_history
):
    """Editing a path matching the POST-FIX manifest row's glob: A3
    sees ``manifest > sentinel`` (γ > γ at later wall-clock) and
    treats the AC as new. With no test file, A3 must DENY (the
    AC is new and unbacked)."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "new.py"
            )
        },
    )
    # The AC IS new (post-fix row > sentinel lex-compare). With no
    # test backing it, A3 denies per AC.TDG.1.
    assert decision.decision == "deny"


def test_AC_TFN_5_pre_fix_row_alone_does_not_flip_predicate(
    tmp_path, gate_dev_mode_mixed_history
):
    """Editing a path matching ONLY the pre-fix β-format row's glob:
    the post-fix γ row also exists for this AC, so A3 STILL marks
    the AC as new. This is correct — the AC was extended after the
    sentinel was written."""
    import tdd_guard as gate

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "old.py"
            )
        },
    )
    # The AC is "new" (one of its rows post-dates the sentinel) but
    # the path matches a row that was registered BEFORE the
    # sentinel — so this Edit isn't admitted by a new-AC row.
    # Per A3's AC.TDG.4 partition logic: not admitted by a new-AC
    # row → allow.
    assert decision.decision == "allow"


def test_AC_TFN_5_pre_fix_only_history_treats_ac_as_existing(
    tmp_path, monkeypatch
):
    """If the entire manifest history is pre-fix β-format AND the
    sentinel is post-fix γ-format: every manifest row lex-sorts
    BEFORE the sentinel (β's ``+`` < γ's ``Z`` at the suffix byte
    when the seconds + microseconds are equal; AND for any β row
    written before the sentinel by wall-clock, the seconds field
    already orders correctly). A3 treats every AC as existing →
    allow.

    Wall-clock-equal β vs γ: ``2026-04-28T12:00:05.000000+00:00``
    (β) vs ``2026-04-28T12:00:05.000000Z`` (γ). Lex-compare flips
    on the suffix byte — β's ``+`` (0x2B) < γ's ``Z`` (0x5A) — so
    β < γ, i.e. row < sentinel. A3 sees no new-AC rows. Allow.
    """
    sentinel = ActiveScopeSentinel(
        scope_id="test-scope-prefix-only",
        plan_path="docs/plans/test.md",
        bindings=(
            ScopeBinding(component="orchestrator", ac_id="AC.MIX.2"),
        ),
        created_at="2026-04-28T12:00:05.000000Z",
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

    class _PreFixOnlyTracker:
        def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
            return [
                {
                    "component": component,
                    "ac_id": ac_id,
                    "source_path_glob": "framework/orchestrator/src/old.py",
                    # β-format, same wall-clock instant as sentinel.
                    "created_at": "2026-04-28T12:00:05.000000+00:00",
                },
            ]

    import tdd_guard as gate
    monkeypatch.setattr(gate, "_open_tracker", lambda _: _PreFixOnlyTracker())

    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "orchestrator" / "src" / "old.py"
            )
        },
    )
    # Pre-fix row lex-sorts before post-fix sentinel; AC treated as
    # existing; A3 allows.
    assert decision.decision == "allow"
