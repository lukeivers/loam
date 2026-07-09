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

"""AC.RVL.1 — the corpus discovered set is FLOOR-determined, not count-
determined; BOTH corpus count gates are converted (RF-1).

Pre-reshape the corpus path had TWO count gates: the SQL candidate window
``candidate_limit = max(num_results * 5, num_results)`` (bounding the pool
at 5x5 = 25) AND the post-re-rank ``rest_out[:num_results]`` truncation
(bounding the returned set at 5). This fixture writes MANY more matching,
floor-clearing docs than EITHER legacy gate and asserts every floor-clearing
doc is returned even when the caller passes the legacy ``num_results = 5`` —
so neither the SQL window nor the tail truncation decides the set.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.corpus_index import (
    CorpusIndex,
    default_index_path,
    discover_corpus,
)

_LEGACY_SQL_WINDOW = 25  # the old max(5*5, 5)
_LEGACY_TAIL_CUT = 5  # the old rest_out[:num_results]
_N = 30  # > both legacy gates


def _tokens(n: int) -> list[str]:
    # Each doc carries its OWN rare token so every doc is a strong (df=1,
    # high-IDF) match that clears the relevance floor — a single shared token
    # would collapse IDF to ~0 and be floored, which is a fixture artefact, not
    # the property under test.
    return [f"widgetronic{i}" for i in range(n)]


def _index(tmp_path: Path, memory_dir: Path) -> CorpusIndex:
    def _discover() -> list[Path]:
        return discover_corpus(memory_dir=memory_dir)

    return CorpusIndex(index_path=default_index_path(tmp_path), discover=_discover)


def _write_matching_corpus(memory_dir: Path, n: int) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (memory_dir / f"feedback_rule_{i}.md").write_text(
            f"# widgetronic{i} rule\n\n"
            f"The widgetronic{i} protocol governs subsystem {i}.\n",
            encoding="utf-8",
        )


def test_AC_RVL_1_all_floor_clearing_corpus_hits_reach_the_merge(
    tmp_path: Path,
) -> None:
    memory_dir = tmp_path / "corpus"
    _write_matching_corpus(memory_dir, _N)
    idx = _index(tmp_path, memory_dir)
    try:
        idx.sync()
        # The caller passes the LEGACY count; it must NOT bound the set.
        hits = idx.search(query_tokens=_tokens(_N), num_results=_LEGACY_TAIL_CUT)
    finally:
        idx.close()

    # Every matching, floor-clearing doc is returned — the relevance floor
    # (MIN_RELEVANCE_SCORE), not a count, determined the set.
    assert len(hits) == _N, (
        f"all {_N} floor-clearing corpus docs must reach the merge; got "
        f"{len(hits)} — a count gate is still cutting the set"
    )
    # Explicitly past BOTH legacy gates: the SQL 25-window AND the 5-tail cut.
    assert len(hits) > _LEGACY_SQL_WINDOW, "the SQL candidate window still bounds"
    assert len(hits) > _LEGACY_TAIL_CUT, "the tail truncation still bounds"


def test_AC_RVL_1_num_results_no_longer_truncates(tmp_path: Path) -> None:
    """Passing a SMALLER num_results does not shrink the floor-clearing set —
    proving num_results no longer truncates (only its <=0 disable guard
    survives)."""
    memory_dir = tmp_path / "corpus"
    _write_matching_corpus(memory_dir, _N)
    idx = _index(tmp_path, memory_dir)
    try:
        idx.sync()
        few = idx.search(query_tokens=_tokens(_N), num_results=1)
        many = idx.search(query_tokens=_tokens(_N), num_results=100)
    finally:
        idx.close()
    assert len(few) == len(many) == _N, (
        "the discovered set is floor-determined; num_results must not change it"
    )


def test_AC_RVL_1_disable_guard_preserved(tmp_path: Path) -> None:
    """num_results <= 0 remains the caller's disable guard (returns [])."""
    memory_dir = tmp_path / "corpus"
    _write_matching_corpus(memory_dir, 3)
    idx = _index(tmp_path, memory_dir)
    try:
        idx.sync()
        assert idx.search(query_tokens=_tokens(3), num_results=0) == []
    finally:
        idx.close()
