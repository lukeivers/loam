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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.RDP.6 (OUTCOME-ALTITUDE) — production ``retrieve()``, no pre-arranged
ranking state.

Memory redesign S2 (design Stage 3). Drives the real resolver + the
production ``retrieve()`` entry-point from an empty starting state (a
freshly-written episode store; no seeded ranking). On a query with two
genuinely-relevant records of different event-age plus one below-threshold
near-miss, the surfaced block carries BOTH relevant records newest-first
and EXCLUDES the near-miss; a query whose only matches are below-threshold
near-misses surfaces an EMPTY block.

This is the whole-pipeline proof: work-anchor → episode search → merge
(relevance threshold + event-recency prioritizer + count cap) → render.
The relevance threshold is passed as a per-call lever (mirrors the sealed
AC-FBM-SAL-4 ``salience_threshold`` per-call pattern), sized between the
fixture's genuine-match and near-miss bands.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

_GROUP = "ws"
# Between the near-miss band (~0.6, a single weak-token match) and the
# genuine multi-term band (~3-5) verified against the live store.
_THRESHOLD = 1.5


def _seed(store: FileMemoryStore, name: str, body: str, *, days_ago: float) -> None:
    store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc) - timedelta(days=days_ago),
        source="message",
        group_id=_GROUP,
    )


def _config(tmp_path: Path, episode_dir: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=tmp_path / "empty-corpus",
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=(_GROUP,),
    )


def _populated_store(tmp_path: Path) -> Path:
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    # Two genuinely-relevant records of different event-age.
    _seed(
        store,
        "complete-new",
        "the kilnbench migration project is complete and shipped to production",
        days_ago=2,
    )
    _seed(
        store,
        "incomplete-old",
        "the kilnbench migration project is incomplete pending final review",
        days_ago=35,
    )
    # A below-threshold near-miss (weak single-token overlap on "project").
    _seed(
        store,
        "near-miss",
        "unrelated standup notes mention the project cadence and scheduling",
        days_ago=5,
    )
    # Filler episodes to populate the FTS index (meaningful IDF regime).
    for i in range(6):
        _seed(
            store,
            f"filler-{i}",
            f"totally unrelated chatter topic {i} weather sports music travel food",
            days_ago=i + 1,
        )
    return episode_dir


def test_AC_RDP_6_OA_relevant_newest_first_near_miss_excluded(tmp_path: Path) -> None:
    """Production retrieve: both genuinely-relevant records surface,
    newest-by-event-time first, and the below-threshold near-miss is
    excluded."""
    episode_dir = _populated_store(tmp_path)
    block = retrieve(
        prompt="kilnbench migration project complete status",
        config=_config(tmp_path, episode_dir),
        relevance_threshold=_THRESHOLD,
    ).lower()

    assert block, "the production surface produced no injection for a relevant query"
    # Both genuine records present.
    assert "shipped to production" in block, f"the 'complete' record is missing; got: {block!r}"
    assert "pending final review" in block, f"the 'incomplete' record is missing; got: {block!r}"
    # Newest-by-event-time first (complete-new before incomplete-old).
    assert block.index("shipped to production") < block.index("pending final review"), (
        f"the newer 'complete' record must be prioritized ahead of the older "
        f"'incomplete' record; got: {block!r}"
    )
    # The below-threshold near-miss is excluded.
    assert "standup notes" not in block and "cadence" not in block, (
        f"the below-threshold near-miss must be excluded; got: {block!r}"
    )


def test_AC_RDP_6_OA_only_near_misses_surfaces_empty(tmp_path: Path) -> None:
    """Production retrieve: a query whose only matches are below-threshold
    (weak single-token) surfaces an EMPTY block — not a forced top-1."""
    episode_dir = _populated_store(tmp_path)
    # "kilnbench" alone is a single weak-token match on the two genuine
    # records (~0.6, below the 1.5 threshold) and matches nothing else
    # strongly → every match is a below-threshold near-miss → empty.
    block = retrieve(
        prompt="kilnbench",
        config=_config(tmp_path, episode_dir),
        relevance_threshold=_THRESHOLD,
    )
    assert block == "", (
        "a query whose only matches are below-threshold must surface an EMPTY "
        f"block, not a forced top-1; got: {block!r}"
    )
