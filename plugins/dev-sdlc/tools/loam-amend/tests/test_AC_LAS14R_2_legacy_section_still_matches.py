"""AC.LAS14R.2 — widened §14 regex STILL matches the legacy
``## 14<separator>`` heading shape (backwards-compat).

Per docs/plans/amendment-136-loam-amend-seal-section-14-backfill-regex-widening.md §4.

Pre-existing plan-docs use ``## 14. Method-decision record`` (legacy
shape). The widening must remain backwards-compatible — every
heading that matched the pre-widening regex MUST still match.
"""

from __future__ import annotations

import re
import pytest

from loam_amend.commands import seal as seal_module


@pytest.fixture
def section_header_re() -> re.Pattern:
    """Reconstruct the production regex from the seal-module source."""
    src_path = seal_module.__file__
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    m = re.search(
        r'section_header_re\s*=\s*re\.compile\(r"([^"]+)"\s*,\s*re\.MULTILINE\)',
        src,
    )
    assert m is not None, (
        "could not locate the section_header_re definition in seal.py"
    )
    return re.compile(m.group(1), re.MULTILINE)


# ----------------------------------------------------------------------
# Legacy heading shapes (AC.LAS14R.2) — backwards compat
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "heading_line",
    [
        # Pre-widening canonical (matched the old `^## 14[.\s]` regex):
        "## 14. Method-decision record",
        # Pre-widening alt (space separator):
        "## 14 Method-decision record",
        # Pre-widening alt (period + section title, builder hint):
        "## 14. Method-decision record (builder, post-build)",
    ],
)
def test_AC_LAS14R_2_legacy_section_header_still_matches(
    section_header_re: re.Pattern, heading_line: str
) -> None:
    """The widened regex must still match every legacy ``## 14<sep>``
    shape — the form used by every plan-doc authored before the
    canonical §-prefix convention landed. Backwards-compat is
    non-negotiable for this widening."""
    text = f"# Fixture plan-doc\n\n## 1. Summary\n\nbody.\n\n{heading_line}\n\nbody.\n"
    m = section_header_re.search(text)
    assert m is not None, (
        f"AC.LAS14R.2 violation: legacy heading {heading_line!r} "
        f"did not match the widened regex {section_header_re.pattern!r} "
        "— widening is NOT backwards-compatible"
    )
    # Match must start at column 0 (line-anchored)
    assert text[m.start():].startswith("## 14"), (
        "match must begin at the literal '## 14' prefix"
    )


def test_AC_LAS14R_2_negative_no_match_on_section_15_or_140(
    section_header_re: re.Pattern,
) -> None:
    """The widened regex must NOT over-match on neighbouring section
    numbers (15, 140, etc.). Anchoring + separator class prevent that
    — this test pins the negative case."""
    bad_texts = [
        "## 15. Some other section\n",
        "## 140 Should-not-match\n",
        "## 14no-separator\n",
        "## §15 — other section\n",
    ]
    for t in bad_texts:
        text = f"# fixture\n\n{t}\n"
        m = section_header_re.search(text)
        assert m is None, (
            f"AC.LAS14R.2 over-match: regex matched non-§14 heading: {t!r}"
        )
