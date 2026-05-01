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

"""AC.J.4 — Bounded retry + dead-letter on terminal write failure.

Outcome (per locked plan §4): given a queue record whose
``add_episode`` call fails repeatedly, the worker retries with
exponential backoff up to a bounded retry count, then writes the
record to ``<workspace>/.pos/memory-write-deadletter.log`` (NDJSON).
The worker continues processing subsequent queue entries — one
record's failure does not block the queue. The dead-letter file is
human-readable and the operator can re-queue an entry by moving
it back to the queue directory.

D-3 default: 5 retries, exponential backoff 2s→60s. This test uses
a tightened test-only config (max_retries=2; backoff 0.0s) for
deterministic + fast assertions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww


class _AlwaysFails:
    """Fake MemoryClient whose ``add_episode`` always raises."""

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("simulated transient mcp failure")

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        return {"query": "", "results": []}


class _AlwaysOk:
    """Fake MemoryClient whose ``add_episode`` always succeeds."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"episode_uuid": "ok-uuid", "nodes_extracted": 1, "edges_extracted": 0}

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        return {"query": "", "results": []}


def _config(max_retries: int = 2) -> dict[str, Any]:
    return {
        "max_retries": max_retries,
        "backoff_initial_s": 0.0,
        "backoff_max_s": 0.0,
        "poll_interval_s": 0.0,
        "tmp_cleanup_age_s": 3600.0,
    }


def test_AC_J_4_terminal_failure_routes_to_deadletter(tmp_path: Path) -> None:
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:fail",
        session_id="s1",
        user_message="fails",
        assistant_reply="fails",
    )
    failing = _AlwaysFails()
    counters = {"deadletter": 0}
    # Drive 3 drain passes (max_retries=2 means failure on attempt
    # 1 → retry, attempt 2 → retry, attempt 3 → dead-letter).
    for _ in range(3):
        c = mww.drain_once(
            workspace_root=tmp_path,
            config=_config(max_retries=2),
            client_factory=lambda _root: failing,
            workspace_slug="test-ws",
            sleep_fn=lambda _s: None,
        )
        counters["deadletter"] += c.get("deadletter", 0)
        if counters["deadletter"]:
            break

    assert counters["deadletter"] == 1
    # Queue is now empty.
    assert mwq.list_queue_entries_oldest_first(tmp_path) == []
    # Dead-letter log carries the record.
    dl_path = mwq.deadletter_path(tmp_path)
    assert dl_path.exists()
    lines = [ln for ln in dl_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["turn_id"] == "s1:fail"
    assert "RuntimeError" in record["last_error"]
    assert record["retry_count"] >= 2


def test_AC_J_4_one_failure_does_not_block_subsequent_entries(tmp_path: Path) -> None:
    """When entry A fails terminally, entry B (queued after) still
    drains successfully on a subsequent worker pass."""
    # Enqueue two distinct turns.
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:a",
        session_id="s1",
        user_message="A-fails",
        assistant_reply="A",
    )
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:b",
        session_id="s1",
        user_message="B-ok",
        assistant_reply="B",
    )

    # Custom client: fails on turn_id ending in :a, succeeds on :b.
    class _Selective:
        def __init__(self) -> None:
            self.ok_calls: list[dict[str, Any]] = []

        async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
            if kwargs.get("name", "").endswith(":a"):
                raise RuntimeError("a always fails")
            self.ok_calls.append(kwargs)
            return {"episode_uuid": "uuid-b"}

        async def search(self, **kwargs: Any) -> dict[str, Any]:
            return {"query": "", "results": []}

    selective = _Selective()

    # Drive enough passes to exhaust A's retries + drain B.
    for _ in range(5):
        mww.drain_once(
            workspace_root=tmp_path,
            config=_config(max_retries=2),
            client_factory=lambda _root: selective,
            workspace_slug="test-ws",
            sleep_fn=lambda _s: None,
        )

    # B's success was recorded.
    assert len(selective.ok_calls) == 1
    assert selective.ok_calls[0]["name"].endswith(":b")
    # A landed in the dead-letter log.
    dl = mwq.deadletter_path(tmp_path)
    assert dl.exists()
    dl_lines = [ln for ln in dl.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert any(json.loads(ln)["turn_id"] == "s1:a" for ln in dl_lines)
    # Queue is empty (both entries terminal).
    assert mwq.list_queue_entries_oldest_first(tmp_path) == []


def test_AC_J_4_retry_count_persists_to_disk(tmp_path: Path) -> None:
    """After a transient failure, the on-disk record's retry_count
    is bumped; a worker restart picks up where it left off."""
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:retry",
        session_id="s1",
        user_message="X",
        assistant_reply="Y",
    )
    failing = _AlwaysFails()
    mww.drain_once(
        workspace_root=tmp_path,
        config=_config(max_retries=5),
        client_factory=lambda _root: failing,
        workspace_slug="test-ws",
        sleep_fn=lambda _s: None,
    )
    # Entry still in queue; retry_count bumped.
    entries = mwq.list_queue_entries_oldest_first(tmp_path)
    assert len(entries) == 1
    record = mwq.read_queue_entry(entries[0])
    assert record is not None
    assert record["retry_count"] == 1
    assert "RuntimeError" in record["last_error"]


def test_AC_J_4_default_curve_2s_to_60s() -> None:
    """The default retry curve matches D-3 lock: 2s→60s exp backoff."""
    initial = 2.0
    cap = 60.0
    delays = [
        mww.compute_backoff_seconds(retry_count=n, initial_s=initial, max_s=cap)
        for n in (1, 2, 3, 4, 5, 6, 7, 8)
    ]
    # 2, 4, 8, 16, 32, 60 (capped), 60, 60.
    assert delays[0] == 2.0
    assert delays[1] == 4.0
    assert delays[2] == 8.0
    assert delays[3] == 16.0
    assert delays[4] == 32.0
    assert delays[5] == 60.0
    assert delays[6] == 60.0
    assert delays[7] == 60.0


def test_AC_J_4_corrupt_entry_routes_to_deadletter(tmp_path: Path) -> None:
    """A queue entry whose JSON is unreadable goes to dead-letter so
    the queue does not block on a corrupt file."""
    qdir = mwq.queue_dir(tmp_path)
    qdir.mkdir(parents=True, exist_ok=True)
    bad = qdir / "s1_corrupt.json"
    bad.write_text("{not json", encoding="utf-8")

    counters = mww.drain_once(
        workspace_root=tmp_path,
        config=_config(max_retries=5),
        client_factory=lambda _root: _AlwaysOk(),
        workspace_slug="test-ws",
        sleep_fn=lambda _s: None,
    )
    assert counters.get("corrupt", 0) == 1
    assert not bad.exists()
    dl = mwq.deadletter_path(tmp_path)
    assert dl.exists()


def test_AC_J_4_workspace_yaml_overrides_default_config(tmp_path: Path) -> None:
    """``<workspace>/.pos/memory-worker.yaml`` overrides defaults."""
    cfg_path = tmp_path / "workspace" / ".pos" / "memory-worker.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        "max_retries: 7\nbackoff_initial_s: 1.5\nbackoff_max_s: 30.0\n",
        encoding="utf-8",
    )
    cfg = mwq.load_worker_config(tmp_path)
    assert cfg["max_retries"] == 7
    assert cfg["backoff_initial_s"] == 1.5
    assert cfg["backoff_max_s"] == 30.0
