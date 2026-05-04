"""AC.LSK.3 — body content shape.

Per sub-plan §5 AC.LSK.3, each SKILL.md body:

1. Has at least one `## ` header section.
2. Carries a "When to use" or equivalent description-mirror naming
   the trigger.
3. References a named loam pattern (CLAUDE.md, F3, ODD, M-FBM,
   FIDRAFT, or equivalent) so the pattern's provenance is
   traceable.
4. Includes a "Composition" or "Out of scope" section naming the
   boundary (graceful-degradation for raw Claude Code).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

EXPECTED_SKILLS = [
    # v0.1.3 bundle.
    "memory-recall",
    "scope-decompose",
    "dispatch-with-gates",
    "onboarding-conversation",
    "session-handoff",
    # v0.1.6 Cycle 2 additions.
    "translation-discipline",
    "audit-block-on-telegram",
    "owner-decision-summary",
]

# Required body section markers (case-insensitive substring match).
REQUIRED_SECTIONS = (
    "## what this skill captures",
    "## when to use",
    "## how the persona applies it",
    "## graceful degradation",
    "## composition",
    "## out of scope",
)

# At least one of these named loam patterns must appear in each
# body — establishes provenance per AC.LSK.3 #3.
LOAM_PATTERN_MARKERS = (
    "CLAUDE.md",
    "F3",
    "F4",
    "ODD",
    "M-FBM",
    "M5",
    "FIDRAFT",
    "Lens 1",
    "Lens 2",
    "Lens 3",
    "loam",
)


def _load_body(skill_name: str) -> str:
    path = SKILLS_DIR / skill_name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n.*?\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"{path}: cannot extract body"
    return match.group(1)


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_body_has_required_sections(skill_name: str) -> None:
    """Each SKILL.md body has the standard section shape that
    matches the existing flat-skill convention plus the new
    graceful-degradation section."""
    body_lower = _load_body(skill_name).lower()
    missing = [
        section for section in REQUIRED_SECTIONS
        if section not in body_lower
    ]
    assert not missing, (
        f"{skill_name}: missing required sections {missing}. "
        f"Required: {REQUIRED_SECTIONS}."
    )


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_body_references_loam_pattern(skill_name: str) -> None:
    """Per AC.LSK.3 #3: body must reference at least one named
    loam pattern so the provenance is traceable. Strangers running
    raw Claude Code see what loam concept the skill captures."""
    body = _load_body(skill_name)
    found = [marker for marker in LOAM_PATTERN_MARKERS if marker in body]
    assert found, (
        f"{skill_name}: body must reference at least one named "
        f"loam pattern from {LOAM_PATTERN_MARKERS}."
    )


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_graceful_degradation_names_raw_claude_code(
    skill_name: str,
) -> None:
    """Per AC.LSK.3 #4: the graceful-degradation section names the
    raw-Claude-Code path — strangers without loam should know what
    to do."""
    body_lower = _load_body(skill_name).lower()
    # Find the graceful-degradation section + read until the next
    # `## ` header.
    match = re.search(
        r"## graceful degradation\s*\n(.*?)(?=\n## |\Z)",
        body_lower,
        re.DOTALL,
    )
    assert match, (
        f"{skill_name}: graceful degradation section missing or "
        "cannot be parsed."
    )
    section = match.group(1)
    assert "claude code" in section or "raw claude" in section, (
        f"{skill_name}: graceful degradation section must name the "
        "raw-Claude-Code path explicitly."
    )
