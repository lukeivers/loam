"""Degraded-mode staging store (Amendment 1 — hands-off-lifecycle).

SQLite-WAL-backed durable queue for memory writes that cannot reach the
Graphiti sidecar right now. Writes stage here during `degraded` /
`recovering` supervisor states and are drained to the sidecar in strict
FIFO order on recovery (see ``drain.py``).

Design per research §Q3:

- One DB per workspace at ``~/.loam/memory-staging.sqlite``.
- ``INSERT`` on stage, ``DELETE`` on confirmed landing — idempotence is
  preserved through a *client-generated* UUID passed to the sidecar,
  not through server-side tracking.
- WAL mode so drain + write coexist without locking.
- Soft cap → advisory OTel warning; hard cap → raise
  ``StagingOverflow`` to the caller. **The staging store never silently
  drops a write.** Silent drops would violate the memory-is-mandatory
  constraint.

Error codes reserved to hands-off-lifecycle (-32090..-32099):

- ``-32095`` ``staging_overflow_hard_cap`` (StagingOverflow)

The store is process-safe via the SQLite WAL; callers from the drain
worker and from ingest paths share the same connection by convention
(the Supervisor holds the canonical instance).
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---- errors ----------------------------------------------------------


class StagingError(Exception):
    """Base class for staging errors."""

    code: int = -32099


class StagingOverflow(StagingError):
    """Hard cap exceeded — raised to the caller per proposal §Q6 ruling.

    The caller (primary persona or background scope) decides how to
    handle it; the supervisor fires a Tier-1 escalation in parallel.
    The orchestrator does NOT halt.
    """

    code: int = -32095

    def __init__(self, message: str, *, size: int, hard_cap: int) -> None:
        super().__init__(message)
        self.size = size
        self.hard_cap = hard_cap


# ---- staged entry ---------------------------------------------------


@dataclass(frozen=True)
class StagedEntry:
    """One pending memory write."""

    id: int  # SQLite rowid — monotonic, preserves FIFO
    created_at: str  # ISO 8601 UTC
    episode_uuid: str  # client-generated; survives retry
    payload_json: str  # serialised IngestRequest
    forward_attempts: int = 0
    last_error: str | None = None
    last_attempt_at: str | None = None

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)


# ---- staging store --------------------------------------------------


_SCHEMA = """
CREATE TABLE IF NOT EXISTS staged_writes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    episode_uuid TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    forward_attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_attempt_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_staged_writes_created_at
  ON staged_writes(created_at);

CREATE TABLE IF NOT EXISTS staged_writes_poison (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    moved_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    episode_uuid TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    forward_attempts INTEGER NOT NULL,
    last_error TEXT
);
"""


class StagingStore:
    """Durable memory-write queue. Thread-safe via one lock."""

    DEFAULT_SOFT_CAP = 10_000
    DEFAULT_HARD_CAP = 50_000

    def __init__(
        self,
        db_path: str | Path,
        *,
        soft_cap: int = DEFAULT_SOFT_CAP,
        hard_cap: int = DEFAULT_HARD_CAP,
    ) -> None:
        self._db_path = Path(db_path).expanduser()
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._soft_cap = int(soft_cap)
        self._hard_cap = int(hard_cap)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self._db_path), check_same_thread=False, isolation_level=None
        )
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.executescript(_SCHEMA)

    # ---- introspection ---------------------------------------------

    @property
    def soft_cap(self) -> int:
        return self._soft_cap

    @property
    def hard_cap(self) -> int:
        return self._hard_cap

    def size(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM staged_writes"
            ).fetchone()
            return int(row["n"])

    def poison_size(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM staged_writes_poison"
            ).fetchone()
            return int(row["n"])

    # ---- write path ------------------------------------------------

    def stage(
        self,
        payload: dict[str, Any],
        *,
        episode_uuid: str | None = None,
    ) -> StagedEntry:
        """Write a pending memory ingest to the queue.

        Returns the staged entry (with assigned rowid). Raises
        :class:`StagingOverflow` at the hard cap. The soft cap is
        advisory — the caller/supervisor observes it via
        :meth:`size` and may begin aggressive recovery.
        """
        uuid_val = episode_uuid or str(uuid.uuid4())
        payload_json = json.dumps(payload, sort_keys=True, default=_json_default)
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM staged_writes"
            ).fetchone()
            current = int(row["n"])
            if current >= self._hard_cap:
                raise StagingOverflow(
                    f"staging hard cap exceeded: {current} >= {self._hard_cap}",
                    size=current,
                    hard_cap=self._hard_cap,
                )
            cur = self._conn.execute(
                "INSERT INTO staged_writes "
                "(created_at, episode_uuid, payload_json) VALUES (?, ?, ?)",
                (now, uuid_val, payload_json),
            )
            rowid = int(cur.lastrowid)
            return StagedEntry(
                id=rowid,
                created_at=now,
                episode_uuid=uuid_val,
                payload_json=payload_json,
            )

    # ---- read path (FIFO) ------------------------------------------

    def list_pending(self, limit: int = 100) -> list[StagedEntry]:
        """Return up to `limit` entries in FIFO (id-ASC) order."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, created_at, episode_uuid, payload_json, "
                "forward_attempts, last_error, last_attempt_at "
                "FROM staged_writes ORDER BY id ASC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [
            StagedEntry(
                id=int(r["id"]),
                created_at=r["created_at"],
                episode_uuid=r["episode_uuid"],
                payload_json=r["payload_json"],
                forward_attempts=int(r["forward_attempts"] or 0),
                last_error=r["last_error"],
                last_attempt_at=r["last_attempt_at"],
            )
            for r in rows
        ]

    def list_recent_for_group(
        self, *, group_id: str, limit: int = 100
    ) -> list[StagedEntry]:
        """Read-path fallback: entries staged for a particular scope.

        Used by ``MemoryAPI.search`` in degraded mode to merge staged
        writes with the last-known Graphiti snapshot. Filtering happens
        on the deserialised payload because SQLite lacks JSON-path
        indexing on older versions; the working set is small in
        practice (soft_cap 10k).
        """
        entries = self.list_pending(limit=limit * 2)
        return [
            e for e in entries if e.payload.get("group_id") == group_id
        ][:limit]

    # ---- drain success / failure ----------------------------------

    def mark_forwarded(self, entry_id: int) -> None:
        """Delete an entry after confirmed landing at the sidecar."""
        with self._lock:
            self._conn.execute(
                "DELETE FROM staged_writes WHERE id = ?", (int(entry_id),)
            )

    def mark_failure(
        self,
        entry_id: int,
        *,
        error: str,
        now: str | None = None,
    ) -> int:
        """Record a forward attempt failure. Returns the new attempt
        count."""
        when = now or datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "UPDATE staged_writes SET "
                "forward_attempts = forward_attempts + 1, "
                "last_error = ?, last_attempt_at = ? "
                "WHERE id = ?",
                (str(error)[:1000], when, int(entry_id)),
            )
            row = self._conn.execute(
                "SELECT forward_attempts FROM staged_writes WHERE id = ?",
                (int(entry_id),),
            ).fetchone()
            if row is None:
                return 0
            return int(row["forward_attempts"])

    def move_to_poison(self, entry_id: int) -> None:
        """Move a persistently-failing entry to the poison table so
        drain can continue. **Never silently drops** — the entry is
        preserved for user review via ``pos staging clear-poison``."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            row = self._conn.execute(
                "SELECT id, created_at, episode_uuid, payload_json, "
                "forward_attempts, last_error FROM staged_writes "
                "WHERE id = ?",
                (int(entry_id),),
            ).fetchone()
            if row is None:
                return
            self._conn.execute(
                "INSERT INTO staged_writes_poison "
                "(moved_at, created_at, episode_uuid, payload_json, "
                " forward_attempts, last_error) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    now,
                    row["created_at"],
                    row["episode_uuid"],
                    row["payload_json"],
                    row["forward_attempts"],
                    row["last_error"],
                ),
            )
            self._conn.execute(
                "DELETE FROM staged_writes WHERE id = ?", (int(entry_id),)
            )

    def list_poison(self, limit: int = 100) -> list[StagedEntry]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, created_at, episode_uuid, payload_json, "
                "forward_attempts, last_error "
                "FROM staged_writes_poison ORDER BY id ASC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [
            StagedEntry(
                id=int(r["id"]),
                created_at=r["created_at"],
                episode_uuid=r["episode_uuid"],
                payload_json=r["payload_json"],
                forward_attempts=int(r["forward_attempts"] or 0),
                last_error=r["last_error"],
            )
            for r in rows
        ]

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def _json_default(o: Any) -> Any:
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)
