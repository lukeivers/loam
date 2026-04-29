"""AC.AG.1 — Agent gate denies wrong-WD dispatch (DEV-MODE-only).

Per the locked plan-doc §4 AC.AG.1: given workspace-mode = ``dev-
mode``, given a Task tool call whose ``tool_input.prompt`` mentions
loam surfaces (the prompt contains at least one of:
``docs/rebuild/``, ``framework/<comp>/src/`` or
``framework/<comp>/tests/`` patterns, the literal ``loam amend``
(post-M1g rename of pre-M1g ``pos-amend``),
the literal "seal commit", the literal canonical path
``/Users/lukeivers/ivers-corp-pos-v2/``, OR an amendment-shape
pattern ``amendment #\\d+``), given the envelope's top-level ``cwd``
does NOT match the canonical pos-v2 path: hook returns
``permissionDecision: "deny"`` with reason naming (a) the detected
pos-v2 surface mentions, (b) the wrong cwd, (c) the canonical path
the dispatch should target, (d) at least one repair direction.
NORMAL USE workspaces no-op this check.
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


def test_AC_AG_1_pos_v2_surface_wrong_cwd_denies(
    tmp_path, monkeypatch
) -> None:
    """Prompt mentions docs/rebuild/ + cwd is non-canonical → deny."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": (
                "Please update docs/rebuild/plans/foo.md and "
                "register the AC."
            ),
            "subagent_type": "general-purpose",
        },
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "wrong-wd"
    assert "AC.AG.1" in decision.reason
    assert "docs/rebuild/" in decision.reason
    assert "/Users/lukeivers/ivers-corp-pos-v2" in decision.reason


def test_AC_AG_1_amendment_mention_wrong_cwd_denies(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": "Build amendment #99 per the plan.",
        },
        envelope_cwd=str(tmp_path / "wrong"),
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "wrong-wd"


def test_AC_AG_1_loam_amend_mention_wrong_cwd_denies(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": "Run loam amend apply --dry-run on the manifest.",
        },
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "wrong-wd"


def test_AC_AG_1_pos_v2_surface_canonical_cwd_admitted(
    tmp_path, monkeypatch
) -> None:
    """Pos-v2 mentions + canonical cwd → admitted."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    # Canonical path resolution — use the actual canonical path.
    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": "Update docs/rebuild/plans/foo.md.",
        },
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    # Allowed because cwd matches canonical.
    assert decision.decision in ("allow", "no-op")


def test_AC_AG_1_no_pos_v2_mention_admitted(
    tmp_path, monkeypatch
) -> None:
    """No pos-v2 surface mentions in prompt → admitted regardless of cwd."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": "Search for occurrences of the word 'foo'.",
        },
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_AG_1_normal_use_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="normal-use")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": "Update docs/rebuild/plans/foo.md.",
        },
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"


def test_AC_AG_1_non_task_tool_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "prompt": "Update docs/rebuild/plans/foo.md.",
        },
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"
