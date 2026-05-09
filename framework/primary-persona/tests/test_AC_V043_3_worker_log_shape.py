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

"""AC.V043.3 — worker-ok diag emission carries `path`, not
`episode_uuid`.

Plan ref: ``docs/plans/v0-4-3-patch-memory-retrieval-bm25-fix.md`` §4
AC.V043.3.

Verifies:
  (a) the `worker-ok` line in `memory-writes.log` has
      `"path": "/tmp/x"` populated from the substrate's return dict;
  (b) the line has NO `"episode_uuid"` key (the file-based store
      does not produce one; the pre-V043 line carried `null`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww


class _StubFileBasedStore:
    """Mirrors the file-based store's add_episode return shape:
    {"path", "name", "group_id"} — NO episode_uuid field."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "path": "/tmp/x",
            "name": kwargs.get("name", "turn/test"),
            "group_id": kwargs.get("group_id", "g"),
        }

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        return {"query": "", "results": []}


def test_AC_V043_3_worker_ok_carries_path_not_episode_uuid(
    tmp_path: Path,
) -> None:
    """Drive one queue entry through the worker against a file-based-
    store stub; read back memory-writes.log; the `worker-ok` line has
    `path` and NOT `episode_uuid`.
    """
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="s-v043:000000000001",
        session_id="s-v043",
        user_message="ac-v043-3 worker log shape",
        assistant_reply="check the diag",
    )
    store = _StubFileBasedStore()
    mww.drain_once(
        workspace_root=tmp_path,
        config={
            "max_retries": 5,
            "backoff_initial_s": 0.0,
            "backoff_max_s": 0.0,
            "poll_interval_s": 0.0,
            "tmp_cleanup_age_s": 3600.0,
        },
        client_factory=lambda _root: store,
        workspace_slug="ws-v043",
        sleep_fn=lambda _s: None,
    )
    assert len(store.calls) == 1, "worker must call add_episode exactly once"

    diag_path = tmp_path / "workspace" / ".pos" / "memory-writes.log"
    assert diag_path.exists()
    lines = [
        json.loads(ln)
        for ln in diag_path.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    worker_ok_lines = [ln for ln in lines if ln.get("kind") == "worker-ok"]
    assert len(worker_ok_lines) == 1, (
        f"expected exactly one worker-ok diag line; got {len(worker_ok_lines)}"
    )

    entry = worker_ok_lines[0]
    # (a) `path` populated from the stub return value.
    assert entry.get("path") == "/tmp/x", (
        f"AC.V043.3 (a) — expected path='/tmp/x'; got {entry.get('path')!r}"
    )
    # (b) no `episode_uuid` key at all.
    assert "episode_uuid" not in entry, (
        f"AC.V043.3 (b) — episode_uuid must be absent; got "
        f"keys={sorted(entry.keys())!r}"
    )
