# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.SKILLCAP.1 — `skill-capture-proposal` SKILL package present +
well-formed.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.1: the SKILL package directory exists at
``plugins/loam-skills/skills/skill-capture-proposal/`` with a valid
``SKILL.md``. Frontmatter ``description`` ≤1536 chars; description
carries trigger-phrase clause; body has all 6 required sections;
body references at least one named loam pattern; graceful-
degradation section names the raw-Claude-Code path explicitly.

The 8 sealed sibling SKILLs already pass the AC.LSK.* test family
(test_AC_LSK_1 / 2 / 3); those tests are extended in this same
cycle to include `skill-capture-proposal`. This file adds
SKILLCAP-specific structural checks the LSK family doesn't cover.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


SKILL_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "skill-capture-proposal"
)
SKILL_PATH = SKILL_DIR / "SKILL.md"

# Anthropic-published cap per
# https://code.claude.com/docs/en/skills (frontmatter reference):
# the combined description + when_to_use text is truncated at
# 1,536 characters in the skill listing.
DESCRIPTION_MAX_CHARS = 1536


def _load_skill() -> tuple[dict, str]:
    """Read SKILL.md, split frontmatter + body, parse frontmatter."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{SKILL_PATH}: SKILL.md must start with YAML frontmatter "
        "delimited by `---` lines."
    )
    return yaml.safe_load(match.group(1)), match.group(2)


def test_skill_directory_exists() -> None:
    """The skill package directory exists at the canonical path."""
    assert SKILL_DIR.is_dir(), (
        f"AC.SKILLCAP.1: directory {SKILL_DIR} must exist."
    )


def test_skill_md_present() -> None:
    """The SKILL.md file exists in the package directory."""
    assert SKILL_PATH.is_file(), (
        f"AC.SKILLCAP.1: SKILL.md must exist at {SKILL_PATH}."
    )


def test_skill_directory_kebab_case() -> None:
    """Directory name follows Anthropic kebab-case convention."""
    name = SKILL_DIR.name
    assert re.match(r"\A[a-z0-9][a-z0-9-]*\Z", name), (
        f"AC.SKILLCAP.1: directory name {name!r} must be kebab-case."
    )
    assert len(name) <= 64, (
        f"AC.SKILLCAP.1: directory name is {len(name)} chars; "
        "Anthropic schema caps at 64."
    )


def test_frontmatter_description_present_and_string() -> None:
    """`description` field is a non-empty string."""
    frontmatter, _body = _load_skill()
    description = frontmatter.get("description")
    assert isinstance(description, str), (
        "AC.SKILLCAP.1: `description` must be a string."
    )
    assert description.strip(), (
        "AC.SKILLCAP.1: `description` must be non-empty."
    )


def test_frontmatter_description_under_anthropic_cap() -> None:
    """`description` is ≤1536 chars per Anthropic's combined cap."""
    frontmatter, _body = _load_skill()
    description = frontmatter["description"]
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        f"AC.SKILLCAP.1: description is {len(description)} chars; "
        f"Anthropic schema caps combined description at "
        f"{DESCRIPTION_MAX_CHARS}."
    )


def test_frontmatter_description_carries_trigger_phrase() -> None:
    """The description tells Claude WHEN to apply the skill — must
    contain a "use when" / "before" / "after" / "when X" clause."""
    frontmatter, _body = _load_skill()
    description = frontmatter["description"].lower()
    when_markers = ("use when", "use this", "before", "after", "when ")
    has_trigger = any(m in description for m in when_markers)
    assert has_trigger, (
        "AC.SKILLCAP.1: description must include a trigger-phrase "
        f"clause (one of {when_markers}). Current first 120: "
        f"{description[:120]!r}..."
    )


def test_body_has_all_six_required_sections() -> None:
    """The body has the standard 6-section shape mirroring 8 sealed
    sibling SKILLs."""
    _frontmatter, body = _load_skill()
    body_lower = body.lower()
    required_sections = (
        "## what this skill captures",
        "## when to use",
        "## how the persona applies it",
        "## graceful degradation",
        "## composition",
        "## out of scope",
    )
    missing = [s for s in required_sections if s not in body_lower]
    assert not missing, (
        f"AC.SKILLCAP.1: missing required sections {missing}. "
        f"Required: {required_sections}."
    )


def test_body_references_loam_pattern() -> None:
    """Body references at least one named loam pattern (CLAUDE.md /
    F3 / F4 / ODD / M-FBM / M5 / FIDRAFT / Lens 1/2/3 / loam) so
    provenance is traceable for strangers running raw Claude Code."""
    _frontmatter, body = _load_skill()
    loam_markers = (
        "CLAUDE.md", "F3", "F4", "ODD", "M-FBM", "M5", "FIDRAFT",
        "Lens 1", "Lens 2", "Lens 3", "loam",
    )
    found = [m for m in loam_markers if m in body]
    assert found, (
        f"AC.SKILLCAP.1: body must reference at least one named "
        f"loam pattern from {loam_markers}."
    )


def test_graceful_degradation_names_raw_claude_code() -> None:
    """The graceful-degradation section names the raw-Claude-Code
    path explicitly — strangers without loam should know what to do."""
    _frontmatter, body = _load_skill()
    body_lower = body.lower()
    match = re.search(
        r"## graceful degradation\s*\n(.*?)(?=\n## |\Z)",
        body_lower,
        re.DOTALL,
    )
    assert match, "AC.SKILLCAP.1: graceful-degradation section missing."
    section = match.group(1)
    assert "claude code" in section or "raw claude" in section, (
        "AC.SKILLCAP.1: graceful-degradation must name raw-Claude-"
        "Code path."
    )
