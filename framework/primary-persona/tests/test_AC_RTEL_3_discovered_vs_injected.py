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

"""AC.RTEL.3 — discovered-vs-injected distinction. When the candidate
pool exceeds the injected set (here forced by a top_n=1 cut over a
corpus hit + an episode hit), the log records the dropped candidate with
injected=false / rank=None AND the surfaced one with injected=true + an
integer rank, and the injected set matches what retrieve() surfaced.

This is the load-bearing "which memories got pulled" signal: without the
discovered-not-injected candidate in the log, the dataset cannot
distinguish a candidate that was considered-and-dropped from one that
was never a candidate.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus
from _helpers_retrieval_telemetry import read_records, seed_episode


def test_AC_RTEL_3_pool_exceeds_injected_and_matches_block(
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
        top_n=1,  # force a cut: corpus hit + episode hit, only one survives
        telemetry_dir=telemetry_dir,
    )
    block = retrieve(prompt="continue the batch", config=cfg)
    assert block, "fixture produced no injection; the test would be vacuous"

    rec = read_records(telemetry_dir)[0]
    cands = rec["candidates"]

    injected = [c for c in cands if c["injected"]]
    dropped = [c for c in cands if not c["injected"]]

    assert len(cands) > len(injected), (
        "pool did not exceed the injected set; the discovered-vs-injected "
        f"distinction is untested. candidates={cands!r}"
    )
    assert dropped, "no discovered-not-injected candidate was recorded"
    assert len(injected) == 1, (
        f"top_n=1 should surface exactly one; got {len(injected)}"
    )

    # The injected candidate carries an integer rank; the dropped one none.
    assert injected[0]["rank"] == 0
    for c in dropped:
        assert c["rank"] is None

    # counts agree with the candidate flags.
    assert rec["counts"]["n_injected"] == len(injected)
    assert rec["counts"]["n_candidates"] == len(cands)
