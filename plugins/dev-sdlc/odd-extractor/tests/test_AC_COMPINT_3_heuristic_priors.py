"""AC.COMPINT.3 — Heuristic pre-pass.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.3:

- Pattern 1 — production-stake-no-security-objective (priority=high).
- Pattern 2 — survey-compliance-no-compliance-objective (priority=high).
- Pattern 3 — data-modify-routes-no-persistence-objective (priority=medium).
- No false-positives on a clean fixture.
- Returns :class:`HeuristicPrior` rows with ``evidence_refs``.
"""

from __future__ import annotations

from loam_odd_extractor import (
    ConfidenceBand,
    HeuristicPrior,
    MultiSourceBundle,
    Objective,
    ObjectiveEvidence,
    heuristic_priors,
)


def _objective(
    *, domain: str = "dispute-flow", idx: int = 1
) -> Objective:
    return Objective(
        objective_id=f"O.{domain}.{idx}",
        text=(
            "Operators file refund disputes against merchant portals "
            f"(variant {idx})."
        ),
        confidence=ConfidenceBand.PLAUSIBLE,
        domain=domain,
        evidence=ObjectiveEvidence(
            readme_excerpts=["File refunds at scale"],
        ),
    )


def _bundle(
    *,
    user_survey: dict | None = None,
    code_patterns: list[dict] | None = None,
) -> MultiSourceBundle:
    return MultiSourceBundle(
        repo_id="test-repo",
        repo_path="/tmp/test-repo",
        repo_sha="abc1234",
        readme_text="# DisputeApp",
        readme_truncated=False,
        design_docs=[],
        test_assertions=[],
        user_survey=user_survey,
        code_patterns=code_patterns or [],
        total_token_estimate=50,
    )


# ---- Pattern 1 — production-stake-no-security ---------------------


def test_heuristic_1_fires_on_production_stake_without_security() -> None:
    survey = {
        "source_path": "~/loam-onboarding-survey.md",
        "parsed": {"production_use": "Yes"},
        "raw_text": "Q4 production_use: Yes",
    }
    objs = [_objective(domain="dispute-flow")]
    priors = heuristic_priors(objs, multi_source_bundle=_bundle(user_survey=survey))
    pattern_ids = {p.pattern_id for p in priors}
    assert "production-stake-no-security-objective" in pattern_ids
    p = next(p for p in priors if p.pattern_id == "production-stake-no-security-objective")
    assert p.priority == "high"
    assert p.evidence_refs  # non-empty


def test_heuristic_1_does_not_fire_when_security_objective_present() -> None:
    survey = {
        "source_path": "~/loam-onboarding-survey.md",
        "parsed": {"production_use": "Yes"},
        "raw_text": "Q4 production_use: Yes",
    }
    objs = [
        _objective(domain="dispute-flow"),
        _objective(domain="auth", idx=2),
    ]
    priors = heuristic_priors(objs, multi_source_bundle=_bundle(user_survey=survey))
    pattern_ids = {p.pattern_id for p in priors}
    assert "production-stake-no-security-objective" not in pattern_ids


# ---- Pattern 2 — survey-compliance-no-compliance-objective --------


def test_heuristic_2_fires_on_compliance_keyword_without_compliance_objective() -> None:
    survey = {
        "source_path": "~/loam-onboarding-survey.md",
        "parsed": {},
        "raw_text": "Q5 SOC-2 audit-trail required",
    }
    objs = [_objective(domain="dispute-flow")]
    priors = heuristic_priors(objs, multi_source_bundle=_bundle(user_survey=survey))
    pattern_ids = {p.pattern_id for p in priors}
    assert "survey-compliance-no-compliance-objective" in pattern_ids


def test_heuristic_2_does_not_fire_when_compliance_objective_present() -> None:
    survey = {
        "source_path": "~/loam-onboarding-survey.md",
        "parsed": {},
        "raw_text": "Q5 SOC-2 audit-trail required",
    }
    objs = [
        _objective(domain="dispute-flow"),
        _objective(domain="compliance", idx=2),
    ]
    priors = heuristic_priors(objs, multi_source_bundle=_bundle(user_survey=survey))
    pattern_ids = {p.pattern_id for p in priors}
    assert "survey-compliance-no-compliance-objective" not in pattern_ids


# ---- Pattern 3 — data-modify-routes-no-persistence-objective ------


def test_heuristic_3_fires_on_post_routes_without_persistence_objective() -> None:
    code_patterns = [
        {"ac_id": "AC.JSTS.1", "text": "Express POST /orders route"},
        {"ac_id": "AC.JSTS.2", "text": "Express DELETE /orders/:id"},
    ]
    objs = [_objective(domain="dispute-flow")]
    priors = heuristic_priors(
        objs, multi_source_bundle=_bundle(code_patterns=code_patterns)
    )
    pattern_ids = {p.pattern_id for p in priors}
    assert "data-modify-routes-no-persistence-objective" in pattern_ids
    p = next(p for p in priors if p.pattern_id == "data-modify-routes-no-persistence-objective")
    assert p.priority == "medium"
    assert p.evidence_refs


def test_heuristic_3_does_not_fire_when_persistence_objective_present() -> None:
    code_patterns = [
        {"ac_id": "AC.JSTS.1", "text": "Express POST /orders route"},
    ]
    objs = [
        _objective(domain="dispute-flow"),
        _objective(domain="persistence", idx=2),
    ]
    priors = heuristic_priors(
        objs, multi_source_bundle=_bundle(code_patterns=code_patterns)
    )
    pattern_ids = {p.pattern_id for p in priors}
    assert "data-modify-routes-no-persistence-objective" not in pattern_ids


# ---- Clean fixture — zero priors ----------------------------------


def test_heuristic_returns_empty_on_clean_fixture() -> None:
    """Survey with no production/compliance signal + no data-modify routes."""
    survey = {
        "source_path": "~/loam-onboarding-survey.md",
        "parsed": {"production_use": "No"},
        "raw_text": "Q4 production_use: No\nQ5 personal project, no specific requirements",
    }
    objs = [_objective(domain="dispute-flow")]
    priors = heuristic_priors(
        objs, multi_source_bundle=_bundle(user_survey=survey, code_patterns=[])
    )
    assert priors == []


def test_heuristic_returns_typed_HeuristicPrior_objects() -> None:
    survey = {
        "source_path": "~/loam-onboarding-survey.md",
        "parsed": {"production_use": "Yes"},
        "raw_text": "Q4 production_use: Yes",
    }
    objs = [_objective(domain="dispute-flow")]
    priors = heuristic_priors(objs, multi_source_bundle=_bundle(user_survey=survey))
    assert all(isinstance(p, HeuristicPrior) for p in priors)
