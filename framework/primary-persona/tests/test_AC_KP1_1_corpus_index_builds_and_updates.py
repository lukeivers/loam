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

"""AC.KP1.1 — BM25/FTS5 index over the markdown corpus builds and
updates; a corpus write is reflected on the next read. No embeddings,
no API call (stdlib sqlite3 FTS5 only)."""

from __future__ import annotations

import time
from pathlib import Path

from loam.primary_persona.keep_pace.corpus_index import (
    CorpusIndex,
    default_index_path,
    discover_corpus,
)

from _helpers_keep_pace import write_corpus


def _index(tmp_path: Path, memory_dir: Path) -> CorpusIndex:
    def _discover() -> list[Path]:
        return discover_corpus(memory_dir=memory_dir)

    return CorpusIndex(
        index_path=default_index_path(tmp_path),
        discover=_discover,
    )


def test_AC_KP1_1_index_builds_from_corpus(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    idx = _index(tmp_path, memory_dir)
    try:
        n = idx.sync()
        assert n == 5  # all five corpus docs indexed
        hits = idx.search(query_tokens=["litrpg", "canon"], num_results=5)
        assert hits
        assert any("litrpg" in str(h["title"]).lower() for h in hits)
    finally:
        idx.close()


def test_AC_KP1_1_no_embeddings_no_api(tmp_path: Path) -> None:
    # The index is sqlite-FTS5 only — the index file is a local sqlite
    # db, and no network/embedding dependency is imported.
    import loam.primary_persona.keep_pace.corpus_index as ci
    import sys

    assert "anthropic" not in sys.modules
    src = Path(ci.__file__).read_text()
    assert "import anthropic" not in src
    assert "embedding" not in src.lower() or "no embedding" in src.lower()


def test_AC_KP1_1_corpus_write_reflected_next_read(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    idx = _index(tmp_path, memory_dir)
    try:
        idx.sync()
        # A unique term not present anywhere yet.
        assert idx.search(query_tokens=["zephyrquark"], num_results=5) == []
        # Write a new corpus doc carrying the term.
        time.sleep(0.01)  # ensure a distinct mtime
        new = memory_dir / "feedback_new_topic.md"
        new.write_text(
            "# Zephyrquark protocol\n\nThe zephyrquark protocol is new.\n",
            encoding="utf-8",
        )
        # Next read reflects it (the search re-syncs).
        hits = idx.search(query_tokens=["zephyrquark"], num_results=5)
        assert hits
        assert any("zephyrquark" in str(h["title"]).lower() for h in hits)
    finally:
        idx.close()


def test_AC_KP1_1_unchanged_corpus_reindexes_nothing(tmp_path: Path) -> None:
    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    idx = _index(tmp_path, memory_dir)
    try:
        first = idx.sync()
        assert first == 5
        # Second sync with no corpus change re-indexes zero docs
        # (mtime-driven; the single-digit-ms unchanged path).
        second = idx.sync()
        assert second == 0
    finally:
        idx.close()
