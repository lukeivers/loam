"""AC.FIXTURES.3 (ruby-only portion) (v0.1.8 Cycle 4b) — end-to-end
band distribution against the canonical ruby-rails-payment fixture.

Mirrors Cycle 4a's ``test_AC_FIXTURES_3_jsts_e2e_band_distribution.py``
shape but bound to the canonical Ruby fixture instead of the JsTs
fixture.

Floor (master plan AC.FIXTURES.3): ≥3 VERIFIED + ≥5 PLAUSIBLE +
≥2 HYPOTHESISED.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from loam_odd_extractor.bands import BandedAC
from loam_odd_extractor.lang.ruby.adapter import extract_rails_acs


def test_canonical_fixture_extraction_meets_band_distribution_floor(
    canonical_ruby_rails_payment_repo: Path,
) -> None:
    """Canonical fixture extraction produces ≥3 VERIFIED + ≥5
    PLAUSIBLE + ≥2 HYPOTHESISED ACs.
    """
    raw = extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
    assert len(raw.acs) > 0, "Adapter produced zero ACs"

    bands = Counter(ac["confidence"] for ac in raw.acs)
    assert bands["VERIFIED"] >= 3, (
        f"Only {bands['VERIFIED']} VERIFIED; AC.FIXTURES.3 floor is 3"
    )
    assert bands["PLAUSIBLE"] >= 5, (
        f"Only {bands['PLAUSIBLE']} PLAUSIBLE; AC.FIXTURES.3 floor is 5"
    )
    assert bands["HYPOTHESISED"] >= 2, (
        f"Only {bands['HYPOTHESISED']} HYPOTHESISED; AC.FIXTURES.3 "
        f"floor is 2"
    )


def test_canonical_fixture_acs_round_trip_through_banded_ac(
    canonical_ruby_rails_payment_repo: Path,
) -> None:
    """Every dict in raw.acs round-trips through
    ``BandedAC.model_validate()`` (Cycle 2 ratification contract pin).
    """
    raw = extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
    for d in raw.acs:
        ac = BandedAC.model_validate(d)
        assert ac.ac_id, "BandedAC.ac_id empty"
        assert ac.text, "BandedAC.text empty"
        assert ac.evidence is not None, "BandedAC.evidence None"


def test_canonical_fixture_extraction_has_ratification_consumable_shape(
    canonical_ruby_rails_payment_repo: Path,
) -> None:
    """The canonical-fixture extraction is consumable by
    ``enqueue_ratification_batch`` at the structural-shape level
    (mirror of Cycle 3's test_AC_RAILS_5 contract pin).
    """
    import inspect

    from loam_odd_extractor.ratify import enqueue_ratification_batch

    raw = extract_rails_acs(repo=canonical_ruby_rails_payment_repo)
    banded_acs = [BandedAC.model_validate(d) for d in raw.acs]
    assert len(banded_acs) > 0

    sig = inspect.signature(enqueue_ratification_batch)
    assert "banded_acs" in sig.parameters
    assert "extraction_id" in sig.parameters
