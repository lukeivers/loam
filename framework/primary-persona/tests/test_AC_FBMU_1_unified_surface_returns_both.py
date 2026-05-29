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

"""AC.FBMU.1 — a single retrieval call returns BOTH an episode-store hit
AND a corpus hit for a query that matches content in both corpora.

D2 unify (merge-at-retrieval): the KP1 UserPromptSubmit contributor is
extended to query ``FileMemoryStore.search`` and merge episode hits into
the corpus result set by score, under the existing top-N + byte budget.
The two physical indexes stay separate; the merge happens at the
retrieval call.

This test seeds ONE episode + ONE corpus doc matching the same query
term, points the production ``retrieve`` entry-point at both, and
asserts both surface in the merged injection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def _seed_episode(memory_dir: Path, *, group_id: str, name: str, body: str) -> None:
    store = FileMemoryStore(memory_dir=memory_dir)
    store.write_episode(
        name=f"turn/{name}",
        body=body,
        source_description="test seed",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id=group_id,
    )


def test_AC_FBMU_1_both_corpus_and_episode_surface(tmp_path: Path) -> None:
    """A query that matches BOTH corpora returns BOTH a corpus hit and
    an episode hit in one merged call.

    The work-anchor injects the active (seed) objective tokens, so both
    the corpus doc and the episode must lie on the litrpg-canon
    objective path (mirrors the proven AC.KP1.6 mechanism). The corpus
    surfaces the canon feedback doc; the episode surfaces a prior turn
    on the same canon topic.
    """
    # The markdown corpus (write_corpus seeds a litrpg-canon doc that
    # the active fiction objective anchor surfaces — AC.KP1.6 path).
    corpus_dir = tmp_path / "memory"
    write_corpus(corpus_dir)

    # One episode on the SAME litrpg-canon topic the objective anchors.
    episode_dir = tmp_path / "episodes-store"
    _seed_episode(
        episode_dir,
        group_id="pos3",
        name="abc123",
        body=(
            "We confirmed the litrpg canon store is the source of truth "
            "for the production pipeline chapter checks."
        ),
    )

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
    )

    block = retrieve(prompt="continue the batch", config=cfg)

    assert block, "the unified surface produced no injection"
    # Corpus hit present (the litrpg-canon feedback doc title).
    assert "canon" in block.lower() or "litrpg" in block.lower(), (
        f"corpus hit missing from merged surface; got: {block!r}"
    )
    # Episode hit present (rendered via the episode pointer prefix).
    assert "from an earlier turn" in block.lower(), (
        f"episode hit missing from merged surface; got: {block!r}"
    )
