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

"""SQLite event-log store with WAL mode and projection cache.

Proposal §2.3: one append-only `scope_events` table is the source of
truth. `scope_state` is a cache rebuildable from events alone. The
upgrade-fidelity test (D7 / v1.1 R1) replays events through a new
projector — drift above a threshold fails the upgrade.

The store is intentionally synchronous inside a thread-safe wrapper;
the runtime wraps it in `asyncio.to_thread` at the async boundary.
SQLite WAL is read-concurrent and write-serialised; for the single-user
cardinality the spec targets (≤10⁴ events/year) this is fine.

Refund semantics (brief §D2):
- A BudgetDebited event records input_tokens/output_tokens/money_cents.
- A BudgetRefunded event reverses a prior debit by call_id. The
  projector sums (debits − refunds) for the per-axis total.
- A failed call where the refund cannot be accurately computed writes
  a refund with amounts equal to the debit (full refund).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from pydantic import TypeAdapter

from .events import ScopeEvent, event_from_row


_EVENT_ADAPTER = TypeAdapter(ScopeEvent)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS scope_events (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_id    TEXT NOT NULL,
    kind        TEXT NOT NULL,
    payload     TEXT NOT NULL,     -- JSON-serialised full event body
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scope_events_scope ON scope_events(scope_id, event_id);
CREATE INDEX IF NOT EXISTS idx_scope_events_kind  ON scope_events(kind, event_id);

CREATE TABLE IF NOT EXISTS scope_state (
    scope_id           TEXT PRIMARY KEY,
    state              TEXT NOT NULL,
    parent_scope_id    TEXT,
    owner_persona      TEXT,
    last_event_id      INTEGER NOT NULL,
    last_transition_at TEXT NOT NULL,
    pause_reason       TEXT,
    goal               TEXT NOT NULL,
    reversibility_class TEXT NOT NULL,
    parent_close_policy TEXT NOT NULL,
    -- cached budget figures (debits − refunds + extensions)
    budget_tokens_cap           INTEGER,
    budget_tokens_consumed      INTEGER NOT NULL DEFAULT 0,
    budget_tokens_extended      INTEGER NOT NULL DEFAULT 0,
    budget_money_cents_cap      INTEGER,
    budget_money_cents_consumed INTEGER NOT NULL DEFAULT 0,
    budget_money_cents_extended INTEGER NOT NULL DEFAULT 0,
    budget_time_seconds_cap     INTEGER,
    budget_time_seconds_extended INTEGER NOT NULL DEFAULT 0,
    active_started_at  TEXT,    -- most recent transition INTO active
    active_cumulative_seconds  INTEGER NOT NULL DEFAULT 0,
    -- JSON blobs for complex fields the projection needs handy
    observers_json     TEXT NOT NULL DEFAULT '[]',
    triggers_json      TEXT NOT NULL DEFAULT '[]',
    pending_extension_axis TEXT
);
CREATE INDEX IF NOT EXISTS idx_scope_state_state ON scope_state(state);
CREATE INDEX IF NOT EXISTS idx_scope_state_parent ON scope_state(parent_scope_id);
"""


@dataclass
class AppendedEvent:
    event_id: int
    event: Any  # a typed ScopeEvent


class EventStore:
    """Thread-safe SQLite WAL event store.

    Used as the durable substrate for the scope runtime. Instances are
    cheap (they hold one sqlite3 connection + a lock); a process
    typically holds one store for the lifetime of the ScopeRuntime.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self._path),
            isolation_level=None,  # autocommit; we use explicit BEGIN
            check_same_thread=False,
            timeout=5.0,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)

    # -- lifecycle -----------------------------------------------------

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    @property
    def path(self) -> Path:
        return self._path

    # -- appends -------------------------------------------------------

    def append(self, event: Any) -> AppendedEvent:
        """Append a single typed event. Returns the row with event_id filled."""
        with self._lock:
            payload = event.model_dump(mode="json")
            payload.pop("event_id", None)
            cur = self._conn.execute(
                "INSERT INTO scope_events(scope_id, kind, payload, created_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    event.scope_id,
                    event.kind,
                    json.dumps(payload, default=str),
                    event.created_at,
                ),
            )
            eid = cur.lastrowid
            # Return a fresh instance with event_id filled.
            patched = event.model_copy(update={"event_id": eid})
            return AppendedEvent(event_id=eid, event=patched)

    # -- reads ---------------------------------------------------------

    def events_for(self, scope_id: str) -> list[Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT event_id, kind, payload FROM scope_events "
                "WHERE scope_id = ? ORDER BY event_id ASC",
                (scope_id,),
            )
            rows = cur.fetchall()
        return [_row_to_event(r) for r in rows]

    def all_events(self) -> list[Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT event_id, kind, payload FROM scope_events ORDER BY event_id ASC"
            )
            rows = cur.fetchall()
        return [_row_to_event(r) for r in rows]

    def events_since(self, event_id_exclusive: int) -> list[Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT event_id, kind, payload FROM scope_events "
                "WHERE event_id > ? ORDER BY event_id ASC",
                (event_id_exclusive,),
            )
            rows = cur.fetchall()
        return [_row_to_event(r) for r in rows]

    # -- projection state I/O ------------------------------------------

    def upsert_state(self, row: dict[str, Any]) -> None:
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "scope_id")
        with self._lock:
            self._conn.execute(
                f"INSERT INTO scope_state({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(scope_id) DO UPDATE SET {assignments}",
                [row[c] for c in cols],
            )

    def read_state(self, scope_id: str) -> dict[str, Any] | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM scope_state WHERE scope_id = ?", (scope_id,)
            )
            r = cur.fetchone()
        return dict(r) if r else None

    def list_states(
        self,
        *,
        states: Sequence[str] | None = None,
        parent_scope_id: str | None = None,
        owner_persona: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if states:
            placeholders = ", ".join("?" for _ in states)
            clauses.append(f"state IN ({placeholders})")
            args.extend(states)
        if parent_scope_id is not None:
            clauses.append("parent_scope_id = ?")
            args.append(parent_scope_id)
        if owner_persona is not None:
            clauses.append("owner_persona = ?")
            args.append(owner_persona)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM scope_state{where} ORDER BY last_event_id ASC"
        with self._lock:
            cur = self._conn.execute(sql, args)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def drop_projection(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM scope_state")

    # -- per-prompt aggregation (v1.1 R12) -----------------------------

    def per_prompt_costs(self) -> list[dict[str, Any]]:
        """Return per-prompt totals (tokens + money) across all scopes.

        Uses JSON1 functions to pull fields directly out of the event
        payload — no secondary table required. Refunds are subtracted.
        """
        sql = """
        WITH debits AS (
            SELECT
                COALESCE(json_extract(payload, '$.prompt_name'), '<unknown>') AS prompt_name,
                COALESCE(json_extract(payload, '$.model'), '<unknown>')       AS model,
                CAST(json_extract(payload, '$.input_tokens')  AS INTEGER)     AS input_tokens,
                CAST(json_extract(payload, '$.output_tokens') AS INTEGER)     AS output_tokens,
                CAST(json_extract(payload, '$.money_cents')   AS INTEGER)     AS money_cents,
                json_extract(payload, '$.call_id')                            AS call_id
            FROM scope_events WHERE kind = 'budget_debited'
        ),
        refunds AS (
            SELECT
                json_extract(payload, '$.call_id')                            AS call_id,
                CAST(json_extract(payload, '$.input_tokens')  AS INTEGER)     AS input_tokens,
                CAST(json_extract(payload, '$.output_tokens') AS INTEGER)     AS output_tokens,
                CAST(json_extract(payload, '$.money_cents')   AS INTEGER)     AS money_cents
            FROM scope_events WHERE kind = 'budget_refunded'
        )
        SELECT
            d.prompt_name AS prompt_name,
            d.model       AS model,
            SUM(d.input_tokens)  - COALESCE(SUM(r.input_tokens), 0)  AS input_tokens,
            SUM(d.output_tokens) - COALESCE(SUM(r.output_tokens), 0) AS output_tokens,
            SUM(d.money_cents)   - COALESCE(SUM(r.money_cents), 0)   AS money_cents,
            COUNT(DISTINCT d.call_id) AS call_count
        FROM debits d
        LEFT JOIN refunds r ON d.call_id = r.call_id
        GROUP BY d.prompt_name, d.model
        ORDER BY (SUM(d.input_tokens) + SUM(d.output_tokens)) DESC
        """
        with self._lock:
            cur = self._conn.execute(sql)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    # -- snapshot (v1.1 R1 substrate-level) ----------------------------

    def snapshot_to(self, target_path: str | Path) -> Path:
        """Copy the database file to `target_path`.

        Callers must ensure no writes are in flight when they snapshot;
        the runtime's upgrade harness quiesces before calling this.
        """

        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            # `VACUUM INTO` gives a consistent snapshot without a WAL
            # checkpoint dance.
            if target.exists():
                target.unlink()
            self._conn.execute("VACUUM INTO ?", (str(target),))
        return target


# ---- helpers ----------------------------------------------------------


def _row_to_event(row: sqlite3.Row) -> Any:
    payload = json.loads(row["payload"])
    payload["event_id"] = row["event_id"]
    return event_from_row(row["kind"], payload)


def rehydrate_events(events_iter: Iterable[Any]) -> list[Any]:
    """No-op pass-through; exists as a hook for tests that want to
    interpose a validator. Kept here to keep the call-site symmetric
    with `event_from_row`."""
    return list(events_iter)
