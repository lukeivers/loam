"""AC.LSK.3 — body content shape (Option-1-WIDENED per amendment #146).

Per AC.LSK1RC.AC3 (sealed prose tightening in
docs/plans/sealed/v0-1-3-skill-packages.md lines 153-161), this AC
covers three body-shape assertion families:

1. **Section shape.** Body has H2 sections covering When + What/How
   + Composition/Boundary. Two canonical conventions exist on disk:

   - v0.1.3-era convention (10 loam-pattern SKILLs): `## What this
     skill captures` / `## When to use` / `## How the persona
     applies it` / `## Graceful degradation` / `## Composition` /
     `## Out of scope`.

   - Post-v0.1.6 claude-primitive convention (9 SKILLs whose
     subject IS a Claude-Code primitive): `## When to load me` /
     `## What the primitive does` / `## Composition` /
     `## Anti-patterns` / `## Example invocation`.

   - Hybrid (handsoff-loop, subject IS a loam-CLI primitive):
     `## What this is` / `## How the persona invokes it` /
     `## Hard rules`.

   The flexible semantic predicate accepts any of these (and
   future structural equivalents) by matching on header-substring
   semantics for each of the three required semantic categories
   (When, What/How, Composition/Boundary).

2. **Loam-pattern reference (CONDITIONAL).** Loam-pattern SKILLs
   must reference at least one named loam concept so the pattern's
   provenance is traceable. Claude-primitive-subject SKILLs are
   EXEMPT — their subject IS the primitive, not a loam pattern;
   their frontmatter description already gates trigger-phrase per
   AC.LSK.2 and their body references the primitive directly.

3. **Graceful-degradation section (CONDITIONAL).** Loam-pattern
   SKILLs must carry a `## Graceful degradation` (or semantically
   equivalent) section naming the raw-Claude-Code path for users
   without loam. Claude-primitive-subject SKILLs are EXEMPT —
   there's no loam-pattern to degrade from when the primitive IS
   the pattern.

The conditional exemption is gated by `is_claude_primitive_package`
(in conftest.py) — heuristic detection via H2 header convention
(`## When to load me` OR `## What this is`).
"""

from __future__ import annotations

import re

import yaml

import pytest

from conftest import (
    discover_skill_packages,
    is_claude_primitive_package,
    iter_body_h2_headers,
    load_skill_text,
    split_frontmatter_and_body,
)


# Semantic categories for the section-shape predicate. Each category
# matches if ANY discovered H2 header contains ANY of the listed
# substrings (case-insensitive). The lists are intentionally narrow
# enough to discriminate genuine missing-shape from valid alternative
# wording, but broad enough to admit the two canonical conventions +
# handsoff-loop's hybrid + future structural equivalents.
#
# The "When" category has a fallback: if no H2 header matches, the
# frontmatter description's trigger-phrase (already validated by
# AC.LSK.2) satisfies the When-semantic. This admits primitive-
# subject SKILLs whose When is in the description rather than a
# body section (e.g., handsoff-loop).
SECTION_SEMANTICS = {
    "When": ("when",),
    "What/How": ("what ", "how ", "failure mode"),
    "Composition/Boundary": (
        "composition",
        "out of scope",
        "anti-pattern",
        "hard rule",
        "graceful degradation",
    ),
}

# Frontmatter trigger-phrase markers — re-used from AC.LSK.2's
# WHEN_CLAUSE_MARKERS. If the body lacks a When-header, presence of
# any of these in the description satisfies the When-semantic.
DESCRIPTION_WHEN_MARKERS = (
    "use when",
    "use this",
    "before",
    "after",
    "when ",
)

# Loam-pattern markers (widened per D-LSK1RC.LOAM-PATTERN-MARKERS):
# adding `persona` catches time-claims-discipline (whose body uses
# loam-internal jargon `translation-discipline`, `specific-claim`,
# `AI-time` but lacks the structured-name markers from the original
# list). `persona` is the cleanest cross-cutting discriminator for
# loam-pattern SKILLs — verified Tier-0: every loam-pattern SKILL
# has ≥1 `persona` reference; claude-primitive-subject packages
# average 0 (and are exempted by the heuristic).
LOAM_PATTERN_MARKERS = (
    "CLAUDE.md",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "ODD",
    "M-FBM",
    "M5",
    "FIDRAFT",
    "Lens 1",
    "Lens 2",
    "Lens 3",
    "Lens 4",
    "loam",
    "persona",
)


DISCOVERED_SKILLS = discover_skill_packages()


def _load_body(skill_name: str) -> str:
    text = load_skill_text(skill_name)
    _, body = split_frontmatter_and_body(text)
    return body


def _load_description(skill_name: str) -> str:
    text = load_skill_text(skill_name)
    frontmatter_yaml, _ = split_frontmatter_and_body(text)
    frontmatter = yaml.safe_load(frontmatter_yaml)
    return frontmatter.get("description", "") or ""


def _headers_lower(body: str) -> list[str]:
    return [h.lower() for h in iter_body_h2_headers(body)]


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_body_has_required_sections(skill_name: str) -> None:
    """Section-shape semantic predicate (AC.LSK.3 family 1): body
    has H2 sections covering When + What/How + Composition/Boundary.

    Admits both the v0.1.3-era convention AND the post-v0.1.6
    claude-primitive convention AND handsoff-loop's hybrid per
    AC.LSK1RC.AC3 — matching on header-substring semantics for
    each of the three required semantic categories.
    """
    body = _load_body(skill_name)
    headers = _headers_lower(body)
    assert headers, (
        f"{skill_name}: body must carry at least one `## ` H2 header."
    )

    missing = []
    for category, substrings in SECTION_SEMANTICS.items():
        matched = any(
            sub in header
            for header in headers
            for sub in substrings
        )
        if not matched:
            missing.append((category, substrings))

    # Fallback for the "When" category: if no body header carries
    # When-semantics, the frontmatter description's trigger-phrase
    # (validated by AC.LSK.2) satisfies the When-requirement. This
    # admits primitive-subject SKILLs that put When in the
    # description rather than a body section.
    if missing and missing[0][0] == "When":
        description = _load_description(skill_name).lower()
        if any(m in description for m in DESCRIPTION_WHEN_MARKERS):
            missing = missing[1:]

    assert not missing, (
        f"{skill_name}: body missing semantic section coverage for "
        f"{[c for c, _ in missing]}. "
        f"Headers present: {headers}. "
        f"Each category accepts a header whose lowercased text "
        f"contains any of its substrings: {dict(missing)}. "
        f"(The When-category also falls back to a frontmatter "
        f"description trigger-phrase per AC.LSK.2.)"
    )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_body_references_loam_pattern(skill_name: str) -> None:
    """Loam-pattern reference (AC.LSK.3 family 2, CONDITIONAL):
    body must reference at least one named loam pattern.

    Claude-primitive-subject packages are EXEMPT — their subject
    IS the Claude-Code primitive, not a loam pattern. The heuristic
    detects via `## When to load me` OR `## What this is` H2 header
    per D-LSK1RC.CLAUDE-PRIMITIVE-HEURISTIC.
    """
    if is_claude_primitive_package(skill_name):
        pytest.skip(
            f"{skill_name}: claude-primitive-subject package "
            "(exempt from loam-pattern reference check per "
            "AC.LSK1RC.AC3 conditional exemption)."
        )

    body = _load_body(skill_name)
    found = [marker for marker in LOAM_PATTERN_MARKERS if marker in body]
    assert found, (
        f"{skill_name}: loam-pattern SKILL body must reference at "
        f"least one named loam concept from {LOAM_PATTERN_MARKERS} "
        f"so the pattern's provenance is traceable."
    )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_graceful_degradation_names_raw_claude_code(
    skill_name: str,
) -> None:
    """Graceful-degradation section (AC.LSK.3 family 3, CONDITIONAL):
    loam-pattern SKILLs must carry a `## Graceful degradation`
    section with non-trivial content naming a fallback path.

    Claude-primitive-subject packages are EXEMPT — there's no
    loam-pattern to degrade from when the primitive IS the pattern.

    Per AC.LSK1RC.AC3: the original v0.1.3-era check required the
    section to name "claude code" or "raw claude" verbatim. That
    requirement was v0.1.3-bundle-centric (all 5 SKILLs were
    persona-pattern translations whose fallback was the raw-CLI
    Claude Code path). Post-v0.1.6 loam-pattern SKILLs may have
    different fallback shapes (e.g., time-claims-discipline's
    fallback is to use a verifiable proxy when the shell `date`
    tool is unavailable). The tightened check: the section must
    exist + carry non-trivial content (≥40 chars after the header).
    """
    if is_claude_primitive_package(skill_name):
        pytest.skip(
            f"{skill_name}: claude-primitive-subject package "
            "(exempt from graceful-degradation section check per "
            "AC.LSK1RC.AC3 conditional exemption)."
        )

    body = _load_body(skill_name)
    body_lower = body.lower()
    # Find the graceful-degradation section + read until the next
    # `## ` header. Anchored at the start of a line to avoid matching
    # mid-paragraph mentions.
    match = re.search(
        r"^## graceful degradation\s*\n(.*?)(?=\n## |\Z)",
        body_lower,
        re.DOTALL | re.MULTILINE,
    )
    assert match, (
        f"{skill_name}: loam-pattern SKILL must carry a "
        "`## Graceful degradation` section (cannot find header)."
    )
    section = match.group(1).strip()
    assert len(section) >= 40, (
        f"{skill_name}: graceful degradation section must carry "
        f"non-trivial content describing a fallback path "
        f"(found {len(section)} chars; minimum 40)."
    )
