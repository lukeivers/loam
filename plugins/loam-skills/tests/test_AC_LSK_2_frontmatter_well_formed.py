"""AC.LSK.2 — frontmatter follows Anthropic SKILL.md schema.

Per amendment #146 (loam-skills-ac-lsk1-root-cause), the SKILL set
checked here is derived from disk via `discover_skill_packages` —
no hardcoded EXPECTED_SKILLS list. Per-skill frontmatter assertions
(per AC.LSK.2's four numbered criteria):

1. Directory name is kebab-case (lowercase letters/numbers/hyphens
   only; ≤64 chars per Anthropic's `name` field rule).
2. If `name` field is present in frontmatter, it matches the
   directory name.
3. `description` informs Claude when to apply the skill — contains
   a "use when" or trigger-phrase clause.
4. No unknown frontmatter fields beyond `name` (optional) and
   `description` — keeps the surface minimal.

Anthropic SKILL.md schema reference:
https://code.claude.com/docs/en/skills
"""

from __future__ import annotations

import re

import yaml

import pytest

from conftest import discover_skill_packages, load_skill_text


# Per Anthropic schema: lowercase letters, numbers, and hyphens;
# max 64 characters.
NAME_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9-]*\Z")
NAME_MAX_LEN = 64

# Allowed frontmatter fields — kept minimal. Future packages may
# extend (allowed-tools, paths, when_to_use, etc.) but the AC.LSK.2
# fence keeps the surface minimal.
ALLOWED_FRONTMATTER_FIELDS = {"name", "description"}

# Common trigger-phrase / when-clause markers that indicate the
# description tells Claude WHEN to apply the skill (per the schema's
# "Put the key use case first" guidance).
WHEN_CLAUSE_MARKERS = (
    "use when",
    "use this",
    "before",
    "after",
    "when ",  # leading space avoids matching mid-word
)


DISCOVERED_SKILLS = discover_skill_packages()


def _load_frontmatter(skill_name: str) -> dict:
    text = load_skill_text(skill_name)
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert match, f"{skill_name}: missing frontmatter delimiters"
    return yaml.safe_load(match.group(1))


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_directory_name_kebab_case(skill_name: str) -> None:
    """Directory name is lowercase letters/numbers/hyphens, ≤64
    chars (Anthropic schema)."""
    assert NAME_PATTERN.match(skill_name), (
        f"{skill_name}: directory name must be kebab-case "
        "(lowercase letters/numbers/hyphens only)."
    )
    assert len(skill_name) <= NAME_MAX_LEN, (
        f"{skill_name}: directory name is {len(skill_name)} chars; "
        f"Anthropic schema caps at {NAME_MAX_LEN}."
    )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_name_field_matches_dir_when_present(skill_name: str) -> None:
    """If `name` field is present, it matches the directory name.
    Per Anthropic schema, omitting `name` causes it to default to
    the directory name; either shape is valid."""
    frontmatter = _load_frontmatter(skill_name)
    name_field = frontmatter.get("name")
    if name_field is not None:
        assert name_field == skill_name, (
            f"{skill_name}: frontmatter `name` ({name_field!r}) "
            f"must match directory name."
        )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_description_carries_trigger_phrase(skill_name: str) -> None:
    """The description tells Claude WHEN to apply the skill — must
    contain a "use when" / "before" / "after" / "when X" clause per
    the schema's guidance."""
    frontmatter = _load_frontmatter(skill_name)
    description = frontmatter["description"].lower()
    has_trigger = any(
        marker in description for marker in WHEN_CLAUSE_MARKERS
    )
    assert has_trigger, (
        f"{skill_name}: description must include a trigger-phrase "
        f"clause (one of {WHEN_CLAUSE_MARKERS}). Current: "
        f"{description[:120]!r}..."
    )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_no_unknown_frontmatter_fields(skill_name: str) -> None:
    """Surface is minimal: only `name` (optional) and `description`.
    Future packages may extend; AC.LSK.2 fences the surface."""
    frontmatter = _load_frontmatter(skill_name)
    unknown = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_FIELDS
    assert not unknown, (
        f"{skill_name}: unknown frontmatter fields {unknown}. "
        f"Allowed: {ALLOWED_FRONTMATTER_FIELDS}."
    )
