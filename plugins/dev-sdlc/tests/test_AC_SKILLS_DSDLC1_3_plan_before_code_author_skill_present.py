"""AC.SKILLS-DSDLC1.3 — `plan-before-code-author` SKILL.md present
and well-formed.

Per v0.1.8 Cycle 5 plan-doc §4 AC.SKILLS-DSDLC1.3: the SKILL.md
file at `plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md`
exists with valid YAML frontmatter, a non-empty body, and the body
mentions key terms covering the ODD-shaped plan-doc skeleton.

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
    / "plan-before-code-author"
    / "SKILL.md"
)

DESCRIPTION_MAX_CHARS = 1536


def _load_skill() -> tuple[dict, str]:
    assert SKILL_PATH.is_file(), (
        f"expected SKILL.md at {SKILL_PATH}; AC.SKILLS-DSDLC1.3 "
        "requires the file exists at the canonical path."
    )
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{SKILL_PATH}: SKILL.md must start with YAML frontmatter."
    )
    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
    return frontmatter, body


def test_skill_file_exists() -> None:
    assert SKILL_PATH.is_file()


def test_skill_frontmatter_valid_with_description() -> None:
    frontmatter, _body = _load_skill()
    assert isinstance(frontmatter, dict)
    description = frontmatter.get("description")
    assert isinstance(description, str)
    assert description.strip()
    assert len(description) <= DESCRIPTION_MAX_CHARS


def test_skill_body_non_empty() -> None:
    _frontmatter, body = _load_skill()
    assert body.strip()


def test_skill_body_mentions_plan_skeleton_terms() -> None:
    """AC.SKILLS-DSDLC1.3 — body covers the ODD-shaped plan-doc
    skeleton: Outcome shape + AC family / Acceptance gate +
    method-decision record."""
    _frontmatter, body = _load_skill()
    body_lower = body.lower()
    # Loam plan-doc terminology uses "AC family" + "acceptance
    # gate" rather than the generic "acceptance criteria"; both
    # variants are accepted to match how the SKILL.md reflects
    # the actual plan-doc section names.
    for term in (
        "outcome shape",
        "method-decision",
    ):
        assert term in body_lower, (
            f"plan-before-code-author: SKILL.md body must mention "
            f"`{term}` (covers the ODD-shaped plan skeleton)."
        )
    assert (
        "ac family" in body_lower
        or "acceptance gate" in body_lower
        or "acceptance criteria" in body_lower
    ), (
        "plan-before-code-author: SKILL.md body must mention one "
        "of `AC family` / `acceptance gate` / `acceptance criteria` "
        "(the plan-doc's AC section)."
    )
