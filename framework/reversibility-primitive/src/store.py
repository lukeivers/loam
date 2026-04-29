"""SQLite persistence for the reversibility primitive.

Two tables:
  - compensation_path_binding     — one row per scope_id, last-writer-wins
  - rollback_invocation           — FSM rows keyed by (scope_id, idempotency_key)

Per proposal §3.1 `~/.loam/reversibility/reversibility.sqlite` is the
default path; a PEP-style Path is injected so tests pass tmp_path.
WAL + synchronous=FULL + foreign_keys=ON per pos-v2 standard (matches
objective-tracker's store).
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any


_LOGGER = logging.getLogger(__name__)

from .spec import (
    CompensationPathBinding,
    RollbackInvocationRecord,
    iso_now,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS compensation_path_binding (
    scope_id         TEXT PRIMARY KEY,
    handle           TEXT NOT NULL,
    description      TEXT NOT NULL DEFAULT '',
    budget_seconds   INTEGER,
    idempotency_key  TEXT NOT NULL,
    registered_at    TEXT NOT NULL,
    registered_by    TEXT NOT NULL DEFAULT 'workspace'
);
CREATE INDEX IF NOT EXISTS idx_binding_handle ON compensation_path_binding(handle);

CREATE TABLE IF NOT EXISTS rollback_invocation (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    invocation_id    TEXT NOT NULL,
    scope_id         TEXT NOT NULL,
    idempotency_key  TEXT NOT NULL,
    state            TEXT NOT NULL,
    reason           TEXT,
    outcome          TEXT,
    narrative        TEXT,
    handle           TEXT,
    requested_at     TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    UNIQUE(scope_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_rollback_scope ON rollback_invocation(scope_id);
CREATE INDEX IF NOT EXISTS idx_rollback_state ON rollback_invocation(state);
"""


class ReversibilityStore:
    """Thread-safe SQLite WAL store for the reversibility primitive."""

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
                # observability. No span in scope; logger.debug is the
                # tightened-CDC fallback.
                _LOGGER.debug(
                    "reversibility_store_close_failed", exc_info=True
                )

    # ---- compensation-path bindings ---------------------------------

    def upsert_binding(
        self, binding: CompensationPathBinding
    ) -> tuple[bool, str | None]:
        """Insert-or-replace a binding. Returns (replaced, prior_handle).

        `replaced` is True when a prior row existed for the same
        scope_id. `prior_handle` carries the replaced handle so the
        telemetry layer can emit `binding_replaced` with audit detail.
        """
        with self._lock:
            cur = self._conn.execute(
                "SELECT handle FROM compensation_path_binding WHERE scope_id = ?",
                (binding.scope_id,),
            )
            row = cur.fetchone()
            prior_handle = row["handle"] if row else None
            self._conn.execute(
                """INSERT INTO compensation_path_binding
                   (scope_id, handle, description, budget_seconds,
                    idempotency_key, registered_at, registered_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(scope_id) DO UPDATE SET
                       handle = excluded.handle,
                       description = excluded.description,
                       budget_seconds = excluded.budget_seconds,
                       idempotency_key = excluded.idempotency_key,
                       registered_at = excluded.registered_at,
                       registered_by = excluded.registered_by""",
                (
                    binding.scope_id,
                    binding.handle,
                    binding.description,
                    binding.budget_seconds,
                    binding.idempotency_key,
                    binding.registered_at,
                    binding.registered_by,
                ),
            )
        return (prior_handle is not None, prior_handle)

    def get_binding(self, scope_id: str) -> CompensationPathBinding | None:
        with self._lock:
            cur = self._conn.execute(
                """SELECT scope_id, handle, description, budget_seconds,
                          idempotency_key, registered_at, registered_by
                   FROM compensation_path_binding
                   WHERE scope_id = ?""",
                (scope_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return CompensationPathBinding(
            scope_id=row["scope_id"],
            handle=row["handle"],
            description=row["description"] or "",
            budget_seconds=row["budget_seconds"],
            idempotency_key=row["idempotency_key"],
            registered_at=row["registered_at"],
            registered_by=row["registered_by"] or "workspace",
        )

    def list_bindings(self) -> list[CompensationPathBinding]:
        with self._lock:
            cur = self._conn.execute(
                """SELECT scope_id, handle, description, budget_seconds,
                          idempotency_key, registered_at, registered_by
                   FROM compensation_path_binding ORDER BY scope_id"""
            )
            rows = cur.fetchall()
        return [
            CompensationPathBinding(
                scope_id=r["scope_id"],
                handle=r["handle"],
                description=r["description"] or "",
                budget_seconds=r["budget_seconds"],
                idempotency_key=r["idempotency_key"],
                registered_at=r["registered_at"],
                registered_by=r["registered_by"] or "workspace",
            )
            for r in rows
        ]

    # ---- rollback invocations ---------------------------------------

    def find_invocation(
        self, *, scope_id: str, idempotency_key: str
    ) -> RollbackInvocationRecord | None:
        with self._lock:
            cur = self._conn.execute(
                """SELECT invocation_id, scope_id, idempotency_key, state,
                          reason, outcome, narrative, handle,
                          requested_at, updated_at
                   FROM rollback_invocation
                   WHERE scope_id = ? AND idempotency_key = ?
                   ORDER BY id DESC LIMIT 1""",
                (scope_id, idempotency_key),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return _row_to_invocation(row)

    def insert_invocation(
        self,
        *,
        invocation_id: str,
        scope_id: str,
        idempotency_key: str,
        reason: str | None,
        handle: str | None,
    ) -> RollbackInvocationRecord:
        now = iso_now()
        with self._lock:
            self._conn.execute(
                """INSERT INTO rollback_invocation
                   (invocation_id, scope_id, idempotency_key, state,
                    reason, outcome, narrative, handle,
                    requested_at, updated_at)
                   VALUES (?, ?, ?, 'requested', ?, NULL, NULL, ?, ?, ?)""",
                (invocation_id, scope_id, idempotency_key, reason, handle, now, now),
            )
        record = self.find_invocation(
            scope_id=scope_id, idempotency_key=idempotency_key
        )
        assert record is not None
        return record

    def transition_invocation(
        self,
        *,
        scope_id: str,
        idempotency_key: str,
        state: str,
        outcome: str | None = None,
        narrative: str | None = None,
    ) -> RollbackInvocationRecord | None:
        now = iso_now()
        with self._lock:
            self._conn.execute(
                """UPDATE rollback_invocation
                   SET state = ?, outcome = COALESCE(?, outcome),
                       narrative = COALESCE(?, narrative), updated_at = ?
                   WHERE scope_id = ? AND idempotency_key = ?""",
                (state, outcome, narrative, now, scope_id, idempotency_key),
            )
        return self.find_invocation(
            scope_id=scope_id, idempotency_key=idempotency_key
        )

    def list_invocations(self) -> list[RollbackInvocationRecord]:
        with self._lock:
            cur = self._conn.execute(
                """SELECT invocation_id, scope_id, idempotency_key, state,
                          reason, outcome, narrative, handle,
                          requested_at, updated_at
                   FROM rollback_invocation ORDER BY id ASC"""
            )
            rows = cur.fetchall()
        return [_row_to_invocation(r) for r in rows]


def _row_to_invocation(row: Any) -> RollbackInvocationRecord:
    return RollbackInvocationRecord(
        invocation_id=row["invocation_id"],
        scope_id=row["scope_id"],
        idempotency_key=row["idempotency_key"],
        state=row["state"],
        reason=row["reason"],
        outcome=row["outcome"],
        narrative=row["narrative"],
        handle=row["handle"],
        requested_at=row["requested_at"],
        updated_at=row["updated_at"],
    )
