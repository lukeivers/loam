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

"""AC.RVL.2 — the episode discovered set is determined by the relevance
floor, not a fetch-side count bound.

Pre-reshape ``_episode_hits`` fetched ``num_results = config.top_n`` (= 5),
so the FETCH COUNT bounded the episode set before the merge floor ran. Now
the fetch requests the generous ``EPISODE_CANDIDATE_WINDOW`` and the merge's
relevance floor + threshold determine the set. With MORE than the legacy 5
episodes clearing the floor, all of them reach the merge.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, rank

_GROUP = "ws"
_N = 10  # > the legacy fetch count of 5


def _seed(store: FileMemoryStore, name: str, body: str) -> None:
    store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id=_GROUP,
    )


def _populated_store(tmp_path: Path, n: int) -> Path:
    episode_dir = tmp_path / "episodes"
    store = FileMemoryStore(memory_dir=episode_dir)
    # Each episode carries its OWN rare token so every one is a strong (df=1)
    # match that clears the floor — a shared token would collapse IDF.
    for i in range(n):
        _seed(store, f"rel-{i}", f"the widgetronic{i} migration project shipped")
    return episode_dir


def _config(tmp_path: Path, episode_dir: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=tmp_path / "empty-corpus",
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        episode_memory_dir=episode_dir,
        episode_group_ids=(_GROUP,),
    )


def test_AC_RVL_2_more_than_legacy_episodes_reach_the_merge(tmp_path: Path) -> None:
    episode_dir = _populated_store(tmp_path, _N)
    prompt = "widgetronic " + " ".join(f"widgetronic{i}" for i in range(_N))
    merged = rank(
        prompt=prompt,
        config=_config(tmp_path, episode_dir),
        relevance_threshold=0.0,  # isolate the FETCH de-count, not the threshold
    )
    # No corpus configured, so every merged hit is an episode. More than the
    # legacy fetch count of 5 reach the merge — the fetch no longer bounds at 5.
    assert len(merged) == _N, (
        f"all {_N} floor-clearing episodes must reach the merge; got "
        f"{len(merged)} — a fetch-side count is still bounding the set"
    )
    assert len(merged) > 5, "the episode set exceeds the legacy fetch count of 5"
