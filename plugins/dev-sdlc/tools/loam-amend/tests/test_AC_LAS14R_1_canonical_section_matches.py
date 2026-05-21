"""AC.LAS14R.1 — widened §14 regex matches the canonical
``## §14<separator>`` heading shape (per plan-doc convention).

Per docs/plans/amendment-136-loam-amend-seal-section-14-backfill-regex-widening.md §4.

This test verifies the regex itself (unit-level) — the in-process
match against the production regex pattern. Behavior on the full
backfill code path is verified by AC.LAS14R.3 (synthetic seal) and
AC.LAS14R.S (outcome-altitude smoke).
"""

from __future__ import annotations

import re
import pytest

# Re-import the production regex pattern directly to ensure the test
# tracks the source-of-truth (any future regex tweak surfaces here).
from loam_amend.commands import seal as seal_module


@pytest.fixture
def section_header_re() -> re.Pattern:
    """Reconstruct the production regex from the seal-module source.

    The regex is local to ``_backfill_plan_doc_shas``; we extract by
    text-search to keep the test resilient against unrelated edits in
    that function. If the source string changes, the test fails loud.
    """
    src_path = seal_module.__file__
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    m = re.search(
        r'section_header_re\s*=\s*re\.compile\(r"([^"]+)"\s*,\s*re\.MULTILINE\)',
        src,
    )
    assert m is not None, (
        "could not locate the section_header_re definition in "
        "seal.py — production regex location changed"
    )
    return re.compile(m.group(1), re.MULTILINE)


# ----------------------------------------------------------------------
# Canonical heading shapes (AC.LAS14R.1)
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "heading_line",
    [
        # Canonical plan-doc-convention shape with em-dash + title:
        "## §14 — Method-decision register",
        # Canonical shape with single space + title:
        "## §14 Method-decision register",
        # Canonical shape with period + space + title:
        "## §14. Method-decision register",
    ],
)
def test_AC_LAS14R_1_canonical_section_header_matches(
    section_header_re: re.Pattern, heading_line: str
) -> None:
    """The widened regex must match every canonical ``## §14<sep>``
    shape — the plan-doc-convention form used by amendment-136 and
    every other plan-doc authored under the current convention."""
    text = f"# Fixture plan-doc\n\n## 1. Summary\n\nbody.\n\n{heading_line}\n\nbody.\n"
    m = section_header_re.search(text)
    assert m is not None, (
        f"AC.LAS14R.1 violation: canonical heading {heading_line!r} "
        f"did not match the widened regex {section_header_re.pattern!r}"
    )
    # Match must start at column 0 (line-anchored)
    assert text[m.start():].startswith("## §14"), (
        "match must begin at the literal '## §14' prefix"
    )
