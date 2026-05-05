# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.13 — Self-contained SKILL body (component-level smoke).

Per ``docs/rebuild/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.13: the SKILL.md body is well-formed enough that the
persona reading it can apply the workflow without referring back
to the plan-doc — i.e., the SKILL is self-contained instruction.

This test asserts every named workflow step is present + named with
concrete file paths + named PM API calls + named ratification
semantics. The component-level smoke; release-level smoke at v0.2.0
SOFT gate (master plan §5).
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "skill-capture-proposal"
    / "SKILL.md"
)


def _load_body() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n.*?\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match
    return match.group(1)


def test_workflow_step_1_detect_and_draft_named() -> None:
    """Step 1 (detect + draft) is named with the .scratch/ draft path."""
    body = _load_body()
    has_step_1 = "step 1" in body.lower() or "Step 1 — Detect" in body
    has_scratch_path = ".scratch/claude-output/skill-draft-" in body
    assert has_step_1 and has_scratch_path, (
        "AC.SKILLCAP.13: Step 1 (detect + draft) must be named with "
        "concrete .scratch/claude-output/skill-draft- path."
    )


def test_workflow_step_2_audit_log_trigger_fire_named() -> None:
    """Step 2 (audit-log trigger fire) is named with the audit-log
    path + event-kind."""
    body = _load_body()
    has_step_2 = "step 2" in body.lower() or "Step 2 — Audit" in body
    has_path = ".loam/skill-capture/audit-log/" in body
    has_event = "skill_capture_trigger_fired" in body
    assert has_step_2 and has_path and has_event, (
        "AC.SKILLCAP.13: Step 2 (audit-log) must be named with "
        "audit-log path + skill_capture_trigger_fired event-kind."
    )


def test_workflow_step_3_pm_surface_named() -> None:
    """Step 3 (PM surface) is named with the PM API call."""
    body = _load_body()
    has_step_3 = "step 3" in body.lower() or "Step 3 — Surface" in body
    has_enqueue = "enqueue_decision" in body
    has_surface = "surface_next_questions_batch" in body
    assert has_step_3 and has_enqueue and has_surface, (
        "AC.SKILLCAP.13: Step 3 (PM surface) must be named with "
        "concrete enqueue_decision + surface_next_questions_batch."
    )


def test_workflow_step_4_ratify_named() -> None:
    """Step 4 (ratify Y/N/R) is named with each branch's behavior."""
    body = _load_body()
    has_step_4 = "step 4" in body.lower() or "Step 4 — Ratify" in body
    has_y_branch = "Y →" in body or "Y →" in body or "**Y →" in body
    has_n_branch = "N →" in body or "**N →" in body
    has_r_branch = "R →" in body or "**R →" in body
    assert has_step_4 and has_y_branch and has_n_branch and has_r_branch, (
        "AC.SKILLCAP.13: Step 4 (ratify) must be named with all "
        "three Y/N/R branches."
    )


def test_workflow_step_5_budget_and_hardcap_named() -> None:
    """Step 5 (budget + hard-cap) is named."""
    body = _load_body()
    has_step_5 = "step 5" in body.lower() or "Step 5 — Per-week" in body
    has_budget = "budget.yaml" in body
    has_hardcap = "hard-cap" in body.lower() or "20 SKILLs" in body or "20 workspace-local" in body
    assert has_step_5 and has_budget and has_hardcap, (
        "AC.SKILLCAP.13: Step 5 (budget + hard-cap) must be named "
        "with budget.yaml + hard-cap."
    )


def test_y_branch_targets_claude_skills_path() -> None:
    """The Y → branch concretely names the .claude/skills/ write
    target."""
    body = _load_body()
    # Search for Y → block + .claude/skills/ in proximity.
    # Permissive: both must appear in the body.
    has_y_marker = "Y →" in body
    has_target = ".claude/skills/" in body
    assert has_y_marker and has_target, (
        "AC.SKILLCAP.13: Y → branch must concretely name the "
        ".claude/skills/<slug>/SKILL.md write target."
    )


def test_skill_references_enable_flag_gate() -> None:
    """SKILL body explicitly names the enable_auto_skill_capture
    flag as the workflow-level gate."""
    body = _load_body()
    assert "enable_auto_skill_capture" in body, (
        "AC.SKILLCAP.13: body must name the "
        "enable_auto_skill_capture flag as the workflow-level gate."
    )
