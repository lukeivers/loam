# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Reservation lifecycle — C9–C13."""

from __future__ import annotations


import pytest

from loam.scope_of_work import ScopeRuntime
from loam.scope_of_work.events import BudgetDebited, BudgetRefunded, StateTransitioned
from loam.scope_of_work.spec import ScopeState

from loam.cost_governance import CostLedger, CostStore

from .conftest import build_config, make_spec


def test_C9_gate_pass_inserts_active_reservation(store: CostStore) -> None:
    config = build_config(session_money=1000)
    ledger = CostLedger(store=store, config=config)
    spec = make_spec(money_cents=50, tokens=100)
    ledger.reserve_or_refuse(spec, scope_id="s1")
    r = store.get_reservation("s1")
    assert r is not None
    assert r.state == "active"
    assert r.reserved_money_cents == 50
    assert r.reserved_tokens == 100
    assert r.actual_money_cents == 0
    assert r.reserved_at


def test_C10_debit_updates_reservation_and_session_rollups(
    store: CostStore, scope_runtime: ScopeRuntime
) -> None:
    config = build_config(session_money=10_000)
    ledger = CostLedger(store=store, config=config)
    ledger.subscribe(scope_runtime)
    spec = make_spec(money_cents=500, tokens=1000)
    ledger.reserve_or_refuse(spec, scope_id="s1")

    # Simulate a debit by calling the handler directly — the pyee
    # emitter on "*" fires sync-style but the test is simpler with
    # direct invocation.
    ledger._on_event(
        BudgetDebited(
            scope_id="s1",
            input_tokens=100,
            output_tokens=200,
            money_cents=50,
            call_id="c1",
        )
    )
    r = store.get_reservation("s1")
    assert r is not None
    assert r.actual_tokens == 300
    assert r.actual_money_cents == 50
    sr = store.get_session_rollup(r.session_id)
    assert sr is not None
    assert sr.total_tokens == 300
    assert sr.total_money_cents == 50


def test_C11_refund_decrements_rollups(store: CostStore) -> None:
    config = build_config(session_money=10_000)
    ledger = CostLedger(store=store, config=config)
    spec = make_spec(money_cents=500, tokens=1000)
    ledger.reserve_or_refuse(spec, scope_id="s1")
    ledger._on_event(
        BudgetDebited(
            scope_id="s1",
            input_tokens=100,
            output_tokens=200,
            money_cents=50,
            call_id="c1",
        )
    )
    ledger._on_event(
        BudgetRefunded(
            scope_id="s1",
            input_tokens=50,
            output_tokens=100,
            money_cents=25,
            call_id="c1",
            reason="test",
        )
    )
    r = store.get_reservation("s1")
    assert r is not None
    assert r.actual_tokens == 150  # 300 - 150
    assert r.actual_money_cents == 25  # 50 - 25
    sr = store.get_session_rollup(r.session_id)
    assert sr is not None
    assert sr.total_tokens == 150
    assert sr.total_money_cents == 25


@pytest.mark.parametrize(
    "terminal", [ScopeState.completed, ScopeState.failed, ScopeState.cancelled, ScopeState.escalated]
)
def test_C12_terminal_state_reconciles_reservation(
    store: CostStore, terminal: ScopeState
) -> None:
    config = build_config(session_money=10_000)
    ledger = CostLedger(store=store, config=config)
    spec = make_spec(money_cents=500)
    ledger.reserve_or_refuse(spec, scope_id="s1")
    ledger._on_event(
        BudgetDebited(
            scope_id="s1",
            input_tokens=50,
            output_tokens=50,
            money_cents=20,
            call_id="c1",
        )
    )
    ledger._on_event(
        StateTransitioned(
            scope_id="s1", from_state=ScopeState.active, to_state=terminal
        )
    )
    r = store.get_reservation("s1")
    assert r is not None
    assert r.state == "reconciled"
    assert r.reconciled_at is not None
    assert r.actual_money_cents == 20  # final values retained


def test_C13_cancel_pre_debit_releases_slack(store: CostStore) -> None:
    config = build_config(session_money=1000)
    ledger = CostLedger(store=store, config=config)
    spec = make_spec(money_cents=600)
    ledger.reserve_or_refuse(spec, scope_id="s1")

    # Second scope would fail because s1 reserves 600 + 500 > 1000.
    spec2 = make_spec(money_cents=500)
    from loam.orchestrator.ipc import ApplicationError
    with pytest.raises(ApplicationError):
        ledger.reserve_or_refuse(spec2, scope_id="s2")

    # Cancel s1 without debits.
    ledger._on_event(
        StateTransitioned(
            scope_id="s1", from_state=ScopeState.active, to_state=ScopeState.cancelled
        )
    )
    r = store.get_reservation("s1")
    assert r is not None
    assert r.state == "reconciled"
    assert r.actual_money_cents == 0

    # Now s2 activation succeeds — slack returned.
    ledger.reserve_or_refuse(spec2, scope_id="s2")
    assert store.get_reservation("s2") is not None
