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

"""AC.SUP.3 — marking never deletes or rewrites the superseded
document's content beyond the marker itself; un-marking restores prior
retrieval behavior.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.corpus_index import (
    CorpusIndex,
    discover_corpus,
)
from loam.primary_persona.supersession import (
    mark_superseded,
    read_supersession,
    unmark_superseded,
)


def test_AC_SUP_3_mark_preserves_content_beyond_marker(
    tmp_path: Path,
) -> None:
    original = "# Old rule\n\nThe whole body, every byte of it.\n"
    doc = tmp_path / "rule.md"
    doc.write_text(original, encoding="utf-8")
    mark_superseded(doc, "newer.md", date="2026-06-09")
    marked = doc.read_text(encoding="utf-8")
    # The document's content beyond the marker block is byte-for-byte
    # intact (the mark prepends a frontmatter block, nothing else).
    assert marked.endswith(original)
    assert marked != original  # the mark IS on disk


def test_AC_SUP_3_unmark_restores_exact_bytes(tmp_path: Path) -> None:
    original = "# Old rule\n\nbody line one\nbody line two\n"
    doc = tmp_path / "rule.md"
    doc.write_text(original, encoding="utf-8")
    mark_superseded(doc, "newer.md", date="2026-06-09")
    unmark_superseded(doc)
    assert doc.read_text(encoding="utf-8") == original
    assert read_supersession(doc) is None


def test_AC_SUP_3_existing_frontmatter_keys_survive_round_trip(
    tmp_path: Path,
) -> None:
    original = "---\nweight: 80\npinned: false\n---\n# Rule\n\nbody\n"
    doc = tmp_path / "weighted.md"
    doc.write_text(original, encoding="utf-8")
    mark_superseded(doc, "newer.md", date="2026-06-09")
    marked = doc.read_text(encoding="utf-8")
    assert "weight: 80" in marked and "pinned: false" in marked
    assert marked.endswith("# Rule\n\nbody\n")
    unmark_superseded(doc)
    assert doc.read_text(encoding="utf-8") == original


def test_AC_SUP_3_unmark_on_unmarked_doc_is_noop(tmp_path: Path) -> None:
    original = "---\nweight: 60\n---\n# Rule\n\nbody\n"
    doc = tmp_path / "plain.md"
    doc.write_text(original, encoding="utf-8")
    unmark_superseded(doc)
    assert doc.read_text(encoding="utf-8") == original


def test_AC_SUP_3_unmark_restores_prior_retrieval_behavior(
    tmp_path: Path,
) -> None:
    """Mark → the demotion applies; unmark → ranking and pointers come
    back exactly as before the mark (fresh index per phase)."""
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir(parents=True)
    stale = memory_dir / "feedback_old.md"
    stale.write_text(
        "# Old cadence rule\n\ncadence cadence cadence ritual cadence\n",
        encoding="utf-8",
    )
    successor = memory_dir / "feedback_new.md"
    successor.write_text(
        "# New cadence rule\n\nthe cadence ritual is continuous now\n",
        encoding="utf-8",
    )
    # Distractors give the query terms real IDF (the zero-IDF relevance
    # floor would otherwise drop every hit in a two-doc corpus).
    for name, body in {
        "feedback_gardening.md": "# Gardening\n\nsoil and compost tips\n",
        "feedback_cooking.md": "# Cooking\n\nbraise the short ribs\n",
        "feedback_travel.md": "# Travel\n\npack light for the mountains\n",
        "feedback_music.md": "# Music\n\npractice scales every morning\n",
    }.items():
        (memory_dir / name).write_text(body, encoding="utf-8")

    def _search(tag: str) -> list[tuple[str, str]]:
        def _discover() -> list[Path]:
            return discover_corpus(memory_dir=memory_dir)

        idx = CorpusIndex(
            index_path=tmp_path / f"index-{tag}.sqlite3",
            discover=_discover,
        )
        try:
            idx.sync()
            hits = idx.search(query_tokens=["cadence", "ritual"], num_results=5)
            return [(str(h["title"]), str(h["pointer"])) for h in hits]
        finally:
            idx.close()

    before = _search("before")
    mark_superseded(stale, successor.name, date="2026-06-09")
    during = _search("during")
    assert during != before, "the mark must change retrieval behavior"
    unmark_superseded(doc := stale)
    assert read_supersession(doc) is None
    after = _search("after")
    assert after == before, (
        "un-marking must restore prior retrieval behavior exactly; "
        f"before={before} after={after}"
    )
