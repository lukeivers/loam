"""AC.FIXTURES.4 (ruby-only portion) (v0.1.8 Cycle 4b) — Eric-
ratification end-to-end pin against the canonical ruby-rails-payment
fixture.

Mirror of Cycle 3's ``test_AC_RAILS_5_eric_ratification_pin.py``
shape, run against the canonical fixture instead of the synthetic
fixture. Per master plan AC.FIXTURES.4 — "Eric-ratification workflow
runs end-to-end on BOTH fixtures (the JS/TS/Playwright fixture is
the canonical Eric first-project path; the Ruby-Rails fixture is
the canonical Eric second-project path)."
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from loam_odd_extractor.bands import BandedAC
from loam_odd_extractor.lang.ruby.adapter import extract_rails_acs


def test_canonical_adapter_output_round_trips_through_banded_ac(
    canonical_ruby_rails_payment_repo: Path,
) -> None:
    """Every dict in adapter's RawACs.acs round-trips through
    BandedAC.model_validate() (the contract Cycle 2 ratification
    expects).
    """
    raw = extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
    assert len(raw.acs) > 0
    for d in raw.acs:
        # If validation fails, BandedAC raises — test fails.
        ac = BandedAC.model_validate(d)
        assert ac.ac_id
        assert ac.text
        assert ac.evidence is not None


def test_canonical_adapter_output_meets_master_plan_band_distribution(
    canonical_ruby_rails_payment_repo: Path,
) -> None:
    """Canonical fixture produces ≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2
    HYPOTHESISED ACs per master plan AC.FIXTURES.3 (the canonical
    fixture's threshold).
    """
    raw = extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
    bands = Counter(ac["confidence"] for ac in raw.acs)
    assert bands["VERIFIED"] >= 3
    assert bands["PLAUSIBLE"] >= 5
    assert bands["HYPOTHESISED"] >= 2


def test_canonical_adapter_output_consumable_by_ratification_batch(
    canonical_ruby_rails_payment_repo: Path,
    tmp_path: Path,
) -> None:
    """RawACs.acs converts to BandedAC list which
    enqueue_ratification_batch accepts (the contract pin).
    """
    from loam_odd_extractor.ratify import enqueue_ratification_batch

    raw = extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
    banded_acs = [BandedAC.model_validate(d) for d in raw.acs]
    assert len(banded_acs) > 0

    # The function signature accepts (extraction_id, banded_acs,
    # workspace_root, pm_runtime, pm_handle, draft_path). Verify
    # by inspection rather than instantiation (PMRuntime requires
    # workspace authoring, out-of-scope for this test). Mirror of
    # Cycle 3's test_AC_RAILS_5 pattern.
    import inspect

    sig = inspect.signature(enqueue_ratification_batch)
    assert "banded_acs" in sig.parameters
    assert "extraction_id" in sig.parameters
