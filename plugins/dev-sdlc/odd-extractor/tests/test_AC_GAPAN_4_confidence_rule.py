"""AC.GAPAN.4 — Confidence rule (STRONG/WEAK).

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.4:

STRONG when:
  - category-a + objective ∈ {V, P} + empty backing.
  - category-b + at least one non-test/non-config orphan row.

WEAK when:
  - category-a + HYPOTHESISED.
  - category-a + all rows WEAK.
  - category-b + all rows test/config.

Halt-on-degenerate (100%-STRONG or 100%-WEAK on a non-trivial
inventory) per the calibration anchor.
"""

from __future__ import annotations

import pytest

from loam_odd_extractor import (
    BackingMapEntry,
    ConfidenceBand,
    GapInventory,
    GapSummary,
    analyze_gaps,
    is_degenerate_distribution,
)
from loam_odd_extractor.gap_analysis import _classify_confidence

from _gapan_helpers import (
    make_aug_set,
    make_backing_map,
    make_objective,
    make_raw_dict,
    make_row,
)


# ---- Table-driven category-a branch coverage ---------------------


@pytest.mark.parametrize(
    "band,rows_present,all_rows_weak,expected",
    [
        # V/P + empty backing → STRONG
        (ConfidenceBand.VERIFIED, False, False, "STRONG"),
        (ConfidenceBand.PLAUSIBLE, False, False, "STRONG"),
        # HYPOTHESISED + empty → WEAK
        (ConfidenceBand.HYPOTHESISED, False, False, "WEAK"),
        # V/P + all-weak rows → WEAK
        (ConfidenceBand.VERIFIED, True, True, "WEAK"),
        (ConfidenceBand.PLAUSIBLE, True, True, "WEAK"),
        # HYPOTHESISED with rows present (rare but valid) → WEAK
        (ConfidenceBand.HYPOTHESISED, True, True, "WEAK"),
        (ConfidenceBand.HYPOTHESISED, True, False, "WEAK"),
    ],
)
def test_category_a_branches(band, rows_present, all_rows_weak, expected) -> None:
    actual = _classify_confidence(
        category="objective_without_verified_backing",
        band=band,
        rows_present=rows_present,
        all_rows_weak=all_rows_weak,
    )
    assert actual == expected


# ---- Table-driven category-b branch coverage ---------------------


@pytest.mark.parametrize(
    "has_non_test_or_config_row,expected",
    [
        (True, "STRONG"),
        (False, "WEAK"),
    ],
)
def test_category_b_branches(has_non_test_or_config_row, expected) -> None:
    actual = _classify_confidence(
        category="implementation_orphan",
        has_non_test_or_config_row=has_non_test_or_config_row,
    )
    assert actual == expected


# ---- Halt-on-degenerate detection -------------------------------


def test_degenerate_all_strong_halts() -> None:
    """100% STRONG on >=2 gaps → halt-and-surface.

    Bypass the summary-mismatch validator with model_construct since we
    only need the summary aggregate for is_degenerate_distribution.
    """
    inv = GapInventory.model_construct(
        schema_version=1,
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
        gaps=[],
        summary=GapSummary(
            category_a_count=2, category_b_count=0,
            strong_count=5, weak_count=0, total=5,
        ),
    )
    assert is_degenerate_distribution(inv) is True


def test_degenerate_all_weak_halts() -> None:
    inv = GapInventory.model_construct(
        schema_version=1,
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
        gaps=[],
        summary=GapSummary(
            category_a_count=4, category_b_count=0,
            strong_count=0, weak_count=4, total=4,
        ),
    )
    assert is_degenerate_distribution(inv) is True


def test_mixed_distribution_not_degenerate() -> None:
    inv = GapInventory.model_construct(
        schema_version=1,
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
        gaps=[],
        summary=GapSummary(
            category_a_count=2, category_b_count=2,
            strong_count=2, weak_count=2, total=4,
        ),
    )
    assert is_degenerate_distribution(inv) is False


def test_single_gap_not_degenerate() -> None:
    """Single-gap inventories cannot span both confidences; not a halt."""
    inv = GapInventory.model_construct(
        schema_version=1,
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
        gaps=[],
        summary=GapSummary(
            category_a_count=1, category_b_count=0,
            strong_count=1, weak_count=0, total=1,
        ),
    )
    assert is_degenerate_distribution(inv) is False


def test_empty_inventory_not_degenerate() -> None:
    inv = GapInventory(
        extraction_id="repo-1",
        analyzed_at="2026-05-04T16:00:00+00:00",
        audit_path="/tmp/audit",
    )
    assert is_degenerate_distribution(inv) is False


# ---- End-to-end: confidence rule applied through analyze_gaps -----


def test_e2e_confidence_via_analyze_gaps() -> None:
    """A mixed scenario produces a non-degenerate distribution."""
    o_strong = make_objective(domain="auth", idx=1, band=ConfidenceBand.PLAUSIBLE)
    o_weak = make_objective(domain="audit", idx=1, band=ConfidenceBand.HYPOTHESISED)
    o_clean = make_objective(domain="orders", idx=1, band=ConfidenceBand.VERIFIED)
    bm = make_backing_map([
        BackingMapEntry(objective_id=o_strong.objective_id, evidence_rows=[]),
        BackingMapEntry(objective_id=o_weak.objective_id, evidence_rows=[]),
        BackingMapEntry(
            objective_id=o_clean.objective_id,
            evidence_rows=[
                make_row(path="src/orders.js", confidence="STRONG"),
            ],
        ),
    ])
    rows = [
        make_raw_dict(path="src/orders.js"),
        make_raw_dict(path="src/orphan-prod.js", kind="route"),
        make_raw_dict(path="tests/orphan.test.js", kind="test"),
    ]
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([o_strong, o_weak, o_clean]),
        backing_map=bm,
        evidence_rows=rows,
        extraction_id="repo-1",
    )
    assert inv.summary.strong_count > 0
    assert inv.summary.weak_count > 0
    assert is_degenerate_distribution(inv) is False
