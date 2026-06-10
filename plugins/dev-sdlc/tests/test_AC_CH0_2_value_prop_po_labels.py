"""AC.CH0.2 — AC.PO.1 / AC.PO.2 defined for real (KEEL Phase 1).

`grep -c "AC\\.PO\\.[12]" docs/VALUE_PROPOSITION.md` >= 2; each label
sits on its corresponding test verbatim and names Charter #0 as its
source. Closes the implementation-fidelity audit's D6 phantom-anchor
finding. Plan: docs/plans/keel-adoption-program.md §5.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALUE_PROP = REPO_ROOT / "docs" / "VALUE_PROPOSITION.md"

PO1_TEST_VERBATIM = (
    "Does this reduce the translation burden between the user's "
    "natural-language intent and AI-effective execution?"
)
PO2_TEST_VERBATIM = "Does this add to the toolkit the primary persona can draw from?"


def test_po_label_count_at_least_two() -> None:
    text = VALUE_PROP.read_text(encoding="utf-8")
    count = len(re.findall(r"AC\.PO\.[12]", text))
    assert count >= 2, f"AC.PO.[12] label count {count} < 2"


def test_po1_label_sits_on_its_test_verbatim() -> None:
    text = VALUE_PROP.read_text(encoding="utf-8")
    m = re.search(r"### AC\.PO\.1[^\n]*\n+(.{0,400})", text, re.S)
    assert m, "AC.PO.1 heading missing"
    assert PO1_TEST_VERBATIM in m.group(1), (
        "AC.PO.1 label does not sit on the primary-persona test verbatim"
    )


def test_po2_label_sits_on_its_test_verbatim() -> None:
    text = VALUE_PROP.read_text(encoding="utf-8")
    m = re.search(r"### AC\.PO\.2[^\n]*\n+(.{0,400})", text, re.S)
    assert m, "AC.PO.2 heading missing"
    assert PO2_TEST_VERBATIM in m.group(1), (
        "AC.PO.2 label does not sit on the harness test verbatim"
    )


def test_labels_name_charter_entry_0_as_source() -> None:
    text = VALUE_PROP.read_text(encoding="utf-8")
    assert "Charter entry #0" in text, (
        "the AC.PO labels must name Charter entry #0 as their source"
    )
    assert "docs/charter.md" in text, (
        "the AC.PO labels must point at docs/charter.md"
    )
