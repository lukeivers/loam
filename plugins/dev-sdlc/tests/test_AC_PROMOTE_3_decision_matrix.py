"""AC.PROMOTE.3 — Decision matrix encoded in SKILL body.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.3: the SKILL body
contains a markdown table mirroring layered-skills §4.2 with all
10 row classes. Each row represents a signal-combination →
recommended action mapping. The 10 action labels (the
Recommendation column entries) must each appear in the body.
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "skill-promotion-review"
    / "SKILL.md"
)

# 10 row-class action labels per layered-skills §4.2 (lines
# 290-307 in docs/rebuild/plans/layered-skill-story-research-
# 2026-05-04.md). Match against the body's recommendation column
# (allow normalized casing / hyphenation).
EXPECTED_ROW_LABELS = (
    "Promote-to-base",
    "Promote-to-plugin",
    "Stay-workspace-local",
    "Author-time-fix",
    "Author-tests",
    "Defer",
    "Deprecate",
    "Promote-with-deprecation-pointer",
    "Fold-into-existing",
)


def _body() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"{SKILL_PATH}: frontmatter parse failed."
    return match.group(2)


def test_body_contains_markdown_table_with_ten_rows() -> None:
    """Body must contain a markdown table; the table must have at
    least 10 data rows (excluding header + separator).

    Markdown-table detection: contiguous lines starting with `|`
    that include the separator row (`|---|...|`). Count data rows
    = lines starting with `|` that are NOT the header and NOT the
    separator.
    """
    body = _body()
    lines = body.splitlines()

    # Find any contiguous run of `|`-led lines that contains a
    # markdown-table separator row (a `|---|...|` line).
    table_data_rows: list[str] = []
    in_table = False
    seen_separator = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            in_table = True
            if re.match(r"^\|[\s\-\|:]+\|$", stripped):
                seen_separator = True
                # Reset: discard prior accumulated lines (they were
                # the header).
                table_data_rows = []
                continue
            if seen_separator:
                table_data_rows.append(stripped)
        else:
            if in_table and seen_separator and len(table_data_rows) >= 10:
                break
            in_table = False
            seen_separator = False
            table_data_rows = []

    assert len(table_data_rows) >= 10, (
        "skill-promotion-review: body must contain a markdown table "
        "with at least 10 data rows (decision-matrix per layered-"
        f"skills §4.2). Found {len(table_data_rows)} data rows."
    )


def test_body_mentions_all_ten_row_class_labels() -> None:
    """All 10 row-class action labels appear in the body so the
    persona walking the matrix can match each candidate to a named
    action."""
    body = _body()
    for label in EXPECTED_ROW_LABELS:
        assert label in body, (
            f"skill-promotion-review: body must mention "
            f"row-class label `{label}` (per layered-skills §4.2 "
            "10-row decision matrix)."
        )
