"""D3 — pre-upgrade snapshot tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from loam.self_upgrade.paths import Paths
from loam.self_upgrade.snapshot import (
    capture_substrate_snapshots,
    restore_substrate_snapshots,
    substrate_components,
)


def _make_sqlite_db(p: Path, rows: list[tuple[int, str]]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, kind TEXT)")
    conn.executemany("INSERT INTO events VALUES (?, ?)", rows)
    conn.commit()
    conn.close()


def _make_directory_db(p: Path, files: dict[str, bytes]) -> None:
    p.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (p / name).write_bytes(content)


@pytest.fixture
def populated_base(tmp_path: Path, monkeypatch) -> Paths:
    """Set up a base dir populated with every component substrate."""
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    _make_directory_db(p.memory_db, {"memory.kuzu": b"kuzu-1", "catalog.bin": b"cat"})
    _make_sqlite_db(p.scope_of_work_db, [(1, "scope_created"), (2, "scope_closed")])
    _make_sqlite_db(p.objective_tracker_db, [(1, "objective_created")])
    _make_sqlite_db(p.orchestrator_db, [(1, "activation"), (2, "compaction_start")])
    _make_sqlite_db(p.degradation_db, [(1, "episode_opened")])
    p.aggregator_db.parent.mkdir(parents=True, exist_ok=True)
    p.aggregator_db.write_bytes(b"fake-duckdb-bytes")
    return p


def test_capture_covers_every_component(populated_base: Paths) -> None:
    tag = "pos-v2-v0.2.0"
    result = capture_substrate_snapshots(populated_base, tag, probe_fn=None)
    for comp in substrate_components():
        assert comp in result.per_component
        snap = result.per_component[comp]
        assert snap.files_copied >= 1


def test_snapshot_drift_raises(populated_base: Paths) -> None:
    tag = "pos-v2-v0.2.0"

    calls = {"n": 0}

    def probe_fn() -> dict:
        calls["n"] += 1
        if calls["n"] == 1:
            return {"memory": "hash-a"}
        return {"memory": "hash-b"}  # drift

    with pytest.raises(RuntimeError, match="snapshot-drift"):
        capture_substrate_snapshots(populated_base, tag, probe_fn=probe_fn)


def test_snapshot_consistent_probe_passes(populated_base: Paths) -> None:
    tag = "pos-v2-v0.2.0"
    result = capture_substrate_snapshots(
        populated_base, tag, probe_fn=lambda: {"all": "stable"}
    )
    assert result.tag == tag


def test_restore_round_trips(populated_base: Paths) -> None:
    tag = "pos-v2-v0.2.0"
    capture_substrate_snapshots(populated_base, tag, probe_fn=None)

    original_memory = (populated_base.memory_db / "memory.kuzu").read_bytes()

    # Corrupt live state
    (populated_base.memory_db / "memory.kuzu").write_bytes(b"corrupt")
    (populated_base.scope_of_work_db).write_bytes(b"corrupt")

    # Restore
    restore_substrate_snapshots(populated_base, tag)

    # Original bytes back
    assert (populated_base.memory_db / "memory.kuzu").read_bytes() == original_memory


def test_restore_missing_snapshot_raises(populated_base: Paths) -> None:
    with pytest.raises(FileNotFoundError):
        restore_substrate_snapshots(populated_base, "pos-v2-vNONE")
