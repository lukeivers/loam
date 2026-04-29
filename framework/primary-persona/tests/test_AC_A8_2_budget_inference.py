"""AC.A8.2 — Budget inferred from the duration-estimation rubric.

Given a dispatch shape carrying only an `expected_duration_seconds`
hint and a task-shape category drawn from the rubric's six-row
table, the wrapper's budget-inference surface returns a `Budget`
whose `time_seconds` and `tokens` axes are non-None and whose values
fall within the rubric's documented bounds. Money axis is None per
D6.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.dispatch_wrapper import (
    _DURATION_RUBRIC,
    _infer_budget_from_duration,
)


@pytest.mark.parametrize("category", list(_DURATION_RUBRIC.keys()))
def test_AC_A8_2_each_category_returns_in_bounds_budget(category):
    row = _DURATION_RUBRIC[category]
    budget = _infer_budget_from_duration(
        duration_seconds=1.0, category=category
    )
    # Time axis non-None.
    assert budget.time_seconds is not None
    # The wrapper picks max(declared, ceiling), so time_seconds >=
    # ceiling.
    assert budget.time_seconds >= row["time_seconds_max"]
    # Tokens axis non-None and within row bounds.
    assert budget.tokens is not None
    assert row["tokens_min"] <= budget.tokens <= row["tokens_max"]
    # Money axis omitted by default (D6).
    assert budget.money_cents is None


def test_AC_A8_2_unknown_category_raises():
    with pytest.raises(ValueError):
        _infer_budget_from_duration(duration_seconds=10.0, category="bogus")


def test_AC_A8_2_pessimistic_duration_honoured():
    """If the caller declares a duration LARGER than the rubric's
    ceiling for a category, the wrapper uses the caller's number."""
    big = _DURATION_RUBRIC["trivial"]["time_seconds_max"] * 100
    budget = _infer_budget_from_duration(
        duration_seconds=big, category="trivial"
    )
    assert budget.time_seconds >= big
