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

"""AC.SUP.2 — corpus retrieval honors the ``superseded-by`` marker: a
superseded document no longer outranks its successor for queries both
match, and when a superseded document IS surfaced it carries its
supersession annotation (the reader sees "superseded by X", never the
bare stale rule).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.corpus_index import (
    CorpusIndex,
    discover_corpus,
)
from loam.primary_persona.supersession import mark_superseded


# The stale rule is HEAVILY topical (high term frequency) so that
# pre-mark it genuinely outranks the successor — the demotion, not the
# raw relevance, must be what flips the order.
_STALE_BODY = (
    "# Old release ritual rule\n\n"
    "The release ritual cadence is weekly. The release ritual cadence "
    "must follow the release ritual checklist. Release ritual cadence "
    "release ritual cadence release ritual. Also: zanthovore.\n"
)
_SUCCESSOR_BODY = (
    "# New release ritual rule\n\n"
    "The release ritual cadence is now continuous.\n"
)
# Distractors give the query terms real IDF — in a corpus where every
# doc matches, FTS5 bm25 scores ~0 and the zero-IDF relevance floor
# (AC.KP1.4) drops everything.
_DISTRACTORS = {
    "feedback_gardening.md": "# Gardening note\n\nSoil mixes and compost tips.\n",
    "feedback_cooking.md": "# Cooking note\n\nBraise the short ribs slowly.\n",
    "feedback_travel.md": "# Travel note\n\nPack light for the mountain trip.\n",
    "feedback_music.md": "# Music note\n\nPractice the scales every morning.\n",
}

_QUERY = ["release", "ritual", "cadence"]
# The stale doc's unique token plus the topic terms: relevance strong
# enough that the doc still clears the relevance floor AFTER the
# demotion — the surfaced-annotated case (the floor applies to the
# penalized score, the same contract as the length penalty).
_STALE_STRONG_QUERY = ["zanthovore", "ritual", "cadence"]


def _write_corpus(memory_dir: Path) -> tuple[Path, Path]:
    memory_dir.mkdir(parents=True, exist_ok=True)
    stale = memory_dir / "feedback_old_release_ritual.md"
    stale.write_text(_STALE_BODY, encoding="utf-8")
    successor = memory_dir / "feedback_new_release_ritual.md"
    successor.write_text(_SUCCESSOR_BODY, encoding="utf-8")
    for name, body in _DISTRACTORS.items():
        (memory_dir / name).write_text(body, encoding="utf-8")
    return stale, successor


def _fresh_search(
    tmp_path: Path, memory_dir: Path, tag: str, tokens: list[str]
) -> list[dict[str, object]]:
    """Search through a FRESH index (per-phase index path — no carried
    index state between the pre-mark and post-mark phases)."""

    def _discover() -> list[Path]:
        return discover_corpus(memory_dir=memory_dir)

    idx = CorpusIndex(
        index_path=tmp_path / f"index-{tag}.sqlite3",
        discover=_discover,
    )
    try:
        idx.sync()
        return idx.search(query_tokens=tokens, num_results=5)
    finally:
        idx.close()


def test_AC_SUP_2_superseded_no_longer_outranks_successor(
    tmp_path: Path,
) -> None:
    memory_dir = tmp_path / "memory"
    stale, successor = _write_corpus(memory_dir)

    # Scenario sanity: pre-mark, the stale rule outranks the successor
    # on the shared topic (otherwise the demotion would prove nothing).
    pre = _fresh_search(tmp_path, memory_dir, "pre", _QUERY)
    pre_titles = [str(h["title"]) for h in pre]
    assert "Old release ritual rule" in pre_titles
    assert "New release ritual rule" in pre_titles
    assert pre_titles.index("Old release ritual rule") < pre_titles.index(
        "New release ritual rule"
    ), f"pre-mark the stale rule must outrank; got {pre_titles}"

    # Mark via the production entry point, then search a FRESH index.
    mark_superseded(stale, successor.name, date="2026-06-09")
    post = _fresh_search(tmp_path, memory_dir, "post", _QUERY)
    post_titles = [str(h["title"]) for h in post]
    assert "New release ritual rule" in post_titles
    if "Old release ritual rule" in post_titles:
        assert post_titles.index("New release ritual rule") < post_titles.index(
            "Old release ritual rule"
        ), (
            "the superseded rule must no longer outrank its successor; "
            f"got {post_titles}"
        )


def test_AC_SUP_2_surfaced_superseded_doc_carries_annotation(
    tmp_path: Path,
) -> None:
    memory_dir = tmp_path / "memory"
    stale, successor = _write_corpus(memory_dir)
    mark_superseded(stale, successor.name, date="2026-06-09")

    # A query the stale doc matches strongly enough to clear the floor
    # post-demotion — it surfaces (demoted in rank, never deleted from
    # the index) and the reader sees the supersession, never the bare
    # stale rule.
    hits = _fresh_search(tmp_path, memory_dir, "ann", _STALE_STRONG_QUERY)
    by_title = {str(h["title"]): h for h in hits}
    assert "Old release ritual rule" in by_title, (
        "the superseded doc must still be surfaceable when relevant "
        f"enough (demote, not delete); hits={sorted(by_title)}"
    )
    hit = by_title["Old release ritual rule"]
    assert str(hit["superseded_by"]) == successor.name
    pointer = str(hit["pointer"])
    assert "superseded by" in pointer.lower(), (
        f"a surfaced superseded doc must carry its annotation; pointer={pointer!r}"
    )
    # Plain-language annotation — no file path / .md name in the pointer.
    assert ".md" not in pointer


def test_AC_SUP_2_unmarked_docs_unchanged(tmp_path: Path) -> None:
    """ADDITIVE ranking factor: unmarked docs carry no marker value and
    no annotation (the no-op multiplier; the byte-identical-score claim
    is held by the existing KP1/P@5/weight no-regression suites)."""
    memory_dir = tmp_path / "memory"
    _write_corpus(memory_dir)
    hits = _fresh_search(tmp_path, memory_dir, "plain", _QUERY)
    assert hits
    for h in hits:
        assert str(h["superseded_by"]) == ""
        assert "superseded by" not in str(h["pointer"]).lower()
