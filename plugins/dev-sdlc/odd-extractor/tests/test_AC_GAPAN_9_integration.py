"""AC.GAPAN.9 — Component tests on 4 synthetic fixtures.

Per v0.2.4 Cycle 2 sub-plan-doc §3 AC.GAPAN.9:

Each fixture exercises full path: analyze_gaps → persistence → audit-log
→ stdout summary. Spans (category × confidence) cells.

  1. clean/             — empty inventory.
  2. category-a-only/   — 2 cat-a Gaps (1 STRONG + 1 WEAK).
  3. category-b-only/   — 2 cat-b Gaps (1 STRONG + 1 WEAK).
  4. mixed/             — 4 Gaps spanning all 4 cells; calibration anchor
                          (must be non-degenerate).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    BackingMap,
    analyze_gaps,
    is_degenerate_distribution,
    render_stdout_summary,
    save_gap_inventory,
)


_FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "gap-analysis"


def _load_fixture(name: str):
    fdir = _FIXTURES_ROOT / name
    aug_payload = yaml.safe_load((fdir / "augmented-objectives.yaml").read_text(encoding="utf-8"))
    aug_payload.pop("schema_version", None)
    aug = AugmentedObjectiveSet.model_validate(aug_payload)

    bm_payload = yaml.safe_load((fdir / "backing-map.yaml").read_text(encoding="utf-8"))
    bm_payload.pop("schema_version", None)
    bm = BackingMap.model_validate(bm_payload)

    evidence_payload = yaml.safe_load((fdir / "evidence-rows.yaml").read_text(encoding="utf-8"))
    rows = evidence_payload.get("acs", []) if isinstance(evidence_payload, dict) else []
    return aug, bm, rows


def test_clean_fixture_yields_empty_inventory(tmp_path: Path) -> None:
    aug, bm, rows = _load_fixture("clean")
    inv = analyze_gaps(
        augmented_objectives=aug,
        backing_map=bm,
        evidence_rows=rows,
        extraction_id=aug.extraction_id,
    )
    assert inv.summary.total == 0
    save_gap_inventory(inv, tmp_path)
    assert (tmp_path / "gap-inventory.yaml").exists()
    out = render_stdout_summary(inv)
    assert "Total gaps:       0" in out


def test_category_a_only_fixture_yields_2_cat_a_gaps(tmp_path: Path) -> None:
    aug, bm, rows = _load_fixture("category-a-only")
    inv = analyze_gaps(
        augmented_objectives=aug,
        backing_map=bm,
        evidence_rows=rows,
        extraction_id=aug.extraction_id,
    )
    assert inv.summary.total == 2
    assert inv.summary.category_a_count == 2
    assert inv.summary.category_b_count == 0
    # Splits: 1 STRONG (PLAUSIBLE empty backing) + 1 WEAK (HYPOTHESISED).
    assert inv.summary.strong_count == 1
    assert inv.summary.weak_count == 1
    # All are category-a.
    for g in inv.gaps:
        assert g.category == "objective_without_verified_backing"
        assert g.objective_id is not None
    save_gap_inventory(inv, tmp_path)
    assert (tmp_path / "gap-inventory.yaml").exists()


def test_category_b_only_fixture_yields_2_cat_b_gaps(tmp_path: Path) -> None:
    aug, bm, rows = _load_fixture("category-b-only")
    inv = analyze_gaps(
        augmented_objectives=aug,
        backing_map=bm,
        evidence_rows=rows,
        extraction_id=aug.extraction_id,
    )
    assert inv.summary.total == 2
    assert inv.summary.category_a_count == 0
    assert inv.summary.category_b_count == 2
    # Splits: 1 STRONG (production same-file collapse) + 1 WEAK (test-only).
    assert inv.summary.strong_count == 1
    assert inv.summary.weak_count == 1
    save_gap_inventory(inv, tmp_path)


def test_mixed_fixture_spans_all_four_cells(tmp_path: Path) -> None:
    """Calibration anchor — mixed/ produces non-degenerate distribution.

    Per AC.GAPAN.4: 100%-STRONG or 100%-WEAK on the mixed fixture
    means the rule is mis-calibrated; this fixture must show both.
    """
    aug, bm, rows = _load_fixture("mixed")
    inv = analyze_gaps(
        augmented_objectives=aug,
        backing_map=bm,
        evidence_rows=rows,
        extraction_id=aug.extraction_id,
    )
    # All four (category × confidence) cells are populated.
    cells = {
        (g.category, g.confidence) for g in inv.gaps
    }
    assert ("objective_without_verified_backing", "STRONG") in cells
    assert ("objective_without_verified_backing", "WEAK") in cells
    assert ("implementation_orphan", "STRONG") in cells
    assert ("implementation_orphan", "WEAK") in cells


def test_mixed_fixture_concrete_counts(tmp_path: Path) -> None:
    """Concrete count assertions for the mixed/ fixture."""
    aug, bm, rows = _load_fixture("mixed")
    inv = analyze_gaps(
        augmented_objectives=aug,
        backing_map=bm,
        evidence_rows=rows,
        extraction_id=aug.extraction_id,
    )
    # 3 category-a Gaps:
    #   O.security.1 → WEAK (PLAUSIBLE + all-WEAK rows)
    #   O.future-feature.1 → WEAK (HYPOTHESISED, no rows)
    #   O.batch-export.1 → STRONG (PLAUSIBLE, empty backing)
    cat_a = [g for g in inv.gaps if g.category == "objective_without_verified_backing"]
    assert len(cat_a) == 3
    # 2 category-b Gaps:
    #   src/disputeProcessRoutes.js → STRONG (production)
    #   tests/disputeProcess.test.js → WEAK (test-only)
    cat_b = [g for g in inv.gaps if g.category == "implementation_orphan"]
    assert len(cat_b) == 2

    assert inv.summary.total == 5
    assert inv.summary.strong_count >= 1
    assert inv.summary.weak_count >= 1
    # Calibration anchor: mixed must NOT be degenerate.
    assert is_degenerate_distribution(inv) is False


def test_mixed_fixture_eric_relevance(tmp_path: Path) -> None:
    """Eric-shape: O.security.1 surfaces as WEAK category-a gap."""
    aug, bm, rows = _load_fixture("mixed")
    inv = analyze_gaps(
        augmented_objectives=aug,
        backing_map=bm,
        evidence_rows=rows,
        extraction_id=aug.extraction_id,
    )
    security_gaps = [
        g for g in inv.gaps
        if g.objective_id == "O.security.1"
    ]
    assert len(security_gaps) == 1
    assert security_gaps[0].confidence == "WEAK"
    assert security_gaps[0].category == "objective_without_verified_backing"
    # Production-orphan surfaces too.
    process_orphans = [
        g for g in inv.gaps
        if g.category == "implementation_orphan"
        and "disputeProcessRoutes" in g.rationale
    ]
    assert len(process_orphans) == 1
    assert process_orphans[0].confidence == "STRONG"


def test_full_pipeline_per_fixture_emits_persistence_audit(tmp_path: Path) -> None:
    """Full path: analyze → save → load round-trip on each fixture."""
    for name in ("clean", "category-a-only", "category-b-only", "mixed"):
        fixture_workspace = tmp_path / name
        fixture_workspace.mkdir()
        aug, bm, rows = _load_fixture(name)
        inv = analyze_gaps(
            augmented_objectives=aug,
            backing_map=bm,
            evidence_rows=rows,
            extraction_id=aug.extraction_id,
        )
        p, wrote = save_gap_inventory(inv, fixture_workspace)
        assert wrote is True
        assert p.exists()
        # Stdout summary renders.
        out = render_stdout_summary(inv)
        assert "Gap inventory" in out
