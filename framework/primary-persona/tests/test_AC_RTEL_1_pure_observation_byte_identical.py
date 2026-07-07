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

"""AC.RTEL.1 — PURE OBSERVATION. ``retrieve()`` returns a byte-identical
injection block whether or not a telemetry sink is configured, on the
same corpus + episode fixture.

This is the load-bearing constraint of the standing-telemetry cycle: the
telemetry records what the ranker ALREADY did; it must never change
recall results or ordering. A difference here means the recorder is
perturbing recall — the one thing it must never do.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus
from _helpers_retrieval_telemetry import seed_episode


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


def test_AC_RTEL_1_block_identical_with_and_without_telemetry(
    tmp_path: Path,
) -> None:
    """Telemetry ON vs OFF over the same fixture => identical block."""
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

    off = retrieve(
        prompt="continue the batch",
        config=_cfg(tmp_path, corpus_dir, episode_dir, telemetry_dir=None),
    )
    on = retrieve(
        prompt="continue the batch",
        config=_cfg(
            tmp_path, corpus_dir, episode_dir, telemetry_dir=tmp_path / "tel"
        ),
    )

    assert off == on, (
        "telemetry perturbed the recall block — the pure-observation "
        f"guarantee is broken.\n off={off!r}\n on={on!r}"
    )
    # Sanity: the fixture actually produced a non-trivial block (so the
    # equality is not the trivial empty-string case).
    assert on, "fixture produced no injection; the test would be vacuous"
