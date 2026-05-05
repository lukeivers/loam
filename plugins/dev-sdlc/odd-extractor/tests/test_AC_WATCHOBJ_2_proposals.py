"""AC.WATCHOBJ.2 — IncrementalProposal at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.WATCHOBJ.2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.diff_classifier import (
    EvidenceClassification,
    OrphanedObjective,
    OutOfDateObjective,
)
from loam_odd_extractor.proposals import (
    IncrementalProposal,
    IncrementalProposalSet,
    generate_proposals,
)
from loam_odd_extractor.spec import (
    EvidenceRowRef,
    Objective,
    ObjectiveEvidence,
)


def _verified_objective(repo_sha: str = "prior_sha") -> Objective:
    return Objective(
        objective_id="O.auth.1",
        text="Operators authenticate with password length validation enforced.",
        confidence=ConfidenceBand.VERIFIED,
        domain="auth",
        evidence=ObjectiveEvidence(
            readme_excerpts=["Auth supports password length"],
            test_name_refs=["tests/test_auth.py::test_password_length"],
            repo_sha=repo_sha,
        ),
    )


def _evidence_row() -> EvidenceRowRef:
    return EvidenceRowRef(
        evidence_row_id="route:app/auth.py:10-25",
        kind="route",
        path="app/auth.py",
        line_range=(10, 25),
    )


def test_out_of_date_yields_proposal_with_refreshed_repo_sha():
    """OutOfDateObjective → IncrementalProposal with proposed_new_evidence."""
    obj = _verified_objective(repo_sha="prior")
    ood = OutOfDateObjective(
        objective=obj,
        drift_kind="evidence_row_line_changed",
        affected_rows=(_evidence_row(),),
        from_sha="prior",
        to_sha="current_sha",
    )
    classification = EvidenceClassification(out_of_date=(ood,))
    proposal_set = generate_proposals(
        classification,
        extraction_id="ext",
        prior_repo_sha="prior",
        current_repo_sha="current_sha",
        generated_at="2026-05-04T00:00:00+00:00",
    )
    assert isinstance(proposal_set, IncrementalProposalSet)
    assert proposal_set.proposal_count == 1
    p = proposal_set.proposals[0]
    assert isinstance(p, IncrementalProposal)
    assert p.objective_id == "O.auth.1"
    assert p.proposed_new_evidence is not None
    assert p.proposed_new_evidence.repo_sha == "current_sha"
    # Multi-source evidence preserved.
    assert p.proposed_new_evidence.readme_excerpts == ["Auth supports password length"]
    assert p.confidence_band is ConfidenceBand.VERIFIED


def test_orphan_yields_proposal_with_none_proposed_evidence():
    """OrphanedObjective → IncrementalProposal with proposed_new_evidence=None."""
    obj = _verified_objective()
    orph = OrphanedObjective(
        objective=obj,
        missing_evidence_rows=(_evidence_row(),),
    )
    classification = EvidenceClassification(orphaned=(orph,))
    proposal_set = generate_proposals(
        classification,
        extraction_id="ext",
        prior_repo_sha="prior",
        current_repo_sha="curr",
        generated_at="2026-05-04T00:00:00+00:00",
    )
    assert proposal_set.proposal_count == 1
    p = proposal_set.proposals[0]
    assert p.proposed_new_evidence is None
    assert p.drift_kind == "orphaned"


def test_band_preservation_decision_i_default_no():
    """Confidence band preserved (Decision I default-no — no silent promotion)."""
    obj = _verified_objective()
    ood = OutOfDateObjective(
        objective=obj,
        drift_kind="evidence_row_file_changed",
        affected_rows=(_evidence_row(),),
        from_sha="p",
        to_sha="c",
    )
    classification = EvidenceClassification(out_of_date=(ood,))
    proposal_set = generate_proposals(
        classification,
        extraction_id="ext",
        prior_repo_sha="p",
        current_repo_sha="c",
        generated_at="ts",
    )
    p = proposal_set.proposals[0]
    assert p.confidence_band is ConfidenceBand.VERIFIED


def test_proposals_sorted_for_determinism():
    """Proposals sorted by objective_id."""
    obj_b = Objective(
        objective_id="O.b.1",
        text="Operators do thing b that is observable from outside the system.",
        confidence=ConfidenceBand.VERIFIED,
        domain="b",
        evidence=ObjectiveEvidence(
            readme_excerpts=["b"],
            test_name_refs=["test_b"],
            repo_sha="abc",
        ),
    )
    obj_a = Objective(
        objective_id="O.a.1",
        text="Operators do thing a that is observable from outside the system.",
        confidence=ConfidenceBand.VERIFIED,
        domain="a",
        evidence=ObjectiveEvidence(
            readme_excerpts=["a"],
            test_name_refs=["test_a"],
            repo_sha="abc",
        ),
    )
    classification = EvidenceClassification(
        out_of_date=(
            OutOfDateObjective(
                objective=obj_b,
                drift_kind="evidence_row_file_changed",
                affected_rows=(),
                from_sha="p",
                to_sha="c",
            ),
            OutOfDateObjective(
                objective=obj_a,
                drift_kind="evidence_row_file_changed",
                affected_rows=(),
                from_sha="p",
                to_sha="c",
            ),
        )
    )
    proposal_set = generate_proposals(
        classification,
        extraction_id="ext",
        prior_repo_sha="p",
        current_repo_sha="c",
        generated_at="ts",
    )
    ids = [p.objective_id for p in proposal_set.proposals]
    assert ids == ["O.a.1", "O.b.1"]
