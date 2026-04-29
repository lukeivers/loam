"""Storage substrate — DuckDB primary, SQLite fallback at identical schema.

The store is the canonical query target. Both ingest paths
(in-process OTel SpanExporter and memory JSONL tailer) write here;
both query surfaces (structured Pydantic API and `pos obs` CLI) read
from here.

Schema rationale (see research §5):
  - One `spans` table; `component` column for cross-component queries.
  - `span_events` for OTel events (state transitions, narrative
    rendered, supersession_inferred, etc.).
  - `tokens` for v1.1 R12 cost attribution by `prompt_name`.
  - `audit` for free-text rationales (memory's audit.jsonl mainly).
  - `ingest_cursors` for tail resumption — byte-offset per source.
  - `daily_rollup`, `monthly_rollup`, `yearly_rollup` for the
    decaying retention tiers.

DuckDB and SQLite differ slightly on type names and JSON support.
The store hides this: the application layer always sees Pydantic
records; the substrate driver translates.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


_LOGGER = logging.getLogger("loam.aggregator.store")

from .config import AggregatorConfig, Substrate
from .schema import (
    AuditRecord,
    EventRecord,
    RetentionClass,
    SpanRecord,
    TokenRecord,
    apply_retention_class,
)


# ---- substrate-agnostic SQL --------------------------------------------
#
# DuckDB and SQLite share enough of standard SQL that we can use one
# CREATE TABLE per substrate (slight syntax differences).

DUCKDB_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS spans (
        trace_id              VARCHAR NOT NULL,
        span_id               VARCHAR NOT NULL,
        parent_span_id        VARCHAR,
        name                  VARCHAR NOT NULL,
        tracer_name           VARCHAR NOT NULL,
        component             VARCHAR NOT NULL,
        kind                  VARCHAR,
        start_time_unix_nano  BIGINT NOT NULL,
        end_time_unix_nano    BIGINT NOT NULL,
        duration_ns           BIGINT NOT NULL,
        status                VARCHAR,
        status_message        VARCHAR,
        attributes            JSON,
        retention_class       VARCHAR NOT NULL,
        ingested_at           TIMESTAMP NOT NULL,
        PRIMARY KEY (span_id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_spans_trace        ON spans(trace_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_spans_start        ON spans(start_time_unix_nano)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_spans_component    ON spans(component)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_spans_name         ON spans(name)
    """,
    """
    CREATE TABLE IF NOT EXISTS span_events (
        event_id        BIGINT,
        span_id         VARCHAR NOT NULL,
        trace_id        VARCHAR NOT NULL,
        name            VARCHAR NOT NULL,
        time_unix_nano  BIGINT NOT NULL,
        attributes      JSON,
        retention_class VARCHAR NOT NULL,
        ingested_at     TIMESTAMP NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_events_trace_time ON span_events(trace_id, time_unix_nano)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_events_span ON span_events(span_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS tokens (
        row_id        BIGINT,
        trace_id      VARCHAR,
        span_id       VARCHAR,
        prompt_name   VARCHAR NOT NULL,
        model         VARCHAR NOT NULL,
        input_tokens  INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        call_count    INTEGER NOT NULL,
        at_time       TIMESTAMP NOT NULL,
        scope_id      VARCHAR,
        component     VARCHAR
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tokens_prompt ON tokens(prompt_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tokens_at ON tokens(at_time)
    """,
    """
    CREATE TABLE IF NOT EXISTS audit (
        audit_id      BIGINT,
        at_time       TIMESTAMP NOT NULL,
        operation     VARCHAR NOT NULL,
        actor         VARCHAR NOT NULL,
        scope_id      VARCHAR,
        subject_uuid  VARCHAR,
        rationale     VARCHAR NOT NULL,
        extras        JSON
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ingest_cursors (
        source_id        VARCHAR PRIMARY KEY,
        source_path      VARCHAR,
        byte_offset      BIGINT NOT NULL,
        last_record_time TIMESTAMP,
        updated_at       TIMESTAMP NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS daily_rollup (
        day             DATE NOT NULL,
        component       VARCHAR NOT NULL,
        span_name       VARCHAR NOT NULL,
        span_count      BIGINT NOT NULL,
        total_duration_ns BIGINT NOT NULL,
        error_count     BIGINT NOT NULL,
        retention_class VARCHAR NOT NULL,
        PRIMARY KEY (day, component, span_name, retention_class)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS monthly_rollup (
        year_month      VARCHAR NOT NULL,
        component       VARCHAR NOT NULL,
        span_name       VARCHAR NOT NULL,
        span_count      BIGINT NOT NULL,
        total_duration_ns BIGINT NOT NULL,
        error_count     BIGINT NOT NULL,
        PRIMARY KEY (year_month, component, span_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS yearly_rollup (
        year            INTEGER NOT NULL,
        component       VARCHAR NOT NULL,
        span_name       VARCHAR NOT NULL,
        span_count      BIGINT NOT NULL,
        total_duration_ns BIGINT NOT NULL,
        error_count     BIGINT NOT NULL,
        PRIMARY KEY (year, component, span_name)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS meta (
        key   VARCHAR PRIMARY KEY,
        value VARCHAR
    )
    """,
]


# SQLite version: identical schema, with TEXT for VARCHAR/JSON, INTEGER for BIGINT.
SQLITE_SCHEMA = [
    s.replace("VARCHAR", "TEXT")
     .replace("JSON", "TEXT")
     .replace("TIMESTAMP", "TEXT")
     .replace("DATE", "TEXT")
     .replace("BIGINT", "INTEGER")
    for s in DUCKDB_SCHEMA
]


class Store:
    """Substrate-agnostic store wrapper.

    Internally holds either a duckdb connection or a sqlite3
    connection; presents the same write/read interface either way.
    All json-shaped attribute bags are persisted as JSON strings; the
    application layer round-trips via `json.dumps` on write and
    `json.loads` on read.
    """

    def __init__(self, config: AggregatorConfig) -> None:
        self.config = config
        self.config.ensure_dirs()
        self.substrate: Substrate = config.substrate
        self.db_path = config.resolved_db_path()
        self._lock = threading.RLock()
        self._conn = self._connect()
        self._init_schema()
        self._next_event_id = self._max_id("span_events", "event_id") + 1
        self._next_token_id = self._max_id("tokens", "row_id") + 1
        self._next_audit_id = self._max_id("audit", "audit_id") + 1

    def _connect(self):
        if self.substrate == "duckdb":
            try:
                import duckdb  # type: ignore
            except ImportError as exc:
                raise RuntimeError(
                    "duckdb required for substrate='duckdb'; install or "
                    "switch substrate to 'sqlite' in config"
                ) from exc
            return duckdb.connect(str(self.db_path))
        # sqlite
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_schema(self) -> None:
        ddl = DUCKDB_SCHEMA if self.substrate == "duckdb" else SQLITE_SCHEMA
        with self._lock:
            for stmt in ddl:
                self._conn.execute(stmt)
            if self.substrate == "sqlite":
                self._conn.commit()

    def _max_id(self, table: str, col: str) -> int:
        with self._lock:
            row = self._conn.execute(
                f"SELECT COALESCE(MAX({col}), 0) FROM {table}"
            ).fetchone()
        if row is None:
            return 0
        return int(row[0] or 0)

    # ---- writes ------------------------------------------------------

    def _placeholders(self, n: int) -> str:
        # both substrates accept ?
        return ", ".join("?" for _ in range(n))

    def insert_span(self, span: SpanRecord) -> None:
        # Apply retention class to attributes at ingest (v1.1 R10).
        attrs = apply_retention_class(span.attributes, span.retention_class)
        with self._lock:
            self._conn.execute(
                f"""
                INSERT OR REPLACE INTO spans (
                    trace_id, span_id, parent_span_id, name, tracer_name,
                    component, kind, start_time_unix_nano, end_time_unix_nano,
                    duration_ns, status, status_message, attributes,
                    retention_class, ingested_at
                ) VALUES ({self._placeholders(15)})
                """ if self.substrate == "sqlite" else
                f"""
                INSERT INTO spans (
                    trace_id, span_id, parent_span_id, name, tracer_name,
                    component, kind, start_time_unix_nano, end_time_unix_nano,
                    duration_ns, status, status_message, attributes,
                    retention_class, ingested_at
                ) VALUES ({self._placeholders(15)})
                ON CONFLICT (span_id) DO NOTHING
                """,
                (
                    span.trace_id,
                    span.span_id,
                    span.parent_span_id,
                    span.name,
                    span.tracer_name,
                    span.component,
                    span.kind,
                    span.start_time_unix_nano,
                    span.end_time_unix_nano,
                    span.duration_ns,
                    span.status,
                    span.status_message,
                    json.dumps(attrs, default=str),
                    span.retention_class.value,
                    self._iso(span.ingested_at),
                ),
            )
            if self.substrate == "sqlite":
                self._conn.commit()

    def insert_event(self, event: EventRecord) -> None:
        attrs = apply_retention_class(event.attributes, event.retention_class)
        with self._lock:
            event_id = self._next_event_id
            self._next_event_id += 1
            self._conn.execute(
                f"""
                INSERT INTO span_events (
                    event_id, span_id, trace_id, name, time_unix_nano,
                    attributes, retention_class, ingested_at
                ) VALUES ({self._placeholders(8)})
                """,
                (
                    event_id,
                    event.span_id,
                    event.trace_id,
                    event.name,
                    event.time_unix_nano,
                    json.dumps(attrs, default=str),
                    event.retention_class.value,
                    self._iso(event.ingested_at),
                ),
            )
            if self.substrate == "sqlite":
                self._conn.commit()

    def insert_token(self, row: TokenRecord) -> None:
        with self._lock:
            row_id = self._next_token_id
            self._next_token_id += 1
            self._conn.execute(
                f"""
                INSERT INTO tokens (
                    row_id, trace_id, span_id, prompt_name, model,
                    input_tokens, output_tokens, call_count, at_time,
                    scope_id, component
                ) VALUES ({self._placeholders(11)})
                """,
                (
                    row_id,
                    row.trace_id,
                    row.span_id,
                    row.prompt_name,
                    row.model,
                    int(row.input_tokens),
                    int(row.output_tokens),
                    int(row.call_count),
                    self._iso(row.at_time),
                    row.scope_id,
                    row.component,
                ),
            )
            if self.substrate == "sqlite":
                self._conn.commit()

    def insert_audit(self, row: AuditRecord) -> None:
        with self._lock:
            audit_id = self._next_audit_id
            self._next_audit_id += 1
            self._conn.execute(
                f"""
                INSERT INTO audit (
                    audit_id, at_time, operation, actor, scope_id,
                    subject_uuid, rationale, extras
                ) VALUES ({self._placeholders(8)})
                """,
                (
                    audit_id,
                    self._iso(row.at_time),
                    row.operation,
                    row.actor,
                    row.scope_id,
                    row.subject_uuid,
                    row.rationale,
                    json.dumps(row.extras, default=str),
                ),
            )
            if self.substrate == "sqlite":
                self._conn.commit()

    # ---- ingest cursors ---------------------------------------------

    def get_cursor(self, source_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT byte_offset FROM ingest_cursors WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        return int(row[0]) if row else 0

    def set_cursor(
        self, source_id: str, source_path: str, byte_offset: int,
        last_record_time: datetime | None = None,
    ) -> None:
        now_iso = self._iso(datetime.now(timezone.utc))
        last_iso = self._iso(last_record_time) if last_record_time else None
        with self._lock:
            existing = self._conn.execute(
                "SELECT source_id FROM ingest_cursors WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            if existing:
                self._conn.execute(
                    """
                    UPDATE ingest_cursors
                    SET source_path = ?, byte_offset = ?, last_record_time = ?, updated_at = ?
                    WHERE source_id = ?
                    """,
                    (source_path, byte_offset, last_iso, now_iso, source_id),
                )
            else:
                self._conn.execute(
                    f"""
                    INSERT INTO ingest_cursors (source_id, source_path, byte_offset, last_record_time, updated_at)
                    VALUES ({self._placeholders(5)})
                    """,
                    (source_id, source_path, byte_offset, last_iso, now_iso),
                )
            if self.substrate == "sqlite":
                self._conn.commit()

    # ---- reads -------------------------------------------------------

    def fetch(self, sql: str, params: Sequence[Any] = ()) -> list[tuple[Any, ...]]:
        with self._lock:
            return list(self._conn.execute(sql, tuple(params)).fetchall())

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        with self._lock:
            self._conn.execute(sql, tuple(params))
            if self.substrate == "sqlite":
                self._conn.commit()

    def file_size_bytes(self) -> int:
        try:
            return self.db_path.stat().st_size
        except FileNotFoundError:
            return 0

    # ---- lifecycle ---------------------------------------------------

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                # Amendment #26 — teardown CDC 2: surface exception to
                # observability. No span in scope; logger.debug is the
                # tightened-CDC fallback. Module logger name follows
                # ingest.py's convention (`loam.aggregator.*`).
                _LOGGER.debug(
                    "aggregator_store_close_failed", exc_info=True
                )

    # ---- helpers -----------------------------------------------------

    @staticmethod
    def _iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()


def open_store(config: AggregatorConfig | None = None) -> Store:
    """Open the configured store, falling back to SQLite if DuckDB unavailable."""
    cfg = config or AggregatorConfig()
    if cfg.substrate == "duckdb":
        try:
            import duckdb  # noqa: F401
        except ImportError:
            cfg.substrate = "sqlite"
    return Store(cfg)
