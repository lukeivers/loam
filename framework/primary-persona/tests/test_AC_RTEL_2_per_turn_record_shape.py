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

"""AC.RTEL.2 — per-turn record shape. A turn that discovers >= 1
candidate appends exactly ONE JSONL record carrying the turn-level keys
{turn_id, ts, prompt, work_anchor_tokens, budget, candidates} and each
candidate carries {source, path, score, injected, rank}.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus
from _helpers_retrieval_telemetry import read_records


def test_AC_RTEL_2_one_record_with_expected_shape(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "memory"
    write_corpus(corpus_dir)
    telemetry_dir = tmp_path / "tel"

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        telemetry_dir=telemetry_dir,
    )
    block = retrieve(prompt="continue the batch", config=cfg)
    assert block, "fixture produced no injection; the test would be vacuous"

    records = read_records(telemetry_dir)
    assert len(records) == 1, f"expected exactly one turn record, got {len(records)}"
    rec = records[0]

    # Turn-level keys.
    for key in (
        "schema_version",
        "turn_id",
        "ts",
        "prompt",
        "work_anchor_tokens",
        "budget",
        "counts",
        "candidates",
    ):
        assert key in rec, f"turn record missing key {key!r}: {rec!r}"

    assert rec["prompt"] == "continue the batch"
    assert isinstance(rec["work_anchor_tokens"], list) and rec["work_anchor_tokens"]
    assert rec["budget"]["top_n"] == cfg.top_n
    assert isinstance(rec["budget"]["char_cap"], int)
    assert rec["candidates"], "at least one candidate expected"

    # Per-candidate keys.
    cand = rec["candidates"][0]
    for key in ("source", "path", "score", "salience", "event_time", "injected", "rank"):
        assert key in cand, f"candidate missing key {key!r}: {cand!r}"
    assert cand["source"] in ("corpus", "episode", "decision")
    assert isinstance(cand["injected"], bool)
