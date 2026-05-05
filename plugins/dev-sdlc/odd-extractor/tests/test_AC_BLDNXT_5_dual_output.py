"""AC.BLDNXT.5 — Output cap + dual output (build-next.md + build-next.yaml).

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.BLDNXT.5:

- Default top-N = 10; ``--limit N`` overrides.
- ``build-next.md`` is human-readable with header + per-candidate
  ``### Rank K — <gap_id>`` block + closing line.
- ``build-next.yaml`` carries the typed ``BuildNextRecommendation``.
- Atomic tmp+rename on both surfaces.
- ``truncated_count`` accurate when underlying-list exceeds limit.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    BuildNextRecommendation,
    GapInventory,
    save_recommendation,
    score_candidates,
    build_next_md_path,
    build_next_yaml_path,
)


_FIXTURES_ROOT = (
    Path(__file__).parent / "fixtures" / "build-next"
)


def _load_fixture(name: str):
    fdir = _FIXTURES_ROOT / name
    aug_payload = yaml.safe_load(
        (fdir / "augmented-objectives.yaml").read_text(encoding="utf-8")
    )
    aug_payload.pop("schema_version", None)
    aug = AugmentedObjectiveSet.model_validate(aug_payload)
    inv_payload = yaml.safe_load(
        (fdir / "gap-inventory.yaml").read_text(encoding="utf-8")
    )
    inv_payload.pop("schema_version", None)
    inv = GapInventory.model_validate(inv_payload)
    return aug, inv


def test_both_files_written(tmp_path: Path):
    aug, inv = _load_fixture("orphan-only")
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
    )
    yaml_p, md_p, wrote = save_recommendation(rec, tmp_path)
    assert wrote is True
    assert yaml_p == build_next_yaml_path(tmp_path)
    assert md_p == build_next_md_path(tmp_path)
    assert yaml_p.exists()
    assert md_p.exists()


def test_yaml_round_trip(tmp_path: Path):
    aug, inv = _load_fixture("orphan-only")
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
    )
    yaml_p, _, _ = save_recommendation(rec, tmp_path)
    raw = yaml.safe_load(yaml_p.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 1
    assert raw["extraction_id"] == inv.extraction_id
    assert len(raw["candidates"]) == 3
    raw.pop("schema_version", None)
    rec2 = BuildNextRecommendation.model_validate(raw)
    assert len(rec2.candidates) == 3


def test_markdown_has_required_structure(tmp_path: Path):
    aug, inv = _load_fixture("orphan-only")
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
    )
    _, md_p, _ = save_recommendation(rec, tmp_path)
    md = md_p.read_text(encoding="utf-8")
    # Header + degenerate flag
    assert md.startswith("# Build-next recommendation for ")
    assert "candidate_count: 3" in md
    assert "degenerate_survey" in md
    # Per-candidate rank headings
    assert "### Rank 1 — `G.ORPHAN.src-aroute-js`" in md
    assert "### Rank 2 — " in md
    assert "### Rank 3 — " in md
    # Composite score field
    assert "composite_score:" in md
    # Closing pull-point line
    assert "Persona invokes via" in md
    assert "informative" in md.lower()


def test_limit_truncates_with_accurate_count(tmp_path: Path):
    """Top-N=2 on a 3-gap inventory → truncated_count=1."""
    aug, inv = _load_fixture("orphan-only")
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
        limit=2,
    )
    assert len(rec.candidates) == 2
    assert rec.truncated_count == 1


def test_default_limit_is_ten(tmp_path: Path):
    """Default keeps all candidates when underlying < 10."""
    aug, inv = _load_fixture("orphan-only")
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
    )
    assert len(rec.candidates) == 3
    assert rec.truncated_count == 0


def test_empty_gap_inventory_renders_clean(tmp_path: Path):
    """Zero gaps → empty candidate list; markdown still renders."""
    from loam_odd_extractor import GapSummary

    aug, _ = _load_fixture("orphan-only")
    inv = GapInventory(
        extraction_id="empty",
        analyzed_at="2026-05-04T00:00:00+00:00",
        audit_path="/tmp",
        gaps=[],
        summary=GapSummary(),
    )
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="empty",
        audit_path="/tmp",
    )
    yaml_p, md_p, _ = save_recommendation(rec, tmp_path)
    md = md_p.read_text(encoding="utf-8")
    assert "(no candidates surfaced" in md
    raw = yaml.safe_load(yaml_p.read_text(encoding="utf-8"))
    assert raw["candidates"] == []
