"""AC.COMPACT.FRONTMATTER — strategic-compact SKILL frontmatter is
valid YAML, carries a `description:` field within the Anthropic
SKILL spec budget, and encodes the SKILL's named triggers + the
owner-class-only constraint.

Per ``docs/plans/strategic-compact-skill-graduation.md`` §2: the
frontmatter is the auto-discovery hook; Claude Code matches it
against turn-context to decide which SKILLs to load. The
constraint surface (owner-class only; not autonomous) must be
named in the description so the surface is operator-visible at
SKILL-load-time, not buried in the body.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_MD = (
    REPO_ROOT
    / "plugins"
    / "loam-skills"
    / "skills"
    / "strategic-compact"
    / "SKILL.md"
)


# Anthropic SKILL spec: `description` field ≤1536 chars.
DESCRIPTION_MAX_CHARS = 1536


def _load_frontmatter_dict() -> dict:
    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert match, (
        f"AC.COMPACT.FRONTMATTER: SKILL.md must open with YAML "
        f"frontmatter delimited by `---`; got non-matching prefix in "
        f"{SKILL_MD}."
    )
    parsed = yaml.safe_load(match.group(1))
    assert isinstance(parsed, dict), (
        "AC.COMPACT.FRONTMATTER: frontmatter must parse as a YAML "
        f"mapping; got {type(parsed).__name__}."
    )
    return parsed


def test_AC_COMPACT_FRONTMATTER_description_present_and_within_budget() -> None:
    """`description:` field exists, is non-empty, ≤1536 chars
    (Anthropic SKILL spec budget)."""
    frontmatter = _load_frontmatter_dict()
    description = frontmatter.get("description")
    assert description, (
        "AC.COMPACT.FRONTMATTER: `description` field must exist + "
        "be non-empty (Anthropic SKILL spec: description IS the "
        "discovery surface)."
    )
    assert isinstance(description, str), (
        "AC.COMPACT.FRONTMATTER: `description` must be a string."
    )
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        f"AC.COMPACT.FRONTMATTER: `description` is {len(description)} "
        f"chars; Anthropic SKILL spec caps at {DESCRIPTION_MAX_CHARS}."
    )


def test_AC_COMPACT_FRONTMATTER_names_compact_clear_triggers() -> None:
    """Description names the explicit owner-class trigger phrases —
    the SKILL fires on `should I /compact?` / `should I /clear?`
    questions (or close paraphrase) + on persona-detected context
    pressure."""
    frontmatter = _load_frontmatter_dict()
    description = frontmatter["description"].lower()

    # The trigger surface MUST be named in the description so Claude
    # Code's discovery matches against the right turn-shapes.
    assert "/compact" in description, (
        "AC.COMPACT.FRONTMATTER: description must name `/compact` "
        "as a trigger surface (the slash-command the SKILL guides)."
    )
    assert "/clear" in description, (
        "AC.COMPACT.FRONTMATTER: description must name `/clear` "
        "as a trigger surface (the slash-command the SKILL guides)."
    )
    # Context-pressure surface — persona-detected proactive trigger.
    assert "context" in description, (
        "AC.COMPACT.FRONTMATTER: description must name the context-"
        "pressure trigger so persona-detected proactive surfacing is "
        "discoverable, not just owner-question reactive surfacing."
    )


def test_AC_COMPACT_FRONTMATTER_encodes_owner_class_only_constraint() -> None:
    """Description names the owner-class-only constraint (the SKILL
    does NOT autonomously fire `/compact` or `/clear` — owner-class
    only per D-COMPACT.TRIGGER + the source memory rule lines
    106-111).

    The constraint is the SKILL's bounding rule; encoding it in the
    description means the surface is operator-visible at SKILL-load
    time, not buried in the body.
    """
    frontmatter = _load_frontmatter_dict()
    description = frontmatter["description"].lower()

    # Accept any of these phrasings — the substantive constraint is
    # "the SKILL is for owner-discretion, not autonomous fire."
    constraint_markers = (
        "owner-class",
        "owner discretion",
        "owner-discretion",
        "not autonomous",
        "not autonomous-agent",
    )
    matched = any(marker in description for marker in constraint_markers)
    assert matched, (
        "AC.COMPACT.FRONTMATTER: description must encode the owner-"
        "class-only constraint per D-COMPACT.TRIGGER + the source "
        "memory rule. Looked for any of "
        f"{constraint_markers}; got description: {description[:200]!r}..."
    )
