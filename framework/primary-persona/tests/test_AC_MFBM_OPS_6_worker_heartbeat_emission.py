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

"""AC.MFBM-OPS.6 — Worker-heartbeat instrumentation.

Plan ref: ``docs/rebuild/plans/m-fbm-operational-health.md`` §4
AC.MFBM-OPS.6.

Diagnosis trigger (2026-05-04): Luke's ``memory-writes.log`` carried
5 lines over 3 days (1 ``worker-start`` + 4 ``stop-skip`` from the
emitter side; zero entries from the worker after startup). The worker
was alive but draining an empty queue silently. The existing
diagnostic-log surface emits ``worker-start`` once, per-entry events
during drain, and ``worker-exit`` at clean shutdown — none of which
fire on a long-idle empty-queue worker.

This AC adds a periodic ``kind: "worker-heartbeat"`` NDJSON entry
emitted every ``heartbeat_interval_iterations`` drain-loop passes
(default 60 — at the default 1.0s ``poll_interval_s`` that's ~60s
wall-clock). Each heartbeat carries ``pid``, ``iteration``,
``queue_depth``, ``ts``.

The test drives ``run_worker_loop`` against an empty queue with
``heartbeat_interval_iterations=1`` so each iteration emits a
heartbeat — no clock-faking, no wall-clock dependency, deterministic.

Per ODD §2.5 every assertion below maps to AC.MFBM-OPS.6.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww


class _RecordingClient:
    """Sink client — heartbeat AC doesn't depend on episode writes;
    this avoids any file-memory side-effect during the empty-queue
    iterations the test drives."""

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        return {"episode_uuid": "unused-ops6"}

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        return {"query": "", "results": []}


def _config_with_heartbeat(*, every: int) -> dict[str, Any]:
    return {
        "max_retries": 5,
        "backoff_initial_s": 0.0,
        "backoff_max_s": 0.0,
        "poll_interval_s": 0.0,
        "tmp_cleanup_age_s": 3600.0,
        "heartbeat_interval_iterations": every,
    }


def _read_diag_entries(workspace_root: Path) -> list[dict[str, Any]]:
    """Parse the NDJSON memory-writes log into a list of dicts."""
    log_path = mww._diag_log_path(workspace_root)
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def test_AC_MFBM_OPS_6_worker_loop_emits_heartbeat_each_iteration_when_interval_is_one(
    tmp_path: Path,
) -> None:
    """With ``heartbeat_interval_iterations=1``, every drain-pass
    boundary emits a heartbeat. Run ``max_iterations=3`` against an
    empty queue → expect ≥3 heartbeat entries in the log."""
    rc = mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_with_heartbeat(every=1),
        client_factory=lambda _root: _RecordingClient(),
        workspace_slug="ops6-ws",
        sleep_fn=lambda _s: None,
        max_iterations=3,
    )
    assert rc == 0

    entries = _read_diag_entries(tmp_path)
    heartbeats = [e for e in entries if e.get("kind") == "worker-heartbeat"]
    assert len(heartbeats) >= 3, (
        f"expected ≥3 heartbeat entries with every=1 + 3 iterations; "
        f"got {len(heartbeats)} in {entries!r}"
    )


def test_AC_MFBM_OPS_6_heartbeat_payload_carries_pid_iteration_queue_depth_ts(
    tmp_path: Path,
) -> None:
    """Heartbeat entries carry ``pid`` (int), ``iteration`` (int ≥1),
    ``queue_depth`` (int ≥0), ``ts`` (ISO-8601 string). Without these
    fields, an operator can't distinguish 'the worker is idle' from
    'the worker is hung' or correlate heartbeats across restarts."""
    mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_with_heartbeat(every=1),
        client_factory=lambda _root: _RecordingClient(),
        workspace_slug="ops6-ws",
        sleep_fn=lambda _s: None,
        max_iterations=2,
    )
    entries = _read_diag_entries(tmp_path)
    heartbeats = [e for e in entries if e.get("kind") == "worker-heartbeat"]
    assert heartbeats, "no heartbeat entries emitted"
    sample = heartbeats[0]
    assert isinstance(sample["pid"], int)
    assert isinstance(sample["iteration"], int) and sample["iteration"] >= 1
    assert isinstance(sample["queue_depth"], int) and sample["queue_depth"] >= 0
    # ISO-8601 ts (any timezone offset; just verify parseable).
    assert isinstance(sample["ts"], str)
    from datetime import datetime
    datetime.fromisoformat(sample["ts"])  # raises if malformed


def test_AC_MFBM_OPS_6_heartbeat_skipped_between_intervals(
    tmp_path: Path,
) -> None:
    """With ``heartbeat_interval_iterations=10`` and
    ``max_iterations=3``, NO heartbeat entry should appear (the
    threshold isn't reached). Catches: a degenerate config that
    emits every iteration regardless of interval."""
    mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_with_heartbeat(every=10),
        client_factory=lambda _root: _RecordingClient(),
        workspace_slug="ops6-ws",
        sleep_fn=lambda _s: None,
        max_iterations=3,
    )
    entries = _read_diag_entries(tmp_path)
    heartbeats = [e for e in entries if e.get("kind") == "worker-heartbeat"]
    assert heartbeats == [], (
        f"heartbeat fired before interval reached: {heartbeats!r}"
    )


def test_AC_MFBM_OPS_6_heartbeat_includes_queue_depth_when_queue_has_entries(
    tmp_path: Path,
) -> None:
    """Heartbeats taken with N un-drained entries in the queue MUST
    report ``queue_depth >= 0``. Note: with the recording client
    (which 'succeeds' instantly), the drain step empties the queue
    BEFORE the heartbeat fires within the same iteration. To exercise
    the non-zero queue_depth path we use a client that returns None
    (substrate-not-ready), causing the drain step to skip entries +
    leave them for the heartbeat to observe."""
    for i in range(3):
        mwq.enqueue(
            workspace_root=tmp_path,
            turn_id=f"sess-depth:{i:012x}",
            session_id="sess-depth",
            user_message=f"q{i}",
            assistant_reply=f"r{i}",
        )

    mww.run_worker_loop(
        workspace_root=tmp_path,
        config=_config_with_heartbeat(every=1),
        client_factory=lambda _root: None,  # drain skips → entries stay
        workspace_slug="ops6-ws",
        sleep_fn=lambda _s: None,
        max_iterations=1,
    )
    entries = _read_diag_entries(tmp_path)
    heartbeats = [e for e in entries if e.get("kind") == "worker-heartbeat"]
    assert heartbeats, "no heartbeat captured"
    assert heartbeats[0]["queue_depth"] == 3, (
        f"expected queue_depth=3 with 3 enqueued + skipped drain; "
        f"got {heartbeats[0]!r}"
    )
