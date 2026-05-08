"""AC.RAILS.6 — Confidence band rules per Rails idiom.

Verifies the band-mapping contract:

- ActiveRecord schema / migrations / callbacks / concerns /
  polymorphic / Sidekiq → PLAUSIBLE.
- Passing RSpec / Minitest test → VERIFIED (with non-null repo_sha).
- LLM-inferred (heuristic in Cycle 3) → HYPOTHESISED.

For each band, the constructed BandedAC's ``evidence`` block carries
the per-band-required fields (per Cycle 2's AC.BANDS.2 model_validator).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.lang.ruby.adapter import extract_rails_acs


def test_active_record_emits_plausible(
    synthetic_rails_repo: Path,
) -> None:
    """ActiveRecord recognizer produces PLAUSIBLE band per AC.RAILS.6."""
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    ar_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.active_record.")
    ]
    assert len(ar_acs) >= 1
    for ac in ar_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value
        assert ac["evidence"]["kind"] == "source"
        assert ac["evidence"]["citations"]


def test_callbacks_emits_plausible(synthetic_rails_repo: Path) -> None:
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    cb_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.callbacks.")
    ]
    assert len(cb_acs) >= 1
    for ac in cb_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value
        assert ac["evidence"]["kind"] == "source"


def test_jobs_emits_plausible(synthetic_rails_repo: Path) -> None:
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    job_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.jobs.")
    ]
    assert len(job_acs) >= 2  # ActiveJob + Sidekiq
    for ac in job_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value


def test_routes_emits_plausible(synthetic_rails_repo: Path) -> None:
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    route_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.routes.")
    ]
    assert len(route_acs) >= 3
    for ac in route_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value


def test_migrations_emits_plausible(
    synthetic_rails_repo: Path,
) -> None:
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    mig_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.migrations.")
    ]
    assert len(mig_acs) >= 1
    for ac in mig_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value


def test_polymorphic_emits_plausible(
    synthetic_rails_repo: Path,
) -> None:
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    poly_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.polymorphic.")
    ]
    assert len(poly_acs) == 1
    for ac in poly_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value


def test_concerns_emits_plausible(synthetic_rails_repo: Path) -> None:
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    concern_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.concerns.")
    ]
    assert len(concern_acs) >= 2  # definition + usage
    for ac in concern_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value


def test_passing_rspec_emits_verified(
    synthetic_rails_repo: Path,
) -> None:
    """RSpec test → VERIFIED with evidence.kind='test' + repo_sha."""
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    test_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.test.rspec.")
    ]
    assert len(test_acs) >= 4
    for ac in test_acs:
        assert ac["confidence"] == ConfidenceBand.VERIFIED.value
        assert ac["evidence"]["kind"] == "test"
        assert ac["evidence"]["repo_sha"] is not None
        assert len(ac["evidence"]["repo_sha"]) == 40
        assert ac["evidence"]["citations"]


def test_passing_minitest_emits_verified(
    synthetic_rails_repo: Path,
) -> None:
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    mt_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.test.minitest.")
    ]
    assert len(mt_acs) >= 1
    for ac in mt_acs:
        assert ac["confidence"] == ConfidenceBand.VERIFIED.value
        assert ac["evidence"]["kind"] == "test"


def test_heuristic_inference_emits_hypothesised(
    synthetic_rails_repo: Path,
) -> None:
    """Heuristic inference → HYPOTHESISED with non-empty rationale."""
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    hyp_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.inferred.")
    ]
    assert len(hyp_acs) >= 2
    for ac in hyp_acs:
        assert ac["confidence"] == ConfidenceBand.HYPOTHESISED.value
        assert ac["evidence"]["kind"] == "inference"
        assert ac["evidence"]["rationale"]
        assert "heuristic:" in ac["evidence"]["rationale"]


def test_test_band_downgrade_when_no_repo_sha(
    synthetic_rails_repo_no_git: Path,
) -> None:
    """Non-git repo → VERIFIED → PLAUSIBLE downgrade per AC.BANDS.2."""
    raw = extract_rails_acs(repo=synthetic_rails_repo_no_git)
    # No VERIFIED ACs; all RSpec/Minitest ACs downgrade to PLAUSIBLE.
    bands = Counter(ac["confidence"] for ac in raw.acs)
    assert bands.get(ConfidenceBand.VERIFIED.value, 0) == 0
    test_acs = [
        ac for ac in raw.acs
        if ac["ac_id"].startswith("AC.RAILS.test.")
    ]
    assert len(test_acs) >= 5
    for ac in test_acs:
        assert ac["confidence"] == ConfidenceBand.PLAUSIBLE.value
        assert ac["evidence"]["repo_sha"] is None


def test_band_distribution_matches_master_plan_seeds(
    synthetic_rails_repo: Path,
) -> None:
    """Master plan AC.RAILS.6 mapping enforced end-to-end."""
    raw = extract_rails_acs(repo=synthetic_rails_repo)
    counter = Counter(ac["confidence"] for ac in raw.acs)
    # All three bands present.
    assert counter[ConfidenceBand.VERIFIED.value] >= 3
    assert counter[ConfidenceBand.PLAUSIBLE.value] >= 5
    assert counter[ConfidenceBand.HYPOTHESISED.value] >= 2
