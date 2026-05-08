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

"""AC.MFBM-OPS.1 — Queue empties under N-entry sustained load.

Plan ref: ``docs/plans/m-fbm-operational-health.md`` §4
AC.MFBM-OPS.1.

Diagnosis trigger (2026-05-04): the worker died on 2026-05-01 and
175 turn-records accumulated in
``<workspace>/.pos/memory-write-queue/`` over three days. The
existing ``AC.J.5`` tests cover single-pass drain semantics + clean
restart; none of them assert that an N-entry burst empties the
queue in one drain pass.

This test pins that invariant: enqueue N=10 synthetic turns,
``drain_once`` once with the file-backed memory client, assert
counters report all OK and the queue dir is empty post-drain.

Per ODD §2.5 every assertion below maps to AC.MFBM-OPS.1.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.file_memory import build_file_backed_memory_client


def _config_no_sleep() -> dict[str, object]:
    return {
        "max_retries": 5,
        "backoff_initial_s": 0.0,
        "backoff_max_s": 0.0,
        "poll_interval_s": 0.0,
        "tmp_cleanup_age_s": 3600.0,
        "heartbeat_interval_iterations": 60,
    }


def test_AC_MFBM_OPS_1_n10_burst_empties_queue_in_one_drain_pass(
    tmp_path: Path,
) -> None:
    """Enqueue 10 turns, run ``drain_once`` once with the file-backed
    client, assert all 10 drained and the queue dir is empty."""
    n_entries = 10
    for i in range(n_entries):
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id=f"sess-load:{i:012x}",
            session_id="sess-load",
            user_message=f"prompt-{i}",
            assistant_reply=f"reply-{i}",
        )

    counters = mww.drain_once(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=build_file_backed_memory_client,
        workspace_slug="ops1-ws",
        sleep_fn=lambda _s: None,
    )

    assert counters == {
        "ok": n_entries,
        "retry": 0,
        "deadletter": 0,
        "skipped-no-client": 0,
        "corrupt": 0,
    }, counters
    # Queue dir is empty after the drain pass.
    remaining = mwq.list_queue_entries_oldest_first(tmp_path)
    assert remaining == [], f"queue not empty post-drain: {remaining}"


def test_AC_MFBM_OPS_1_drain_processes_oldest_first(tmp_path: Path) -> None:
    """Diagnostic: confirm FIFO ordering — without it, an N-entry
    burst could starve older entries indefinitely under back-pressure
    even when this AC's assertion passes. The existing AC.J family
    asserts FIFO indirectly; this AC pins it explicitly under the
    operational-health surface."""
    enqueued_turn_ids: list[str] = []
    for i in range(5):
        turn_id = f"sess-fifo:{i:012x}"
        enqueued_turn_ids.append(turn_id)
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id=turn_id,
            session_id="sess-fifo",
            user_message=f"q{i}",
            assistant_reply=f"r{i}",
        )

    # Snapshot the list of oldest-first entry filenames before drain.
    pre_drain = mwq.list_queue_entries_oldest_first(tmp_path)
    assert len(pre_drain) == 5
    # The filenames carry the turn-id substring; verify the order
    # matches enqueue order (oldest mtime first → enqueue order).
    for path, turn_id in zip(pre_drain, enqueued_turn_ids, strict=True):
        assert turn_id.split(":")[-1] in path.name

    counters = mww.drain_once(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=build_file_backed_memory_client,
        workspace_slug="ops1-ws",
        sleep_fn=lambda _s: None,
    )
    assert counters["ok"] == 5
    assert mwq.list_queue_entries_oldest_first(tmp_path) == []
