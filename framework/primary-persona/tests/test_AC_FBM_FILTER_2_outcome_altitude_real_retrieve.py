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

"""AC-FBM-FILTER-2 (Slice B / B4) — OUTCOME-ALTITUDE.

Drive the PRODUCTION ``retrieve()`` over a REAL ``FileMemoryStore`` with NO
pre-arranged retrieval state. The store is seeded (through the production
``write_episode`` ingest) with:

  (a) a below-floor weak episode (matches only a low-IDF common query token),
  (b) a near-duplicate PAIR of episodes (near-identical openings),
  (c) a genuinely-relevant distinct episode.

The single ``retrieve()`` call's injected block must: EXCLUDE the below-floor
episode, contain only ONE member of the near-dup pair, and STILL contain the
genuinely-relevant distinct episode. Exercised end-to-end through
``retrieve -> _episode_hits -> store.search -> _merge_by_score ->
_render_injection`` with no internal-call shortcut.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


# A distinctive high-IDF anchor token that the relevant episodes carry.
SHARED = "quizzlefarn"
# A low-IDF common token: present in many filler episodes AND the query, so the
# weak episode that matches ONLY this token scores below the absolute floor
# (populated-index regime — verified Tier-0 the weak episode scores 0.0 < 0.1
# while the relevant ones score 5–11).
COMMON = "today"


def _write(store: FileMemoryStore, *, name: str, user: str, now: datetime) -> None:
    store.write_episode(
        name=f"turn/{name}",
        body=f"[user]\n{user}\n\n[assistant]\nacknowledged and recorded.\n",
        source_description="test seed",
        reference_time=now,
        source="message",
        group_id="pos3",
    )


def test_AC_FBM_FILTER_2_floor_and_dedup_in_one_real_retrieve(tmp_path: Path) -> None:
    episode_dir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=episode_dir)
    now = datetime.now(timezone.utc)

    # Populate the IDF space so the index is NOT sparse — every filler carries the
    # COMMON token (driving its IDF toward zero) with otherwise-distinct vocab.
    for i in range(30):
        _write(
            store,
            name=f"filler{i}",
            user=f"word{i}a word{i}b word{i}c {COMMON} routine note",
            now=now,
        )

    # (c) the genuinely-relevant distinct episode.
    relevant_marker = "decide what surfaces in retrieval"
    _write(
        store,
        name="relevant",
        user=(
            f"How does the {SHARED} relevance floor and dedup "
            f"{relevant_marker}?"
        ),
        now=now,
    )

    # (b) the near-duplicate pair — near-identical openings (>0.85 Jaccard).
    nd_base = (
        f"the {SHARED} canon store is the source of truth for the chapter "
        "continuity checks"
    )
    _write(store, name="nd-a", user=f"{nd_base} exactly", now=now)
    _write(store, name="nd-b", user=f"{nd_base} precisely", now=now)

    # (a) the below-floor weak episode — matches ONLY the low-IDF COMMON token.
    weak_marker = "totally unrelated chatter"
    _write(store, name="weak", user=f"{weak_marker} {COMMON} here", now=now)

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=None,  # isolate the episode-side filter behaviour
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        top_n=5,
    )

    # The query carries the high-IDF anchor + the low-IDF common token, so the
    # weak episode is a (sub-floor) lexical match and would surface WITHOUT the
    # floor.
    block = retrieve(
        prompt=(
            f"remind me about the {SHARED} relevance floor and dedup and the "
            f"canon store source of truth {COMMON}"
        ),
        config=cfg,
    )

    # B1 — the below-floor weak episode is excluded.
    assert weak_marker not in block, (
        f"the below-floor weak episode must be excluded; block={block!r}"
    )

    # B2 — only ONE member of the near-dup pair occupies a slot. Both share the
    # identical opening, so the kept member renders that opening exactly once.
    canon_opening = "canon store is the source of truth"
    assert block.count(canon_opening) == 1, (
        "exactly one member of the near-dup pair must surface; "
        f"count={block.count(canon_opening)} block={block!r}"
    )

    # B4 — the genuinely-relevant distinct episode STILL surfaces (the filter
    # removes noise + duplicates, never the real memory).
    assert relevant_marker in block, (
        f"the genuinely-relevant distinct episode must still surface; "
        f"block={block!r}"
    )
