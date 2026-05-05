"""AC.PROMOTE.1 — `skill-promotion-review` SKILL package well-formed.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.1: the SKILL.md file at
`plugins/dev-sdlc/skills/skill-promotion-review/SKILL.md` exists
with valid YAML frontmatter (description-only, non-empty,
≤1536 chars per Anthropic's combined-cap; no `name` field per
the 21 sealed SKILL precedent), a non-empty body, and the body
covers the 6-section convention from v0.1.8 Cycle 5 + v0.1.9
Cycle 3 (What this skill captures / When to use / How the
persona applies it / Graceful degradation / Composition / Out
of scope).

Anthropic SKILL.md schema reference:
https://code.claude.com/docs/en/skills
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "skill-promotion-review"
    / "SKILL.md"
)

# Anthropic-published cap per
# https://code.claude.com/docs/en/skills (frontmatter reference):
# combined description + when_to_use text is truncated at 1,536
# characters in the skill listing.
DESCRIPTION_MAX_CHARS = 1536

REQUIRED_SECTIONS = (
    "## What this skill captures",
    "## When to use",
    "## How the persona applies it",
    "## Graceful degradation",
    "## Composition",
    "## Out of scope",
)


def _load_skill() -> tuple[dict, str]:
    """Read SKILL.md, split frontmatter + body, parse frontmatter."""
    assert SKILL_PATH.is_file(), (
        f"expected SKILL.md at {SKILL_PATH}; AC.PROMOTE.1 "
        "requires the file exists at the canonical path."
    )
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{SKILL_PATH}: SKILL.md must start with YAML frontmatter "
        "delimited by `---` lines."
    )
    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return frontmatter, body


def test_skill_file_exists() -> None:
    assert SKILL_PATH.is_file(), (
        f"expected skill-promotion-review SKILL.md at {SKILL_PATH}"
    )


def test_skill_frontmatter_description_only() -> None:
    """Frontmatter is description-only per the 21 sealed SKILL
    precedents. No `name` field — Anthropic's discovery infers the
    SKILL name from the directory path."""
    frontmatter, _body = _load_skill()
    assert isinstance(frontmatter, dict), (
        "skill-promotion-review: frontmatter must parse as a YAML "
        "mapping."
    )
    assert "description" in frontmatter, (
        "skill-promotion-review: frontmatter must include a "
        "`description` field."
    )
    assert "name" not in frontmatter, (
        "skill-promotion-review: frontmatter must NOT include a "
        "`name` field; Anthropic infers name from the directory "
        "path. Mirrors 21 sealed SKILL precedents."
    )


def test_skill_description_valid_and_under_cap() -> None:
    frontmatter, _body = _load_skill()
    description = frontmatter["description"]
    assert isinstance(description, str), (
        "skill-promotion-review: `description` must be a string."
    )
    assert description.strip(), (
        "skill-promotion-review: `description` must be non-empty."
    )
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        f"skill-promotion-review: `description` is "
        f"{len(description)} chars; Anthropic schema caps combined "
        f"description at {DESCRIPTION_MAX_CHARS}."
    )


def test_skill_body_non_empty() -> None:
    _frontmatter, body = _load_skill()
    assert body.strip(), (
        "skill-promotion-review: SKILL.md body (post-frontmatter) "
        "must be non-empty markdown."
    )


def test_skill_body_six_section_convention() -> None:
    """AC.PROMOTE.1 — body covers the 6-section dev-sdlc
    convention: What / When / How / Graceful degradation /
    Composition / Out of scope."""
    _frontmatter, body = _load_skill()
    for section in REQUIRED_SECTIONS:
        assert section in body, (
            f"skill-promotion-review: SKILL.md body must include "
            f"the section heading `{section}` (6-section dev-sdlc "
            "convention from v0.1.8 Cycle 5 + v0.1.9 Cycle 3)."
        )
