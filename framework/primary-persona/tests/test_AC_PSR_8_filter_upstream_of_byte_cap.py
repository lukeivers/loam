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

"""AC.PSR.8 — the session filter engages UPSTREAM of the byte-budget cap
(the RVL-specific falsifier).

Outcome (plan §4 AC.PSR.8): in persona P's per-turn keep-pace block,
when the store holds other-persona episodes that BOTH out-rank P's by
BM25 AND collectively exceed the ``INJECTION_CHAR_CAP`` byte budget, the
rendered block still contains P's episodes (not a budget filled by
other-persona episodes). A post-render (or any post-byte-cap) filter
fails this: the budget fills with the higher-BM25 other-persona episodes
and P's block returns empty.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import (
    INJECTION_CHAR_CAP,
    RetrievalConfig,
    retrieve,
)

from _helpers_keep_pace import write_corpus


def _seed(root: Path) -> tuple[Path, Path]:
    corpus = root / "memory"
    write_corpus(corpus)
    ep = root / "ws-memory"
    store = FileMemoryStore(memory_dir=ep)
    now = datetime.now(timezone.utc)
    # Other-persona episodes: dense query-term repetition (higher BM25)
    # AND large bodies whose sum exceeds the byte budget on its own.
    big = ("kilnbench telemetry " * 60) + "OTHERPERSONA payload "
    assert len(big) * 6 > INJECTION_CHAR_CAP
    for i in range(6):
        store.write_episode(
            name=f"turn/q-{i}",
            body=big + str(i),
            source_description="t",
            reference_time=now,
            source="message",
            group_id="pos3",
            session_key="loam-dev",
        )
    # Persona P: small, sparser.
    for i in range(3):
        store.write_episode(
            name=f"turn/p-{i}",
            body=f"kilnbench telemetry PERSONAP note {i}",
            source_description="t",
            reference_time=now,
            source="message",
            group_id="pos3",
            session_key="master-control",
        )
    return corpus, ep


def test_AC_PSR_8_P_survives_the_byte_cap(tmp_path: Path) -> None:
    corpus, ep = _seed(tmp_path)
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=ep,
        episode_group_ids=("pos3",),
        episode_session_key="master-control",
    )
    block = retrieve(prompt="kilnbench telemetry status", config=cfg)
    assert "PERSONAP" in block, (
        "P's episodes must render — the filter engaged during candidate "
        "selection, ahead of the byte cap (a post-cap filter empties P)"
    )
    assert "OTHERPERSONA" not in block, (
        "no higher-BM25 other-persona episode may consume P's budget"
    )
