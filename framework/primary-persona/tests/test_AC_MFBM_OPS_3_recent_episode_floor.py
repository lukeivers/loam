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

"""AC.MFBM-OPS.3 — Recent-episode floor.

Plan ref: ``docs/rebuild/plans/m-fbm-operational-health.md`` §4
AC.MFBM-OPS.3.

Diagnosis trigger (2026-05-04): the worker reported `worker-ok` for
each drained item but no episode files reached disk for ~3 days.
The existing ``AC.MFBM.1`` tests cover ``FileMemoryStore.write_episode``
in isolation; none of them assert that the **end-to-end queue-drain
path** produces an episode file with a current mtime.

This test pins that floor: enqueue ONE turn, ``drain_once`` once
with the file-backed client, assert the episode dir contains a
file whose mtime is at-or-after the pre-enqueue moment.

Per ODD §2.5 every assertion below maps to AC.MFBM-OPS.3.
"""

from __future__ import annotations

import time
from pathlib import Path

from loam.primary_persona import memory_write_queue as mwq
from loam.primary_persona import memory_write_worker as mww
from loam.primary_persona.file_memory import (
    build_file_backed_memory_client,
    memory_dir_for_workspace,
)


def _config_no_sleep() -> dict[str, object]:
    return {
        "max_retries": 5,
        "backoff_initial_s": 0.0,
        "backoff_max_s": 0.0,
        "poll_interval_s": 0.0,
        "tmp_cleanup_age_s": 3600.0,
        "heartbeat_interval_iterations": 60,
    }


def test_AC_MFBM_OPS_3_single_drain_writes_episode_file_with_current_mtime(
    tmp_path: Path,
) -> None:
    """Enqueue → drain → episode file exists with mtime ≥ t_before."""
    t_before = time.time()
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="sess-floor:abc123",
        session_id="sess-floor",
        user_message="hello",
        assistant_reply="world",
    )

    counters = mww.drain_once(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=build_file_backed_memory_client,
        workspace_slug="ops3-ws",
        sleep_fn=lambda _s: None,
    )
    assert counters["ok"] == 1, counters

    # The file-backed substrate writes episodes under
    # ``<workspace>/workspace/.loam/memory/episodes/<group>/<date>/<stem>.md``
    # per AC.MFBM.1 path-shape. We don't pin the date partition here
    # (that's AC.MFBM.1's job); we assert the floor — at least one
    # markdown file exists in the episode tree with mtime ≥ t_before.
    memory_dir = memory_dir_for_workspace(tmp_path)
    episode_files = list((memory_dir / "episodes").rglob("*.md"))
    assert episode_files, (
        f"no episode files written under {memory_dir}/episodes/"
    )
    most_recent_mtime = max(p.stat().st_mtime for p in episode_files)
    # Allow a 1s slack on either side for filesystem clock skew.
    assert most_recent_mtime >= t_before - 1.0, (
        f"episode mtime {most_recent_mtime} predates enqueue moment "
        f"{t_before}"
    )


def test_AC_MFBM_OPS_3_episode_file_carries_turn_body(
    tmp_path: Path,
) -> None:
    """The drained episode body carries the user-message + reply
    bundle so downstream retrieval has substantive content (not just
    a placeholder). Catches: a worker that 'succeeds' but writes an
    empty/sentinel episode."""
    user_text = "what does the M-FBM substrate do?"
    reply_text = "It is the file-based memory floor at v0.1.0."
    mwq.enqueue(
        workspace_root=tmp_path,
        turn_id="sess-floor:body-check",
        session_id="sess-floor",
        user_message=user_text,
        assistant_reply=reply_text,
    )
    mww.drain_once(
        workspace_root=tmp_path,
        config=_config_no_sleep(),
        client_factory=build_file_backed_memory_client,
        workspace_slug="ops3-ws",
        sleep_fn=lambda _s: None,
    )

    memory_dir = memory_dir_for_workspace(tmp_path)
    episode_files = list((memory_dir / "episodes").rglob("*.md"))
    assert episode_files
    contents = episode_files[0].read_text(encoding="utf-8")
    assert user_text in contents, (
        f"user_message missing from episode body: {contents!r}"
    )
    assert reply_text in contents, (
        f"assistant_reply missing from episode body: {contents!r}"
    )
