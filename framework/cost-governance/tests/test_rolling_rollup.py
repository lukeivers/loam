"""Rolling-window rollup — C17, C18."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cost_governance import (
    CostStore,
    Reservation,
    RollingRollup,
    RollupTask,
)

from .conftest import build_config


def _seed_reconciled(store: CostStore, *, scope_id: str, at_unix: float, money: int) -> None:
    iso = datetime.fromtimestamp(at_unix, tz=timezone.utc).isoformat()
    r = Reservation(
        scope_id=scope_id,
        session_id="sess",
        state="reconciled",
        reserved_money_cents=money,
        actual_money_cents=money,
        reconciled_at=iso,
    )
    store.insert_reservation(r)


def test_C17_rollup_idempotent_under_double_run(store: CostStore) -> None:
    """Running the rollup task twice produces no duplicate rows."""
    config = build_config()
    task = RollupTask(store=store, config=config)

    now = 10_000.0  # fake "now" in unix seconds
    # Seed a reconciled reservation at now-1800 (30 min ago) — inside
    # hourly + daily windows.
    _seed_reconciled(store, scope_id="s1", at_unix=now - 1800, money=42)

    r1 = task.run_once(now=now)
    r2 = task.run_once(now=now)
    # Second run cannot insert the same (window_kind, interval_end_unix)
    # again; intervals_closed on r2 is 0.
    assert r2.intervals_closed == 0
    # Total rollup rows did not duplicate.
    all_rollups = store.list_rolling_rollups()
    assert len(all_rollups) == r1.intervals_closed


def test_C17_rollup_handles_clock_skew(store: CostStore) -> None:
    """After a big forward time jump (suspend/resume), skipped
    intervals close correctly.
    """
    config = build_config()
    task = RollupTask(store=store, config=config)

    # First pass at time T.
    now = 100_000.0
    _seed_reconciled(store, scope_id="s1", at_unix=now - 500, money=10)
    task.run_once(now=now)
    rollups_after_first = store.list_rolling_rollups()
    assert len(rollups_after_first) > 0

    # Jump forward by 5 hours — all intermediate hourly buckets must
    # close.
    jumped_now = now + 5 * 3600
    result = task.run_once(now=jumped_now)
    # Hourly buckets: ~5 new; daily buckets may also advance.
    assert result.intervals_closed >= 5


def test_C18_rolling_rollup_row_carries_start_and_end(store: CostStore) -> None:
    """Both start_unix and end_unix are persisted; PK prevents duplicates."""
    rr = RollingRollup(
        window_kind="hourly",
        interval_start_unix=1000.0,
        interval_end_unix=4600.0,
        total_money_cents=123,
    )
    inserted = store.upsert_rolling_rollup(rr)
    assert inserted is True

    # Second insert with same PK is a silent no-op (returns False).
    rr2 = rr.model_copy(update={"total_money_cents": 999})
    inserted_again = store.upsert_rolling_rollup(rr2)
    assert inserted_again is False

    rows = store.list_rolling_rollups()
    assert len(rows) == 1
    assert rows[0].interval_start_unix == 1000.0
    assert rows[0].interval_end_unix == 4600.0
    # First row's value was preserved.
    assert rows[0].total_money_cents == 123
