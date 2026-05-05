"""AC.BLDNXT.4 — Idempotence semantics.

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.BLDNXT.4:

- Re-run on unchanged inputs produces content-identical outputs
  (excluding ``analyzed_at``).
- Skip-write on no-change.
- LLM-judge structured-JSON variance bounded — temperature=0,
  identical stub returns same shape.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    GapInventory,
    save_recommendation,
    score_candidates,
    load_recommendation,
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
    survey_path = fdir / "onboarding-survey.md"
    survey_text = (
        survey_path.read_text(encoding="utf-8") if survey_path.exists() else None
    )
    return aug, inv, survey_text


def test_three_sequential_runs_byte_identical_no_survey(tmp_path: Path):
    """Three sequential runs against no-survey-context produce
    content-identical outputs (modulo analyzed_at)."""
    aug, inv, survey = _load_fixture("no-survey-context")
    fixed_ts = "2026-05-04T12:00:00+00:00"

    rec_first = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=survey,
        extraction_id=inv.extraction_id,
        audit_path=str(tmp_path / "audit-log"),
        analyzed_at=fixed_ts,
    )
    yaml_p, md_p, wrote1 = save_recommendation(rec_first, tmp_path)
    assert wrote1 is True
    yaml_text_first = yaml_p.read_text(encoding="utf-8")
    md_text_first = md_p.read_text(encoding="utf-8")

    # Run 2 — same inputs, same fixed timestamp → byte-identical YAML
    # AND skip-write fires (wrote=False) since content-hash matches.
    rec_second = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=survey,
        extraction_id=inv.extraction_id,
        audit_path=str(tmp_path / "audit-log"),
        analyzed_at=fixed_ts,
    )
    yaml_p2, md_p2, wrote2 = save_recommendation(rec_second, tmp_path)
    assert wrote2 is False  # idempotent skip
    yaml_text_second = yaml_p2.read_text(encoding="utf-8")
    md_text_second = md_p2.read_text(encoding="utf-8")
    assert yaml_text_first == yaml_text_second
    assert md_text_first == md_text_second

    # Run 3 — same inputs, DIFFERENT analyzed_at → still skip-write
    # because analyzed_at is excluded from the content-hash.
    rec_third = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=survey,
        extraction_id=inv.extraction_id,
        audit_path=str(tmp_path / "audit-log"),
        analyzed_at="2026-05-04T13:00:00+00:00",
    )
    _, _, wrote3 = save_recommendation(rec_third, tmp_path)
    assert wrote3 is False


def test_changed_input_triggers_rewrite(tmp_path: Path):
    """When inputs change, save_recommendation rewrites both files."""
    aug, inv, survey = _load_fixture("no-survey-context")
    rec1 = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=survey,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
    )
    save_recommendation(rec1, tmp_path)

    # Now use a different fixture's inputs; expect rewrite.
    aug2, inv2, survey2 = _load_fixture("orphan-only")
    rec2 = score_candidates(
        gap_inventory=inv2,
        augmented_objectives=aug2,
        survey_text=survey2,
        extraction_id=inv2.extraction_id,
        audit_path="/tmp/audit-log",
    )
    _, _, wrote = save_recommendation(rec2, tmp_path)
    assert wrote is True


def test_load_after_save_round_trip(tmp_path: Path):
    aug, inv, survey = _load_fixture("no-survey-context")
    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=survey,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
    )
    save_recommendation(rec, tmp_path)
    loaded = load_recommendation(tmp_path)
    assert loaded is not None
    assert loaded.extraction_id == rec.extraction_id
    assert len(loaded.candidates) == len(rec.candidates)
    for a, b in zip(loaded.candidates, rec.candidates):
        assert a.gap_id == b.gap_id
        assert a.priority_match_signal == b.priority_match_signal
        assert abs(a.composite_score - b.composite_score) < 1e-6


def test_load_returns_none_when_absent(tmp_path: Path):
    assert load_recommendation(tmp_path) is None
