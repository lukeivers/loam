"""AC.WATCHOBJ.3 — domain_batching groups by O.<domain>.<n> regex.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.WATCHOBJ.3.
"""

from __future__ import annotations

import pytest

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.domain_batching import (
    group_proposals_by_domain,
    infer_domain,
)
from loam_odd_extractor.proposals import IncrementalProposal
from loam_odd_extractor.spec import Objective, ObjectiveEvidence


def _make_objective(objective_id: str, domain: str) -> Objective:
    return Objective(
        objective_id=objective_id,
        text=f"Operators do something verifiable in {domain} that survives implementation rewrite.",
        confidence=ConfidenceBand.PLAUSIBLE,
        domain=domain,
        evidence=ObjectiveEvidence(
            readme_excerpts=[f"{domain} support"],
        ),
    )


def _make_proposal(objective_id: str, domain: str) -> IncrementalProposal:
    obj = _make_objective(objective_id, domain)
    return IncrementalProposal(
        objective=obj,
        current_evidence=obj.evidence,
        proposed_new_evidence=obj.evidence,
        confidence_band=obj.confidence,
        drift_kind="evidence_row_file_changed",
        affected_rows=(),
    )


def test_infer_domain_parses_objective_id_regex():
    """O.<domain>.<n> → domain."""
    obj = _make_objective("O.dispute-flow.1", "dispute-flow")
    assert infer_domain(obj) == "dispute-flow"


def test_infer_domain_parses_simple_domain():
    obj = _make_objective("O.auth.5", "auth")
    assert infer_domain(obj) == "auth"


def test_group_proposals_by_domain_groups_correctly():
    """5 proposals across 3 domains → 3 domain buckets."""
    proposals = [
        _make_proposal("O.auth.1", "auth"),
        _make_proposal("O.auth.2", "auth"),
        _make_proposal("O.orders.1", "orders"),
        _make_proposal("O.payments.1", "payments"),
        _make_proposal("O.payments.2", "payments"),
    ]
    buckets = group_proposals_by_domain(proposals)
    assert set(buckets.keys()) == {"auth", "orders", "payments"}
    assert len(buckets["auth"]) == 2
    assert len(buckets["orders"]) == 1
    assert len(buckets["payments"]) == 2


def test_group_proposals_by_domain_deterministic_keys():
    """Same input → same output (sorted keys for determinism)."""
    proposals = [
        _make_proposal("O.zeta.1", "zeta"),
        _make_proposal("O.alpha.1", "alpha"),
    ]
    buckets = group_proposals_by_domain(proposals)
    assert list(buckets.keys()) == ["alpha", "zeta"]


def test_empty_proposals_yield_empty_buckets():
    buckets = group_proposals_by_domain([])
    assert dict(buckets) == {}
