"""Framework-owned probe set for the observability aggregator.

The aggregator does not expose a named ``snapshot_probe()`` surface.
Rather than unseal the aggregator, Luke approved that the framework
carries its own probe set as a declared collection of deterministic
DuckDB / SQLite queries whose results round-trip across an upgrade.

The queries are **shape-only** — counts, histograms, stable aggregates
— never values that depend on wall-clock time. Two successive calls
against the same db must be equal; a post-upgrade call against an
unchanged db must match the pre-upgrade call.

If a query fails (table missing, substrate mid-migration), the probe
returns ``{"error": str(exc), "query_id": qid}`` for that query so the
drift check has something deterministic to compare.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Each query is a pure SELECT that returns a small fixed-shape result.
# The framework owns this list. Adding a query bumps the probe-set
# version so old manifests can declare which probe-set version they
# expect.
_PROBE_QUERIES: tuple[tuple[str, str], ...] = (
    ("spans_total", "SELECT COUNT(*) AS n FROM spans"),
    (
        "spans_by_component",
        "SELECT component, COUNT(*) AS n FROM spans "
        "GROUP BY component ORDER BY component ASC",
    ),
    (
        "spans_by_status",
        "SELECT status, COUNT(*) AS n FROM spans "
        "GROUP BY status ORDER BY status ASC",
    ),
    (
        "span_events_total",
        "SELECT COUNT(*) AS n FROM span_events",
    ),
    (
        "span_events_by_name",
        "SELECT name, COUNT(*) AS n FROM span_events "
        "GROUP BY name ORDER BY name ASC LIMIT 50",
    ),
    ("tokens_total", "SELECT COUNT(*) AS n FROM tokens"),
    (
        "tokens_by_prompt",
        "SELECT prompt_name, COUNT(*) AS n FROM tokens "
        "GROUP BY prompt_name ORDER BY prompt_name ASC LIMIT 100",
    ),
    ("audit_total", "SELECT COUNT(*) AS n FROM audit"),
)

PROBE_SET_VERSION = 1


@dataclass(frozen=True)
class AggregatorProbeResult:
    probe_set_version: int
    substrate: str
    queries: dict[str, Any]


def _detect_substrate(db_path: Path) -> str:
    """Return 'duckdb' or 'sqlite' based on extension."""
    if db_path.suffix == ".duckdb":
        return "duckdb"
    return "sqlite"


def run_aggregator_probes(db_path: str | Path) -> AggregatorProbeResult:
    """Execute every query against the aggregator db.

    Errors on a per-query basis are captured rather than raised so the
    result remains comparable in the face of schema evolution.
    """
    p = Path(db_path)
    substrate = _detect_substrate(p)
    queries: dict[str, Any] = {}

    if not p.exists():
        for qid, _sql in _PROBE_QUERIES:
            queries[qid] = {"error": "db_missing"}
        return AggregatorProbeResult(
            probe_set_version=PROBE_SET_VERSION,
            substrate=substrate,
            queries=queries,
        )

    if substrate == "duckdb":
        try:
            import duckdb  # type: ignore
        except ImportError:
            for qid, _sql in _PROBE_QUERIES:
                queries[qid] = {"error": "duckdb_not_installed"}
            return AggregatorProbeResult(
                probe_set_version=PROBE_SET_VERSION,
                substrate=substrate,
                queries=queries,
            )
        conn = duckdb.connect(str(p), read_only=True)
        try:
            for qid, sql in _PROBE_QUERIES:
                queries[qid] = _run_one(conn, sql, qid)
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            for qid, sql in _PROBE_QUERIES:
                queries[qid] = _run_one(conn, sql, qid)
        finally:
            conn.close()

    return AggregatorProbeResult(
        probe_set_version=PROBE_SET_VERSION,
        substrate=substrate,
        queries=queries,
    )


def _run_one(conn: Any, sql: str, qid: str) -> Any:
    try:
        rows = conn.execute(sql).fetchall()
    except Exception as exc:  # substrate, schema, missing-table…
        return {"error": type(exc).__name__, "detail": str(exc)[:200]}
    # Normalise rows to JSON-stable dicts (list-of-dicts if multi-col;
    # single int if single-col single-row).
    if not rows:
        return {"rows": []}
    first = rows[0]
    # DuckDB returns tuples; SQLite returns Row (dict-like). Handle both.
    if isinstance(first, sqlite3.Row):
        return {"rows": [dict(r) for r in rows]}
    # tuples — no column names available at fetchall time without description
    try:
        cols = [c[0] for c in conn.description]
    except Exception:
        cols = [f"c{i}" for i in range(len(first))]
    return {"rows": [dict(zip(cols, r)) for r in rows]}


def aggregator_probe_hash(result: AggregatorProbeResult) -> str:
    """A stable hash over the probe result, used by D3's consistency
    check (pre-snapshot vs post-snapshot)."""
    import hashlib
    import json

    body = json.dumps(
        {
            "probe_set_version": result.probe_set_version,
            "substrate": result.substrate,
            "queries": result.queries,
        },
        sort_keys=True,
        default=str,
    ).encode()
    return hashlib.sha256(body).hexdigest()
