"""AC.GAPAN.3 — analyze_gaps pure function.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.3:

- analyze_gaps(*, augmented_objectives, backing_map, evidence_rows,
  extraction_id) -> GapInventory.
- Pure function, no I/O, deterministic, no LLM call.
- For each objective: empty backing OR all-rows-WEAK OR
  HYPOTHESISED-with-no-rows → category-a Gap.
- For each unclaimed evidence row: orphan → category-b Gap; same-file
  collapse.
- Group-key in rationale.
"""

from __future__ import annotations

from loam_odd_extractor import (
    BackingMapEntry,
    ConfidenceBand,
    analyze_gaps,
)

from _gapan_helpers import (
    make_aug_set,
    make_backing_map,
    make_objective,
    make_raw_dict,
    make_row,
)


def test_clean_full_backing_no_gaps() -> None:
    obj = make_objective(idx=1, band=ConfidenceBand.VERIFIED)
    row = make_row(path="src/dispute.js", kind="route", confidence="STRONG")
    bm = make_backing_map(
        [
            BackingMapEntry(
                objective_id=obj.objective_id,
                evidence_rows=[row],
                match_rationale="STRONG match",
            ),
        ],
    )
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[
            make_raw_dict(path="src/dispute.js", kind="route"),
        ],
        extraction_id="repo-1",
    )
    assert inv.summary.total == 0
    assert inv.summary.category_a_count == 0
    assert inv.summary.category_b_count == 0


def test_empty_backing_plausible_yields_strong_category_a() -> None:
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    bm = make_backing_map(
        [
            BackingMapEntry(
                objective_id=obj.objective_id,
                evidence_rows=[],
                match_rationale="no rows matched",
            ),
        ],
    )
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[],
        extraction_id="repo-1",
    )
    assert inv.summary.category_a_count == 1
    assert inv.summary.strong_count == 1
    assert inv.gaps[0].category == "objective_without_verified_backing"
    assert inv.gaps[0].confidence == "STRONG"
    assert inv.gaps[0].objective_id == obj.objective_id


def test_hypothesised_no_rows_yields_weak_category_a() -> None:
    obj = make_objective(idx=1, band=ConfidenceBand.HYPOTHESISED)
    bm = make_backing_map(
        [
            BackingMapEntry(
                objective_id=obj.objective_id,
                evidence_rows=[],
                match_rationale="LLM-derived; no implementation",
            ),
        ],
    )
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[],
        extraction_id="repo-1",
    )
    assert inv.summary.weak_count == 1
    assert inv.gaps[0].confidence == "WEAK"
    assert inv.gaps[0].category == "objective_without_verified_backing"


def test_all_weak_rows_yields_weak_category_a() -> None:
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    weak_row = make_row(path="src/auth.js", confidence="WEAK")
    bm = make_backing_map(
        [
            BackingMapEntry(
                objective_id=obj.objective_id,
                evidence_rows=[weak_row],
                match_rationale="weak signal only",
            ),
        ],
    )
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[make_raw_dict(path="src/auth.js")],
        extraction_id="repo-1",
    )
    assert inv.summary.category_a_count == 1
    assert inv.gaps[0].confidence == "WEAK"
    assert inv.gaps[0].evidence_rows  # WEAK rows preserved


def test_orphan_same_file_collapses_to_one_gap() -> None:
    obj = make_objective(idx=1, band=ConfidenceBand.VERIFIED)
    bm = make_backing_map(
        [
            BackingMapEntry(
                objective_id=obj.objective_id,
                evidence_rows=[make_row(path="src/known.js", confidence="STRONG")],
                match_rationale="claimed",
            ),
        ],
    )
    # Three rows in the same orphan file collapse to one Gap.
    evidence_rows = [
        make_raw_dict(path="src/known.js"),  # claimed; not orphan
        make_raw_dict(path="src/orphan.js", line=10, kind="route"),
        make_raw_dict(path="src/orphan.js", line=30, kind="route"),
        make_raw_dict(path="src/orphan.js", line=50, kind="callback"),
    ]
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=evidence_rows,
        extraction_id="repo-1",
    )
    orphan_gaps = [
        g for g in inv.gaps if g.category == "implementation_orphan"
    ]
    assert len(orphan_gaps) == 1
    assert orphan_gaps[0].confidence == "STRONG"  # production rows
    assert "path:src/orphan.js" in orphan_gaps[0].rationale
    assert len(orphan_gaps[0].evidence_rows) == 3


def test_orphan_test_only_yields_weak_category_b() -> None:
    obj = make_objective(idx=1, band=ConfidenceBand.VERIFIED)
    bm = make_backing_map([
        BackingMapEntry(
            objective_id=obj.objective_id,
            evidence_rows=[make_row(path="src/known.js", confidence="STRONG")],
            match_rationale="claimed",
        ),
    ])
    evidence_rows = [
        make_raw_dict(path="src/known.js"),  # claimed
        make_raw_dict(path="tests/orphan.test.js", kind="test"),
        make_raw_dict(path="tests/orphan.test.js", kind="test", line=20),
    ]
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=evidence_rows,
        extraction_id="repo-1",
    )
    orphan_gaps = [g for g in inv.gaps if g.category == "implementation_orphan"]
    assert len(orphan_gaps) == 1
    assert orphan_gaps[0].confidence == "WEAK"


def test_determinism_repeated_calls_byte_identical() -> None:
    """analyze_gaps is deterministic; same input → same output."""
    obj1 = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    obj2 = make_objective(idx=2, band=ConfidenceBand.HYPOTHESISED)
    bm = make_backing_map([
        BackingMapEntry(objective_id=obj1.objective_id, evidence_rows=[]),
        BackingMapEntry(objective_id=obj2.objective_id, evidence_rows=[]),
    ])
    rows = [
        make_raw_dict(path="src/a.js"),
        make_raw_dict(path="src/b.js", kind="callback"),
    ]
    fixed_ts = "2026-05-04T16:00:00+00:00"
    inv1 = analyze_gaps(
        augmented_objectives=make_aug_set([obj1, obj2]),
        backing_map=bm,
        evidence_rows=rows,
        extraction_id="repo-1",
        analyzed_at=fixed_ts,
        audit_path="/tmp/audit",
    )
    inv2 = analyze_gaps(
        augmented_objectives=make_aug_set([obj1, obj2]),
        backing_map=bm,
        evidence_rows=rows,
        extraction_id="repo-1",
        analyzed_at=fixed_ts,
        audit_path="/tmp/audit",
    )
    # Same gap_ids in same order, same payload.
    assert [g.gap_id for g in inv1.gaps] == [g.gap_id for g in inv2.gaps]
    assert inv1.model_dump() == inv2.model_dump()


def test_orphan_path_sort_order_deterministic() -> None:
    """Orphans are clustered + iterated in path-sorted order."""
    obj = make_objective(idx=1, band=ConfidenceBand.VERIFIED)
    bm = make_backing_map([
        BackingMapEntry(
            objective_id=obj.objective_id,
            evidence_rows=[make_row(path="src/known.js", confidence="STRONG")],
        ),
    ])
    evidence_rows = [
        make_raw_dict(path="src/known.js"),
        make_raw_dict(path="src/zzz.js"),
        make_raw_dict(path="src/aaa.js"),
        make_raw_dict(path="src/mmm.js"),
    ]
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=evidence_rows,
        extraction_id="repo-1",
    )
    orphan_paths = [
        g.gap_id for g in inv.gaps
        if g.category == "implementation_orphan"
    ]
    # gap_ids carry slugified path; sort order is alphabetic by path.
    assert orphan_paths == [
        "G.ORPHAN.src-aaa-js",
        "G.ORPHAN.src-mmm-js",
        "G.ORPHAN.src-zzz-js",
    ]


def test_missing_backing_entry_treated_as_empty() -> None:
    """Objective with NO backing-map entry behaves like empty backing."""
    obj = make_objective(idx=1, band=ConfidenceBand.PLAUSIBLE)
    bm = make_backing_map([])  # empty backing-map
    inv = analyze_gaps(
        augmented_objectives=make_aug_set([obj]),
        backing_map=bm,
        evidence_rows=[],
        extraction_id="repo-1",
    )
    assert inv.summary.category_a_count == 1
    assert inv.gaps[0].confidence == "STRONG"
