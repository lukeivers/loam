# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.S — outcome-altitude end-to-end test for closed-loop
engagement.

Per amendment #144 plan §4 (AC.CLE.S outcome-altitude: true): a
synthetic end-to-end test scaffolds a fresh workspace against a
plugins/ tree shipping handsoff-loop, writes settings.json with the
generalised UserPromptSubmit chain (persona + intent-classifier),
simulates a soft user prompt arriving via the UserPromptSubmit hook
JSON envelope, invokes the intent-classifier subprocess, verifies the
resulting ``additionalContext`` would inject the closed-loop directive
into the persona's context AND the ``handsoff-loop`` SKILL is
discoverable from the scaffolded ``.claude/skills/``.

Prime-objective ladder (per
``feedback_value_proposition_as_prime_objective`` +
``feedback_test_outcome_altitude_required``): AC.PO.1 + AC.PO.2 in
VALUE_PROPOSITION.md depend on non-tech users being able to invoke
loam's full power via plain language. This test is the structural
verification that the full path engages on a fresh workspace.

Outcome-altitude rules (per
``feedback_test_outcome_altitude_required``): the test invokes the
production entry-point (``python -m loam.primary_persona.cli
intent-classifier``) with no pre-arranged classifier-output state —
the classifier runs against a real soft prompt; the discovery walk
runs against a real symlinked SKILL.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from loam.workspace_bootstrap.workspace_cli import rescaffold_skills


_HANDSOFF_SKILL_BODY = """---
name: handsoff-loop
description: When the user wants a buildable artifact AND wants evidence it works (build-with-verification intent), invoke this closed-loop methodology.
---

# handsoff-loop

Closed-loop build methodology: intake -> approval -> decompose ->
dispatch -> judge. This SKILL is the destination for the
build-with-verification intent classifier's additionalContext
injection.
"""

_USER_SOFT_PROMPT = "I want a tool that converts X to Y. show me it works"


def _author_handsoff_plugin(plugins_root: Path) -> None:
    plugin_dir = plugins_root / "loam-skills"
    skills_dir = plugin_dir / "skills"
    handsoff_dir = skills_dir / "handsoff-loop"
    handsoff_dir.mkdir(parents=True)
    (handsoff_dir / "SKILL.md").write_text(
        _HANDSOFF_SKILL_BODY, encoding="utf-8"
    )


def test_AC_CLE_S_closed_loop_engagement_path_engages_end_to_end(
    tmp_path: Path,
) -> None:
    """End-to-end: a synthetic fresh workspace with handsoff-loop
    plugin-shipped, the intent-classifier subprocess invoked against
    a soft user prompt, the resulting additionalContext referencing
    handsoff-loop, AND the SKILL discoverable from .claude/skills/.

    Single test (n=1 architectural verification per
    ``feedback_n1_architectural_vs_n3_statistical``) — the question
    is "does the intervention work AT ALL on the target failure
    mode?", and the load-bearing case is the build-with-verification
    intent on a fresh workspace."""
    # ---- (1) Scaffold the fresh workspace ----
    workspace = tmp_path / "fresh-workspace"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _author_handsoff_plugin(plugins)

    # Rescaffold registers the plugin SKILLs (the rescaffold + fresh-
    # scaffold paths share the underlying ``_symlink_plugin_skills``
    # primitive — exercising rescaffold here doubles as a fresh-
    # scaffold smoke).
    rescaffold_skills(workspace)

    # ---- (2) Verify handsoff-loop SKILL is discoverable ----
    workspace_handsoff_skill_md = (
        workspace / ".claude" / "skills" / "handsoff-loop" / "SKILL.md"
    )
    assert workspace_handsoff_skill_md.is_file(), (
        f"handsoff-loop SKILL.md not discoverable in fresh workspace "
        f"at {workspace_handsoff_skill_md}; closed-loop engagement is "
        f"impossible without the SKILL — AC.CLE.S RED."
    )

    # ---- (3) Simulate the UserPromptSubmit hook envelope ----
    # Claude Code passes a JSON envelope to the UserPromptSubmit hook
    # via stdin. The envelope carries the user's prompt + session
    # metadata. We invoke the intent-classifier subprocess (the same
    # entry-point Claude Code invokes via the settings.json hook
    # chain) and inspect its stdout.
    envelope = {
        "prompt": _USER_SOFT_PROMPT,
        "session_id": "test-outcome-altitude-session",
        "cwd": str(workspace),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "loam.primary_persona.cli",
            "intent-classifier",
        ],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
        cwd=str(workspace),
    )
    assert result.returncode == 0, (
        f"intent-classifier subprocess exited non-zero "
        f"(stderr: {result.stderr!r}); the hook chain would break on "
        f"this prompt — AC.CLE.S RED."
    )
    assert result.stdout.strip(), (
        f"intent-classifier emitted no additionalContext for a soft "
        f"build-with-verification prompt — the closed-loop directive "
        f"would never reach the persona's context. AC.CLE.S RED."
    )

    # ---- (4) Verify the additionalContext routes to handsoff-loop ----
    hook_output = json.loads(result.stdout)
    assert hook_output["hookEventName"] == "UserPromptSubmit"
    additional_context = hook_output["hookSpecificOutput"]["additionalContext"]
    assert "handsoff-loop" in additional_context, (
        "additionalContext does NOT reference handsoff-loop — Claude "
        "Code's SKILL matcher has nothing to bind to. AC.CLE.S RED."
    )

    # ---- (5) Verify the hook's prescription matches Scope B ruling ---
    # Per TG 11881 ruling, the hook MUST NOT prescribe verbatim slash-
    # command typing. The reconciled prescription says auto-load is
    # the primary mechanism. This is the AC.CLE.RECONCILE.1 substance
    # at the structural-enforcement layer.
    additional_context_lower = additional_context.lower()
    assert "auto-load" in additional_context_lower, (
        "additionalContext missing auto-load reference — Scope B's "
        "reconciliation broke at the hook layer. AC.CLE.S RED."
    )
    assert "no slash command typing is required" in additional_context_lower, (
        "additionalContext missing the explicit no-slash-typing "
        "prescription — TG 11881 ruling not surfaced. AC.CLE.S RED."
    )
    assert "do not build inline" in additional_context_lower, (
        "additionalContext missing the inline-build prohibition — "
        "the structural backstop is incomplete. AC.CLE.S RED."
    )

    # ---- (6) The closed-loop engagement path is now wired end-to-end ----
    # The intent classifier fired on a soft prompt → emitted
    # additionalContext naming handsoff-loop + auto-load + no-slash-
    # typing → the handsoff-loop SKILL is discoverable on disk for
    # Claude Code's matcher. Non-tech users in fresh workspaces can
    # engage the closed-loop methodology without knowing or typing
    # any slash command. AC.CLE.S GREEN.
