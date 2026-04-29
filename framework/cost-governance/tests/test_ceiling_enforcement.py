"""Activation-gate enforcement — scope × axis matrix (C1–C8)."""

from __future__ import annotations

import pytest

from loam.orchestrator.ipc import ApplicationError
from pydantic import ValidationError
from loam.scope_of_work import Budget, ScopeSpec, SuccessCriterion

from loam.cost_governance import (
    CostLedger,
    CostStore,
    IPC_COST_ROLLING_CEILING_EXCEEDED,
    IPC_COST_SESSION_CEILING_EXCEEDED,
)

from .conftest import build_config, make_spec


def test_C1_scope_with_no_axis_declared_refused_upstream() -> None:
    """scope-of-work `model_post_init` enforces at-least-one-axis-declared.
    Cost governance does not duplicate — C1 asserts the behaviour lives
    upstream and is not our concern.
    """
    with pytest.raises(ValidationError) as exc:
        ScopeSpec(
            goal="empty budget",
            constraints=(),
            budget=Budget(),  # nothing declared
            reversibility_class="fully_reversible",
            success_criteria=(
                SuccessCriterion(criterion_id="c", description="d"),
            ),
            observers=(),
            escalation_triggers=(),
        )
    # The error text cites the budget constraint — verifies the check
    # is in scope-of-work, not here.
    assert "Budget" in str(exc.value) or "budget" in str(exc.value).lower()


def test_C2_session_money_ceiling_exceeded(store: CostStore) -> None:
    config = build_config(session_money=1000)
    ledger = CostLedger(store=store, config=config)
    # Pre-existing spend puts us at 600; declared 500 pushes past 1000.
    ledger.store.apply_debit_to_session(
        session_id=ledger.default_session_id, money_delta=600
    )
    spec = make_spec(money_cents=500)
    with pytest.raises(ApplicationError) as exc:
        ledger.reserve_or_refuse(spec, scope_id="s1")
    assert exc.value.code == IPC_COST_SESSION_CEILING_EXCEEDED
    assert exc.value.data["axis"] == "money"
    # No reservation written.
    assert store.get_reservation("s1") is None


def test_C3_session_tokens_ceiling_exceeded(store: CostStore) -> None:
    config = build_config(session_tokens=10000)
    ledger = CostLedger(store=store, config=config)
    ledger.store.apply_debit_to_session(
        session_id=ledger.default_session_id, tokens_delta=6000
    )
    spec = make_spec(tokens=5000)
    with pytest.raises(ApplicationError) as exc:
        ledger.reserve_or_refuse(spec, scope_id="s1")
    assert exc.value.code == IPC_COST_SESSION_CEILING_EXCEEDED
    assert exc.value.data["axis"] == "tokens"


def test_C4_session_time_ceiling_exceeded(store: CostStore) -> None:
    config = build_config(session_time=3600)
    ledger = CostLedger(store=store, config=config)
    ledger.store.apply_debit_to_session(
        session_id=ledger.default_session_id, time_delta=3000
    )
    spec = make_spec(time_seconds=1000)
    with pytest.raises(ApplicationError) as exc:
        ledger.reserve_or_refuse(spec, scope_id="s1")
    assert exc.value.code == IPC_COST_SESSION_CEILING_EXCEEDED
    assert exc.value.data["axis"] == "time"


def test_C5_rolling_daily_money_exceeded(store: CostStore) -> None:
    config = build_config(daily_money=500)
    ledger = CostLedger(store=store, config=config)
    # Seed a reconciled reservation inside the day window so the
    # daily rollup has real material; rollups close reconciled-only.
    from loam.cost_governance import Reservation
    now = 0
    r = Reservation(
        scope_id="past",
        session_id="prev",
        state="reconciled",
        reserved_money_cents=300,
        actual_money_cents=400,
        reconciled_at="2099-01-01T00:00:00+00:00",
    )
    # Shortcut: put a rollup row in directly — simpler than waiting
    # on the rollup task here.
    from loam.cost_governance import RollingRollup, unix_now
    store.upsert_rolling_rollup(
        RollingRollup(
            window_kind="daily",
            interval_start_unix=unix_now() - 3600,
            interval_end_unix=unix_now() - 1,
            total_money_cents=400,
        )
    )
    spec = make_spec(money_cents=200)
    with pytest.raises(ApplicationError) as exc:
        ledger.reserve_or_refuse(spec, scope_id="s1")
    assert exc.value.code == IPC_COST_ROLLING_CEILING_EXCEEDED
    assert exc.value.data["axis"] == "money"
    assert exc.value.data["window_kind"] == "daily"


def test_C6_rolling_hourly_money_exceeded(store: CostStore) -> None:
    config = build_config(daily_money=1_000_000, hourly_money=500)
    ledger = CostLedger(store=store, config=config)
    from loam.cost_governance import RollingRollup, unix_now
    store.upsert_rolling_rollup(
        RollingRollup(
            window_kind="hourly",
            interval_start_unix=unix_now() - 600,
            interval_end_unix=unix_now() - 1,
            total_money_cents=400,
        )
    )
    spec = make_spec(money_cents=200)
    with pytest.raises(ApplicationError) as exc:
        ledger.reserve_or_refuse(spec, scope_id="s1")
    assert exc.value.code == IPC_COST_ROLLING_CEILING_EXCEEDED
    assert exc.value.data["window_kind"] == "hourly"


def test_C7_per_axis_independence(store: CostStore) -> None:
    """Scope declares only money; tokens/time caps are NOT checked.

    A scope with `tokens=None` and `time_seconds=None` contributes
    zero to those reservation math axes, regardless of declared caps.
    """
    config = build_config(
        session_money=10_000,
        session_tokens=100,  # would fail, but scope doesn't declare tokens
        session_time=10,     # would fail, but scope doesn't declare time
    )
    ledger = CostLedger(store=store, config=config)
    ledger.store.apply_debit_to_session(
        session_id=ledger.default_session_id,
        tokens_delta=99,
        time_delta=9,
    )
    # Scope declares only money; None on tokens/time. Gate passes.
    spec = make_spec(
        time_seconds=None,
        tokens=None,
        money_cents=100,
    )
    reservation = ledger.reserve_or_refuse(spec, scope_id="s1")
    assert reservation.scope_id == "s1"
    assert reservation.reserved_tokens is None
    assert reservation.reserved_time_seconds is None


def test_C8_baseline_pass_case(store: CostStore) -> None:
    config = build_config(session_money=10_000, daily_money=10_000)
    ledger = CostLedger(store=store, config=config)
    spec = make_spec(money_cents=50, tokens=100, time_seconds=30)
    reservation = ledger.reserve_or_refuse(spec, scope_id="s1")
    assert reservation.state == "active"
    assert reservation.reserved_money_cents == 50
    assert reservation.reserved_tokens == 100
    assert reservation.reserved_time_seconds == 30
    # Reservation row is present.
    fetched = store.get_reservation("s1")
    assert fetched is not None
    assert fetched.scope_id == "s1"
