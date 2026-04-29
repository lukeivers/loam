"""AC.J.7 — Idempotency: queue + worker do not double-write.

Outcome (per locked plan §4): given two identical turn records
enqueued back-to-back, the worker writes exactly one ``add_episode``
call to the memory service.

Two-line dedupe:

  1. The on-disk filename is keyed on ``turn_id`` (sanitised), so a
     repeat enqueue overwrites the same file atomically — at most
     one queue entry exists per turn.
  2. The Stop-hook's last-turn-id marker (#48 D4) short-circuits a
     same-turn re-fire before enqueue, so most repeat fires don't
     even reach the queue.

This test exercises line 1 (the structural dedupe at the queue
layer). The Stop-hook-side line-2 dedupe is exercised in
``test_AC_M_8_no_double_write_on_repeat_stop.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww


class _CountingClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"episode_uuid": f"u-{len(self.calls)}"}

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        return {"query": "", "results": []}


def test_AC_J_7_repeat_enqueue_overwrites_same_file(tmp_path: Path) -> None:
    """Enqueueing the same turn_id twice produces exactly one queue
    entry — the second write overwrites the first via os.replace."""
    a = mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:dup",
        session_id="s1",
        user_message="msg",
        assistant_reply="reply",
    )
    b = mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:dup",
        session_id="s1",
        user_message="msg",
        assistant_reply="reply-updated",
    )
    assert a == b  # same on-disk path
    entries = mwq.list_queue_entries_oldest_first(tmp_path)
    assert len(entries) == 1
    record = mwq.read_queue_entry(entries[0])
    assert record is not None
    # Second enqueue's payload won.
    assert record["assistant_reply"] == "reply-updated"


def test_AC_J_7_drain_writes_exactly_one_episode_per_dedup_collapse(
    tmp_path: Path,
) -> None:
    """Two enqueues of the same turn → one queue entry → one
    add_episode call at drain. Observable count is exactly one."""
    for body in ("first", "second", "third"):
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id="s1:once",
            session_id="s1",
            user_message=body,
            assistant_reply=body,
        )
    # Three enqueues collapsed to one queue entry.
    assert len(mwq.list_queue_entries_oldest_first(tmp_path)) == 1

    client = _CountingClient()
    counters = mww.drain_once(
        workspace_root=tmp_path,
        config={
            "max_retries": 5,
            "backoff_initial_s": 0.0,
            "backoff_max_s": 0.0,
            "poll_interval_s": 0.0,
            "tmp_cleanup_age_s": 3600.0,
        },
        client_factory=lambda _root: client,
        workspace_slug="ws",
        sleep_fn=lambda _s: None,
    )
    # Exactly one add_episode call.
    assert counters.get("ok", 0) == 1
    assert len(client.calls) == 1


def test_AC_J_7_distinct_turn_ids_each_get_their_own_entry(tmp_path: Path) -> None:
    """Sanity: AC.J.7 dedupe is by turn_id, not session-id alone.
    Different turn-ids land their own queue entries."""
    for tid in ("s1:a", "s1:b", "s2:a"):
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id=tid,
            session_id=tid.split(":")[0],
            user_message=tid,
            assistant_reply=tid,
        )
    entries = mwq.list_queue_entries_oldest_first(tmp_path)
    assert len(entries) == 3
