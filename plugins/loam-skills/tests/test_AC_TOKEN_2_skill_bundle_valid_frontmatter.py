"""AC.TOKEN.2 — A SKILL bundle exists at
``plugins/loam-skills/skills/cost-optimised-defaults/SKILL.md`` with
valid YAML frontmatter (``description`` field present + non-empty)
that describes the invocation criteria (user cost-signal patterns +
explicit ``/skill`` invocation).

Per ``docs/plans/drafts/token-defaults-optin-skill.md`` §4 AC.TOKEN.2
+ AC.PO.2 ladder (harness toolkit — SKILL adds to the toolkit the
persona invokes on cost-signal).

Mirrors the AC.COMPACT.FRONTMATTER precedent at
``plugins/loam-skills/tests/test_AC_COMPACT_FRONTMATTER_valid_and_
constraints_named.py`` (same Anthropic SKILL spec budget; same
frontmatter-shape check pattern).
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
    / "cost-optimised-defaults"
    / "SKILL.md"
)


# Anthropic SKILL spec: `description` field ≤1536 chars.
DESCRIPTION_MAX_CHARS = 1536

# At least one cost-signal trigger pattern must appear in the
# description. These are the canonical patterns named in §1 of the
# plan-doc; the frontmatter must name at least one to be
# auto-discoverable on cost-signal context.
COST_SIGNAL_TRIGGER_TOKENS = [
    "loam is expensive",
    "tokens are burning",
    "cut my costs",
    "what should my settings be",
    "cost",  # broad fallback — anything in the cost-signal family
]

# The user-approval / explicit-approval constraint MUST be named in
# the description per D-TOKEN.ENFORCE — the SKILL is opt-in only and
# the description is the operator-visible-at-SKILL-load-time surface
# for that constraint.
APPROVAL_CONSTRAINT_TOKENS = [
    "approval",
    "approve",
]

# The non-destructive merge / preserve constraint MUST be named —
# this is the sovereignty surface (AC.TOKEN.3 ladder).
PRESERVE_CONSTRAINT_TOKENS = [
    "preserve",
    "existing",
    "non-destructive",
]


def _load_frontmatter_dict() -> dict:
    assert SKILL_MD.exists(), (
        f"AC.TOKEN.2: SKILL.md must exist at {SKILL_MD}."
    )
    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert match, (
        f"AC.TOKEN.2: SKILL.md must open with YAML frontmatter "
        f"delimited by `---`; got non-matching prefix in {SKILL_MD}."
    )
    parsed = yaml.safe_load(match.group(1))
    assert isinstance(parsed, dict), (
        "AC.TOKEN.2: frontmatter must parse as a YAML mapping; got "
        f"{type(parsed).__name__}."
    )
    return parsed


def test_skill_md_exists_at_canonical_path() -> None:
    """SKILL.md exists at the canonical path."""
    assert SKILL_MD.exists(), (
        f"AC.TOKEN.2: SKILL.md must exist at canonical path "
        f"`plugins/loam-skills/skills/cost-optimised-defaults/"
        f"SKILL.md` (resolved to {SKILL_MD}); not found."
    )


def test_frontmatter_has_description_field() -> None:
    """The frontmatter has a non-empty `description` field."""
    fm = _load_frontmatter_dict()
    assert "description" in fm, (
        "AC.TOKEN.2: frontmatter must contain a `description` field "
        "(Anthropic SKILL spec); not found."
    )
    description = fm["description"]
    assert isinstance(description, str), (
        f"AC.TOKEN.2: frontmatter `description` must be a string; "
        f"got {type(description).__name__}."
    )
    assert description.strip(), (
        "AC.TOKEN.2: frontmatter `description` must be non-empty; "
        "got empty/whitespace-only string."
    )


def test_description_within_spec_budget() -> None:
    """The description fits the Anthropic SKILL spec budget."""
    fm = _load_frontmatter_dict()
    description = fm["description"]
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        f"AC.TOKEN.2: frontmatter `description` must be "
        f"≤{DESCRIPTION_MAX_CHARS} chars (Anthropic SKILL spec); "
        f"got {len(description)} chars."
    )


def test_description_names_at_least_one_cost_signal_trigger() -> None:
    """The description names at least one cost-signal trigger
    pattern."""
    fm = _load_frontmatter_dict()
    description = fm["description"].lower()
    matched = [
        token for token in COST_SIGNAL_TRIGGER_TOKENS
        if token.lower() in description
    ]
    assert matched, (
        f"AC.TOKEN.2: frontmatter `description` must name at least "
        f"one cost-signal trigger pattern from "
        f"{COST_SIGNAL_TRIGGER_TOKENS}; none found in description."
    )


def test_description_names_approval_constraint() -> None:
    """The description names the user-approval constraint."""
    fm = _load_frontmatter_dict()
    description = fm["description"].lower()
    matched = [
        token for token in APPROVAL_CONSTRAINT_TOKENS
        if token.lower() in description
    ]
    assert matched, (
        f"AC.TOKEN.2: frontmatter `description` must name the user-"
        f"approval constraint (one of {APPROVAL_CONSTRAINT_TOKENS}); "
        f"none found in description."
    )


def test_description_names_preserve_constraint() -> None:
    """The description names the non-destructive-merge constraint."""
    fm = _load_frontmatter_dict()
    description = fm["description"].lower()
    matched = [
        token for token in PRESERVE_CONSTRAINT_TOKENS
        if token.lower() in description
    ]
    assert matched, (
        f"AC.TOKEN.2: frontmatter `description` must name the non-"
        f"destructive-merge / preserve constraint (one of "
        f"{PRESERVE_CONSTRAINT_TOKENS}); none found in description."
    )
