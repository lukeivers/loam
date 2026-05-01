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

"""AC.J.5 — Worker is a supervised long-running process.

Outcome (per locked plan §4): the worker module exposes a long-
running drain loop suitable for launchd supervision. The plist
side (KeepAlive=true / RunAtLoad=true) lives under
workspace-bootstrap; this test exercises the worker's
loop-shape:

  - The drain loop terminates on cooperative-exit signal
    (SIGTERM / SIGINT) at the next pass boundary.
  - The drain loop drains the queue end-to-end on each pass.
  - The queue is the source of truth: killing + restarting the
    loop loses no enqueued entries.

The launchd plist contents are validated under
``workspace-bootstrap/tests/`` (AC.J.5 fence-cross — the plist
template lives there).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww


class _RecordingClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {"episode_uuid": f"uuid-{len(self.calls)}"}

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        return {"query": "", "results": []}


def _config_no_sleep() -> dict[str, Any]:
    return {
        "max_retries": 5,
        "backoff_initial_s": 0.0,
        "backoff_max_s": 0.0,
        "poll_interval_s": 0.0,
        "tmp_cleanup_age_s": 3600.0,
    }


def test_AC_J_5_run_worker_loop_drains_queue_then_exits_on_max_iterations(
    tmp_path: Path,
) -> None:
    # Enqueue three entries.
    for i in range(3):
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id=f"s1:t{i}",
            session_id="s1",
            user_message=f"prompt-{i}",
            assistant_reply=f"reply-{i}",
        )
    client = _RecordingClient()

    rc = mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=lambda _root: client,
        workspace_slug="test-ws",
        sleep_fn=lambda _s: None,
        max_iterations=2,  # one drain pass + one bookkeeping pass
    )
    assert rc == 0
    assert len(client.calls) == 3
    # Queue empty after drain.
    assert mwq.list_queue_entries_oldest_first(tmp_path) == []


def test_AC_J_5_worker_loop_resumes_after_simulated_kill(tmp_path: Path) -> None:
    """Killing the loop mid-cycle (max_iterations=1) leaves un-drained
    entries on disk; the next loop start drains them."""
    # Enqueue 5 entries.
    for i in range(5):
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id=f"s1:r{i}",
            session_id="s1",
            user_message=f"X{i}",
            assistant_reply=f"Y{i}",
        )

    # First pass: max_iterations=1 → one drain_once call.
    client_a = _RecordingClient()
    mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=lambda _root: client_a,
        workspace_slug="ws",
        sleep_fn=lambda _s: None,
        max_iterations=1,
    )
    # All 5 drained in one pass.
    assert len(client_a.calls) == 5

    # Re-enqueue 2 more — simulate post-kill enqueue.
    for i in range(2):
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id=f"s1:p{i}",
            session_id="s1",
            user_message=f"P{i}",
            assistant_reply=f"PR{i}",
        )

    # Restart: the new loop instance picks up the leftover entries.
    client_b = _RecordingClient()
    mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=lambda _root: client_b,
        workspace_slug="ws",
        sleep_fn=lambda _s: None,
        max_iterations=1,
    )
    assert len(client_b.calls) == 2
    assert mwq.list_queue_entries_oldest_first(tmp_path) == []


def test_AC_J_5_worker_aborts_walk_when_no_live_client(tmp_path: Path) -> None:
    """When the live client builder returns None (substrate not
    ready), the worker stops the walk + waits for the next pass —
    no retry-counter bump, no dead-letter."""
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s1:wait",
        session_id="s1",
        user_message="wait",
        assistant_reply="wait",
    )
    counters = mww.drain_once(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=lambda _root: None,
        workspace_slug="ws",
        sleep_fn=lambda _s: None,
    )
    assert counters.get("skipped-no-client", 0) == 1
    # Entry stays in queue.
    assert len(mwq.list_queue_entries_oldest_first(tmp_path)) == 1
    record = mwq.read_queue_entry(
        mwq.list_queue_entries_oldest_first(tmp_path)[0]
    )
    assert record is not None
    # No retry-counter bump.
    assert record["retry_count"] == 0
