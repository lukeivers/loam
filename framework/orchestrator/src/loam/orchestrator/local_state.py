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

"""Local SQLite for orchestrator process-lifecycle state (D6).

Event-sourced. Mirrors the Phase 1 pattern (scope-of-work, objective-
tracker, memory-system): an append-only `events` table with a small
set of read-side helpers derived from it.

Schema:
    events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,
           event_type TEXT NOT NULL,
           recorded_at TEXT NOT NULL,          -- ISO-8601 UTC
           payload TEXT NOT NULL,              -- JSON
           schema_version INTEGER NOT NULL DEFAULT 1)

Event types:
    process_started       — orchestrator boot, includes pid
    process_stopped       — graceful stop
    process_crashed       — informational (next boot detects & records)
    heartbeat             — periodic tick; attrs: tick_id, uptime_seconds
    bind_refused          — bind_scope rejection; attrs: scope_id,
                            objective_id, cause_kind, cause_message
    scope_activated       — activate_scope succeeded
    pause_activation      — pause_activation called; attrs: reason
    resume_activation     — resume_activation called
    compaction_flag_set   — PreCompact received; attrs: session_id
    compaction_restored   — post-compaction UserPromptSubmit completed
    bootstrap_refused     — workspace bootstrap missing/errored
    upgrade_probe         — v1.1 R1 semantic round-trip probe

Why SQLite / WAL: the file survives process crashes, a sibling
session process can read it concurrently, and WAL gives us durable
appends without lock contention on read.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

_SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS events (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type     TEXT NOT NULL,
    recorded_at    TEXT NOT NULL,
    payload        TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_recorded_at ON events (recorded_at);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class LocalEvent:
    event_id: int
    event_type: str
    recorded_at: str
    payload: dict[str, Any]
    schema_version: int = _SCHEMA_VERSION


class LocalStateStore:
    """Append-only local store.

    Thread-safe (a single Lock guards the connection). The store is
    instantiated once per orchestrator process. Consumers that only
    need to read (e.g. tests, diagnostic scripts) can open a separate
    connection on the same file — WAL supports concurrent readers.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self._path),
            isolation_level=None,  # autocommit
            check_same_thread=False,
        )
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_DDL)
            self._conn.execute(
                "INSERT OR IGNORE INTO meta (key, value) VALUES (?, ?)",
                ("schema_version", str(_SCHEMA_VERSION)),
            )

    @property
    def path(self) -> Path:
        return self._path

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def append(self, event_type: str, payload: dict[str, Any] | None = None) -> LocalEvent:
        recorded = datetime.now(timezone.utc).isoformat()
        body = json.dumps(payload or {}, sort_keys=True)
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO events (event_type, recorded_at, payload, schema_version) "
                "VALUES (?, ?, ?, ?)",
                (event_type, recorded, body, _SCHEMA_VERSION),
            )
            event_id = cur.lastrowid
        return LocalEvent(
            event_id=int(event_id) if event_id is not None else -1,
            event_type=event_type,
            recorded_at=recorded,
            payload=payload or {},
        )

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def all_events(self) -> list[LocalEvent]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT event_id, event_type, recorded_at, payload, schema_version "
                "FROM events ORDER BY event_id ASC"
            ).fetchall()
        return [_row_to_event(r) for r in rows]

    def events_of_type(self, event_type: str) -> list[LocalEvent]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT event_id, event_type, recorded_at, payload, schema_version "
                "FROM events WHERE event_type = ? ORDER BY event_id ASC",
                (event_type,),
            ).fetchall()
        return [_row_to_event(r) for r in rows]

    def latest_event(self, event_type: str) -> LocalEvent | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT event_id, event_type, recorded_at, payload, schema_version "
                "FROM events WHERE event_type = ? ORDER BY event_id DESC LIMIT 1",
                (event_type,),
            ).fetchone()
        return _row_to_event(row) if row else None

    def count(self, event_type: str | None = None) -> int:
        with self._lock:
            if event_type is None:
                row = self._conn.execute(
                    "SELECT COUNT(*) AS n FROM events"
                ).fetchone()
            else:
                row = self._conn.execute(
                    "SELECT COUNT(*) AS n FROM events WHERE event_type = ?",
                    (event_type,),
                ).fetchone()
        return int(row["n"])

    # ------------------------------------------------------------------
    # Compaction flag helpers (stored as events for upgrade fidelity)
    # ------------------------------------------------------------------

    def set_compaction_flag(self, *, session_id: str | None = None) -> LocalEvent:
        return self.append(
            "compaction_flag_set",
            {"session_id": session_id, "cleared": False},
        )

    def clear_compaction_flag(self) -> LocalEvent:
        # Append a new event; flag state is derived from "latest of
        # (set, restored)" comparisons.
        return self.append("compaction_restored", {})

    def compaction_flag_pending(self) -> bool:
        """True iff the most recent compaction-related event is
        `compaction_flag_set`."""
        with self._lock:
            row = self._conn.execute(
                "SELECT event_type FROM events "
                "WHERE event_type IN ('compaction_flag_set', 'compaction_restored') "
                "ORDER BY event_id DESC LIMIT 1"
            ).fetchone()
        return bool(row) and row["event_type"] == "compaction_flag_set"

    # ------------------------------------------------------------------
    # Bind-refused log helpers
    # ------------------------------------------------------------------

    def bind_refused_events(self) -> list[LocalEvent]:
        return self.events_of_type("bind_refused")

    # ------------------------------------------------------------------
    # v1.1 R1 semantic round-trip upgrade probe
    # ------------------------------------------------------------------

    def snapshot_probe(self) -> dict[str, Any]:
        """Capture a semantic snapshot for pre/post-upgrade comparison.

        The probe records: total event count, type histogram, latest
        event of each type's payload keys (stable schema shape). Two
        successive snapshots from the same db must be equal.
        """
        with self._lock:
            total = self._conn.execute(
                "SELECT COUNT(*) AS n FROM events"
            ).fetchone()["n"]
            histogram = {
                r["event_type"]: r["n"]
                for r in self._conn.execute(
                    "SELECT event_type, COUNT(*) AS n FROM events "
                    "GROUP BY event_type ORDER BY event_type ASC"
                )
            }
            latest = {}
            for et in histogram.keys():
                row = self._conn.execute(
                    "SELECT payload FROM events WHERE event_type = ? "
                    "ORDER BY event_id DESC LIMIT 1",
                    (et,),
                ).fetchone()
                if row:
                    payload = json.loads(row["payload"])
                    latest[et] = sorted(payload.keys())
        return {
            "total": int(total),
            "histogram": histogram,
            "latest_keys": latest,
            "schema_version": _SCHEMA_VERSION,
        }


def _row_to_event(row: sqlite3.Row | None) -> LocalEvent | None:  # type: ignore[return-value]
    if row is None:
        return None  # type: ignore[return-value]
    payload = json.loads(row["payload"])
    return LocalEvent(
        event_id=int(row["event_id"]),
        event_type=str(row["event_type"]),
        recorded_at=str(row["recorded_at"]),
        payload=payload,
        schema_version=int(row["schema_version"]),
    )
