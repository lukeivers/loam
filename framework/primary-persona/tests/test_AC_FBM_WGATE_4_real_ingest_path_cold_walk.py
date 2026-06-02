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

"""AC-FBM-WGATE-4 (OUTCOME-ALTITUDE) — write-gate on the REAL ingest path.

Drives the production memory-write ingest chain end to end with NO pre-arranged
store state:

    enqueue() -> memory_write_worker.drain_once
      -> _process_one_entry -> FileBackedMemoryClient.add_episode
        -> FileMemoryStore.write_episode

with the DEFAULT production ``build_file_backed_memory_client`` factory (no test
double inserted at the ingest seam). One boilerplate queue entry + one
substantive queue entry are drained; post-drain the hot tier (EPISODES_SUBDIR +
FTS ``search``) holds EXACTLY the substantive turn and the cold tier
(COLD_SUBDIR) holds EXACTLY the boilerplate turn. This exercises the actual
Stop-hook turn-close write path the persona runs in production.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.file_memory import (
    COLD_SUBDIR,
    EPISODES_SUBDIR,
    FileMemoryStore,
    memory_dir_for_workspace,
)


_SLUG = "pos3"

_JUNK_USER = (
    "<task-notification>\n"
    "<task-id>wgate4-junk</task-id>\n"
    "<status>completed</status>\n"
    "<result>boilerplate_only_token agent done.</result>\n"
    "</task-notification>"
)

_REAL_USER = (
    "Move the salience gate onto the write path and seal the amendment, "
    "then report the cold-tier mechanism and the seal SHA."
)


def test_AC_FBM_WGATE_4_real_drain_splits_hot_and_cold(tmp_path: Path) -> None:
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir(parents=True, exist_ok=True)

    # No pre-arranged store state: enqueue through the production enqueue path.
    mwq.enqueue(
        workspace_root=workspace_root,
        turn_id="wgate4-junk",
        session_id="sess-1",
        user_message=_JUNK_USER,
        assistant_reply="Acknowledged.",
    )
    mwq.enqueue(
        workspace_root=workspace_root,
        turn_id="wgate4-real",
        session_id="sess-1",
        user_message=_REAL_USER,
        assistant_reply="On it.",
    )

    # Drive the REAL drain with the DEFAULT production client factory
    # (client_factory=None -> build_file_backed_memory_client). No internal
    # call shortcut; no test double at the ingest seam.
    counters = mww.drain_once(
        workspace_root=workspace_root,
        workspace_slug=_SLUG,
    )
    assert counters["ok"] == 2, f"both entries should drain ok; {counters}"

    memory_dir = memory_dir_for_workspace(workspace_root)
    store = FileMemoryStore(memory_dir=memory_dir)

    # --- HOT tier: exactly the substantive turn ---
    hot_root = memory_dir / EPISODES_SUBDIR
    hot_files = list(hot_root.rglob("*.md")) if hot_root.exists() else []
    assert len(hot_files) == 1, (
        f"hot tier must hold exactly the substantive turn; found {hot_files}"
    )
    hot_raw = hot_files[0].read_text(encoding="utf-8")
    assert "wgate4-real" in hot_raw
    assert "boilerplate_only_token" not in hot_raw

    # The substantive turn surfaces through the production search (FTS-indexed).
    surfaced = store.search(
        query="salience gate write path",
        group_ids=[_SLUG],
        num_results=5,
    )
    surfaced_names = [e.get("name", "") for e in surfaced["episodes"]]
    assert any("wgate4-real" in n for n in surfaced_names), (
        f"substantive turn must surface from the hot index; {surfaced_names!r}"
    )
    # The boilerplate token never surfaces (it is not in the hot index).
    junk_surfaced = store.search(
        query="boilerplate_only_token",
        group_ids=[_SLUG],
        num_results=5,
    )
    assert junk_surfaced["episodes"] == [], (
        f"boilerplate must not surface; got {junk_surfaced['episodes']!r}"
    )

    # --- COLD tier: exactly the boilerplate turn ---
    cold_root = memory_dir / COLD_SUBDIR
    cold_files = list(cold_root.rglob("*.md")) if cold_root.exists() else []
    assert len(cold_files) == 1, (
        f"cold tier must hold exactly the boilerplate turn; found {cold_files}"
    )
    cold_raw = cold_files[0].read_text(encoding="utf-8")
    assert "boilerplate_only_token" in cold_raw
    assert "salience: 0.0" in cold_raw  # tagged junk, on disk, never deleted
