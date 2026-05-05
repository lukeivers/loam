"""AC.BLDNXT.7 — Cost band ($0.10 default; $0.02-$0.30 halt).

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.BLDNXT.7:

- Default ceiling $0.10 (10 cents).
- Halt band $0.02-$0.30 (2-30 cents).
- ``--budget-cents`` overrides.
- Pre-flight estimate via ``estimate_build_next_cost_cents``.
- Halt on pre-flight breach.
"""

from __future__ import annotations

import pytest

from loam_odd_extractor import (
    BUILD_NEXT_DEFAULT_BUDGET_CENTS,
    BUILD_NEXT_LLM_JUDGE_INVOCATION_CAP,
    OddExtractorError,
    check_build_next_cost_band,
    estimate_build_next_cost_cents,
)


def test_default_budget_cents_is_ten():
    assert BUILD_NEXT_DEFAULT_BUDGET_CENTS == 10


def test_estimate_zero_when_survey_absent():
    """Survey absent → no LLM-judge calls → 0 cost."""
    assert estimate_build_next_cost_cents(
        gap_count=20, survey_present=False
    ) == 0.0


def test_estimate_zero_when_no_gaps():
    assert estimate_build_next_cost_cents(
        gap_count=0, survey_present=True
    ) == 0.0


def test_estimate_caps_at_invocation_cap():
    """Conservative upper-bound: cap-of-5 × ~$0.02 per call = $0.10."""
    high = estimate_build_next_cost_cents(
        gap_count=100, survey_present=True
    )
    assert high == 5 * 2.0  # 10 cents
    # Cap of 5 holds even with way more gaps.
    assert high <= 5 * 2.0 + 0.01


def test_default_budget_passes():
    """Default ceiling absorbs the cap-of-5 estimate."""
    estimated = estimate_build_next_cost_cents(
        gap_count=50, survey_present=True
    )
    check_build_next_cost_band(
        estimated_cost_cents=estimated,
        budget_cents=float(BUILD_NEXT_DEFAULT_BUDGET_CENTS),
    )  # no raise


def test_upper_halt_band_breach_raises():
    """>$0.30 estimate → halt regardless of budget."""
    with pytest.raises(OddExtractorError) as excinfo:
        check_build_next_cost_band(
            estimated_cost_cents=50.0,  # 50 cents
            budget_cents=100.0,
        )
    assert "upper halt band" in str(excinfo.value)


def test_budget_override_with_high_cents_within_halt_band():
    """Override raises budget_cents threshold; below upper halt is OK."""
    # 25 cents estimate; budget 30 cents; under upper halt band 30¢ →
    # passes (no halt).
    check_build_next_cost_band(
        estimated_cost_cents=25.0,
        budget_cents=30.0,
    )


def test_budget_below_estimate_raises():
    """Default budget 10¢; estimate 12¢ → raise."""
    with pytest.raises(OddExtractorError) as excinfo:
        check_build_next_cost_band(
            estimated_cost_cents=12.0,
            budget_cents=10.0,
        )
    assert "exceeds configured budget" in str(excinfo.value)


def test_invocation_cap_constant():
    assert BUILD_NEXT_LLM_JUDGE_INVOCATION_CAP == 5
