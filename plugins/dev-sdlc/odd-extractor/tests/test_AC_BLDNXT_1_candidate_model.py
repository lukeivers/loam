"""AC.BLDNXT.1 — BuildNextCandidate Pydantic model.

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.BLDNXT.1:

- ``gap_id`` matches the gap-id regex.
- ``composite_score`` ∈ [0.0, 1.0]; equals factor product (with
  priority_match_factor=1.0 substituted when None).
- All factor fields ∈ [0.0, 1.0]; ``priority_match_factor`` may be
  None on the degenerate-survey path.
- ``priority_match_signal`` ∈ {survey, interview, keyword, llm_judge,
  none}.
- ``rationale`` ≥ 40 chars.
- ``category`` mirrors source Gap; ``objective_id`` set iff
  category-a.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import BuildNextCandidate, BuildNextRecommendation


# ---- Round-trip --------------------------------------------------


def test_candidate_roundtrip_minimal_category_a():
    c = BuildNextCandidate(
        gap_id="G.BACKING.o-security-1",
        composite_score=0.9,
        gap_confidence_factor=1.0,
        priority_match_factor=1.0,
        estimated_impact_factor=0.9,
        priority_match_signal="survey",
        rationale=(
            "This gap surfaces O.security.1 (PLAUSIBLE) — backing-"
            "confidence is STRONG; survey priorities matched."
        ),
        category="objective_without_verified_backing",
        objective_id="O.security.1",
    )
    assert c.gap_id == "G.BACKING.o-security-1"
    assert c.priority_match_signal == "survey"
    payload = c.model_dump(mode="json")
    c2 = BuildNextCandidate.model_validate(payload)
    assert c == c2


def test_candidate_roundtrip_orphan_with_none_priority_match():
    c = BuildNextCandidate(
        gap_id="G.ORPHAN.src-aroute-js",
        composite_score=0.6,
        gap_confidence_factor=1.0,
        priority_match_factor=None,
        estimated_impact_factor=0.6,
        priority_match_signal="none",
        rationale=(
            "This gap surfaces an implementation orphan cluster "
            "(3 unclaimed rows). No survey context available; "
            "priority-match degenerate."
        ),
        category="implementation_orphan",
        objective_id=None,
    )
    assert c.priority_match_factor is None
    # Round-trip: None excluded by exclude_none, so factor missing
    # roundtrips to None default.
    payload = c.model_dump(mode="json", exclude_none=True)
    assert "priority_match_factor" not in payload
    c2 = BuildNextCandidate.model_validate(payload)
    assert c2.priority_match_factor is None


# ---- Validation failures ----------------------------------------


def test_candidate_invalid_gap_id_regex():
    with pytest.raises(ValidationError):
        BuildNextCandidate(
            gap_id="not-a-valid-id",
            composite_score=0.5,
            gap_confidence_factor=1.0,
            priority_match_factor=1.0,
            estimated_impact_factor=0.5,
            priority_match_signal="survey",
            rationale="x" * 50,
            category="objective_without_verified_backing",
            objective_id="O.x.1",
        )


def test_candidate_composite_out_of_range():
    with pytest.raises(ValidationError):
        BuildNextCandidate(
            gap_id="G.BACKING.x",
            composite_score=1.5,  # > 1.0
            gap_confidence_factor=1.0,
            priority_match_factor=1.0,
            estimated_impact_factor=1.0,
            priority_match_signal="survey",
            rationale="x" * 50,
            category="objective_without_verified_backing",
            objective_id="O.x.1",
        )


def test_candidate_factor_product_must_match_composite():
    """Per AC.BLDNXT.1 — model_validator enforces consistency."""
    with pytest.raises(ValidationError) as excinfo:
        BuildNextCandidate(
            gap_id="G.BACKING.x",
            composite_score=0.99,  # but factors product = 0.5
            gap_confidence_factor=1.0,
            priority_match_factor=1.0,
            estimated_impact_factor=0.5,
            priority_match_signal="survey",
            rationale="x" * 50,
            category="objective_without_verified_backing",
            objective_id="O.x.1",
        )
    assert "composite_score" in str(excinfo.value)


def test_candidate_factor_product_with_none_pm_uses_one():
    """When priority_match_factor is None, composite = gc × 1 × impact."""
    c = BuildNextCandidate(
        gap_id="G.BACKING.x",
        composite_score=0.5,
        gap_confidence_factor=1.0,
        priority_match_factor=None,
        estimated_impact_factor=0.5,
        priority_match_signal="none",
        rationale="x" * 50,
        category="objective_without_verified_backing",
        objective_id="O.x.1",
    )
    assert c.composite_score == 0.5


def test_candidate_rationale_min_length_40():
    with pytest.raises(ValidationError):
        BuildNextCandidate(
            gap_id="G.BACKING.x",
            composite_score=0.5,
            gap_confidence_factor=1.0,
            priority_match_factor=1.0,
            estimated_impact_factor=0.5,
            priority_match_signal="survey",
            rationale="too short",
            category="objective_without_verified_backing",
            objective_id="O.x.1",
        )


def test_candidate_category_a_requires_objective_id():
    with pytest.raises(ValidationError):
        BuildNextCandidate(
            gap_id="G.BACKING.x",
            composite_score=0.5,
            gap_confidence_factor=1.0,
            priority_match_factor=1.0,
            estimated_impact_factor=0.5,
            priority_match_signal="survey",
            rationale="x" * 50,
            category="objective_without_verified_backing",
            objective_id=None,
        )


def test_candidate_category_b_forbids_objective_id():
    with pytest.raises(ValidationError):
        BuildNextCandidate(
            gap_id="G.ORPHAN.x",
            composite_score=0.5,
            gap_confidence_factor=1.0,
            priority_match_factor=1.0,
            estimated_impact_factor=0.5,
            priority_match_signal="survey",
            rationale="x" * 50,
            category="implementation_orphan",
            objective_id="O.x.1",
        )


def test_candidate_signal_value_must_be_known_literal():
    with pytest.raises(ValidationError):
        BuildNextCandidate(
            gap_id="G.BACKING.x",
            composite_score=0.5,
            gap_confidence_factor=1.0,
            priority_match_factor=1.0,
            estimated_impact_factor=0.5,
            priority_match_signal="random-string",
            rationale="x" * 50,
            category="objective_without_verified_backing",
            objective_id="O.x.1",
        )


# ---- BuildNextRecommendation container ----------------------


def test_recommendation_no_duplicate_gap_ids():
    c = BuildNextCandidate(
        gap_id="G.BACKING.x",
        composite_score=0.5,
        gap_confidence_factor=1.0,
        priority_match_factor=1.0,
        estimated_impact_factor=0.5,
        priority_match_signal="survey",
        rationale="x" * 50,
        category="objective_without_verified_backing",
        objective_id="O.x.1",
    )
    with pytest.raises(ValidationError):
        BuildNextRecommendation(
            extraction_id="x",
            analyzed_at="2026-05-04T00:00:00+00:00",
            audit_path="/tmp",
            candidates=[c, c],
        )


def test_recommendation_truncated_count_must_be_nonneg():
    with pytest.raises(ValidationError):
        BuildNextRecommendation(
            extraction_id="x",
            analyzed_at="2026-05-04T00:00:00+00:00",
            audit_path="/tmp",
            truncated_count=-1,
        )


def test_recommendation_round_trip():
    c = BuildNextCandidate(
        gap_id="G.ORPHAN.x",
        composite_score=0.5,
        gap_confidence_factor=1.0,
        priority_match_factor=None,
        estimated_impact_factor=0.5,
        priority_match_signal="none",
        rationale="x" * 50,
        category="implementation_orphan",
        objective_id=None,
    )
    rec = BuildNextRecommendation(
        extraction_id="x",
        analyzed_at="2026-05-04T00:00:00+00:00",
        audit_path="/tmp/audit-log",
        candidates=[c],
        degenerate_survey=True,
    )
    payload = rec.model_dump(mode="json", exclude_none=True)
    rec2 = BuildNextRecommendation.model_validate(payload)
    assert rec2.degenerate_survey is True
    assert len(rec2.candidates) == 1
