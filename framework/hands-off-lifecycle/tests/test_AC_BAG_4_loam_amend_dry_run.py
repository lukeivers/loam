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

"""AC.BAG.4 — Bash gate denies amendment-shape commit when
``loam amend apply --dry-run`` would fail (DEV-MODE-only).

Per the locked plan-doc §4 AC.BAG.4: given workspace-mode = ``dev-
mode``, given the ``tool_input.command`` matches a sealed-amendment
commit pattern (``git commit -m "(feat|fix|chore|seal)\\(<comp>\\)``):
the hook invokes ``loam amend apply --dry-run <manifest>``; on exit
≠ 0, hook returns ``permissionDecision: "deny"`` with reason that
includes the dry-run's stderr/stdout output + at least one repair
direction. NORMAL USE workspaces no-op this check.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path



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


def _stub_modules(monkeypatch, *, mode: str, sentinel):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: sentinel
    ass_mod.ActiveScopeSentinel = ActiveScopeSentinel
    ass_mod.ScopeBinding = ScopeBinding
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


def test_AC_BAG_4_amendment_shape_dry_run_failure_denies(
    tmp_path, monkeypatch
) -> None:
    """Amendment-shape commit + dry-run exit ≠ 0 → deny."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    import bash_guard

    # Stub the dry-run invocation to return a failure code.
    monkeypatch.setattr(
        bash_guard,
        "_loam_amend_dry_run",
        lambda _ws, _m: (1, "BASELINE pin failed"),
    )
    monkeypatch.setattr(
        bash_guard,
        "_candidate_manifest_paths",
        lambda _ws, _s: [tmp_path / "manifest.yaml"],
    )

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                'git commit -m "feat(hands-off-lifecycle): something"'
            )
        },
        env={},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "loam-amend-dry-run-failure"
    assert "AC.BAG.4" in decision.reason
    assert "BASELINE pin failed" in decision.reason
    assert "loam amend" in decision.reason


def test_AC_BAG_4_amendment_shape_dry_run_success_admitted(
    tmp_path, monkeypatch
) -> None:
    """Amendment-shape commit + dry-run exit = 0 → admitted."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    import bash_guard

    monkeypatch.setattr(
        bash_guard,
        "_loam_amend_dry_run",
        lambda _ws, _m: (0, "ok"),
    )
    monkeypatch.setattr(
        bash_guard,
        "_candidate_manifest_paths",
        lambda _ws, _s: [tmp_path / "manifest.yaml"],
    )

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                'git commit -m "fix(orchestrator): foo"'
            )
        },
        env={},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_4_non_amendment_commit_admitted(
    tmp_path, monkeypatch
) -> None:
    """git commit -m 'plain' (not amendment-shape) → no dry-run."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    import bash_guard

    invoked = []

    def fake_dry_run(ws, m):
        invoked.append(m)
        return (1, "shouldn't have been called")

    monkeypatch.setattr(bash_guard, "_loam_amend_dry_run", fake_dry_run)
    monkeypatch.setattr(
        bash_guard,
        "_candidate_manifest_paths",
        lambda _ws, _s: [tmp_path / "manifest.yaml"],
    )

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": "git commit -m 'plain message'"
        },
        env={},
    )
    assert decision.decision in ("allow", "no-op")
    assert not invoked, (
        "dry-run should not be invoked on non-amendment commits"
    )


def test_AC_BAG_4_normal_use_no_op(tmp_path, monkeypatch) -> None:
    """NORMAL USE + amendment-shape → no-op (DEV-MODE-only)."""
    _stub_modules(monkeypatch, mode="normal-use", sentinel=None)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                'git commit -m "feat(hands-off-lifecycle): X"'
            )
        },
        env={},
    )
    assert decision.decision == "no-op"


def test_AC_BAG_4_env_override_admits(tmp_path, monkeypatch) -> None:
    """POS_BASH_GUARD_ALLOW=1 admits AC.BAG.4 (DEV-MODE-only class)."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                'git commit -m "feat(hands-off-lifecycle): X"'
            )
        },
        env={"POS_BASH_GUARD_ALLOW": "1"},
    )
    # With override, no dry-run is invoked → admitted.
    assert decision.decision in ("allow", "no-op")
