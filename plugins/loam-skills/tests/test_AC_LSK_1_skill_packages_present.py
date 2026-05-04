"""AC.LSK.1 — five SKILL.md packages present and well-formed.

Per sub-plan §5 AC.LSK.1: five SKILL.md files exist at the
canonical paths. Each file: starts with valid YAML frontmatter
delimited by `---` lines; frontmatter parses without error and is
a mapping; carries a non-empty `description` field (string,
≤1536 chars per Anthropic's combined-cap); body (post-frontmatter)
is non-empty markdown.

Anthropic SKILL.md schema reference:
https://code.claude.com/docs/en/skills
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

import pytest


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

EXPECTED_SKILLS = [
    "memory-recall",
    "scope-decompose",
    "dispatch-with-gates",
    "onboarding-conversation",
    "session-handoff",
]

# Anthropic-published cap per
# https://code.claude.com/docs/en/skills (frontmatter reference):
# the combined description + when_to_use text is truncated at
# 1,536 characters in the skill listing.
DESCRIPTION_MAX_CHARS = 1536


def _load_skill(skill_name: str) -> tuple[dict, str]:
    """Read SKILL.md, split frontmatter + body, parse frontmatter."""
    path = SKILLS_DIR / skill_name / "SKILL.md"
    assert path.is_file(), (
        f"expected SKILL.md at {path}; AC.LSK.1 requires the file "
        "exists at the canonical path."
    )
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{path}: SKILL.md must start with YAML frontmatter "
        "delimited by `---` lines."
    )
    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return frontmatter, body


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_skill_file_exists_with_frontmatter_and_body(
    skill_name: str,
) -> None:
    """Per-skill: file exists; frontmatter parses as mapping;
    description present + non-empty + ≤1536 chars; body non-empty."""
    frontmatter, body = _load_skill(skill_name)

    # Frontmatter is a mapping.
    assert isinstance(frontmatter, dict), (
        f"{skill_name}: frontmatter must parse as a YAML mapping."
    )

    # Description present, non-empty, within combined-cap.
    description = frontmatter.get("description")
    assert isinstance(description, str), (
        f"{skill_name}: `description` field is required + a string."
    )
    assert description.strip(), (
        f"{skill_name}: `description` must be non-empty."
    )
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        f"{skill_name}: `description` is {len(description)} chars; "
        f"Anthropic schema caps combined description at "
        f"{DESCRIPTION_MAX_CHARS}."
    )

    # Body (post-frontmatter) is non-empty.
    assert body.strip(), (
        f"{skill_name}: SKILL.md body (post-frontmatter) must be "
        "non-empty markdown."
    )


def test_all_five_skills_discovered() -> None:
    """Cross-check: walking the skills/ directory yields exactly
    the five expected packages — no orphans, no misnames."""
    on_disk = sorted(
        p.name for p in SKILLS_DIR.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )
    assert on_disk == sorted(EXPECTED_SKILLS), (
        f"discovered skills {on_disk} != expected {sorted(EXPECTED_SKILLS)}; "
        "AC.LSK.1 requires exactly the named five packages."
    )
