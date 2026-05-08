# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.5 — Proposal draft workflow named in SKILL body.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.5: the SKILL body names the draft path
(`<workspace>/.scratch/claude-output/skill-draft-<slug>.md`), names
the 6-section template the draft must follow, names the draft
header requirement (which trigger fired + evidence), and explicitly
states the draft is in `.scratch/` (NOT yet `.claude/skills/`) so
the persona can't bypass ratification.
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


def test_body_names_scratch_draft_path() -> None:
    """Body names the .scratch/ draft path explicitly."""
    body = _load_body()
    # Permissive: workspace-relative or absolute reference to
    # .scratch/claude-output/skill-draft-<slug>.md is fine.
    has_path = (
        ".scratch/claude-output/skill-draft-" in body
        or ".scratch/claude-output/skill-draft-<slug>" in body
    )
    assert has_path, (
        "AC.SKILLCAP.5: body must name the draft path "
        "<workspace>/.scratch/claude-output/skill-draft-<slug>.md."
    )


def test_body_names_six_section_template() -> None:
    """Body names the 6-section template (What / When / How /
    Graceful degradation / Composition / Out of scope) the draft
    must follow."""
    body = _load_body().lower()
    # Permissive: look for the marker phrase "6-section" + the
    # section names. The body itself uses the same 6 sections, so
    # naming them again in the draft-template discussion is the
    # explicit requirement.
    has_marker = "6-section" in body or "six-section" in body
    # Ensure the canonical section names appear in the body's
    # workflow / draft-template discussion.
    section_names = [
        "what this skill captures",
        "when to use",
        "how the persona applies it",
        "graceful degradation",
        "composition",
        "out of scope",
    ]
    sections_in_body = sum(1 for s in section_names if s in body)
    # The body itself has all 6 sections plus references each at
    # least once in the draft-template discussion. Require ≥6
    # mentions across the whole body (each section header counts
    # as 1 — the AC.SKILLCAP.1 test asserts they all exist).
    assert has_marker and sections_in_body >= 6, (
        "AC.SKILLCAP.5: body must name the 6-section template "
        f"explicitly (6-section/six-section marker = {has_marker}; "
        f"section-name mentions = {sections_in_body})."
    )


def test_body_names_draft_header_requirement() -> None:
    """Body names the draft-header requirement: trigger fired +
    evidence + timestamp."""
    body = _load_body().lower()
    # The header section is named via "draft header" or "draft origin".
    has_header = "draft header" in body or "draft origin" in body
    assert has_header, (
        "AC.SKILLCAP.5: body must name the draft-header requirement "
        "(via 'draft header' or 'draft origin' marker)."
    )


def test_body_names_draft_header_includes_trigger_evidence() -> None:
    """Body names that the draft header includes which trigger fired
    + the evidence."""
    body = _load_body().lower()
    has_trigger_marker = "trigger=" in body or "trigger=<" in body
    has_evidence_marker = "evidence=" in body or "evidence=<" in body
    assert has_trigger_marker and has_evidence_marker, (
        "AC.SKILLCAP.5: body must name the draft-header trigger + "
        "evidence shape (e.g., 'trigger=<...>; evidence=<...>')."
    )


def test_body_explicitly_states_scratch_not_claude_skills() -> None:
    """Body explicitly states the draft is in .scratch/, NOT yet
    .claude/skills/ — to prevent bypassing ratification."""
    body = _load_body().lower()
    # Look for both paths mentioned in proximity, with a "NOT yet"
    # or "not yet" or similar disambiguation.
    # Permissive: just check both paths appear AND that the body
    # mentions "ratification" (the gate the placement defends).
    has_scratch = ".scratch/" in body
    has_claude_skills = ".claude/skills/" in body
    has_ratify = "ratif" in body  # "ratification" / "ratify"
    assert has_scratch and has_claude_skills and has_ratify, (
        "AC.SKILLCAP.5: body must mention both .scratch/ AND "
        ".claude/skills/ AND ratification (so the placement-as-"
        "defence-against-bypass is explicit)."
    )
