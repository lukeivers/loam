"""AC.OBJX.1 — Objective Pydantic model.

- Construction success per V/P/H band.
- ValidationError on band/evidence mismatch (two-source rule for
  VERIFIED; single-source minimum for PLAUSIBLE; rationale for
  HYPOTHESISED).
- Round-trip through model_dump / model_validate.
- ID regex enforcement (must match ``^O\\.[a-z][a-z0-9-]*\\.\\d+$``).
- text >= 20 chars enforced.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import (
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
)


_OUTCOME_TEXT = (
    "Operators file refund disputes against merchant portals at scale, "
    "replacing manual portal clickwork."
)


# ---- Construction / happy path -------------------------------------


def test_verified_band_two_source_rule_passes() -> None:
    """VERIFIED needs test_name_refs + (readme OR design_doc) + repo_sha."""
    o = Objective(
        objective_id="O.dispute-flow.1",
        text=_OUTCOME_TEXT,
        confidence=ConfidenceBand.VERIFIED,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            test_name_refs=["tests/dispute.spec.ts::it should file disputes"],
            readme_excerpts=["files refund disputes at scale"],
            repo_sha="abc1234",
        ),
    )
    assert o.confidence is ConfidenceBand.VERIFIED


def test_plausible_band_single_source_passes() -> None:
    o = Objective(
        objective_id="O.dispute-flow.2",
        text=_OUTCOME_TEXT,
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            readme_excerpts=["files disputes at scale"],
        ),
    )
    assert o.confidence is ConfidenceBand.PLAUSIBLE


def test_hypothesised_band_with_rationale_passes() -> None:
    o = Objective(
        objective_id="O.dispute-flow.3",
        text=_OUTCOME_TEXT,
        confidence=ConfidenceBand.HYPOTHESISED,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            code_pattern_refs=["src/routes/disputes.js:42"],
            rationale="Express route shape suggests dispute-filing surface",
        ),
    )
    assert o.confidence is ConfidenceBand.HYPOTHESISED


# ---- Per-band invariants (model_validator) -------------------------


def test_verified_rejects_missing_tests() -> None:
    with pytest.raises(ValidationError) as exc:
        Objective(
            objective_id="O.x.1",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.VERIFIED,
            domain="x",
            evidence=ObjectiveEvidence(
                readme_excerpts=["x"],
                repo_sha="abc",
            ),
        )
    assert "test_name_refs" in str(exc.value)


def test_verified_rejects_missing_two_source() -> None:
    """VERIFIED with tests but no readme/design-doc fails."""
    with pytest.raises(ValidationError) as exc:
        Objective(
            objective_id="O.x.1",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.VERIFIED,
            domain="x",
            evidence=ObjectiveEvidence(
                test_name_refs=["t.spec.ts::a"],
                repo_sha="abc",
            ),
        )
    assert "two-source" in str(exc.value)


def test_verified_rejects_missing_repo_sha() -> None:
    with pytest.raises(ValidationError) as exc:
        Objective(
            objective_id="O.x.1",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.VERIFIED,
            domain="x",
            evidence=ObjectiveEvidence(
                test_name_refs=["t.spec.ts::a"],
                readme_excerpts=["x"],
            ),
        )
    assert "repo_sha" in str(exc.value)


def test_plausible_rejects_no_evidence() -> None:
    with pytest.raises(ValidationError) as exc:
        Objective(
            objective_id="O.x.1",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="x",
            evidence=ObjectiveEvidence(),
        )
    assert "single-source" in str(exc.value)


def test_hypothesised_rejects_no_rationale() -> None:
    with pytest.raises(ValidationError) as exc:
        Objective(
            objective_id="O.x.1",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.HYPOTHESISED,
            domain="x",
            evidence=ObjectiveEvidence(),
        )
    assert "rationale" in str(exc.value)


# ---- ID regex enforcement ------------------------------------------


def test_id_regex_rejects_uppercase() -> None:
    with pytest.raises(ValidationError):
        Objective(
            objective_id="O.Dispute.1",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="x",
            evidence=ObjectiveEvidence(readme_excerpts=["x"]),
        )


def test_id_regex_rejects_missing_number_suffix() -> None:
    with pytest.raises(ValidationError):
        Objective(
            objective_id="O.dispute",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="x",
            evidence=ObjectiveEvidence(readme_excerpts=["x"]),
        )


def test_id_regex_rejects_wrong_prefix() -> None:
    with pytest.raises(ValidationError):
        Objective(
            objective_id="X.dispute.1",
            text=_OUTCOME_TEXT,
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="x",
            evidence=ObjectiveEvidence(readme_excerpts=["x"]),
        )


# ---- text length ---------------------------------------------------


def test_text_below_20_chars_rejected() -> None:
    with pytest.raises(ValidationError):
        Objective(
            objective_id="O.x.1",
            text="too short",  # < 20
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="x",
            evidence=ObjectiveEvidence(readme_excerpts=["x"]),
        )


# ---- Round-trip ----------------------------------------------------


def test_round_trip_through_model_dump_and_validate() -> None:
    o1 = Objective(
        objective_id="O.dispute-flow.1",
        text=_OUTCOME_TEXT,
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="dispute-flow",
        evidence=ObjectiveEvidence(
            readme_excerpts=["files disputes at scale"],
        ),
    )
    payload = o1.model_dump(mode="json")
    o2 = Objective.model_validate(payload)
    assert o1.objective_id == o2.objective_id
    assert o1.confidence == o2.confidence
    assert o1.evidence.readme_excerpts == o2.evidence.readme_excerpts
