"""AC.SKILLS-DSDLC2.7 — all dev-sdlc SKILLs auto-discoverable.

Per v0.1.9 Cycle 3 plan-doc §4 AC.SKILLS-DSDLC2.7 (extended by
v0.2.1 Cycle 2 to admit `skill-promotion-review`): walking
`plugins/dev-sdlc/skills/` yields exactly the 13 expected SKILL
packages (each containing a valid SKILL.md) — 6 from v0.1.8
Cycle 5 first pass + 6 from v0.1.9 Cycle 3 second pass + 1 from
v0.2.1 Cycle 2 — in addition to the flat-file `start-project.md`
shipped with v0.1.0.

The Anthropic SKILL.md auto-discovery primitive walks
`<plugin>/skills/<name>/SKILL.md` files; v0.1.7 Cycle 3
(`bcf699a`) added `_symlink_plugin_skills()` in
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/
adapters/first_run_scaffold.py` which auto-symlinks each
plugin's SKILL packages into `<workspace>/.claude/skills/<name>/`
at first-run scaffold. This test verifies the disk-side
precondition (the 12 SKILLs exist as discoverable directories);
the symlinking mechanism is verified by AC.LAYERED.2 in
v0.1.7 Cycle 3.

Anthropic SKILL.md schema reference:
https://code.claude.com/docs/en/skills
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

# 6 from v0.1.8 Cycle 5 (first pass) + 6 from v0.1.9 Cycle 3
# (second pass) + 1 from v0.2.1 Cycle 2 + 1 (odd-test-altitude-
# discipline) admitted into the registry as part of the v0.5.0
# AC.V050.4 no-regression closure (pre-existing orphan from the
# odd-test-altitude-discipline shipping cycle, surfaced by AC.V050.4)
# + 1 from v0.5.0 Cycle 1 (subagent-routing) = 15 total.
EXPECTED_SKILLS = [
    # First pass (v0.1.8 Cycle 5, sealed e4512b9):
    "loam-amend-cycle",
    "dispatch-brief-authoring",
    "plan-before-code-author",
    "fidraft-capture",
    "front-load-principle-walk",
    "audit-finding-triage",
    # Second pass (v0.1.9 Cycle 3):
    "seal-narrative-writer",
    "plan-docs-author",
    "hook-violation-recovery",
    "component-scaffold-author",
    "graceful-fallthrough-with-detection",
    "loam-amend-status-quick",
    # Third pass (v0.2.1 Cycle 2):
    "skill-promotion-review",
    # Fourth pass (odd-test-altitude-discipline shipping cycle —
    # admitted into the registry by v0.5.0 AC.V050.4 to clear the
    # pre-existing no-orphans regression in this test):
    "odd-test-altitude-discipline",
    # Fifth pass (v0.5.0 Cycle 1, subagent-routing — closes the
    # consumption-gap on the v0.1.7 typed personas):
    "subagent-routing",
]

DESCRIPTION_MAX_CHARS = 1536


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_each_expected_skill_directory_exists(skill_name: str) -> None:
    """AC.SKILLS-DSDLC2.7 — each expected SKILL has a directory
    with a SKILL.md file at the canonical path."""
    skill_dir = SKILLS_DIR / skill_name
    skill_md = skill_dir / "SKILL.md"
    assert skill_dir.is_dir(), (
        f"expected directory at {skill_dir}; "
        "AC.SKILLS-DSDLC2.7 requires Anthropic-discoverable "
        "subdirectory shape."
    )
    assert skill_md.is_file(), (
        f"expected SKILL.md at {skill_md}; "
        "AC.SKILLS-DSDLC2.7 requires the file at the canonical "
        "discovery path."
    )


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_each_expected_skill_has_valid_frontmatter(
    skill_name: str,
) -> None:
    """AC.SKILLS-DSDLC2.7 — each expected SKILL has valid YAML
    frontmatter with non-empty description ≤ Anthropic
    combined-cap."""
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{skill_md}: SKILL.md must start with YAML frontmatter "
        "delimited by `---` lines."
    )
    frontmatter = yaml.safe_load(match.group(1))
    body = match.group(2)
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


def test_all_twelve_dev_sdlc_skills_discovered() -> None:
    """AC.SKILLS-DSDLC2.7 cross-check — walking the skills/
    directory yields the expected dev-sdlc SKILL packages.
    Asserts no orphans (no extra subdirectories with SKILL.md)
    and no misnames. Extended by v0.2.1 Cycle 2 to include
    `skill-promotion-review` (13th SKILL)."""
    discovered = sorted(
        p.name for p in SKILLS_DIR.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )
    assert discovered == sorted(EXPECTED_SKILLS), (
        f"discovered dev-sdlc SKILLs {discovered} != expected "
        f"{sorted(EXPECTED_SKILLS)}; AC.SKILLS-DSDLC2.7 requires "
        "exactly the named packages."
    )


def test_skills_count_thirteen() -> None:
    """v0.1.9 Cycle 3 set the bundle at 12 (6 first pass from
    v0.1.8 Cycle 5 + 6 second pass from v0.1.9 Cycle 3); v0.2.1
    Cycle 2 added `skill-promotion-review` as the 13th. v0.5.0 AC.V050.4
    extended the registry to 15 — admitted `odd-test-altitude-
    discipline` (pre-existing orphan; clears that regression) and
    `subagent-routing` (new this cycle).

    The function name retains the historical 'thirteen' wording for
    git-blame continuity with the v0.2.1 + v0.5.0 amendment record;
    the assertion tracks the current count. Future amendments that
    add SKILLs update this value + the EXPECTED_SKILLS list together.
    """
    assert len(EXPECTED_SKILLS) == 15
