"""AC.LSK.1 — SKILL.md packages present and well-formed.

Per amendment #146 (loam-skills-ac-lsk1-root-cause), the SKILL set
checked here is derived from disk via `discover_skill_packages` —
every subdirectory of plugins/loam-skills/skills/ containing a
SKILL.md file. The previous hardcoded EXPECTED_SKILLS list +
count-pinning + all-skills-discovered cross-check were the
enumeration-trap surface (corpus grows but list didn't); the
derive-from-disk pattern eliminates that defect class at root cause.

Per-skill well-formedness assertions (per AC.LSK.1's four numbered
criteria as tightened by AC.LSK1RC.AC1 in
docs/plans/sealed/v0-1-3-skill-packages.md):

1. Starts with valid YAML frontmatter delimited by `---` lines.
2. Frontmatter parses without error and is a mapping.
3. Carries a non-empty `description` field (string, ≤1536 chars per
   Anthropic's combined-cap).
4. Body (post-frontmatter) is non-empty markdown.

Anthropic SKILL.md schema reference:
https://code.claude.com/docs/en/skills
"""

from __future__ import annotations

import yaml

import pytest

from conftest import (
    discover_skill_packages,
    load_skill_text,
    split_frontmatter_and_body,
)


# Anthropic-published cap per
# https://code.claude.com/docs/en/skills (frontmatter reference):
# the combined description + when_to_use text is truncated at
# 1,536 characters in the skill listing.
DESCRIPTION_MAX_CHARS = 1536


# Discovery happens at module-import time so pytest can parametrize.
# `discover_skill_packages` is the production-altitude discovery
# entry-point (per amendment #146). A test failure points at the
# specific skill_name from the discovered set.
DISCOVERED_SKILLS = discover_skill_packages()


def test_at_least_one_skill_discovered() -> None:
    """AC.LSK.1 baseline: there is at least one well-formed SKILL.md
    package on disk. Guards against the SKILLS_DIR pointing at a
    nonexistent or empty tree (in which case parametrized tests
    silently zero out — that's its own defect surface)."""
    assert DISCOVERED_SKILLS, (
        "no SKILL.md packages discovered under "
        "plugins/loam-skills/skills/; AC.LSK.1 requires at least one "
        "well-formed package on disk. Check that the directory "
        "exists and contains subdirectories with SKILL.md files."
    )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_skill_file_exists_with_frontmatter_and_body(
    skill_name: str,
) -> None:
    """Per-skill: file exists; frontmatter delimited + parses as
    mapping; description present + non-empty + ≤1536 chars; body
    non-empty."""
    text = load_skill_text(skill_name)
    frontmatter_yaml, body = split_frontmatter_and_body(text)

    frontmatter = yaml.safe_load(frontmatter_yaml)
    assert isinstance(frontmatter, dict), (
        f"{skill_name}: frontmatter must parse as a YAML mapping."
    )

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

    assert body.strip(), (
        f"{skill_name}: SKILL.md body (post-frontmatter) must be "
        "non-empty markdown."
    )
