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

"""AC.RTEL.7 (OUTCOME-ALTITUDE) — the production ``retrieve()`` entry-
point over a real corpus + episode store + telemetry sink, from an empty
starting state (no pre-arranged ranking state, no injected index).

A genuine retrieval writes ONE well-formed record whose injected=true
candidates match the returned block's records (their source paths appear
in the block), AND the returned block equals the block produced with
telemetry off. This exercises the full pipeline —
retrieve -> rank -> _merge_by_score -> _render_injection + the real
record_retrieval side-effect — with nothing mocked.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus
from _helpers_retrieval_telemetry import read_records, seed_episode


def _cfg(
    tmp_path: Path, corpus_dir: Path, episode_dir: Path, telemetry_dir
) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        telemetry_dir=telemetry_dir,
    )


def test_AC_RTEL_7_OA_record_matches_live_block(tmp_path: Path) -> None:
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

    # Telemetry-off reference block.
    off = retrieve(
        prompt="continue the batch",
        config=_cfg(tmp_path, corpus_dir, episode_dir, telemetry_dir=None),
    )

    # Production path with a live telemetry sink, cold start.
    telemetry_dir = tmp_path / "tel"
    block = retrieve(
        prompt="continue the batch",
        config=_cfg(tmp_path, corpus_dir, episode_dir, telemetry_dir=telemetry_dir),
    )

    assert block, "production retrieve produced no injection"
    assert block == off, "telemetry changed the production block (pure-observation)"

    records = read_records(telemetry_dir)
    assert len(records) == 1
    rec = records[0]

    injected = [c for c in rec["candidates"] if c["injected"]]
    assert injected, "no injected candidate recorded for a non-empty block"

    # Every injected candidate's source path is present in the surfaced
    # block — the log's injected set reflects what the turn actually saw.
    for c in injected:
        assert c["path"], f"injected candidate has no path: {c!r}"
        assert c["path"] in block, (
            f"injected candidate {c['path']!r} is not in the surfaced block"
        )

    # Injected ranks are a contiguous 0..k-1 ordering.
    ranks = sorted(c["rank"] for c in injected)
    assert ranks == list(range(len(injected))), f"non-contiguous ranks: {ranks}"
