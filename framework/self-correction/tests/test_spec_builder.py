"""CR11, CR12 — spec builder refuses irreversible; budget floors+scale."""

from __future__ import annotations

import pytest
from loam.scope_of_work import Budget, ReversibilityClass

from loam.self_correction import (
    CorrectionConfig,
    IrreversibleCorrectionSpecError,
    build_correction_spec,
    build_trigger_from_user_report,
)


def _trigger():
    return build_trigger_from_user_report(
        description="test",
        related_scope_id=None,
        reporter="eve",
    )


def test_CR11_builder_forces_compensatable() -> None:
    spec = build_correction_spec(_trigger(), failure_class="x")
    assert spec.reversibility_class == ReversibilityClass.compensatable


def test_CR11_builder_refuses_irreversible() -> None:
    with pytest.raises(IrreversibleCorrectionSpecError):
        build_correction_spec(
            _trigger(),
            failure_class="x",
            requested_reversibility_class=ReversibilityClass.irreversible,
        )


def test_CR11_builder_refuses_fully_reversible() -> None:
    # compensatable is the ONLY allowed class — fully_reversible is
    # also refused because compensation binding is load-bearing for
    # the rollback path (CR13, CR20).
    with pytest.raises(IrreversibleCorrectionSpecError):
        build_correction_spec(
            _trigger(),
            failure_class="x",
            requested_reversibility_class=ReversibilityClass.fully_reversible,
        )


def test_CR12_budget_inherits_and_scales_by_half() -> None:
    cfg = CorrectionConfig()  # default scale=0.5, floors 60/2000
    tb = Budget(time_seconds=1000, tokens=50_000, money_cents=10_000)
    spec = build_correction_spec(
        _trigger(), failure_class="x", triggering_budget=tb, config=cfg
    )
    assert spec.budget.time_seconds == 500
    assert spec.budget.tokens == 25_000
    assert spec.budget.money_cents == 5000


def test_CR12_budget_floors_applied_before_scale_on_tiny_triggering() -> None:
    cfg = CorrectionConfig()  # time_floor 60, token_floor 2000, scale 0.5
    tb = Budget(time_seconds=10, tokens=100)
    spec = build_correction_spec(
        _trigger(), failure_class="x", triggering_budget=tb, config=cfg
    )
    # floor-raised 60 * 0.5 = 30; floor-raised 2000 * 0.5 = 1000.
    assert spec.budget.time_seconds == 30
    assert spec.budget.tokens == 1000


def test_CR12_money_axis_has_no_floor_just_scale() -> None:
    cfg = CorrectionConfig()
    tb = Budget(time_seconds=1000, money_cents=100)
    spec = build_correction_spec(
        _trigger(), failure_class="x", triggering_budget=tb, config=cfg
    )
    assert spec.budget.money_cents == 50


def test_CR12_undeclared_axes_stay_undeclared() -> None:
    # Triggering scope only declared time → correction declares time,
    # not tokens/money (honest declaration).
    cfg = CorrectionConfig()
    tb = Budget(time_seconds=500)
    spec = build_correction_spec(
        _trigger(), failure_class="x", triggering_budget=tb, config=cfg
    )
    assert spec.budget.time_seconds == 250
    assert spec.budget.tokens is None
    assert spec.budget.money_cents is None


def test_CR12_no_triggering_budget_uses_floors() -> None:
    cfg = CorrectionConfig()
    spec = build_correction_spec(
        _trigger(), failure_class="x", triggering_budget=None, config=cfg
    )
    assert spec.budget.time_seconds == 30  # 60 * 0.5
    assert spec.budget.tokens == 1000  # 2000 * 0.5


def test_CR12_objective_template_mentions_class_and_source() -> None:
    spec = build_correction_spec(_trigger(), failure_class="bad_routing")
    assert "bad_routing" in spec.goal
    assert "user_reported" in spec.goal
    assert "four-part" in spec.goal
