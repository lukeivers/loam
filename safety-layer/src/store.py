"""SQLite persistence for the safety layer.

Three tables:
  - ask_decisions      — approvals + refusals, scoped by structural hash
  - kill_events        — audit rows, one per kill issuance
  - system_kill_state  — terminal system-kill record read at bootstrap

The store is intentionally small: pure-CRUD, no async. The safety layer
is on the activation path, which means its reads happen synchronously
inside an IPC handler. SQLite is fast enough for single-digit-ms reads
at the scale the gate fires.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .events import (
    AskDecisionRecord,
    KillEventRecord,
    KillLevel,
    SystemKillStateRecord,
    iso_now,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS ask_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_id TEXT,
    scope_spec_hash TEXT NOT NULL,
    action_classes TEXT NOT NULL,
    state TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    expires_at TEXT,
    decided_by TEXT NOT NULL DEFAULT 'user',
    reasoning TEXT
);
CREATE INDEX IF NOT EXISTS idx_ask_spec_hash ON ask_decisions (scope_spec_hash);

CREATE TABLE IF NOT EXISTS kill_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    reason TEXT NOT NULL,
    source TEXT NOT NULL,
    scope_id TEXT,
    issued_at TEXT NOT NULL,
    cancelled_scope_ids TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS system_kill_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    killed_at TEXT NOT NULL,
    reason TEXT NOT NULL,
    source TEXT NOT NULL,
    cleared_at TEXT,
    cleared_reason TEXT
);
"""


class SafetyStore:
    """Thin SQLite wrapper for safety's three tables."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path))
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    # ---- ask decisions ----------------------------------------------

    def record_decision(self, record: AskDecisionRecord) -> int:
        cur = self._conn.execute(
            """INSERT INTO ask_decisions
               (scope_id, scope_spec_hash, action_classes, state,
                decided_at, expires_at, decided_by, reasoning)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.scope_id,
                record.scope_spec_hash,
                ",".join(record.action_classes),
                record.state,
                record.decided_at,
                record.expires_at,
                record.decided_by,
                record.reasoning,
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    def find_active_approval(
        self, scope_spec_hash: str, *, now: datetime | None = None
    ) -> AskDecisionRecord | None:
        """Return the most recent unexpired approved decision for a hash."""
        now = now or datetime.now(timezone.utc)
        now_iso = now.isoformat()
        cur = self._conn.execute(
            """SELECT scope_id, scope_spec_hash, action_classes, state,
                      decided_at, expires_at, decided_by, reasoning
               FROM ask_decisions
               WHERE scope_spec_hash = ?
                 AND state = 'approved'
                 AND (expires_at IS NULL OR expires_at > ?)
               ORDER BY id DESC LIMIT 1""",
            (scope_spec_hash, now_iso),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return _row_to_decision(row)

    def list_decisions(self) -> list[AskDecisionRecord]:
        cur = self._conn.execute(
            """SELECT scope_id, scope_spec_hash, action_classes, state,
                      decided_at, expires_at, decided_by, reasoning
               FROM ask_decisions ORDER BY id"""
        )
        return [_row_to_decision(r) for r in cur.fetchall()]

    # ---- kill events ------------------------------------------------

    def record_kill(self, record: KillEventRecord) -> int:
        cur = self._conn.execute(
            """INSERT INTO kill_events
               (level, reason, source, scope_id, issued_at, cancelled_scope_ids)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                record.level.value,
                record.reason,
                record.source,
                record.scope_id,
                record.issued_at,
                ",".join(record.cancelled_scope_ids),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    def list_kills(self) -> list[KillEventRecord]:
        cur = self._conn.execute(
            """SELECT level, reason, source, scope_id, issued_at,
                      cancelled_scope_ids
               FROM kill_events ORDER BY id"""
        )
        return [_row_to_kill(r) for r in cur.fetchall()]

    # ---- system kill state -----------------------------------------

    def record_system_kill(
        self, *, reason: str, source: str, killed_at: str | None = None
    ) -> int:
        cur = self._conn.execute(
            """INSERT INTO system_kill_state (killed_at, reason, source)
               VALUES (?, ?, ?)""",
            (killed_at or iso_now(), reason, source),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    def clear_system_kill(self, *, reason: str) -> bool:
        """Mark the most recent non-cleared system-kill row as cleared.
        Returns True if a row was updated, False if no active row existed."""
        cur = self._conn.execute(
            """UPDATE system_kill_state
               SET cleared_at = ?, cleared_reason = ?
               WHERE id = (
                 SELECT id FROM system_kill_state
                 WHERE cleared_at IS NULL
                 ORDER BY id DESC LIMIT 1
               )""",
            (iso_now(), reason),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def active_system_kill(self) -> SystemKillStateRecord | None:
        cur = self._conn.execute(
            """SELECT killed_at, reason, source, cleared_at, cleared_reason
               FROM system_kill_state
               WHERE cleared_at IS NULL
               ORDER BY id DESC LIMIT 1"""
        )
        row = cur.fetchone()
        if row is None:
            return None
        return SystemKillStateRecord(
            killed_at=row[0],
            reason=row[1],
            source=row[2],
            cleared_at=row[3],
            cleared_reason=row[4],
        )


# ---- helpers -----------------------------------------------------------


def _row_to_decision(row: Iterable[Any]) -> AskDecisionRecord:
    (
        scope_id,
        scope_spec_hash,
        action_classes,
        state,
        decided_at,
        expires_at,
        decided_by,
        reasoning,
    ) = row
    return AskDecisionRecord(
        scope_id=scope_id,
        scope_spec_hash=scope_spec_hash,
        action_classes=tuple(s for s in action_classes.split(",") if s),
        state=state,
        decided_at=decided_at,
        expires_at=expires_at,
        decided_by=decided_by,
        reasoning=reasoning,
    )


def _row_to_kill(row: Iterable[Any]) -> KillEventRecord:
    (level, reason, source, scope_id, issued_at, cancelled_scope_ids) = row
    return KillEventRecord(
        level=KillLevel(level),
        reason=reason,
        source=source,
        scope_id=scope_id,
        issued_at=issued_at,
        cancelled_scope_ids=tuple(
            s for s in cancelled_scope_ids.split(",") if s
        ),
    )
