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

"""Retention — C19, C20, C21.

30d reservations after reconciliation, 365d session rollups after
ended_at, indefinite rolling rollups.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.cost_governance import (
    CostStore,
    Reservation,
    RollingRollup,
    RollupTask,
    SessionRollup,
)

from .conftest import build_config


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def test_C19_reservations_pruned_after_30d(store: CostStore) -> None:
    """Reconciled rows older than 30d are pruned; active rows never are."""
    store.insert_reservation(
        Reservation(
            scope_id="old",
            session_id="s",
            state="reconciled",
            reserved_money_cents=10,
            actual_money_cents=10,
            reconciled_at=_iso_days_ago(40),
        )
    )
    store.insert_reservation(
        Reservation(
            scope_id="recent",
            session_id="s",
            state="reconciled",
            reserved_money_cents=10,
            actual_money_cents=10,
            reconciled_at=_iso_days_ago(10),
        )
    )
    store.insert_reservation(
        Reservation(
            scope_id="active_old",
            session_id="s",
            state="active",
            reserved_money_cents=10,
            actual_money_cents=0,
        )
    )
    task = RollupTask(
        store=store,
        config=build_config(),
        reservation_retention_days=30,
    )
    task.run_once()

    # Old reconciled gone; recent and active still there.
    assert store.get_reservation("old") is None
    assert store.get_reservation("recent") is not None
    assert store.get_reservation("active_old") is not None


def test_C20_session_rollups_pruned_after_365d(store: CostStore) -> None:
    """Per Luke's ruling #3: 365 days, not 30."""
    # Seed an ended session from 400 days ago.
    store.upsert_session_start("old_sess")
    import sqlite3
    with store._lock:
        store._conn.execute(
            "UPDATE session_rollups SET ended_at = ? WHERE session_id = ?",
            (_iso_days_ago(400), "old_sess"),
        )

    # Recent ended session — 100 days.
    store.upsert_session_start("recent_sess")
    with store._lock:
        store._conn.execute(
            "UPDATE session_rollups SET ended_at = ? WHERE session_id = ?",
            (_iso_days_ago(100), "recent_sess"),
        )

    # Open session — ended_at is NULL.
    store.upsert_session_start("open_sess")

    task = RollupTask(
        store=store,
        config=build_config(),
        session_retention_days=365,
    )
    task.run_once()

    assert store.get_session_rollup("old_sess") is None
    assert store.get_session_rollup("recent_sess") is not None
    assert store.get_session_rollup("open_sess") is not None


def test_C21_rolling_rollups_never_pruned_by_time(store: CostStore) -> None:
    """Rolling rollups are retained indefinitely — low volume, audit."""
    # Seed a "very old" rollup at interval_end_unix = 0 (1970).
    old = RollingRollup(
        window_kind="hourly",
        interval_start_unix=-3600.0,
        interval_end_unix=0.0,
        total_money_cents=99,
    )
    store.upsert_rolling_rollup(old)

    task = RollupTask(
        store=store,
        config=build_config(),
        reservation_retention_days=1,   # aggressive — should NOT touch rollups
        session_retention_days=1,
    )
    task.run_once()

    all_rollups = store.list_rolling_rollups()
    # Our seed row must still be there.
    assert any(r.interval_end_unix == 0.0 for r in all_rollups)
