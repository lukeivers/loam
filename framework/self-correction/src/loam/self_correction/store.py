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

"""SQLite persistence for self-correction.

Four tables with WAL + `synchronous=FULL` + `foreign_keys=ON`:

  - correction_triggers          — intake log
  - correction_episodes          — one row per opened or refused episode
  - correction_episode_records   — four record types; UNIQUE(episode_id, record_type)
  - correction_trigger_dedup     — hash + expires_at; pruned by TTL
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


_LOGGER = logging.getLogger(__name__)

from .spec import (
    CorrectionEpisode,
    CorrectionTrigger,
    EpisodeState,
    RecordType,
    TriggerSource,
    iso_now,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS correction_triggers (
    trigger_id          TEXT PRIMARY KEY,
    source              TEXT NOT NULL
                        CHECK (source IN (
                            'scope_failure','otel_anomaly',
                            'review_verdict','user_reported'
                        )),
    scope_id            TEXT,
    trace_id            TEXT,
    failure_class_hint  TEXT,
    raw_payload_json    TEXT NOT NULL DEFAULT '{}',
    received_at         TEXT NOT NULL,
    reporter            TEXT,
    dedup_key           TEXT
);
CREATE INDEX IF NOT EXISTS idx_triggers_source ON correction_triggers(source);
CREATE INDEX IF NOT EXISTS idx_triggers_scope ON correction_triggers(scope_id);
CREATE INDEX IF NOT EXISTS idx_triggers_dedup ON correction_triggers(dedup_key);

CREATE TABLE IF NOT EXISTS correction_episodes (
    episode_id              TEXT PRIMARY KEY,
    trigger_id              TEXT NOT NULL,
    correction_scope_id     TEXT,
    parent_correction_id    TEXT,
    failure_class           TEXT NOT NULL,
    state                   TEXT NOT NULL
                            CHECK (state IN ('running','completed','escalated','refused')),
    opened_at               TEXT NOT NULL,
    closed_at               TEXT,
    refusal_reason          TEXT,
    FOREIGN KEY (trigger_id) REFERENCES correction_triggers(trigger_id),
    FOREIGN KEY (parent_correction_id) REFERENCES correction_episodes(episode_id)
);
CREATE INDEX IF NOT EXISTS idx_episodes_state ON correction_episodes(state);
CREATE INDEX IF NOT EXISTS idx_episodes_scope ON correction_episodes(correction_scope_id);
CREATE INDEX IF NOT EXISTS idx_episodes_parent ON correction_episodes(parent_correction_id);
CREATE INDEX IF NOT EXISTS idx_episodes_class ON correction_episodes(failure_class);
CREATE INDEX IF NOT EXISTS idx_episodes_opened ON correction_episodes(opened_at);

CREATE TABLE IF NOT EXISTS correction_episode_records (
    episode_id      TEXT NOT NULL,
    record_type     TEXT NOT NULL
                    CHECK (record_type IN (
                        'failure_class','instance_fix',
                        'cause_diagnosed','structural_remedy'
                    )),
    payload_json    TEXT NOT NULL,
    at              TEXT NOT NULL,
    PRIMARY KEY (episode_id, record_type),
    FOREIGN KEY (episode_id) REFERENCES correction_episodes(episode_id)
);

CREATE TABLE IF NOT EXISTS correction_trigger_dedup (
    dedup_key       TEXT PRIMARY KEY,
    trigger_id      TEXT NOT NULL,
    expires_at_unix REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dedup_expiry ON correction_trigger_dedup(expires_at_unix);
"""


class CorrectionStore:
    """Thread-safe SQLite WAL store for self-correction."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()
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
                    "self_correction_store_close_failed", exc_info=True
                )

    # ---- triggers --------------------------------------------------

    def insert_trigger(self, t: CorrectionTrigger) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT OR IGNORE INTO correction_triggers
                   (trigger_id, source, scope_id, trace_id,
                    failure_class_hint, raw_payload_json, received_at,
                    reporter, dedup_key)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    t.trigger_id,
                    t.source.value,
                    t.scope_id,
                    t.trace_id,
                    t.failure_class_hint,
                    json.dumps(t.raw_payload),
                    t.received_at,
                    t.reporter,
                    t.dedup_key,
                ),
            )

    def get_trigger(self, trigger_id: str) -> CorrectionTrigger | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM correction_triggers WHERE trigger_id = ?",
                (trigger_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return CorrectionTrigger(
            trigger_id=row["trigger_id"],
            source=TriggerSource(row["source"]),
            scope_id=row["scope_id"],
            trace_id=row["trace_id"],
            failure_class_hint=row["failure_class_hint"],
            raw_payload=json.loads(row["raw_payload_json"] or "{}"),
            received_at=row["received_at"],
            reporter=row["reporter"],
            dedup_key=row["dedup_key"],
        )

    # ---- dedup -----------------------------------------------------

    def try_reserve_dedup(
        self, dedup_key: str, trigger_id: str, ttl_seconds: int
    ) -> bool:
        """Insert if absent or expired. Returns True on reserve.

        Re-entry within ttl returns False without updating.
        """
        now = time.time()
        expires = now + ttl_seconds
        with self._lock:
            # Best-effort prune of expired rows first (cheap, bounded).
            self._conn.execute(
                "DELETE FROM correction_trigger_dedup WHERE expires_at_unix < ?",
                (now,),
            )
            # Try insert — on conflict, the key is still live.
            cur = self._conn.execute(
                """INSERT OR IGNORE INTO correction_trigger_dedup
                   (dedup_key, trigger_id, expires_at_unix)
                   VALUES (?, ?, ?)""",
                (dedup_key, trigger_id, expires),
            )
            return (cur.rowcount or 0) > 0

    def dedup_count(self) -> int:
        with self._lock:
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM correction_trigger_dedup"
            )
            return int(cur.fetchone()[0])

    # ---- episodes --------------------------------------------------

    def insert_episode(self, ep: CorrectionEpisode) -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO correction_episodes
                   (episode_id, trigger_id, correction_scope_id,
                    parent_correction_id, failure_class, state,
                    opened_at, closed_at, refusal_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ep.episode_id,
                    ep.trigger_id,
                    ep.correction_scope_id,
                    ep.parent_correction_id,
                    ep.failure_class,
                    ep.state.value,
                    ep.opened_at,
                    ep.closed_at,
                    ep.refusal_reason,
                ),
            )

    def update_episode_state(
        self,
        episode_id: str,
        state: EpisodeState,
        *,
        refusal_reason: str | None = None,
    ) -> None:
        closed = iso_now() if state in (
            EpisodeState.completed,
            EpisodeState.escalated,
            EpisodeState.refused,
        ) else None
        with self._lock:
            self._conn.execute(
                """UPDATE correction_episodes
                   SET state = ?,
                       closed_at = COALESCE(?, closed_at),
                       refusal_reason = COALESCE(?, refusal_reason)
                   WHERE episode_id = ?""",
                (state.value, closed, refusal_reason, episode_id),
            )

    def get_episode(self, episode_id: str) -> CorrectionEpisode | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM correction_episodes WHERE episode_id = ?",
                (episode_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return _row_to_episode(row)

    def get_episode_by_scope(self, scope_id: str) -> CorrectionEpisode | None:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM correction_episodes WHERE correction_scope_id = ?",
                (scope_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return _row_to_episode(row)

    def list_episodes_by_class_since(
        self, failure_class: str, since_unix: float
    ) -> list[CorrectionEpisode]:
        """Return running/completed episodes with the given class whose
        opened_at is >= since_unix (excludes `refused`)."""
        since_iso = _unix_to_iso(since_unix)
        with self._lock:
            cur = self._conn.execute(
                """SELECT * FROM correction_episodes
                   WHERE failure_class = ?
                     AND state IN ('running','completed','escalated')
                     AND opened_at >= ?
                   ORDER BY opened_at""",
                (failure_class, since_iso),
            )
            rows = cur.fetchall()
        return [_row_to_episode(r) for r in rows]

    def list_all_episodes(self) -> list[CorrectionEpisode]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM correction_episodes ORDER BY opened_at"
            )
            rows = cur.fetchall()
        return [_row_to_episode(r) for r in rows]

    # ---- records ---------------------------------------------------

    def insert_record(
        self,
        *,
        episode_id: str,
        record_type: RecordType,
        payload: dict[str, Any],
        at: str | None = None,
    ) -> None:
        at = at or iso_now()
        with self._lock:
            # Reject duplicate records for the same type — the
            # four-part protocol records each part exactly once.
            self._conn.execute(
                """INSERT INTO correction_episode_records
                   (episode_id, record_type, payload_json, at)
                   VALUES (?, ?, ?, ?)""",
                (episode_id, record_type.value, json.dumps(payload), at),
            )

    def record_types_for(self, episode_id: str) -> set[RecordType]:
        with self._lock:
            cur = self._conn.execute(
                """SELECT record_type FROM correction_episode_records
                   WHERE episode_id = ?""",
                (episode_id,),
            )
            rows = cur.fetchall()
        return {RecordType(r["record_type"]) for r in rows}

    def list_records(self, episode_id: str) -> list[dict[str, Any]]:
        with self._lock:
            cur = self._conn.execute(
                """SELECT record_type, payload_json, at
                   FROM correction_episode_records
                   WHERE episode_id = ? ORDER BY at""",
                (episode_id,),
            )
            rows = cur.fetchall()
        return [
            {
                "record_type": r["record_type"],
                "payload": json.loads(r["payload_json"]),
                "at": r["at"],
            }
            for r in rows
        ]


def _row_to_episode(row: sqlite3.Row) -> CorrectionEpisode:
    return CorrectionEpisode(
        episode_id=row["episode_id"],
        trigger_id=row["trigger_id"],
        correction_scope_id=row["correction_scope_id"],
        parent_correction_id=row["parent_correction_id"],
        failure_class=row["failure_class"],
        state=EpisodeState(row["state"]),
        opened_at=row["opened_at"],
        closed_at=row["closed_at"],
        refusal_reason=row["refusal_reason"],
    )


def _unix_to_iso(unix_ts: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc).isoformat()
