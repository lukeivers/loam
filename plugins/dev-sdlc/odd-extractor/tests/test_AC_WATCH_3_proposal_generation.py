"""AC.WATCH.3 — re-extraction proposal generation.

Tests `generate_proposals`:

- One proposal per out-of-date AC (still_current ACs skipped).
- One proposal per orphaned AC (proposed_new_evidence=None).
- Confidence band preserved (Decision I default-no — no silent
  promotion).
- Proposed evidence has current_repo_sha pin.
- Sorted output for determinism (load-bearing for AC.WATCH.4
  idempotency).
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.diff_classifier import (
    EvidenceClassification,
    OrphanedAC,
    OutOfDateAC,
)
from loam_odd_extractor.proposals import generate_proposals

from _incremental_helpers import (  # type: ignore[import-not-found]
    make_hypothesised_ac,
    make_plausible_ac,
    make_verified_ac,
    now_iso,
)


def test_one_proposal_per_out_of_date_ac() -> None:
    ac1 = make_plausible_ac(
        ac_id="AC.PAYMENT.1",
        backing_files=["app/payment/charge.rb"],
        citations=["app/payment/charge.rb:1-10"],
    )
    ac2 = make_plausible_ac(
        ac_id="AC.PAYMENT.2",
        backing_files=["app/payment/refund.rb"],
        citations=["app/payment/refund.rb:1-10"],
    )
    classification = EvidenceClassification(
        still_current=(),
        out_of_date=(
            OutOfDateAC(
                ac=ac1,
                drift_kind="backing_file_changed",
                affected_files=("app/payment/charge.rb",),
                from_sha=None,
                to_sha="def4567890",
            ),
            OutOfDateAC(
                ac=ac2,
                drift_kind="backing_file_changed",
                affected_files=("app/payment/refund.rb",),
                from_sha=None,
                to_sha="def4567890",
            ),
        ),
        orphaned=(),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-1",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    assert pset.proposal_count == 2
    assert {p.ac_id for p in pset.proposals} == {
        "AC.PAYMENT.1",
        "AC.PAYMENT.2",
    }


def test_orphan_proposal_has_no_proposed_evidence() -> None:
    ac = make_hypothesised_ac(
        ac_id="AC.LEGACY.1",
        backing_files=["app/legacy/old.rb"],
    )
    classification = EvidenceClassification(
        orphaned=(
            OrphanedAC(
                ac=ac,
                missing_files=("app/legacy/old.rb",),
            ),
        ),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-2",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    assert pset.proposal_count == 1
    p = pset.proposals[0]
    assert p.drift_kind == "orphaned"
    assert p.proposed_new_evidence is None
    assert p.confidence_band is ConfidenceBand.HYPOTHESISED


def test_still_current_acs_skipped() -> None:
    ac = make_plausible_ac(
        ac_id="AC.AUTH.1",
        backing_files=["app/auth/login.rb"],
        citations=["app/auth/login.rb:1-5"],
    )
    classification = EvidenceClassification(
        still_current=(ac,),
        out_of_date=(),
        orphaned=(),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-3",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    assert pset.proposal_count == 0


def test_confidence_band_preserved() -> None:
    """Decision I default-no — re-extraction must NOT silently
    promote PLAUSIBLE→VERIFIED."""
    plausible = make_plausible_ac(
        ac_id="AC.PAYMENT.1",
        backing_files=["app/payment/charge.rb"],
        citations=["app/payment/charge.rb:1-10"],
    )
    classification = EvidenceClassification(
        out_of_date=(
            OutOfDateAC(
                ac=plausible,
                drift_kind="backing_file_changed",
                affected_files=("app/payment/charge.rb",),
                from_sha=None,
                to_sha="def4567890",
            ),
        ),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-4",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    p = pset.proposals[0]
    assert p.confidence_band is ConfidenceBand.PLAUSIBLE
    assert p.proposed_new_evidence is not None
    assert p.proposed_new_evidence.kind == "source"


def test_verified_proposal_carries_current_sha() -> None:
    verified = make_verified_ac(
        ac_id="AC.PAYMENT.2",
        backing_files=[
            "app/payment/charge.rb",
            "tests/test_charge.rb",
        ],
        citations=[
            "tests/test_charge.rb::test_idempotency",
            "app/payment/charge.rb:55-72",
        ],
        repo_sha="abc1234567890def",
    )
    classification = EvidenceClassification(
        out_of_date=(
            OutOfDateAC(
                ac=verified,
                drift_kind="citation_line_changed",
                affected_files=("app/payment/charge.rb",),
                from_sha="abc1234567890def",
                to_sha="def4567890abcdef",
            ),
        ),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-5",
        prior_repo_sha="abc1234567890def",
        current_repo_sha="def4567890abcdef",
        generated_at=now_iso(),
    )
    p = pset.proposals[0]
    assert p.confidence_band is ConfidenceBand.VERIFIED
    assert p.proposed_new_evidence is not None
    assert (
        p.proposed_new_evidence.repo_sha == "def4567890abcdef"
    )
    assert p.proposed_new_evidence.kind == "test"


def test_proposals_sorted_by_ac_id() -> None:
    """Determinism — load-bearing for AC.WATCH.4 idempotency."""
    ac1 = make_plausible_ac(
        ac_id="AC.PAYMENT.2",
        backing_files=["app/payment/refund.rb"],
        citations=["app/payment/refund.rb:1-10"],
    )
    ac2 = make_plausible_ac(
        ac_id="AC.PAYMENT.1",
        backing_files=["app/payment/charge.rb"],
        citations=["app/payment/charge.rb:1-10"],
    )
    classification = EvidenceClassification(
        out_of_date=(
            OutOfDateAC(
                ac=ac1,
                drift_kind="backing_file_changed",
                affected_files=("app/payment/refund.rb",),
                from_sha=None,
                to_sha="def4567890",
            ),
            OutOfDateAC(
                ac=ac2,
                drift_kind="backing_file_changed",
                affected_files=("app/payment/charge.rb",),
                from_sha=None,
                to_sha="def4567890",
            ),
        ),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-6",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    ids = [p.ac_id for p in pset.proposals]
    assert ids == ["AC.PAYMENT.1", "AC.PAYMENT.2"]


def test_mixed_out_of_date_and_orphan_proposals() -> None:
    """6 ACs: 3 out-of-date + 1 orphan + 2 still-current → 4
    proposals (3 + 1)."""
    out_of_date_acs = [
        make_plausible_ac(
            ac_id=f"AC.X.{i}",
            backing_files=[f"app/x/{i}.rb"],
            citations=[f"app/x/{i}.rb:1-1"],
        )
        for i in range(1, 4)
    ]
    orphan_ac = make_hypothesised_ac(
        ac_id="AC.Y.1",
        backing_files=["app/y/old.rb"],
    )
    classification = EvidenceClassification(
        out_of_date=tuple(
            OutOfDateAC(
                ac=ac,
                drift_kind="backing_file_changed",
                affected_files=tuple(ac.backing_files),
                from_sha=None,
                to_sha="def4567890",
            )
            for ac in out_of_date_acs
        ),
        orphaned=(
            OrphanedAC(
                ac=orphan_ac,
                missing_files=("app/y/old.rb",),
            ),
        ),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-7",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    assert pset.proposal_count == 4
    drift_kinds = {p.drift_kind for p in pset.proposals}
    assert "backing_file_changed" in drift_kinds
    assert "orphaned" in drift_kinds
