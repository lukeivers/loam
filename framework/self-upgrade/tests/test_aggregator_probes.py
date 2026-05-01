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

"""Framework-owned aggregator probe set tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from loam.self_upgrade.aggregator_probes import (
    PROBE_SET_VERSION,
    aggregator_probe_hash,
    run_aggregator_probes,
)


_SQLITE_SCHEMA = [
    """CREATE TABLE spans (
        span_id TEXT PRIMARY KEY,
        trace_id TEXT,
        component TEXT,
        status TEXT,
        name TEXT
    )""",
    """CREATE TABLE span_events (
        event_id INTEGER PRIMARY KEY,
        span_id TEXT,
        name TEXT
    )""",
    """CREATE TABLE tokens (
        row_id INTEGER PRIMARY KEY,
        prompt_name TEXT,
        input_tokens INTEGER,
        output_tokens INTEGER
    )""",
    """CREATE TABLE audit (
        audit_id INTEGER PRIMARY KEY,
        component TEXT,
        payload TEXT
    )""",
]


def _seed_sqlite_aggregator(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    for stmt in _SQLITE_SCHEMA:
        conn.execute(stmt)
    conn.executemany(
        "INSERT INTO spans VALUES (?, ?, ?, ?, ?)",
        [
            ("s1", "t1", "memory", "OK", "memory.write"),
            ("s2", "t1", "scope_of_work", "OK", "scope.activate"),
            ("s3", "t2", "orchestrator", "ERROR", "ipc.rpc"),
        ],
    )
    conn.executemany(
        "INSERT INTO span_events (span_id, name) VALUES (?, ?)",
        [("s1", "memory.fact_added"), ("s2", "scope.paused")],
    )
    conn.executemany(
        "INSERT INTO tokens (prompt_name, input_tokens, output_tokens) VALUES (?, ?, ?)",
        [("eve.dispatch", 500, 200), ("ori.review", 300, 150)],
    )
    conn.execute(
        "INSERT INTO audit (component, payload) VALUES (?, ?)",
        ("memory", '{"rationale":"x"}'),
    )
    conn.commit()
    conn.close()


def test_sqlite_probe_runs(tmp_path: Path) -> None:
    db = tmp_path / "observability.sqlite"
    _seed_sqlite_aggregator(db)
    result = run_aggregator_probes(db)
    assert result.probe_set_version == PROBE_SET_VERSION
    assert result.substrate == "sqlite"
    assert result.queries["spans_total"]["rows"][0]["n"] == 3
    assert result.queries["span_events_total"]["rows"][0]["n"] == 2
    assert result.queries["tokens_total"]["rows"][0]["n"] == 2
    assert result.queries["audit_total"]["rows"][0]["n"] == 1
    by_comp = result.queries["spans_by_component"]["rows"]
    components = sorted(r["component"] for r in by_comp)
    assert components == ["memory", "orchestrator", "scope_of_work"]


def test_probe_hash_is_stable(tmp_path: Path) -> None:
    db = tmp_path / "observability.sqlite"
    _seed_sqlite_aggregator(db)
    r1 = run_aggregator_probes(db)
    r2 = run_aggregator_probes(db)
    assert aggregator_probe_hash(r1) == aggregator_probe_hash(r2)


def test_probe_hash_changes_with_writes(tmp_path: Path) -> None:
    db = tmp_path / "observability.sqlite"
    _seed_sqlite_aggregator(db)
    r1 = run_aggregator_probes(db)
    conn = sqlite3.connect(str(db))
    conn.execute(
        "INSERT INTO spans VALUES ('s4','t3','degradation','OK','deg.detect')"
    )
    conn.commit()
    conn.close()
    r2 = run_aggregator_probes(db)
    assert aggregator_probe_hash(r1) != aggregator_probe_hash(r2)


def test_missing_db_gives_per_query_error(tmp_path: Path) -> None:
    db = tmp_path / "nonexistent.sqlite"
    result = run_aggregator_probes(db)
    for val in result.queries.values():
        assert "error" in val


def test_schema_fragment_handles_missing_table(tmp_path: Path) -> None:
    db = tmp_path / "partial.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    # Only create spans — other tables missing
    for stmt in _SQLITE_SCHEMA[:1]:
        conn.execute(stmt)
    conn.commit()
    conn.close()
    result = run_aggregator_probes(db)
    assert "rows" in result.queries["spans_total"]
    assert "error" in result.queries["tokens_total"]
    assert "error" in result.queries["audit_total"]
