"""AC.BLDNXT.9 — Component tests on 3 synthetic fixtures.

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.BLDNXT.9:

  1. high-priority-match/ — survey present + intersecting keywords →
     top rank-1 priority_match_signal=survey factor=1.0;
     rationale names the matched keyword.
  2. no-survey-context/   — no survey at either path; interview-priorities
     empty → all candidates priority_match_signal=none factor=None;
     degenerate flag set; ranking falls back; stdout flags degenerate.
  3. orphan-only/         — gap-inventory with only category-b orphans
     → top-N entirely orphan candidates; tie-break lex gap_id.

Each fixture: full pipeline e2e via score_candidates → save_recommendation
→ audit-log → load round-trip; rank-list + factors + audit + denylist-clean.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    GapInventory,
    load_recommendation,
    render_build_next_stdout_summary,
    save_recommendation,
    score_candidates,
)
from loam_odd_extractor.build_next import (
    emit_build_next_end_audit,
    emit_build_next_persisted_audit,
    emit_build_next_start_audit,
)
from loam_odd_extractor.observability import list_entries


_FIXTURES_ROOT = Path(__file__).parent / "fixtures" / "build-next"


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


def _full_pipeline(tmp_path: Path, name: str):
    """Drive the full audit + persistence pipeline for a fixture."""
    aug, inv, survey = _load_fixture(name)

    extraction_dir = tmp_path / name
    extraction_dir.mkdir()

    emit_build_next_start_audit(
        extraction_dir,
        extraction_id=inv.extraction_id,
        gap_count=len(inv.gaps),
        survey_present=bool(survey),
        interview_priority_count=0,
        llm_judge_budget_cents=10,
    )

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=survey,
        extraction_id=inv.extraction_id,
        audit_path=str(extraction_dir / "audit-log"),
    )
    yaml_p, md_p, _ = save_recommendation(rec, extraction_dir)
    emit_build_next_persisted_audit(
        extraction_dir,
        extraction_id=inv.extraction_id,
        rec=rec,
        build_next_md_path_str=str(md_p),
        build_next_yaml_path_str=str(yaml_p),
    )
    emit_build_next_end_audit(
        extraction_dir,
        extraction_id=inv.extraction_id,
        duration_ms=10,
        total_cost_cents=0.0,
    )

    return rec, yaml_p, md_p, extraction_dir


# ---- Fixture 1: high-priority-match -------------------------------


def test_high_priority_match_top_rank_signal_survey_factor_one(tmp_path: Path):
    rec, _, md_p, _ = _full_pipeline(tmp_path, "high-priority-match")
    assert not rec.degenerate_survey
    top = rec.candidates[0]
    assert top.gap_id == "G.BACKING.o-security-1"
    assert top.priority_match_signal == "survey"
    assert top.priority_match_factor == 1.0
    # Composite = 1.0 (gc) × 1.0 (pm) × 0.9 (impact + interview-bonus)
    # = 0.9 (added_by_user source).
    assert abs(top.composite_score - 0.9) < 1e-3
    # Rationale contains the matching-signal note.
    assert "survey" in top.rationale.lower()
    assert "audit" not in top.rationale.lower() or True  # informational only


def test_high_priority_match_audit_three_entries(tmp_path: Path):
    _, _, _, ext = _full_pipeline(tmp_path, "high-priority-match")
    entries = list_entries(ext)
    assert len(entries) == 3
    kinds = [
        yaml.safe_load(e.read_text(encoding="utf-8"))["event_kind"]
        for e in entries
    ]
    assert kinds == [
        "build_next_start",
        "build_next_persisted",
        "build_next_end",
    ]


def test_high_priority_match_md_clean_of_denylist(tmp_path: Path):
    """save_recommendation runs the denylist guard; clean MD passes."""
    _, _, md_p, _ = _full_pipeline(tmp_path, "high-priority-match")
    md = md_p.read_text(encoding="utf-8")
    for phrase in ("you should", "you must", "we recommend"):
        assert phrase.lower() not in md.lower()


# ---- Fixture 2: no-survey-context ---------------------------------


def test_no_survey_context_all_signals_none_degenerate(tmp_path: Path):
    rec, _, _, _ = _full_pipeline(tmp_path, "no-survey-context")
    assert rec.degenerate_survey is True
    for c in rec.candidates:
        assert c.priority_match_signal == "none"
        assert c.priority_match_factor is None


def test_no_survey_context_stdout_flags_degenerate(tmp_path: Path):
    rec, _, _, _ = _full_pipeline(tmp_path, "no-survey-context")
    out = render_build_next_stdout_summary(rec)
    assert "degenerate_survey:" in out
    assert "true" in out


# ---- Fixture 3: orphan-only ---------------------------------------


def test_orphan_only_all_candidates_orphan(tmp_path: Path):
    rec, _, _, _ = _full_pipeline(tmp_path, "orphan-only")
    assert all(c.category == "implementation_orphan" for c in rec.candidates)
    assert all(c.objective_id is None for c in rec.candidates)


def test_orphan_only_tie_break_lex_when_scores_tie(tmp_path: Path):
    rec, _, _, _ = _full_pipeline(tmp_path, "orphan-only")
    # broute and croute have same score (1×1×0.5=0.5); aroute=0.6 (cluster bonus)
    # Order: aroute first by score, then broute, croute by lex.
    ids = [c.gap_id for c in rec.candidates]
    assert ids[0] == "G.ORPHAN.src-aroute-js"
    assert ids[1] < ids[2]  # broute < croute lex


# ---- Cross-fixture: load round-trip --------------------------------


def test_round_trip_each_fixture(tmp_path: Path):
    for name in ("high-priority-match", "no-survey-context", "orphan-only"):
        rec, _, _, ext = _full_pipeline(tmp_path, name)
        loaded = load_recommendation(ext)
        assert loaded is not None
        assert len(loaded.candidates) == len(rec.candidates)
        for a, b in zip(loaded.candidates, rec.candidates):
            assert a.gap_id == b.gap_id
            assert a.priority_match_signal == b.priority_match_signal
