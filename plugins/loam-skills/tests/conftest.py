"""Shared discovery helper for the AC.LSK family tests.

Per amendment #146 (loam-skills-ac-lsk1-root-cause), the SKILL set
checked by the AC.LSK.{1,2,3} tests is derived from disk (every
subdirectory of plugins/loam-skills/skills/ containing a SKILL.md
file) rather than enumerated by name. This module centralizes:

1. The discovery function (`discover_skill_packages`) — used by the
   three rewritten test files in lockstep, so a future SKILL
   addition automatically inherits well-formedness gating with no
   list-bump required.

2. The `is_claude_primitive_package` classifier — heuristic detection
   for SKILLs whose subject IS a Claude-Code primitive (or loam-CLI
   primitive). Used by AC.LSK.3's conditional logic to exempt
   primitive-subject packages from the loam-pattern + graceful-
   degradation checks (those requirements apply to loam-pattern
   SKILLs only, per AC.LSK1RC.AC3 / D-LSK1RC.CLAUDE-PRIMITIVE-
   HEURISTIC).

The heuristic: a SKILL.md body that carries `## When to load me`
(the post-v0.1.6 claude-primitive convention) OR `## What this is`
(handsoff-loop's primitive-subject hybrid convention) is classified
as primitive-subject. Loam-pattern SKILLs use `## What this skill
captures` instead — verified Tier-0 across all 20 packages.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def discover_skill_packages(skills_dir: Path | None = None) -> list[str]:
    """Walk `skills_dir` and return every subdirectory that contains a
    SKILL.md file. Sorted for deterministic test ordering.

    Default `skills_dir` is the production tree at
    plugins/loam-skills/skills/. Callers can override with a tmp_path
    mirror for fixture-based verification (per AC.LSK1RC.S).
    """
    base = skills_dir if skills_dir is not None else SKILLS_DIR
    if not base.is_dir():
        return []
    return sorted(
        p.name for p in base.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )


def load_skill_text(skill_name: str, skills_dir: Path | None = None) -> str:
    """Read the SKILL.md file's full text (frontmatter + body)."""
    base = skills_dir if skills_dir is not None else SKILLS_DIR
    return (base / skill_name / "SKILL.md").read_text(encoding="utf-8")


def split_frontmatter_and_body(text: str) -> tuple[str, str]:
    """Split SKILL.md text into (frontmatter_yaml_str, body_md_str).

    Raises AssertionError if the frontmatter delimiters are missing
    or malformed — this is the well-formedness contract surface and
    callers expect a clear failure pointing at the malformed file.
    """
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        "SKILL.md must start with YAML frontmatter delimited by `---` "
        "lines on their own (well-formedness contract)."
    )
    return match.group(1), match.group(2)


# Claude-primitive-subject detection: presence of either H2 header
# below classifies the package as primitive-subject (subject IS a
# Claude-Code primitive or loam-CLI primitive). Verified Tier-0
# against all 20 packages on disk at amendment-#146 build time:
# 9 packages carry `## When to load me`; 1 package (handsoff-loop)
# carries `## What this is`; the 10 loam-pattern SKILLs carry
# `## What this skill captures` instead (no overlap with either
# primitive marker).
_PRIMITIVE_HEADERS = (
    "## When to load me",
    "## What this is",
)


def is_claude_primitive_package(
    skill_name: str,
    skills_dir: Path | None = None,
) -> bool:
    """Return True if the SKILL.md describes a primitive (Claude-Code
    or loam-CLI), False if it describes a loam-pattern.

    Per AC.LSK1RC.AC3 / D-LSK1RC.CLAUDE-PRIMITIVE-HEURISTIC: the
    loam-pattern reference + graceful-degradation section checks
    apply to loam-pattern SKILLs only; primitive-subject SKILLs are
    exempt (the primitive IS the pattern; there's no loam-pattern
    to degrade from).
    """
    base = skills_dir if skills_dir is not None else SKILLS_DIR
    path = base / skill_name / "SKILL.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    # Match the H2 header on its own line (avoid matching mid-paragraph
    # quoted text).
    for header in _PRIMITIVE_HEADERS:
        if re.search(rf"^{re.escape(header)}\s*$", text, re.MULTILINE):
            return True
    return False


def iter_body_h2_headers(body: str) -> Iterable[str]:
    """Yield every `## ` H2 header line from the body, stripped of the
    `## ` prefix and trailing whitespace. Used by the section-shape
    semantic predicate."""
    for line in body.splitlines():
        if line.startswith("## "):
            yield line[3:].strip()
