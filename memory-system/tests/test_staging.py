"""Staging store tests (Amendment 1 — hands-off-lifecycle).

Covers H-criteria from proposal §5.3:

    H11 — FIFO preservation + client UUIDs
    H13 — StagingOverflow raises at hard_cap
    H15 — read-path fallback during degraded mode (staging-filtered)

H12 / H14 land in test_drain.py (drain-worker tests).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.staging import StagedEntry, StagingOverflow, StagingStore


@pytest.fixture
def db(tmp_path: Path) -> StagingStore:
    return StagingStore(tmp_path / "staging.sqlite")


# ---- H11 FIFO + UUID preservation ------------------------------------


def test_H11_staged_entries_preserve_FIFO_order(db: StagingStore) -> None:
    e1 = db.stage({"name": "first", "body": "one", "group_id": "s"})
    e2 = db.stage({"name": "second", "body": "two", "group_id": "s"})
    e3 = db.stage({"name": "third", "body": "three", "group_id": "s"})
    pending = db.list_pending()
    assert [p.id for p in pending] == [e1.id, e2.id, e3.id]
    assert [p.payload["name"] for p in pending] == ["first", "second", "third"]


def test_H11_client_supplied_uuid_preserved(db: StagingStore) -> None:
    uid = "fixed-client-uuid-123"
    entry = db.stage({"name": "x", "body": "b", "group_id": "s"}, episode_uuid=uid)
    assert entry.episode_uuid == uid
    reloaded = db.list_pending()[0]
    assert reloaded.episode_uuid == uid


def test_H11_duplicate_uuid_rejected(db: StagingStore) -> None:
    db.stage({"name": "x", "body": "b", "group_id": "s"}, episode_uuid="dup")
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        db.stage({"name": "y", "body": "c", "group_id": "s"}, episode_uuid="dup")


# ---- H13 StagingOverflow at hard cap ---------------------------------


def test_H13_stage_raises_StagingOverflow_at_hard_cap(tmp_path: Path) -> None:
    db = StagingStore(
        tmp_path / "staging.sqlite", soft_cap=2, hard_cap=3
    )
    db.stage({"name": "a", "body": "1", "group_id": "s"})
    db.stage({"name": "b", "body": "2", "group_id": "s"})
    db.stage({"name": "c", "body": "3", "group_id": "s"})
    with pytest.raises(StagingOverflow) as excinfo:
        db.stage({"name": "d", "body": "4", "group_id": "s"})
    assert excinfo.value.hard_cap == 3
    assert excinfo.value.size == 3
    assert excinfo.value.code == -32095


# ---- H15 read-path fallback (group-filtered) -------------------------


def test_H15_list_recent_for_group_filters_by_group_id(db: StagingStore) -> None:
    db.stage({"name": "a", "body": "1", "group_id": "team-alpha"})
    db.stage({"name": "b", "body": "2", "group_id": "team-beta"})
    db.stage({"name": "c", "body": "3", "group_id": "team-alpha"})
    alpha = db.list_recent_for_group(group_id="team-alpha")
    beta = db.list_recent_for_group(group_id="team-beta")
    assert [e.payload["name"] for e in alpha] == ["a", "c"]
    assert [e.payload["name"] for e in beta] == ["b"]


# ---- drain lifecycle helpers ----------------------------------------


def test_mark_forwarded_removes_entry(db: StagingStore) -> None:
    e = db.stage({"name": "x", "body": "b", "group_id": "s"})
    db.mark_forwarded(e.id)
    assert db.size() == 0


def test_mark_failure_increments_attempts(db: StagingStore) -> None:
    e = db.stage({"name": "x", "body": "b", "group_id": "s"})
    n1 = db.mark_failure(e.id, error="boom")
    n2 = db.mark_failure(e.id, error="boom again")
    assert (n1, n2) == (1, 2)


def test_move_to_poison_preserves_entry(db: StagingStore) -> None:
    e = db.stage({"name": "bad", "body": "b", "group_id": "s"})
    db.move_to_poison(e.id)
    assert db.size() == 0
    assert db.poison_size() == 1
    poison = db.list_poison()
    assert poison[0].episode_uuid == e.episode_uuid
    # Staged payload preserved intact — never silently dropped.
    assert poison[0].payload == {"name": "bad", "body": "b", "group_id": "s"}


# ---- WAL mode / concurrent readers ----------------------------------


def test_journal_mode_is_WAL(db: StagingStore) -> None:
    with db._lock:  # type: ignore[attr-defined]
        row = db._conn.execute("PRAGMA journal_mode").fetchone()  # type: ignore[attr-defined]
    assert str(row[0]).lower() == "wal"
