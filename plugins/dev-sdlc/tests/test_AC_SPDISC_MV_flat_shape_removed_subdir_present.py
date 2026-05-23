"""AC.SPDISC.MV — `start-project` SKILL relocated from flat-shape to
subdirectory shape.

Per the amendment-A-PROMOTE-START-PROJECT plan-doc §4 AC.SPDISC.MV
(plan-doc at `docs/plans/loam-skills-start-project-discoverable.md`):
asserts the old flat-shape path is GONE, the new subdirectory-shape
path EXISTS, and the body section headers are preserved verbatim
(pure relocation; no body content changes per plan §3 out-of-scope).

RED-on-mutation: reverting the `git mv` (restoring start-project.md
and removing start-project/SKILL.md) flips both flat-shape and
subdirectory-shape assertions to red.

Ladder: AC.SPDISC.MV → AC.SPDISC.OSSM69 (the v0.1.0 contract whose
shape is now correct) → AC.OSS-M6.9 → AC.PO.1 (translation-burden
reduction: discoverable SKILL is the first-click intent-routing
surface).
"""

from __future__ import annotations

from pathlib import Path


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
FLAT_SHAPE_PATH = SKILLS_DIR / "start-project.md"
SUBDIR_SHAPE_DIR = SKILLS_DIR / "start-project"
SUBDIR_SHAPE_SKILL = SUBDIR_SHAPE_DIR / "SKILL.md"

EXPECTED_BODY_HEADERS = (
    "## What this skill does",
    "## Underlying mechanics",
    "## Operator surface",
    "## Composition",
)


def test_flat_shape_removed() -> None:
    """AC.SPDISC.MV — the v0.1.0 flat-shape file is GONE."""
    assert not FLAT_SHAPE_PATH.exists(), (
        f"flat-shape SKILL at {FLAT_SHAPE_PATH} still exists; "
        "A-PROMOTE-START-PROJECT requires the file to be relocated "
        "to subdirectory shape (git mv)."
    )


def test_subdirectory_shape_present() -> None:
    """AC.SPDISC.MV — the subdirectory-shape SKILL.md is present at
    the auto-symlinker-discoverable path."""
    assert SUBDIR_SHAPE_DIR.is_dir(), (
        f"expected SKILL directory at {SUBDIR_SHAPE_DIR}; "
        "A-PROMOTE-START-PROJECT requires subdirectory shape for "
        "_symlink_plugin_skills discoverability."
    )
    assert SUBDIR_SHAPE_SKILL.is_file(), (
        f"expected SKILL.md at {SUBDIR_SHAPE_SKILL}; the "
        "subdirectory-shape file is the Anthropic-spec discovery "
        "target."
    )


def test_body_section_headers_preserved() -> None:
    """AC.SPDISC.MV — body content is byte-identical post-move
    (modulo the optional frontmatter `name:` field per plan §10
    D-SPDISC.NAME-FIELD which rules KEEPS the field). Verified via
    section-header presence — pure relocation; no body revision."""
    body = SUBDIR_SHAPE_SKILL.read_text(encoding="utf-8")
    for header in EXPECTED_BODY_HEADERS:
        assert header in body, (
            f"expected section header {header!r} preserved in "
            f"relocated SKILL.md at {SUBDIR_SHAPE_SKILL}; "
            "A-PROMOTE-START-PROJECT is pure relocation (body content "
            "changes are out-of-scope per plan §3)."
        )
