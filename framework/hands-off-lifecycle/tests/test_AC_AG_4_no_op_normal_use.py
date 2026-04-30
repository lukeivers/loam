"""AC.AG.4 — Agent gate is no-op for non-targeted dispatches
(UNIVERSAL behaviour — applies regardless of mode for unmatched
dispatches).

Per the locked plan-doc §4 AC.AG.4: given a Task tool call whose
prompt matches no AC.AG.1..AC.AG.3 pattern (or workspace-mode is
``normal-use`` for DEV-MODE-only checks): hook returns no
``permissionDecision``.
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


def _stub_modules(monkeypatch, *, mode: str):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


def test_AC_AG_4_normal_use_short_circuit(
    tmp_path, monkeypatch
) -> None:
    """Mode = normal-use → no-op regardless of prompt content."""
    _stub_modules(monkeypatch, mode="normal-use")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={
            "prompt": (
                "Build amendment #51 in docs/rebuild/plans/foo.md. "
                + ("x" * 5000)
            )
        },
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"


@pytest.mark.parametrize(
    "prompt",
    [
        "Help me read this file.",
        "What's the syntax for a Python list comprehension?",
        "Find all occurrences of foo in the project.",
        "Run the test suite.",
    ],
)
def test_AC_AG_4_dev_mode_non_matching_prompt_admitted(
    tmp_path, monkeypatch, prompt
) -> None:
    """DEV MODE + non-matching prompt → admitted."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={"prompt": prompt},
        envelope_cwd=agent_guard.CANONICAL_LOAM_PATH,
    )
    assert decision.decision != "deny"


def test_AC_AG_4_non_task_tool_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={"prompt": "anything"},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"


def test_AC_AG_4_missing_prompt_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import agent_guard

    decision = agent_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Task",
        tool_input={},
        envelope_cwd=str(tmp_path),
    )
    assert decision.decision == "no-op"
