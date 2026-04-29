"""D6 — local SQLite for orchestrator state.

Acceptance (from brief D6):
- Database exists at configured path on first start.
- Tables cover: heartbeats, compaction flags, bind-refused log,
  lifecycle events (start/stop/crash).
- Event-sourced pattern matches Phase 1 primitives' pattern.
- v1.1 R1 semantic round-trip upgrade test passes.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from loam.orchestrator import Orchestrator
from loam.orchestrator.local_state import LocalStateStore


@pytest.mark.asyncio
async def test_database_exists_on_first_start(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running():
        assert tmp_config.local_sqlite_path.exists()


@pytest.mark.asyncio
async def test_all_required_event_types_writable(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        # Simulate each required event type.
        o.local_state.append("heartbeat", {"tick_id": 1, "uptime_seconds": 0.5})
        o.local_state.append(
            "bind_refused",
            {
                "scope_id": "scope-x",
                "objective_id": "obj-y",
                "cause_kind": "UnresolvedObjectiveError",
                "cause_message": "demo",
            },
        )
        o.local_state.append(
            "scope_activated",
            {"scope_id": "scope-x", "objective_id": "obj-y"},
        )
        o.local_state.append("pause_activation", {"reason": "demo"})
        o.local_state.append("resume_activation", {})
        o.local_state.set_compaction_flag(session_id="s1")

        for kind in (
            "process_started",
            "heartbeat",
            "bind_refused",
            "scope_activated",
            "pause_activation",
            "resume_activation",
            "compaction_flag_set",
        ):
            assert o.local_state.count(kind) >= 1, f"no events of type {kind}"


def test_event_sourced_pattern_schema(tmp_path):
    """The schema matches the Phase 1 event-sourced pattern: an
    append-only events table with auto-incrementing event_id and ISO
    timestamps."""
    store = LocalStateStore(tmp_path / "t.sqlite")
    store.append("a", {"x": 1})
    store.append("b", {"y": 2})
    store.append("a", {"x": 2})

    with sqlite3.connect(str(tmp_path / "t.sqlite")) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT event_id, event_type, recorded_at, payload FROM events ORDER BY event_id"
        ).fetchall()
    assert [r["event_id"] for r in rows] == [1, 2, 3]
    assert [r["event_type"] for r in rows] == ["a", "b", "a"]
    store.close()


def test_semantic_round_trip_upgrade_probe(tmp_path):
    """v1.1 R1 semantic round-trip upgrade test:
    capture a probe before "upgrade", replay events into a fresh db,
    capture the probe again, assert drift == 0.

    In a real upgrade, "replay" would be a schema migration routine.
    The probe-based test here captures the invariant: the semantic
    shape (types + counts + payload keys) survives the migration.
    """
    db1 = tmp_path / "pre.sqlite"
    store = LocalStateStore(db1)
    # Seed a realistic event sequence.
    store.append("process_started", {"pid": 1000, "workspace": "w"})
    for i in range(5):
        store.append("heartbeat", {"tick_id": i, "uptime_seconds": float(i)})
    store.append(
        "bind_refused",
        {
            "scope_id": "s1",
            "objective_id": "o1",
            "cause_kind": "UnresolvedObjectiveError",
            "cause_message": "missing",
        },
    )
    store.append("scope_activated", {"scope_id": "s2", "objective_id": "o2"})
    store.append("pause_activation", {"reason": "api outage"})
    store.append("resume_activation", {"prior_reason": "api outage"})
    store.set_compaction_flag(session_id="sess-1")
    pre_probe = store.snapshot_probe()

    # Replay all events into a fresh db (the "post-upgrade" db).
    events = store.all_events()
    store.close()

    db2 = tmp_path / "post.sqlite"
    store2 = LocalStateStore(db2)
    for e in events:
        store2.append(e.event_type, e.payload)
    post_probe = store2.snapshot_probe()
    store2.close()

    # Structural shape identical. (event_ids may renumber, which is
    # why the probe uses counts + payload keys, not ids.)
    assert pre_probe == post_probe, (
        f"semantic drift: pre={pre_probe}, post={post_probe}"
    )


def test_compaction_flag_lifecycle(tmp_path):
    store = LocalStateStore(tmp_path / "c.sqlite")
    assert not store.compaction_flag_pending()
    store.set_compaction_flag(session_id="s1")
    assert store.compaction_flag_pending()
    store.clear_compaction_flag()
    assert not store.compaction_flag_pending()
    store.close()


def test_bind_refused_events_queryable(tmp_path):
    store = LocalStateStore(tmp_path / "b.sqlite")
    store.append("bind_refused", {"scope_id": "s1", "cause_kind": "A"})
    store.append("bind_refused", {"scope_id": "s2", "cause_kind": "B"})
    store.append("heartbeat", {"tick_id": 1})
    refused = store.bind_refused_events()
    assert len(refused) == 2
    assert {e.payload["cause_kind"] for e in refused} == {"A", "B"}
    store.close()
