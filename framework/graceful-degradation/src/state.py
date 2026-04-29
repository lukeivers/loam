"""State preservation + restart reconciliation (D8).

Own SQLite at ~/.loam/degradation.sqlite (configurable). Three tables
per the proposal:

    detection_events   — append-only signal log
    episodes           — append-only episode rows (resolved_at nullable)
    fsm_state          — singleton-per-mode cache; rebuildable

Event-sourced pattern matches scope-of-work, objective-tracker, memory-
system, and the orchestrator. A semantic snapshot (`snapshot_probe`)
supports v1.1 R1 round-trip upgrade fidelity.

Restart reconciliation handles four cross-state cases with
`OrchestratorHooks`:

    1. orchestrator paused + degradation open    → continue half-open cycle
    2. orchestrator paused + degradation closed  → re-open with restart tag
    3. orchestrator not paused + degradation open → resume_activation()
    4. orchestrator not paused + degradation closed → normal
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS detection_events (
    event_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    mode           TEXT NOT NULL,
    signal         TEXT NOT NULL,
    ok             INTEGER NOT NULL,
    call_id        TEXT,
    prompt_name    TEXT,
    latency_seconds REAL,
    status_code    INTEGER,
    retry_after    REAL,
    recorded_at    TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_de_mode ON detection_events (mode);
CREATE INDEX IF NOT EXISTS idx_de_recorded_at ON detection_events (recorded_at);

CREATE TABLE IF NOT EXISTS episodes (
    episode_id          TEXT PRIMARY KEY,
    mode                TEXT NOT NULL,
    signal              TEXT NOT NULL,
    policy              TEXT NOT NULL,
    started_at          TEXT NOT NULL,
    resolved_at         TEXT,
    resolution_kind     TEXT,
    paused_scope_ids    TEXT NOT NULL DEFAULT '[]',
    failed_scope_ids    TEXT NOT NULL DEFAULT '[]',
    notification_sent_at TEXT,
    resume_notification_sent_at TEXT,
    notification_threshold TEXT,
    schema_version      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS fsm_state (
    mode                TEXT PRIMARY KEY,
    state               TEXT NOT NULL,
    state_entered_at    REAL NOT NULL,
    retry_after_until   REAL,
    consecutive_probe_successes INTEGER DEFAULT 0,
    updated_at          TEXT NOT NULL,
    schema_version      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


# ---- dataclasses mirroring rows ---------------------------------------


@dataclass
class EpisodeRow:
    episode_id: str
    mode: str
    signal: str
    policy: str
    started_at: str
    resolved_at: str | None
    resolution_kind: str | None
    paused_scope_ids: list[str]
    failed_scope_ids: list[str]
    notification_sent_at: str | None
    resume_notification_sent_at: str | None
    notification_threshold: str | None


@dataclass
class FSMStateRow:
    mode: str
    state: str
    state_entered_at: float
    retry_after_until: float | None
    consecutive_probe_successes: int
    updated_at: str


# ---- store -------------------------------------------------------------


class DegradationStore:
    """SQLite-backed event store for graceful-degradation."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path).expanduser()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            str(self._path), isolation_level=None, check_same_thread=False
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

    # ---- detection events ----------------------------------------

    def append_detection_event(
        self,
        *,
        mode: str,
        signal: str,
        ok: bool,
        call_id: str | None,
        prompt_name: str | None,
        latency_seconds: float | None,
        status_code: int | None,
        retry_after: float | None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO detection_events "
                "(mode, signal, ok, call_id, prompt_name, latency_seconds, "
                "status_code, retry_after, recorded_at, schema_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    mode,
                    signal,
                    1 if ok else 0,
                    call_id,
                    prompt_name,
                    latency_seconds,
                    status_code,
                    retry_after,
                    now,
                    _SCHEMA_VERSION,
                ),
            )
            return int(cur.lastrowid or 0)

    def detection_event_count(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM detection_events"
            ).fetchone()
        return int(row["n"])

    # ---- episodes -----------------------------------------------

    def create_episode(
        self,
        *,
        episode_id: str,
        mode: str,
        signal: str,
        policy: str,
        paused_scope_ids: list[str],
        failed_scope_ids: list[str] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO episodes "
                "(episode_id, mode, signal, policy, started_at, "
                "paused_scope_ids, failed_scope_ids, schema_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    episode_id,
                    mode,
                    signal,
                    policy,
                    now,
                    json.dumps(paused_scope_ids),
                    json.dumps(failed_scope_ids or []),
                    _SCHEMA_VERSION,
                ),
            )

    def set_episode_notification(
        self,
        *,
        episode_id: str,
        threshold: str,
        kind: str = "alert",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        field = (
            "resume_notification_sent_at" if kind == "resume" else "notification_sent_at"
        )
        with self._lock:
            self._conn.execute(
                f"UPDATE episodes SET {field} = ?, notification_threshold = COALESCE(notification_threshold, ?) "
                "WHERE episode_id = ?",
                (now, threshold, episode_id),
            )

    def resolve_episode(
        self,
        *,
        episode_id: str,
        resolution_kind: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "UPDATE episodes SET resolved_at = ?, resolution_kind = ? "
                "WHERE episode_id = ?",
                (now, resolution_kind, episode_id),
            )

    def get_episode(self, episode_id: str) -> EpisodeRow | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM episodes WHERE episode_id = ?",
                (episode_id,),
            ).fetchone()
        return _row_to_episode(row) if row else None

    def unresolved_episodes(self) -> list[EpisodeRow]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM episodes WHERE resolved_at IS NULL "
                "ORDER BY started_at ASC"
            ).fetchall()
        return [_row_to_episode(r) for r in rows]

    def all_episodes(self) -> list[EpisodeRow]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM episodes ORDER BY started_at ASC"
            ).fetchall()
        return [_row_to_episode(r) for r in rows]

    # ---- fsm_state ---------------------------------------------------

    def upsert_fsm_state(self, row: FSMStateRow) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO fsm_state "
                "(mode, state, state_entered_at, retry_after_until, "
                "consecutive_probe_successes, updated_at, schema_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    row.mode,
                    row.state,
                    row.state_entered_at,
                    row.retry_after_until,
                    row.consecutive_probe_successes,
                    row.updated_at,
                    _SCHEMA_VERSION,
                ),
            )

    def all_fsm_states(self) -> list[FSMStateRow]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT mode, state, state_entered_at, retry_after_until, "
                "consecutive_probe_successes, updated_at FROM fsm_state"
            ).fetchall()
        return [
            FSMStateRow(
                mode=r["mode"],
                state=r["state"],
                state_entered_at=float(r["state_entered_at"]),
                retry_after_until=(
                    float(r["retry_after_until"])
                    if r["retry_after_until"] is not None
                    else None
                ),
                consecutive_probe_successes=int(r["consecutive_probe_successes"]),
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    # ---- snapshot probe (v1.1 R1) ----------------------------------

    def snapshot_probe(self) -> dict[str, Any]:
        """Stable semantic snapshot for pre/post-upgrade comparison.

        Two successive snapshots from the same db must be equal. Stable
        fields only: counts and histograms, not monotonic timestamps.
        """
        with self._lock:
            de_total = int(
                self._conn.execute(
                    "SELECT COUNT(*) AS n FROM detection_events"
                ).fetchone()["n"]
            )
            ep_total = int(
                self._conn.execute(
                    "SELECT COUNT(*) AS n FROM episodes"
                ).fetchone()["n"]
            )
            ep_unresolved = int(
                self._conn.execute(
                    "SELECT COUNT(*) AS n FROM episodes "
                    "WHERE resolved_at IS NULL"
                ).fetchone()["n"]
            )
            fsm_histogram = {
                r["state"]: r["n"]
                for r in self._conn.execute(
                    "SELECT state, COUNT(*) AS n FROM fsm_state "
                    "GROUP BY state ORDER BY state ASC"
                )
            }
            mode_histogram = {
                r["mode"]: r["n"]
                for r in self._conn.execute(
                    "SELECT mode, COUNT(*) AS n FROM detection_events "
                    "GROUP BY mode ORDER BY mode ASC"
                )
            }
        return {
            "schema_version": _SCHEMA_VERSION,
            "detection_events.total": de_total,
            "detection_events.by_mode": mode_histogram,
            "episodes.total": ep_total,
            "episodes.unresolved": ep_unresolved,
            "fsm_state.by_state": fsm_histogram,
        }


# ---- helpers -----------------------------------------------------------


def _row_to_episode(row: sqlite3.Row) -> EpisodeRow:
    return EpisodeRow(
        episode_id=row["episode_id"],
        mode=row["mode"],
        signal=row["signal"],
        policy=row["policy"],
        started_at=row["started_at"],
        resolved_at=row["resolved_at"],
        resolution_kind=row["resolution_kind"],
        paused_scope_ids=json.loads(row["paused_scope_ids"]) if row["paused_scope_ids"] else [],
        failed_scope_ids=json.loads(row["failed_scope_ids"]) if row["failed_scope_ids"] else [],
        notification_sent_at=row["notification_sent_at"],
        resume_notification_sent_at=row["resume_notification_sent_at"],
        notification_threshold=row["notification_threshold"],
    )


# ---- reconciliation ---------------------------------------------------


@dataclass
class ReconciliationPlan:
    """Outcome of a restart reconciliation step.

    `actions` is a list of descriptive strings — what was done, for
    logging / OTel emission. The component applies the plan before
    resuming normal operation.
    """

    case: int  # 1 / 2 / 3 / 4 per the research's four cases
    actions: list[str]
    should_reemit_notification: bool
    should_call_resume_activation: bool
    active_episode_id: str | None


def reconcile(
    *,
    orchestrator_paused: bool,
    unresolved_episodes: list[EpisodeRow],
) -> ReconciliationPlan:
    """Decide what to do at startup given the cross-state case.

    Called by the component on startup before resuming FSM operation.
    """
    has_active_episode = len(unresolved_episodes) > 0
    active_ep = unresolved_episodes[0].episode_id if has_active_episode else None

    if orchestrator_paused and has_active_episode:
        return ReconciliationPlan(
            case=1,
            actions=[
                "continue_probe_cycle",
                f"resume_episode:{active_ep}",
            ],
            should_reemit_notification=False,
            should_call_resume_activation=False,
            active_episode_id=active_ep,
        )
    if orchestrator_paused and not has_active_episode:
        return ReconciliationPlan(
            case=2,
            actions=[
                "recreate_recovered_episode",
                "reopen_with_restart_tag",
            ],
            should_reemit_notification=False,
            should_call_resume_activation=False,
            active_episode_id=None,
        )
    if not orchestrator_paused and has_active_episode:
        return ReconciliationPlan(
            case=3,
            actions=[
                f"resolve_episode:{active_ep}:reconciled_on_restart",
                "call_resume_activation",
            ],
            should_reemit_notification=False,
            should_call_resume_activation=True,
            active_episode_id=active_ep,
        )
    return ReconciliationPlan(
        case=4,
        actions=["no_action"],
        should_reemit_notification=False,
        should_call_resume_activation=False,
        active_episode_id=None,
    )
