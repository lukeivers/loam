"""AC.SKILLS-DSDLC2.6 — `loam-amend-status-quick` SKILL.md present
and well-formed.

Per v0.1.9 Cycle 3 plan-doc §4 AC.SKILLS-DSDLC2.6: the SKILL.md
file at `plugins/dev-sdlc/skills/loam-amend-status-quick/SKILL.md`
exists with valid YAML frontmatter, a non-empty body, and the
body mentions key terms covering the quick-status check (status
+ commit + coverage + progress).

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
    / "loam-amend-status-quick"
    / "SKILL.md"
)

DESCRIPTION_MAX_CHARS = 1536


def _load_skill() -> tuple[dict, str]:
    assert SKILL_PATH.is_file(), (
        f"expected SKILL.md at {SKILL_PATH}; AC.SKILLS-DSDLC2.6 "
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


def test_skill_body_mentions_status_quick_terms() -> None:
    """AC.SKILLS-DSDLC2.6 — body covers the quick-status walk:
    status + commit + coverage + progress."""
    _frontmatter, body = _load_skill()
    body_lower = body.lower()
    for term in ("status", "commit", "coverage", "progress"):
        assert term in body_lower, (
            f"loam-amend-status-quick: SKILL.md body must mention "
            f"`{term}` (covers the quick-status diagnostic walk)."
        )
