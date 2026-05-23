"""AC.SKILLS-DSDLC1.7 — all 6 dev-sdlc SKILLs auto-discoverable.

Per v0.1.8 Cycle 5 plan-doc §4 AC.SKILLS-DSDLC1.7: walking
`plugins/dev-sdlc/skills/` yields the 6 expected SKILL packages
(each containing a valid SKILL.md), alongside the `start-project/`
SKILL package promoted from flat-shape to subdirectory shape by
amendment-A-PROMOTE-START-PROJECT (slug
`loam-skills-start-project-discoverable`).

The Anthropic SKILL.md auto-discovery primitive walks
`<plugin>/skills/<name>/SKILL.md` files; v0.1.7 Cycle 3
(`bcf699a`) added `_symlink_plugin_skills()` in
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/
adapters/first_run_scaffold.py` which auto-symlinks each
plugin's SKILL packages into `<workspace>/.claude/skills/<name>/`
at first-run scaffold. This test verifies the disk-side
precondition (the 6 SKILLs exist as discoverable directories);
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

EXPECTED_SKILLS = [
    "loam-amend-cycle",
    "dispatch-brief-authoring",
    "plan-before-code-author",
    "fidraft-capture",
    "front-load-principle-walk",
    "audit-finding-triage",
]

DESCRIPTION_MAX_CHARS = 1536


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_each_expected_skill_directory_exists(skill_name: str) -> None:
    """AC.SKILLS-DSDLC1.7 — each expected SKILL has a directory
    with a SKILL.md file at the canonical path."""
    skill_dir = SKILLS_DIR / skill_name
    skill_md = skill_dir / "SKILL.md"
    assert skill_dir.is_dir(), (
        f"expected directory at {skill_dir}; "
        "AC.SKILLS-DSDLC1.7 requires Anthropic-discoverable "
        "subdirectory shape."
    )
    assert skill_md.is_file(), (
        f"expected SKILL.md at {skill_md}; "
        "AC.SKILLS-DSDLC1.7 requires the file at the canonical "
        "discovery path."
    )


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
def test_each_expected_skill_has_valid_frontmatter(
    skill_name: str,
) -> None:
    """AC.SKILLS-DSDLC1.7 — each expected SKILL has valid YAML
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


def test_all_six_dev_sdlc_skills_discovered() -> None:
    """AC.SKILLS-DSDLC1.7 cross-check — walking the skills/
    directory shows each of the 6 first-pass SKILL packages is
    present. Per `feedback_loose_AC_text_fix_AC_not_implementation`
    the AC's original "exactly 6" reading was tightened in v0.1.9
    Cycle 3 to "the 6 first-pass SKILLs are present" (subset
    check) — the canonical orphan/misnamed check now lives in
    AC.SKILLS-DSDLC2.7's `test_all_twelve_dev_sdlc_skills_
    discovered` which asserts exact equality against the full
    12-SKILL bundle (6 first-pass + 6 second-pass)."""
    discovered = {
        p.name for p in SKILLS_DIR.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    }
    missing = set(EXPECTED_SKILLS) - discovered
    assert missing == set(), (
        f"AC.SKILLS-DSDLC1.7: first-pass SKILLs missing from "
        f"plugins/dev-sdlc/skills/: {sorted(missing)}. "
        "These 6 SKILLs were sealed at v0.1.8 Cycle 5 (e4512b9) "
        "and must remain present."
    )


def test_skills_count_six() -> None:
    """v0.1.8 Cycle 5 — the first-pass dev-sdlc SKILL bundle is
    6 SKILLs (this test pins the first-pass count; the full
    bundle's count lives in AC.SKILLS-DSDLC2.7's
    `test_skills_count_twelve` post-v0.1.9 Cycle 3)."""
    assert len(EXPECTED_SKILLS) == 6
