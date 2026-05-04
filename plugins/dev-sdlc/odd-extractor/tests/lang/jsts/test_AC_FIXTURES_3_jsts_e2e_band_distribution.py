"""AC.FIXTURES.3 (jsts-only) — End-to-end band-distribution smoke.

Per the cycle plan-doc §4 AC.FIXTURES.3:

- Run the JsTs adapter against the jsts-playwright-app fixture.
- Assert: ≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED.
- :class:`RawACs.acs` round-trips through
  :meth:`BandedAC.model_validate` for every entry.
- Per-AC `ac_id` is unique across the result.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from loam_odd_extractor.bands import BandedAC, ConfidenceBand
from loam_odd_extractor.lang.jsts import extract_jsts_acs


def test_band_distribution(jsts_playwright_app_repo: Path) -> None:
    result = extract_jsts_acs(repo=jsts_playwright_app_repo)
    bands = Counter(ac.get("confidence") for ac in result.acs)

    verified_count = bands.get(ConfidenceBand.VERIFIED.value, 0)
    plausible_count = bands.get(ConfidenceBand.PLAUSIBLE.value, 0)
    hypothesised_count = bands.get(ConfidenceBand.HYPOTHESISED.value, 0)

    assert verified_count >= 3, (
        f"expected ≥3 VERIFIED ACs from fixture; got {verified_count}"
    )
    assert plausible_count >= 5, (
        f"expected ≥5 PLAUSIBLE ACs from fixture; got {plausible_count}"
    )
    assert hypothesised_count >= 2, (
        f"expected ≥2 HYPOTHESISED ACs from fixture; got "
        f"{hypothesised_count}"
    )


def test_round_trip_validation(
    jsts_playwright_app_repo: Path,
) -> None:
    result = extract_jsts_acs(repo=jsts_playwright_app_repo)
    for ac_dict in result.acs:
        # Round-trip cleanly.
        BandedAC.model_validate(ac_dict)


def test_ac_ids_unique(jsts_playwright_app_repo: Path) -> None:
    result = extract_jsts_acs(repo=jsts_playwright_app_repo)
    ac_ids = [ac.get("ac_id") for ac in result.acs]
    duplicates = [
        i for i, c in Counter(ac_ids).items() if c > 1
    ]
    assert duplicates == [], (
        f"duplicate ac_ids in extraction result: {duplicates}"
    )


def test_no_unhandled_paths(jsts_playwright_app_repo: Path) -> None:
    """Every JS/TS/HTML file in the fixture is handled by some
    recognizer (unhandled = parser failure or missing recognizer).
    """
    result = extract_jsts_acs(repo=jsts_playwright_app_repo)
    assert result.unhandled_paths == [], (
        f"fixture should produce no unhandled files; got "
        f"{[str(p) for p in result.unhandled_paths]}"
    )


def test_total_acs_meet_minimum(
    jsts_playwright_app_repo: Path,
) -> None:
    """The fixture should produce a meaningful number of ACs (>=20)
    given the recognizer surface area.
    """
    result = extract_jsts_acs(repo=jsts_playwright_app_repo)
    assert len(result.acs) >= 20, (
        f"expected ≥20 ACs from fixture; got {len(result.acs)}"
    )


def test_eric_ratification_consumability(
    jsts_playwright_app_repo: Path,
) -> None:
    """Surface verification — the banded contract produced by the
    JsTs adapter is structurally consumable by Cycle 2's
    :func:`enqueue_ratification_batch`.

    We don't run the full PM workflow here (that's covered by
    Cycle 2's test suite); we verify the ACs that flow into
    ratification are well-formed BandedACs in dict form, which is
    exactly what Cycle 2 expects.
    """
    result = extract_jsts_acs(repo=jsts_playwright_app_repo)
    # Every AC has the keys ratification expects: ac_id, text,
    # confidence, evidence (kind + citations).
    for ac in result.acs:
        assert "ac_id" in ac and ac["ac_id"]
        assert "text" in ac and ac["text"]
        assert "confidence" in ac
        assert "evidence" in ac
        assert "kind" in ac["evidence"]
