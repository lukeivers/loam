"""AC.PROMOTE.12 — `skill-promotion-review` discoverable in canonical pos-v2.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.12: the SKILL appears
in the discovered-skills listing produced by walking
`plugins/dev-sdlc/skills/`. Anthropic's filesystem-discovery
primitive walks `<plugin>/skills/<name>/SKILL.md`; v0.1.7 Cycle 3
(`bcf699a`) added the layered-skill-discovery harness which
auto-symlinks each plugin's SKILL packages into
`<workspace>/.claude/skills/<name>/` at first-run scaffold. This
test verifies the disk-side precondition (the SKILL exists at
the canonical path under `plugins/dev-sdlc/skills/`).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
SKILL_NAME = "skill-promotion-review"
SKILL_DIR = SKILLS_DIR / SKILL_NAME
SKILL_MD = SKILL_DIR / "SKILL.md"


def test_skill_directory_present_in_dev_sdlc_skills() -> None:
    """Walking `plugins/dev-sdlc/skills/` yields a directory named
    `skill-promotion-review`."""
    assert SKILLS_DIR.is_dir(), f"expected skills dir at {SKILLS_DIR}"
    discovered = sorted(
        p.name for p in SKILLS_DIR.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )
    assert SKILL_NAME in discovered, (
        f"expected `{SKILL_NAME}` in discovered dev-sdlc SKILLs; "
        f"found {discovered}."
    )


def test_skill_md_at_canonical_path() -> None:
    """The SKILL.md is at the canonical Anthropic-discovery path:
    `plugins/dev-sdlc/skills/skill-promotion-review/SKILL.md`."""
    assert SKILL_MD.is_file(), (
        f"expected SKILL.md at {SKILL_MD}; AC.PROMOTE.12 requires "
        "the canonical Anthropic-discovery path."
    )


def test_skill_frontmatter_anthropic_discovery_compatible() -> None:
    """The frontmatter must parse + carry a non-empty description
    so Anthropic's auto-load discovery can match user intent."""
    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{SKILL_MD}: SKILL.md must start with YAML frontmatter."
    )
    frontmatter = yaml.safe_load(match.group(1))
    assert isinstance(frontmatter, dict), (
        f"{SKILL_MD}: frontmatter must parse as a YAML mapping."
    )
    description = frontmatter.get("description")
    assert isinstance(description, str) and description.strip(), (
        f"{SKILL_MD}: `description` must be a non-empty string for "
        "Anthropic discovery auto-load matching."
    )
