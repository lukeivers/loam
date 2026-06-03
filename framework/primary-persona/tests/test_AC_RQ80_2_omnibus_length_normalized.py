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

"""AC.RQ80.2 (#80 omnibus length-normalization) — ``CorpusIndex.search()``
applies a bounded length penalty so a SHORT focused single-rule doc out-ranks a
LONG omnibus doc that matched the query terms among much unrelated text. Without
the penalty the omnibus wins on term mass; with it the focused doc wins.

Plan: docs/plans/fbm-retrieval-quality-anchor-cap-omnibus-norm.md §Lever 2.
"""

from __future__ import annotations

from pathlib import Path

import sys

from loam.primary_persona.keep_pace import corpus_index as ci
from loam.primary_persona.keep_pace.corpus_index import (
    CorpusIndex,
    LENGTH_NORM_PIVOT_TOKENS,
    default_index_path,
    discover_corpus,
    read_corpus_docs,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _helpers_keep_pace import write_corpus  # noqa: E402


def _write_two_doc_corpus(memory_dir: Path) -> None:
    """A SHORT focused doc on the query topic + a LONG omnibus doc that mentions
    the query topic once among much unrelated prose (the omnibus-bias shape),
    PLUS a handful of distractor docs (via ``write_corpus``) so the FTS5 index
    is not sparse — with only two docs BM25's IDF term collapses and every
    score is 0.0 (the documented sparse regime), which would make the test
    measure nothing. The distractors give BM25 a real non-zero score for the
    penalty to act on."""
    write_corpus(memory_dir)
    memory_dir.mkdir(parents=True, exist_ok=True)
    # The focused rule: short, densely on-topic for "widget calibration".
    (memory_dir / "feedback_widget_calibration.md").write_text(
        "# Widget calibration procedure\n\n"
        "Calibrate the widget before each run. The widget calibration "
        "constant is tuned per batch.\n",
        encoding="utf-8",
    )
    # The omnibus: long, mentions "widget calibration" once, padded well past
    # the pivot with unrelated prose. The length signal is DISTINCT-token
    # vocabulary breadth (an omnibus has broad vocabulary; a focused rule
    # narrow), so the filler must carry GENUINELY-DISTINCT tokens past the pivot
    # — synthesize > pivot unique words so the omnibus's doc_token_len clears it.
    unique_filler = " ".join(
        f"topic{i}word covering area{i}domain and subject{i}matter"
        for i in range(LENGTH_NORM_PIVOT_TOKENS + 400)
    )
    omnibus_body = (
        "# Omnibus operating principles index\n\n"
        "Among many topics: calibrate the widget when needed. " + unique_filler
    )
    (memory_dir / "feedback_omnibus_index.md").write_text(
        omnibus_body, encoding="utf-8"
    )


def _build_index(tmp_path: Path, memory_dir: Path) -> CorpusIndex:
    def _discover() -> list[Path]:
        return discover_corpus(memory_dir=memory_dir, claude_homes=(), objectives_path=None)

    idx = CorpusIndex(index_path=default_index_path(tmp_path), discover=_discover)
    idx.sync()
    return idx


def test_AC_RQ80_2_focused_doc_outranks_omnibus_after_length_norm(
    tmp_path: Path,
) -> None:
    """With the length penalty the SHORT focused doc out-ranks the LONG omnibus;
    the fixture is constructed so the omnibus is genuinely longer than the
    pivot and the focused doc is well under it (so the penalty discriminates)."""
    memory_dir = tmp_path / "memory"
    _write_two_doc_corpus(memory_dir)

    # Sanity: the fixture docs straddle the pivot (the penalty can discriminate).
    docs = {
        Path(d.path).name: d
        for d in read_corpus_docs(
            discover_corpus(memory_dir=memory_dir, claude_homes=(), objectives_path=None)
        )
    }
    assert docs["feedback_widget_calibration.md"].doc_token_len < LENGTH_NORM_PIVOT_TOKENS
    assert docs["feedback_omnibus_index.md"].doc_token_len > LENGTH_NORM_PIVOT_TOKENS

    idx = _build_index(tmp_path, memory_dir)
    try:
        hits = idx.search(query_tokens=["widget", "calibration"], num_results=5)
    finally:
        idx.close()

    pointers = [str(h["pointer"]) for h in hits]
    assert any("Widget calibration" in p for p in pointers), (
        f"the focused doc must be retrieved; got {pointers}"
    )
    # The focused doc out-ranks the omnibus (it appears first).
    focused_rank = next(
        i for i, p in enumerate(pointers) if "Widget calibration" in p
    )
    omnibus_ranks = [i for i, p in enumerate(pointers) if "Omnibus" in p]
    if omnibus_ranks:
        assert focused_rank < omnibus_ranks[0], (
            f"the focused doc must out-rank the omnibus after length-norm; "
            f"pointers={pointers}"
        )


def _omnibus_score(memory_dir: Path, index_path: Path) -> float:
    """The omnibus doc's surfaced relevance score for the query."""
    def _discover() -> list[Path]:
        return discover_corpus(memory_dir=memory_dir, claude_homes=(), objectives_path=None)

    idx = CorpusIndex(index_path=index_path, discover=_discover)
    idx.sync()
    try:
        hits = idx.search(query_tokens=["widget", "calibration"], num_results=10)
    finally:
        idx.close()
    for h in hits:
        if "Omnibus" in str(h["pointer"]):
            return float(h["score"])
    return 0.0


def test_AC_RQ80_2_penalty_demotes_the_omnibus_score(
    tmp_path: Path, monkeypatch
) -> None:
    """Control isolating the LEVER: the SAME omnibus doc scores STRICTLY LOWER
    with the length penalty active than with it neutralized (pivot pushed above
    every doc length). This proves the penalty — not some other factor — is what
    demotes the omnibus, and (with the companion test above) that the demotion
    is enough to keep a focused doc ahead of it. SQLite's built-in bm25 already
    length-normalizes at b=0.75; this lever ADDS a bounded penalty on top, and
    the assertion is the honest, directly-verifiable effect (a strict score
    decrease), not a contrived rank-flip."""
    memory_dir = tmp_path / "memory"
    _write_two_doc_corpus(memory_dir)

    # Penalty NEUTRALIZED (pivot above any doc length → no-op).
    monkeypatch.setattr(ci, "LENGTH_NORM_PIVOT_TOKENS", 10_000_000)
    score_without = _omnibus_score(memory_dir, default_index_path(tmp_path / "a"))

    # Penalty ACTIVE (the shipped pivot).
    monkeypatch.setattr(ci, "LENGTH_NORM_PIVOT_TOKENS", 1250)
    score_with = _omnibus_score(memory_dir, default_index_path(tmp_path / "b"))

    assert score_without > 0.0, "fixture sanity: the omnibus must score non-zero"
    assert score_with < score_without, (
        "the length penalty must DEMOTE the omnibus's score (it is longer than "
        f"the pivot); with={score_with} without={score_without}"
    )
    # And it is demoted, NOT zeroed (AC.RQ80.3 boundedness, re-checked here).
    assert score_with > 0.0, "the omnibus must stay retrievable (not zeroed)"
