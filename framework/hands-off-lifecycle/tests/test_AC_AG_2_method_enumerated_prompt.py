"""AC.AG.2 — Agent gate denies method-enumerated prompt above length
threshold (DEV-MODE-only).

Per the locked plan-doc §4 AC.AG.2: given workspace-mode = ``dev-
mode``, given a Task tool call whose ``tool_input.prompt`` length
exceeds **2500 characters**: hook returns ``permissionDecision:
"deny"`` with reason naming the rule
(``feedback_agent_prompts_scope_only`` — scope-only-dispatch CDC),
the prompt length, and at least one repair direction. NORMAL USE
workspaces no-op this check.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


def _stub_modules(monkeypatch, *, mode: str):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


def test_AC_AG_2_threshold_named_2500(tmp_path) -> None:
    """The threshold value is NAMED in the AC; not method per ODD §7.4.

    Verifies the constant exposed by the module matches the plan-doc."""
    import agent_guard

    assert agent_guard.PROMPT_LENGTH_THRESHOLD == 2500


def test_AC_AG_2_long_prompt_denies(tmp_path, monkeypatch) -> None:
    """Prompt length > 2500 → deny."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    long_prompt = "a" * 2501
    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": long_prompt},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "method-enumerated-prompt"
    assert "AC.AG.2" in decision.reason
    assert "2500" in decision.reason
    assert "2501" in decision.reason


def test_AC_AG_2_at_threshold_admitted(tmp_path, monkeypatch) -> None:
    """Exactly 2500 chars → admitted (threshold is exclusive)."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "a" * 2500},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_AG_2_short_prompt_admitted(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "Find the bug in this file."},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_AG_2_normal_use_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="normal-use")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "a" * 5000},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"


def test_AC_AG_2_reason_names_repair_direction(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": "x" * 3000},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision == "deny"
    # Repair direction names plan-doc / extraction.
    assert (
        "plan-doc" in decision.reason.lower()
        or "scope" in decision.reason.lower()
        or "extract" in decision.reason.lower()
    )
