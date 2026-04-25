"""SQLite event-log store for the objective tracker.

Separate WAL database from scope-of-work (proposal §Persistence). One
append-only `objective_events` table is the source of truth;
`objective_state` caches the current projection; `scope_objective_binding`
is the sidecar enforcement table.

The store is synchronous inside a thread-safe wrapper; the runtime
wraps it in an `asyncio.Lock` at the async boundary. SQLite WAL is
read-concurrent and write-serialised; for the single-user cardinality
the spec targets (≤10⁴ events/year) this is fine.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .events import ObjectiveEvent, event_from_row


_SCHEMA = """
CREATE TABLE IF NOT EXISTS objective_events (
    event_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    objective_id  TEXT NOT NULL,
    kind          TEXT NOT NULL,
    payload       TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_obj_events_obj  ON objective_events(objective_id, event_id);
CREATE INDEX IF NOT EXISTS idx_obj_events_kind ON objective_events(kind, event_id);

CREATE TABLE IF NOT EXISTS objective_state (
    objective_id         TEXT PRIMARY KEY,
    goal                 TEXT NOT NULL,
    parent_id            TEXT,
    authored_by          TEXT NOT NULL,
    owner                TEXT,
    status               TEXT NOT NULL,
    time_bound_json      TEXT NOT NULL,
    criteria_json        TEXT NOT NULL,
    parent_close_policy  TEXT NOT NULL,
    last_event_id        INTEGER NOT NULL,
    last_transition_at   TEXT NOT NULL,
    criteria_latest_json TEXT NOT NULL DEFAULT '{}',
    lifted_from_json     TEXT NOT NULL DEFAULT 'null'
);
CREATE INDEX IF NOT EXISTS idx_obj_state_parent   ON objective_state(parent_id);
CREATE INDEX IF NOT EXISTS idx_obj_state_status   ON objective_state(status);
CREATE INDEX IF NOT EXISTS idx_obj_state_authored ON objective_state(authored_by);

CREATE TABLE IF NOT EXISTS scope_objective_binding (
    scope_id       TEXT PRIMARY KEY,
    objective_id   TEXT NOT NULL,
    bound_event_id INTEGER NOT NULL,
    bound_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_binding_obj ON scope_objective_binding(objective_id);
"""


@dataclass
class AppendedEvent:
    event_id: int
    event: Any


class EventStore:
    """Thread-safe SQLite WAL store for the objective tracker.

    Instances are cheap (one sqlite3 connection + one lock). A process
    holds one store for the lifetime of the ObjectiveRuntime.
    """

    def __init__(self, db_path: str | Path) -> None:
        self._path = Path(db_path)
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
        # Amendment #38: in-place additive widening for pre-widening
        # databases that already have `objective_state` without the
        # new `lifted_from_json` column. SQLite has no IF NOT EXISTS
        # for ADD COLUMN; check the existing column set and add only
        # if missing. NOT NULL DEFAULT 'null' fills existing rows
        # with the no-provenance sentinel — the AC38.2 round-trip
        # preservation invariant.
        cols = {
            row[1]
            for row in self._conn.execute(
                "PRAGMA table_info(objective_state)"
            ).fetchall()
        }
        if "lifted_from_json" not in cols:
            self._conn.execute(
                "ALTER TABLE objective_state ADD COLUMN "
                "lifted_from_json TEXT NOT NULL DEFAULT 'null'"
            )

    @property
    def path(self) -> Path:
        return self._path

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- appends -------------------------------------------------------

    def append(self, event: Any) -> AppendedEvent:
        with self._lock:
            payload = event.model_dump(mode="json")
            payload.pop("event_id", None)
            cur = self._conn.execute(
                "INSERT INTO objective_events(objective_id, kind, payload, created_at) "
                "VALUES (?, ?, ?, ?)",
                (
                    event.objective_id,
                    event.kind,
                    json.dumps(payload, default=str),
                    event.created_at,
                ),
            )
            eid = cur.lastrowid
            patched = event.model_copy(update={"event_id": eid})
            return AppendedEvent(event_id=eid, event=patched)

    # -- reads ---------------------------------------------------------

    def events_for(self, objective_id: str) -> list[Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT event_id, kind, payload FROM objective_events "
                "WHERE objective_id = ? ORDER BY event_id ASC",
                (objective_id,),
            )
            rows = cur.fetchall()
        return [_row_to_event(r) for r in rows]

    def all_events(self) -> list[Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT event_id, kind, payload FROM objective_events "
                "ORDER BY event_id ASC"
            )
            rows = cur.fetchall()
        return [_row_to_event(r) for r in rows]

    def events_since(self, event_id_exclusive: int) -> list[Any]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT event_id, kind, payload FROM objective_events "
                "WHERE event_id > ? ORDER BY event_id ASC",
                (event_id_exclusive,),
            )
            rows = cur.fetchall()
        return [_row_to_event(r) for r in rows]

    # -- projection state I/O ------------------------------------------

    def upsert_state(self, row: dict[str, Any]) -> None:
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        assignments = ", ".join(
            f"{c}=excluded.{c}" for c in cols if c != "objective_id"
        )
        with self._lock:
            self._conn.execute(
                f"INSERT INTO objective_state({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(objective_id) DO UPDATE SET {assignments}",
                [row[c] for c in cols],
            )

    def read_state(self, objective_id: str) -> dict[str, Any] | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM objective_state WHERE objective_id = ?",
                (objective_id,),
            )
            r = cur.fetchone()
        return dict(r) if r else None

    def list_states(
        self,
        *,
        parent_id: str | None = None,
        status: Sequence[str] | None = None,
        authored_by: str | None = None,
        is_root: bool | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        args: list[Any] = []
        if parent_id is not None:
            clauses.append("parent_id = ?")
            args.append(parent_id)
        if status:
            placeholders = ", ".join("?" for _ in status)
            clauses.append(f"status IN ({placeholders})")
            args.extend(status)
        if authored_by is not None:
            clauses.append("authored_by = ?")
            args.append(authored_by)
        if is_root is True:
            clauses.append("parent_id IS NULL")
        elif is_root is False:
            clauses.append("parent_id IS NOT NULL")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM objective_state{where} ORDER BY last_event_id ASC"
        with self._lock:
            cur = self._conn.execute(sql, args)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def drop_projection(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM objective_state")
            self._conn.execute("DELETE FROM scope_objective_binding")

    # -- binding sidecar ----------------------------------------------

    def upsert_binding(
        self,
        *,
        scope_id: str,
        objective_id: str,
        bound_event_id: int,
        bound_at: str,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO scope_objective_binding("
                "scope_id, objective_id, bound_event_id, bound_at) "
                "VALUES (?, ?, ?, ?) "
                "ON CONFLICT(scope_id) DO UPDATE SET "
                "objective_id=excluded.objective_id, "
                "bound_event_id=excluded.bound_event_id, "
                "bound_at=excluded.bound_at",
                (scope_id, objective_id, bound_event_id, bound_at),
            )

    def read_binding(self, scope_id: str) -> dict[str, Any] | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM scope_objective_binding WHERE scope_id = ?",
                (scope_id,),
            )
            r = cur.fetchone()
        return dict(r) if r else None

    def list_bindings(
        self, *, objective_id: str | None = None
    ) -> list[dict[str, Any]]:
        if objective_id is None:
            sql = "SELECT * FROM scope_objective_binding ORDER BY bound_event_id ASC"
            args: list[Any] = []
        else:
            sql = (
                "SELECT * FROM scope_objective_binding WHERE objective_id = ? "
                "ORDER BY bound_event_id ASC"
            )
            args = [objective_id]
        with self._lock:
            cur = self._conn.execute(sql, args)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    # -- snapshot (D8) -------------------------------------------------

    def snapshot_to(self, target_path: str | Path) -> Path:
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if target.exists():
                target.unlink()
            self._conn.execute("VACUUM INTO ?", (str(target),))
        return target


def _row_to_event(row: sqlite3.Row) -> Any:
    payload = json.loads(row["payload"])
    payload["event_id"] = row["event_id"]
    return event_from_row(row["kind"], payload)
