# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.PSAFE.5 — foreign-codebase BudgetEnvelope Pydantic model.

Per ``docs/plans/v0-1-6-production-safety-and-base-skills.md``
§5 AC.PSAFE.5: the model declares
``hard_cap_money_cents``, ``soft_cap_money_cents``, ``overrun_action``
(enum: ``warn`` | ``halt`` | ``continue``). Pydantic validation
rejects malformed envelopes (negative caps, soft > hard, unknown
overrun-action).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.cost_governance.dry_run import BudgetEnvelope, OverrunAction


def test_budget_envelope_well_formed_construction() -> None:
    """Valid envelope constructs cleanly."""
    env = BudgetEnvelope(
        hard_cap_money_cents=10000,
        soft_cap_money_cents=8000,
        overrun_action=OverrunAction.warn,
    )
    assert env.hard_cap_money_cents == 10000
    assert env.soft_cap_money_cents == 8000
    assert env.overrun_action == OverrunAction.warn


def test_budget_envelope_rejects_negative_hard_cap() -> None:
    """Pydantic Field(ge=0) rejects negative caps (C28-style
    structural defence-in-depth)."""
    with pytest.raises(ValidationError):
        BudgetEnvelope(
            hard_cap_money_cents=-100,
            soft_cap_money_cents=0,
            overrun_action=OverrunAction.warn,
        )


def test_budget_envelope_rejects_negative_soft_cap() -> None:
    with pytest.raises(ValidationError):
        BudgetEnvelope(
            hard_cap_money_cents=100,
            soft_cap_money_cents=-1,
            overrun_action=OverrunAction.warn,
        )


def test_budget_envelope_rejects_soft_above_hard() -> None:
    """soft_cap > hard_cap is rejected by the model_validator."""
    with pytest.raises(ValidationError) as exc_info:
        BudgetEnvelope(
            hard_cap_money_cents=1000,
            soft_cap_money_cents=2000,
            overrun_action=OverrunAction.halt,
        )
    assert "soft_cap_money_cents" in str(exc_info.value)


def test_budget_envelope_accepts_equal_caps() -> None:
    """soft_cap == hard_cap is valid (degenerate but not malformed)."""
    env = BudgetEnvelope(
        hard_cap_money_cents=500,
        soft_cap_money_cents=500,
        overrun_action=OverrunAction.continue_,
    )
    assert env.soft_cap_money_cents == env.hard_cap_money_cents


def test_overrun_action_enum_values() -> None:
    """The three named overrun-actions are present."""
    assert OverrunAction.warn.value == "warn"
    assert OverrunAction.halt.value == "halt"
    assert OverrunAction.continue_.value == "continue"


def test_overrun_action_from_value_handles_continue_string() -> None:
    """`OverrunAction.from_value('continue')` returns the
    `continue_` member (Python keyword namespace dance)."""
    assert OverrunAction.from_value("continue") is OverrunAction.continue_
    assert OverrunAction.from_value("warn") is OverrunAction.warn
    assert OverrunAction.from_value("halt") is OverrunAction.halt


def test_budget_envelope_rejects_unknown_field() -> None:
    """extra=forbid rejects unknown fields."""
    with pytest.raises(ValidationError):
        BudgetEnvelope(  # type: ignore[call-arg]
            hard_cap_money_cents=1000,
            soft_cap_money_cents=500,
            overrun_action=OverrunAction.warn,
            unknown_field="x",
        )
