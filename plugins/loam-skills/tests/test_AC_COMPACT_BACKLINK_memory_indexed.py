"""AC.COMPACT.BACKLINK — the source memory file prepends a one-
paragraph backlink at the top naming the SKILL's canonical path;
the remainder of the file is byte-identical to pre-graduation
content.

Per ``docs/plans/strategic-compact-skill-graduation.md`` §2 +
D-COMPACT.MEMORY-FATE (ratified): the memory rule becomes the
index pointing at the SKILL; the SKILL becomes the operative
source-of-truth. The memory file is RETAINED (not deleted) so
existing memory-load mechanisms that depend on the file existing
keep working; the prepended paragraph makes the SKILL the
operative substance-source.

The memory file lives at
`~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_compact_
clear_decision_heuristic.md` (outside the loam canonical repo).
Per §5 halt-trigger #2 + §8 Q3 the build environment may not have
write access; this test SKIPS gracefully when the file is absent
and reports as a no-op rather than failing the build.
"""

from __future__ import annotations

from pathlib import Path

import pytest


MEMORY_FILE_PATH = (
    Path.home()
    / ".claude"
    / "projects"
    / "-Users-lukeivers-pos3"
    / "memory"
    / "feedback_compact_clear_decision_heuristic.md"
)

# The original v1-stable header lines from the source memory rule.
# Captured Tier-0 at plan-author time (file unchanged since 2026-05-14
# per its captured-2026-05-14 header). These substrings must survive
# the backlink prepend — the rest of the file is byte-identical to
# pre-graduation content per AC.COMPACT.BACKLINK contract.
ORIGINAL_SECTION_HEADERS = (
    "# Manual /compact and /clear — token-cost-aware decision heuristic",
    "## The three options + their cost profiles",
    "### Continue (no compaction, no clear)",
    "### `/compact` (auto-summarize + retain)",
    "### `/clear` (discard entirely)",
    "## The decision rule",
    "## Composes with",
    "## Activation",
    "## Composes with the autonomy directive",
)


def test_AC_COMPACT_BACKLINK_memory_file_carries_skill_backlink() -> None:
    """If the source memory file is accessible in the build
    environment, it carries a one-paragraph backlink at the top of
    the file naming the SKILL's canonical path. If the file is not
    accessible (build environment lacks the maintainer's home-
    directory memory tree per §5 halt-trigger #2 + §8 Q3), the
    test SKIPS — the build is not at fault; the file lives outside
    the loam canonical repo and the maintainer applies the backlink
    edit manually per the fallback path.
    """
    if not MEMORY_FILE_PATH.is_file():
        pytest.skip(
            f"AC.COMPACT.BACKLINK: source memory file not accessible "
            f"at {MEMORY_FILE_PATH} (build environment lacks the "
            "maintainer's home-directory memory tree per §5 halt-"
            "trigger #2 + §8 Q3). The backlink edit is applied "
            "manually by the maintainer in that environment; the "
            "AC's outcome is unaffected by the test skipping here."
        )

    content = MEMORY_FILE_PATH.read_text(encoding="utf-8")

    # The backlink paragraph MUST name the SKILL's canonical path so
    # a reader of the memory file is pointed at the operative source.
    assert (
        "plugins/loam-skills/skills/strategic-compact/SKILL.md" in content
    ), (
        "AC.COMPACT.BACKLINK: memory file must carry a backlink "
        "naming the SKILL's canonical path "
        "`plugins/loam-skills/skills/strategic-compact/SKILL.md` so "
        "memory-recall consumers are pointed at the operative "
        "substance-source post-graduation."
    )

    # The backlink-naming verbiage must signal the graduation —
    # accept any of "graduated", "SKILL", "operative" so the
    # wording-method stays the builder's call.
    backlink_markers = ("Graduated to SKILL", "graduated to SKILL", "operative content lives")
    has_backlink_signal = any(marker in content for marker in backlink_markers)
    assert has_backlink_signal, (
        "AC.COMPACT.BACKLINK: backlink paragraph must signal the "
        "graduation pattern (memory-becomes-index; SKILL-becomes-"
        f"operative). Looked for any of {backlink_markers}."
    )


def test_AC_COMPACT_BACKLINK_original_content_preserved() -> None:
    """The remainder of the memory file (everything after the
    prepended backlink paragraph) is byte-identical to pre-
    graduation content. Verified by section-header substring
    assertions: every original ## / ### header from the pre-
    graduation file is still present.

    Skips when the memory file is not accessible (same condition as
    AC.COMPACT.BACKLINK_memory_file_carries_skill_backlink).
    """
    if not MEMORY_FILE_PATH.is_file():
        pytest.skip(
            f"AC.COMPACT.BACKLINK: source memory file not accessible "
            f"at {MEMORY_FILE_PATH}; test skipped per §5 halt-trigger "
            "#2 + §8 Q3."
        )

    content = MEMORY_FILE_PATH.read_text(encoding="utf-8")

    missing_headers = [
        header for header in ORIGINAL_SECTION_HEADERS if header not in content
    ]
    assert not missing_headers, (
        "AC.COMPACT.BACKLINK: pre-graduation memory-file content was "
        "modified beyond the prepended backlink paragraph. Missing "
        f"original section headers: {missing_headers}. The contract "
        "is backlink-prepend + remainder-byte-identical."
    )
