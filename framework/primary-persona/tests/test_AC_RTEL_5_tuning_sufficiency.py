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

"""AC.RTEL.5 — tuning-sufficiency. Each candidate record carries the raw
discovery ``score``; an episode candidate additionally carries a non-null
``event_time``. An offline reader can therefore recompute BOTH a
relevance-threshold cut (per-candidate score + injected flag) AND a
recency re-order (event_time) from the log alone — the two knobs the
coming ranker cycle tunes.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus
from _helpers_retrieval_telemetry import read_records, seed_episode


def test_AC_RTEL_5_scores_present_and_episode_event_time(
    tmp_path: Path,
) -> None:
    corpus_dir = tmp_path / "memory"
    write_corpus(corpus_dir)
    episode_dir = tmp_path / "episodes"
    seed_episode(
        episode_dir,
        group_id="pos3",
        name="canon1",
        body=(
            "We confirmed the litrpg canon store is the source of truth "
            "for the production pipeline chapter checks."
        ),
    )
    telemetry_dir = tmp_path / "tel"

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        telemetry_dir=telemetry_dir,
    )
    block = retrieve(prompt="continue the batch", config=cfg)
    assert block, "fixture produced no injection; the test would be vacuous"

    cands = read_records(telemetry_dir)[0]["candidates"]

    # Every candidate carries a numeric discovery score.
    for c in cands:
        assert isinstance(c["score"], (int, float)), (
            f"candidate has no numeric discovery score: {c!r}"
        )

    episodes = [c for c in cands if c["source"] == "episode"]
    corpus = [c for c in cands if c["source"] == "corpus"]
    assert episodes, "expected at least one episode candidate in the pool"
    assert corpus, "expected at least one corpus candidate in the pool"

    # The episode candidate carries its EVENT time (recency-tuning input).
    assert episodes[0]["event_time"], (
        f"episode candidate missing event_time: {episodes[0]!r}"
    )
