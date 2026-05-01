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

"""SQLite persistence for cost governance.

Four tables, matching the proposal §3.1 layout:
  - reservations         — one row per activation that passed the gate
  - session_rollups      — in-place aggregate per session
  - rolling_rollups      — closed-interval rollups keyed on (window, interval_end_unix)
  - ceiling_adjustments  — append-only audit log

Structural defence (C27): SQL `CHECK (>= 0)` constraints on every
amount column match the Pydantic `ge=0` constraints. A negative
total cannot be stored.

WAL + synchronous=FULL + foreign_keys=ON per pos-v2 standard (matches
reversibility-primitive's store).
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable


_LOGGER = logging.getLogger(__name__)

from .spec import (
    CeilingAdjustment,
    Reservation,
    RollingRollup,
    SessionRollup,
    iso_now,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS reservations (
    scope_id                TEXT PRIMARY KEY,
    session_id              TEXT NOT NULL,
    state                   TEXT NOT NULL CHECK (state IN ('active','reconciled')),
    reserved_time_seconds   INTEGER CHECK (reserved_time_seconds IS NULL OR reserved_time_seconds >= 0),
    reserved_tokens         INTEGER CHECK (reserved_tokens IS NULL OR reserved_tokens >= 0),
    reserved_money_cents    INTEGER CHECK (reserved_money_cents IS NULL OR reserved_money_cents >= 0),
    actual_time_seconds     INTEGER NOT NULL DEFAULT 0 CHECK (actual_time_seconds >= 0),
    actual_tokens           INTEGER NOT NULL DEFAULT 0 CHECK (actual_tokens >= 0),
    actual_money_cents      INTEGER NOT NULL DEFAULT 0 CHECK (actual_money_cents >= 0),
    reserved_at             TEXT NOT NULL,
    reconciled_at           TEXT
);
CREATE INDEX IF NOT EXISTS idx_reservations_session ON reservations(session_id);
CREATE INDEX IF NOT EXISTS idx_reservations_state ON reservations(state);
CREATE INDEX IF NOT EXISTS idx_reservations_reconciled ON reservations(reconciled_at);

CREATE TABLE IF NOT EXISTS session_rollups (
    session_id           TEXT PRIMARY KEY,
    total_time_seconds   INTEGER NOT NULL DEFAULT 0 CHECK (total_time_seconds >= 0),
    total_tokens         INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    total_money_cents    INTEGER NOT NULL DEFAULT 0 CHECK (total_money_cents >= 0),
    started_at           TEXT NOT NULL,
    ended_at             TEXT
);
CREATE INDEX IF NOT EXISTS idx_session_rollups_ended ON session_rollups(ended_at);

CREATE TABLE IF NOT EXISTS rolling_rollups (
    window_kind          TEXT NOT NULL,
    interval_end_unix    REAL NOT NULL,
    interval_start_unix  REAL NOT NULL,
    total_time_seconds   INTEGER NOT NULL DEFAULT 0 CHECK (total_time_seconds >= 0),
    total_tokens         INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    total_money_cents    INTEGER NOT NULL DEFAULT 0 CHECK (total_money_cents >= 0),
    closed_at            TEXT NOT NULL,
    PRIMARY KEY (window_kind, interval_end_unix)
);
CREATE INDEX IF NOT EXISTS idx_rolling_rollups_window ON rolling_rollups(window_kind);

CREATE TABLE IF NOT EXISTS ceiling_adjustments (
    audit_record_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ceiling_kind         TEXT NOT NULL CHECK (ceiling_kind IN ('session','rolling')),
    axis                 TEXT NOT NULL CHECK (axis IN ('money','tokens','time')),
    window_kind          TEXT,
    new_value            INTEGER CHECK (new_value IS NULL OR new_value >= 0),
    reason               TEXT NOT NULL,
    adjusted_at          TEXT NOT NULL,
    adjusted_by          TEXT NOT NULL DEFAULT 'ipc'
);
CREATE INDEX IF NOT EXISTS idx_ceiling_adjustments_kind ON ceiling_adjustments(ceiling_kind, axis);
"""


class CostStore:
    """Thread-safe SQLite WAL store for cost governance."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self._path),
            isolation_level=None,
            check_same_thread=False,
            timeout=5.0,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)

    @property
    def path(self) -> Path:
        return self._path

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                # Amendment #26 — teardown CDC 2: surface exception to
                # observability. No span in scope at this catch site;
                # logger.debug is the tightened-CDC fallback.
                _LOGGER.debug(
                    "cost_store_close_failed", exc_info=True
                )

    # ---- reservations ----------------------------------------------

    def insert_reservation(self, r: Reservation) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO reservations
                   (scope_id, session_id, state,
                    reserved_time_seconds, reserved_tokens, reserved_money_cents,
                    actual_time_seconds, actual_tokens, actual_money_cents,
                    reserved_at, reconciled_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    r.scope_id, r.session_id, r.state,
                    r.reserved_time_seconds, r.reserved_tokens, r.reserved_money_cents,
                    r.actual_time_seconds, r.actual_tokens, r.actual_money_cents,
                    r.reserved_at, r.reconciled_at,
                ),
            )

    def get_reservation(self, scope_id: str) -> Reservation | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM reservations WHERE scope_id = ?", (scope_id,)
            )
            row = cur.fetchone()
        return _row_to_reservation(row) if row else None

    def list_active_reservations(
        self, *, session_id: str | None = None
    ) -> list[Reservation]:
        with self._lock:
            if session_id is None:
                cur = self._conn.execute(
                    "SELECT * FROM reservations WHERE state = 'active'"
                )
            else:
                cur = self._conn.execute(
                    "SELECT * FROM reservations WHERE state = 'active' AND session_id = ?",
                    (session_id,),
                )
            rows = cur.fetchall()
        return [_row_to_reservation(r) for r in rows]

    def list_all_reservations(self) -> list[Reservation]:
        with self._lock:
            cur = self._conn.execute("SELECT * FROM reservations ORDER BY reserved_at")
            rows = cur.fetchall()
        return [_row_to_reservation(r) for r in rows]

    def apply_debit_to_reservation(
        self,
        *,
        scope_id: str,
        time_delta: int = 0,
        tokens_delta: int = 0,
        money_delta: int = 0,
    ) -> None:
        """Apply a debit (positive) or refund (negative) to the
        active reservation row. SQL clamps the result at zero via
        `MAX(col + delta, 0)` so a refund cannot push actuals negative.

        The outer CHECK constraint still holds (>= 0) because of the
        MAX clamp.
        """
        with self._lock:
            self._conn.execute(
                """UPDATE reservations SET
                   actual_time_seconds = MAX(actual_time_seconds + ?, 0),
                   actual_tokens = MAX(actual_tokens + ?, 0),
                   actual_money_cents = MAX(actual_money_cents + ?, 0)
                   WHERE scope_id = ?""",
                (time_delta, tokens_delta, money_delta, scope_id),
            )

    def reconcile_reservation(self, *, scope_id: str) -> Reservation | None:
        now = iso_now()
        with self._lock:
            self._conn.execute(
                """UPDATE reservations SET state = 'reconciled', reconciled_at = ?
                   WHERE scope_id = ?""",
                (now, scope_id),
            )
        return self.get_reservation(scope_id)

    def prune_reconciled_before(self, *, iso_cutoff: str) -> int:
        """Delete reconciled rows whose `reconciled_at < iso_cutoff`.

        Returns the number of rows pruned. Active rows are never pruned.
        """
        with self._lock:
            cur = self._conn.execute(
                """DELETE FROM reservations
                   WHERE state = 'reconciled' AND reconciled_at IS NOT NULL
                     AND reconciled_at < ?""",
                (iso_cutoff,),
            )
            return cur.rowcount or 0

    # ---- session rollups -------------------------------------------

    def upsert_session_start(self, session_id: str) -> None:
        now = iso_now()
        with self._lock:
            self._conn.execute(
                """INSERT OR IGNORE INTO session_rollups
                   (session_id, started_at) VALUES (?, ?)""",
                (session_id, now),
            )

    def apply_debit_to_session(
        self,
        *,
        session_id: str,
        time_delta: int = 0,
        tokens_delta: int = 0,
        money_delta: int = 0,
    ) -> None:
        self.upsert_session_start(session_id)
        with self._lock:
            self._conn.execute(
                """UPDATE session_rollups SET
                   total_time_seconds = MAX(total_time_seconds + ?, 0),
                   total_tokens = MAX(total_tokens + ?, 0),
                   total_money_cents = MAX(total_money_cents + ?, 0)
                   WHERE session_id = ?""",
                (time_delta, tokens_delta, money_delta, session_id),
            )

    def get_session_rollup(self, session_id: str) -> SessionRollup | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM session_rollups WHERE session_id = ?",
                (session_id,),
            )
            row = cur.fetchone()
        return _row_to_session(row) if row else None

    def close_session(self, session_id: str) -> None:
        now = iso_now()
        with self._lock:
            self._conn.execute(
                "UPDATE session_rollups SET ended_at = ? WHERE session_id = ?",
                (now, session_id),
            )

    def prune_sessions_before(self, *, iso_cutoff: str) -> int:
        with self._lock:
            cur = self._conn.execute(
                """DELETE FROM session_rollups
                   WHERE ended_at IS NOT NULL AND ended_at < ?""",
                (iso_cutoff,),
            )
            return cur.rowcount or 0

    # ---- rolling rollups -------------------------------------------

    def upsert_rolling_rollup(self, rr: RollingRollup) -> bool:
        """Insert a closed-interval rollup, idempotent on the PK.

        Returns True if a new row was inserted, False on PK conflict
        (already closed — the job ran again). Used directly by the
        rollup task which computes totals from the reservation + debit
        stream.
        """
        with self._lock:
            try:
                self._conn.execute(
                    """INSERT INTO rolling_rollups
                       (window_kind, interval_end_unix, interval_start_unix,
                        total_time_seconds, total_tokens, total_money_cents,
                        closed_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        rr.window_kind,
                        rr.interval_end_unix,
                        rr.interval_start_unix,
                        rr.total_time_seconds,
                        rr.total_tokens,
                        rr.total_money_cents,
                        rr.closed_at,
                    ),
                )
                return True
            except sqlite3.IntegrityError:
                return False

    def list_rolling_rollups(
        self, *, window_kind: str | None = None
    ) -> list[RollingRollup]:
        with self._lock:
            if window_kind is None:
                cur = self._conn.execute(
                    """SELECT * FROM rolling_rollups
                       ORDER BY window_kind, interval_end_unix"""
                )
            else:
                cur = self._conn.execute(
                    """SELECT * FROM rolling_rollups WHERE window_kind = ?
                       ORDER BY interval_end_unix""",
                    (window_kind,),
                )
            rows = cur.fetchall()
        return [_row_to_rolling(r) for r in rows]

    def sum_rolling_since(
        self, *, window_kind: str, since_unix: float
    ) -> tuple[int, int, int]:
        """Sum totals for one window across intervals with
        `interval_end_unix > since_unix`. Used by the live
        window-spend query (reservation math adds in-flight on top).
        Returns (time, tokens, money_cents).
        """
        with self._lock:
            cur = self._conn.execute(
                """SELECT COALESCE(SUM(total_time_seconds),0),
                          COALESCE(SUM(total_tokens),0),
                          COALESCE(SUM(total_money_cents),0)
                   FROM rolling_rollups
                   WHERE window_kind = ? AND interval_end_unix > ?""",
                (window_kind, since_unix),
            )
            row = cur.fetchone()
        return int(row[0] or 0), int(row[1] or 0), int(row[2] or 0)

    # ---- ceiling adjustments ---------------------------------------

    def append_ceiling_adjustment(
        self, adj: CeilingAdjustment
    ) -> CeilingAdjustment:
        with self._lock:
            cur = self._conn.execute(
                """INSERT INTO ceiling_adjustments
                   (ceiling_kind, axis, window_kind, new_value, reason,
                    adjusted_at, adjusted_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    adj.ceiling_kind, adj.axis, adj.window_kind,
                    adj.new_value, adj.reason,
                    adj.adjusted_at, adj.adjusted_by,
                ),
            )
            audit_id = cur.lastrowid
        return adj.model_copy(update={"audit_record_id": int(audit_id or 0)})

    def list_ceiling_adjustments(self) -> list[CeilingAdjustment]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM ceiling_adjustments ORDER BY audit_record_id"
            )
            rows = cur.fetchall()
        return [
            CeilingAdjustment(
                audit_record_id=r["audit_record_id"],
                ceiling_kind=r["ceiling_kind"],
                axis=r["axis"],
                window_kind=r["window_kind"],
                new_value=r["new_value"],
                reason=r["reason"],
                adjusted_at=r["adjusted_at"],
                adjusted_by=r["adjusted_by"],
            )
            for r in rows
        ]


# ---- row factories --------------------------------------------------


def _row_to_reservation(row: Any) -> Reservation:
    return Reservation(
        scope_id=row["scope_id"],
        session_id=row["session_id"],
        state=row["state"],
        reserved_time_seconds=row["reserved_time_seconds"],
        reserved_tokens=row["reserved_tokens"],
        reserved_money_cents=row["reserved_money_cents"],
        actual_time_seconds=row["actual_time_seconds"],
        actual_tokens=row["actual_tokens"],
        actual_money_cents=row["actual_money_cents"],
        reserved_at=row["reserved_at"],
        reconciled_at=row["reconciled_at"],
    )


def _row_to_session(row: Any) -> SessionRollup:
    return SessionRollup(
        session_id=row["session_id"],
        total_time_seconds=row["total_time_seconds"],
        total_tokens=row["total_tokens"],
        total_money_cents=row["total_money_cents"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
    )


def _row_to_rolling(row: Any) -> RollingRollup:
    return RollingRollup(
        window_kind=row["window_kind"],
        interval_start_unix=row["interval_start_unix"],
        interval_end_unix=row["interval_end_unix"],
        total_time_seconds=row["total_time_seconds"],
        total_tokens=row["total_tokens"],
        total_money_cents=row["total_money_cents"],
        closed_at=row["closed_at"],
    )
