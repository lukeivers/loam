# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.PSAFE.4 — cost-governance dry_run_estimate primitive returns
EstimateResult.

Per ``docs/plans/v0-1-6-production-safety-and-base-skills.md``
§5 AC.PSAFE.4: the primitive returns an ``EstimateResult`` carrying
``estimated_money_cents``, ``estimated_tokens``,
``estimated_time_seconds``, ``confidence_band`` (HIGH / MEDIUM / LOW
depending on sample-size of recent actuals).
"""

from __future__ import annotations

from loam.cost_governance.dry_run import (
    ConfidenceBand,
    EstimateResult,
    dry_run_estimate,
)


def _actual(money: int, tokens: int, time_s: int) -> dict:
    return {"money_cents": money, "tokens": tokens, "time_seconds": time_s}


def test_dry_run_returns_estimate_result_shape() -> None:
    """The return type carries all 4 named fields with correct types."""
    result = dry_run_estimate(
        scope_id="dispatch:foo",
        recent_actuals=[_actual(100, 1000, 10)],
    )
    assert isinstance(result, EstimateResult)
    assert isinstance(result.estimated_money_cents, int)
    assert isinstance(result.estimated_tokens, int)
    assert isinstance(result.estimated_time_seconds, int)
    assert isinstance(result.confidence_band, ConfidenceBand)


def test_dry_run_cold_start_returns_low_confidence_zeros() -> None:
    """Empty actuals → zeros + LOW band + non-empty reason."""
    result = dry_run_estimate(scope_id="dispatch:cold", recent_actuals=[])
    assert result.estimated_money_cents == 0
    assert result.estimated_tokens == 0
    assert result.estimated_time_seconds == 0
    assert result.confidence_band == ConfidenceBand.LOW
    assert result.reason is not None
    assert "cold-start" in result.reason


def test_dry_run_high_confidence_at_5_or_more_actuals() -> None:
    """5+ actuals → HIGH confidence band."""
    actuals = [_actual(100, 1000, 10) for _ in range(5)]
    result = dry_run_estimate(scope_id="dispatch:hi", recent_actuals=actuals)
    assert result.confidence_band == ConfidenceBand.HIGH
    assert result.estimated_money_cents == 100
    assert result.estimated_tokens == 1000
    assert result.estimated_time_seconds == 10


def test_dry_run_medium_confidence_at_2_to_4_actuals() -> None:
    """2-4 actuals → MEDIUM band."""
    for n in (2, 3, 4):
        actuals = [_actual(100, 1000, 10) for _ in range(n)]
        result = dry_run_estimate(
            scope_id=f"dispatch:n={n}", recent_actuals=actuals
        )
        assert result.confidence_band == ConfidenceBand.MEDIUM, (
            f"n={n} should be MEDIUM"
        )


def test_dry_run_low_confidence_at_1_actual() -> None:
    """1 actual → LOW band (sample-size below 2)."""
    actuals = [_actual(100, 1000, 10)]
    result = dry_run_estimate(scope_id="dispatch:single", recent_actuals=actuals)
    assert result.confidence_band == ConfidenceBand.LOW


def test_dry_run_mean_extrapolation() -> None:
    """The estimate is the mean of recent actuals."""
    actuals = [
        _actual(100, 1000, 10),
        _actual(200, 2000, 20),
        _actual(300, 3000, 30),
        _actual(400, 4000, 40),
        _actual(500, 5000, 50),
    ]
    result = dry_run_estimate(scope_id="dispatch:varied", recent_actuals=actuals)
    # mean of (100, 200, 300, 400, 500) = 300
    assert result.estimated_money_cents == 300
    assert result.estimated_tokens == 3000
    assert result.estimated_time_seconds == 30


def test_dry_run_estimate_result_extra_forbid() -> None:
    """EstimateResult rejects unknown fields (pydantic extra=forbid)."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        EstimateResult(  # type: ignore[call-arg]
            estimated_money_cents=0,
            estimated_tokens=0,
            estimated_time_seconds=0,
            confidence_band=ConfidenceBand.LOW,
            unknown_field="x",
        )
