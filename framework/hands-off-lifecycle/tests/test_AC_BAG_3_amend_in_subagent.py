"""AC.BAG.3 — Bash gate denies ``git commit --amend`` in subagent
context (DEV-MODE-only).

Per the locked plan-doc §4 AC.BAG.3: given workspace-mode = ``dev-
mode``, given an active-scope sentinel is present (proxy for "this
is a subagent build context"), given the ``tool_input.command``
matches ``git commit\\s+(.*\\s+)?--amend`` (anywhere in the command,
including pipes/heredocs): hook returns ``permissionDecision: "deny"``
with reason naming the rule (``feedback_no_amend_in_agent_dispatches``),
the sentinel state, and at least one repair direction. NORMAL USE
workspaces no-op this check.
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


def _stub_modules(monkeypatch, *, mode: str, sentinel):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: sentinel
    ass_mod.ActiveScopeSentinel = ActiveScopeSentinel
    ass_mod.ScopeBinding = ScopeBinding
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


def _make_sentinel():
    return ActiveScopeSentinel(
        scope_id="amendment-72-build",
        plan_path="docs/rebuild/plans/structural-enforcement-a4-bash-and-agent-context-guards.md",
        bindings=(
            ScopeBinding(component="hands-off-lifecycle", ac_id="AC.BAG.3"),
        ),
        created_at="2026-04-28T12:00:00+00:00",
        session_id=None,
    )


def test_AC_BAG_3_amend_with_sentinel_denies(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=_make_sentinel())
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git commit --amend"},
        env={},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "amend-in-subagent"
    assert "AC.BAG.3" in decision.reason
    assert "amendment-72-build" in decision.reason
    assert (
        "corrective" in decision.reason.lower()
        or "new" in decision.reason.lower()
    )


def test_AC_BAG_3_amend_with_message_flag_denies(
    tmp_path, monkeypatch
) -> None:
    """git commit --amend -m '...' → deny (regex tolerates flag order)."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=_make_sentinel())
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": "git commit --amend -m 'fix message'"
        },
        env={},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "amend-in-subagent"


def test_AC_BAG_3_amend_no_sentinel_admitted(
    tmp_path, monkeypatch
) -> None:
    """DEV MODE + no sentinel → admitted (main-session amend)."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git commit --amend"},
        env={},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_3_normal_use_no_op(tmp_path, monkeypatch) -> None:
    """NORMAL USE + sentinel-present + amend → no-op (DEV-MODE-only)."""
    _stub_modules(
        monkeypatch, mode="normal-use", sentinel=_make_sentinel()
    )
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git commit --amend"},
        env={},
    )
    assert decision.decision == "no-op"


def test_AC_BAG_3_env_override_admits(tmp_path, monkeypatch) -> None:
    """POS_BASH_GUARD_ALLOW=1 admits the amend (DEV-MODE-only class)."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=_make_sentinel())
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git commit --amend"},
        env={"POS_BASH_GUARD_ALLOW": "1"},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_3_no_match_no_op(tmp_path, monkeypatch) -> None:
    """git commit (no --amend) → admitted."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=_make_sentinel())
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git commit -m 'normal'"},
        env={},
    )
    assert decision.decision in ("allow", "no-op")
