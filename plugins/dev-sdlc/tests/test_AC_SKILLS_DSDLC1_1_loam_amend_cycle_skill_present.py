"""AC.SKILLS-DSDLC1.1 — `loam-amend-cycle` SKILL.md present and well-formed.

Per v0.1.8 Cycle 5 plan-doc §4 AC.SKILLS-DSDLC1.1: the SKILL.md
file at `plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md` exists
with valid YAML frontmatter (description present, non-empty,
≤1536 chars per Anthropic's combined-cap), a non-empty body, and
the body mentions key terms covering the sealed-component
amendment workflow.

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
    / "loam-amend-cycle"
    / "SKILL.md"
)

# Anthropic-published cap per
# https://code.claude.com/docs/en/skills (frontmatter reference):
# combined description + when_to_use text is truncated at 1,536
# characters in the skill listing.
DESCRIPTION_MAX_CHARS = 1536


def _load_skill() -> tuple[dict, str]:
    """Read SKILL.md, split frontmatter + body, parse frontmatter."""
    assert SKILL_PATH.is_file(), (
        f"expected SKILL.md at {SKILL_PATH}; AC.SKILLS-DSDLC1.1 "
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
        f"expected loam-amend-cycle SKILL.md at {SKILL_PATH}"
    )


def test_skill_frontmatter_valid_with_description() -> None:
    frontmatter, _body = _load_skill()
    assert isinstance(frontmatter, dict), (
        "loam-amend-cycle: frontmatter must parse as a YAML mapping."
    )
    description = frontmatter.get("description")
    assert isinstance(description, str), (
        "loam-amend-cycle: `description` field is required + a string."
    )
    assert description.strip(), (
        "loam-amend-cycle: `description` must be non-empty."
    )
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        f"loam-amend-cycle: `description` is {len(description)} chars; "
        f"Anthropic schema caps combined description at "
        f"{DESCRIPTION_MAX_CHARS}."
    )


def test_skill_body_non_empty() -> None:
    _frontmatter, body = _load_skill()
    assert body.strip(), (
        "loam-amend-cycle: SKILL.md body (post-frontmatter) must be "
        "non-empty markdown."
    )


def test_skill_body_mentions_amend_cycle_terms() -> None:
    """AC.SKILLS-DSDLC1.1 — body covers the sealed-component
    amendment workflow: plan-doc → manifest → apply → seal →
    backfill."""
    _frontmatter, body = _load_skill()
    body_lower = body.lower()
    for term in ("plan-doc", "manifest", "apply", "seal"):
        assert term in body_lower, (
            f"loam-amend-cycle: SKILL.md body must mention `{term}` "
            "(covers the sealed-component amendment workflow)."
        )
