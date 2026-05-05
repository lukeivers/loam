"""AC.PROMOTE.11 — Synthetic workspace-local SKILL fixtures.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.11: 4 synthetic-skill
fixtures live under
`plugins/dev-sdlc/tests/fixtures/skill-promotion-review/synthetic-skills/`
covering the named signal-evaluation paths (HARNESS-GENERAL +
DEV-SPECIFIC + DUPLICATE + Quality FAIL). The signal-evaluation
*algorithm* lives in the SKILL body the persona reads (NOT in a
Python function); this test validates the fixtures themselves are
well-shaped — they exist, they have the right frontmatter shape
(or intentionally-malformed shape for the Quality FAIL fixture),
they exercise the named signal paths.

The SKILL body itself references these fixtures by path so a
session-fresh persona can use them as worked examples when
reviewing real workspace SKILLs.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


FIXTURES_DIR = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "skill-promotion-review"
    / "synthetic-skills"
)

EXPECTED_FIXTURES = (
    "well-formed-harness-general",
    "well-formed-dev-specific",
    "duplicate-of-existing",
    "quality-fail",
)

DESCRIPTION_MAX_CHARS = 1536


def _read_skill_md(fixture: str) -> tuple[dict | None, str]:
    """Read a fixture's SKILL.md; return (frontmatter | None, body).

    Frontmatter is None when the YAML mapping is malformed (the
    quality-fail fixture's `description` may be empty / missing,
    which yields a parsed mapping with the expected key absent or
    None — the caller handles that)."""
    skill_md = FIXTURES_DIR / fixture / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"{skill_md}: SKILL.md must start with YAML frontmatter "
        "delimited by `---` lines."
    )
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        frontmatter = None
    body = match.group(2)
    return frontmatter, body


def test_all_four_fixture_directories_exist() -> None:
    """The 4 fixture directories must each exist with a SKILL.md
    inside."""
    assert FIXTURES_DIR.is_dir(), (
        f"expected fixtures directory at {FIXTURES_DIR}"
    )
    for fixture in EXPECTED_FIXTURES:
        skill_dir = FIXTURES_DIR / fixture
        skill_md = skill_dir / "SKILL.md"
        assert skill_dir.is_dir(), (
            f"expected fixture directory at {skill_dir}"
        )
        assert skill_md.is_file(), (
            f"expected fixture SKILL.md at {skill_md}"
        )


def test_well_formed_harness_general_shape() -> None:
    """The HARNESS-GENERAL fixture must have valid frontmatter
    (description present + non-empty + ≤1536 chars) + non-empty
    body. This fixture exercises the matrix row 1 path
    (Promote-to-base recommendation)."""
    frontmatter, body = _read_skill_md("well-formed-harness-general")
    assert isinstance(frontmatter, dict), (
        "well-formed-harness-general: frontmatter must parse as a "
        "YAML mapping."
    )
    description = frontmatter.get("description")
    assert isinstance(description, str) and description.strip(), (
        "well-formed-harness-general: `description` must be a "
        "non-empty string (well-formed fixture)."
    )
    assert len(description) <= DESCRIPTION_MAX_CHARS, (
        "well-formed-harness-general: `description` must be "
        f"≤{DESCRIPTION_MAX_CHARS} chars (well-formed fixture)."
    )
    assert body.strip(), (
        "well-formed-harness-general: body must be non-empty."
    )


def test_well_formed_dev_specific_shape_and_keywords() -> None:
    """The DEV-SPECIFIC fixture must have valid frontmatter + body
    + body mentions dev-mode partition keywords (loam-amend OR
    plan-before-code OR sealed-component). This fixture exercises
    matrix row 2/3 (Promote-to-plugin recommendation)."""
    frontmatter, body = _read_skill_md("well-formed-dev-specific")
    assert isinstance(frontmatter, dict), (
        "well-formed-dev-specific: frontmatter must parse as YAML."
    )
    description = frontmatter.get("description")
    assert isinstance(description, str) and description.strip(), (
        "well-formed-dev-specific: `description` must be non-empty."
    )
    body_lower = body.lower()
    # At least one of the dev-mode partition keywords must appear.
    dev_keywords = (
        "loam-amend",
        "loam amend",
        "plan-before-code",
        "sealed-component",
        "pos-amend",
        "odd §2.5",
        "amendment",
    )
    assert any(kw in body_lower for kw in dev_keywords), (
        "well-formed-dev-specific: body must mention at least one "
        f"dev-mode partition keyword from {dev_keywords}."
    )


def test_duplicate_of_existing_overlaps_loam_amend_cycle() -> None:
    """The DUPLICATE fixture's description must overlap heavily
    with the existing `loam-amend-cycle` SKILL's description (the
    Conflict=DUPLICATE signal path is exercised by description-
    keyword overlap >70%; verify the fixture's description names
    the same vocabulary)."""
    frontmatter, _body = _read_skill_md("duplicate-of-existing")
    assert isinstance(frontmatter, dict), (
        "duplicate-of-existing: frontmatter must parse as YAML."
    )
    description = frontmatter.get("description", "").lower()
    assert description.strip(), (
        "duplicate-of-existing: `description` must be non-empty."
    )
    # The fixture must share the loam-amend-cycle vocabulary so the
    # description-keyword-overlap heuristic identifies DUPLICATE.
    overlap_terms = (
        "sealed-component",
        "amendment",
        "plan-doc",
        "manifest",
        "loam amend apply",
        "loam amend seal",
    )
    matches = [t for t in overlap_terms if t in description]
    assert len(matches) >= 4, (
        "duplicate-of-existing: description must share ≥4 "
        f"vocabulary terms with `loam-amend-cycle` (matched: "
        f"{matches}; needed for Conflict=DUPLICATE signal path)."
    )


def test_quality_fail_fixture_exercises_quality_fail_path() -> None:
    """The Quality FAIL fixture must intentionally violate the
    structural-test convention — either empty `description` OR
    missing required body section. This exercises matrix row 5
    (Author-time-fix recommendation)."""
    frontmatter, body = _read_skill_md("quality-fail")
    # Acceptance: at least one of the structural-test convention
    # checks fails. (description is empty / missing OR body is
    # missing the 6-section convention.)
    description_fails = (
        not isinstance(frontmatter, dict)
        or not isinstance(frontmatter.get("description"), str)
        or not frontmatter.get("description", "").strip()
    )
    required_sections = (
        "## What this skill captures",
        "## When to use",
        "## How the persona applies it",
        "## Graceful degradation",
        "## Composition",
        "## Out of scope",
    )
    body_fails = not all(s in body for s in required_sections)
    assert description_fails or body_fails, (
        "quality-fail: fixture must intentionally violate the "
        "structural-test convention (empty description OR missing "
        "required body section) so it exercises the matrix row 5 "
        "Quality=FAIL → Author-time-fix path. Currently passes both "
        "checks — adjust the fixture to break at least one."
    )


def test_skill_body_references_fixtures_by_path() -> None:
    """The SKILL.md body must reference these fixtures by path so a
    session-fresh persona can use them as worked examples
    (mitigation for §6.10 — fixture-validation-only critique)."""
    skill_path = (
        Path(__file__).resolve().parent.parent
        / "skills"
        / "skill-promotion-review"
        / "SKILL.md"
    )
    body = skill_path.read_text(encoding="utf-8")
    assert "skill-promotion-review/synthetic-skills" in body, (
        "skill-promotion-review: body must reference the synthetic-"
        "skill fixtures path so the persona can use them as worked "
        "examples."
    )
    # All 4 fixture names should appear in the body so the persona
    # has a complete reference set.
    for fixture in EXPECTED_FIXTURES:
        assert fixture in body, (
            f"skill-promotion-review: body must reference fixture "
            f"`{fixture}` by name (worked-example completeness)."
        )
