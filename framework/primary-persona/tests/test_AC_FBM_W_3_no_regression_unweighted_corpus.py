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

"""AC-FBM-W-3 (NO-REGRESSION) — corpus docs with NO weight/pinned frontmatter
behave exactly as today.

Three legs:
1. A no-frontmatter doc parses to ``weight=BASELINE_WEIGHT, pinned=False`` and
   its indexed body is byte-identical to the raw file (the frontmatter strip is
   a no-op when there is no frontmatter).
2. A frontmatter doc that declares NO weight/pinned keys resolves to the same
   baseline default.
3. The no-episode merge early-return is byte-identical (no boost / partition /
   normalization runs on it) — the FBMU.2 invariant.

The sealed ``test_AC_FBMU_*`` + rank-normalize tests staying green (run by the
suite sweep at seal time) is the fourth leg of AC-FBM-W-3, asserted there.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.corpus_index import (
    BASELINE_WEIGHT,
    read_corpus_docs,
)
from loam.primary_persona.keep_pace.retrieval import _merge_by_score


def test_AC_FBM_W_3_no_frontmatter_doc_is_baseline_and_body_unchanged(
    tmp_path: Path,
) -> None:
    """A doc with no frontmatter: baseline weight, unpinned, body byte-identical."""
    body = (
        "# Plain rule doc\n\n"
        "This rule carries no frontmatter at all — the 102-of-132 majority.\n"
    )
    p = tmp_path / "feedback_plain.md"
    p.write_text(body, encoding="utf-8")
    (doc,) = read_corpus_docs([p])
    assert doc.weight == BASELINE_WEIGHT
    assert doc.pinned is False
    assert doc.body == body, "no-frontmatter body must index byte-identically"


def test_AC_FBM_W_3_frontmatter_without_weight_keys_is_baseline(
    tmp_path: Path,
) -> None:
    """A frontmatter doc that declares no weight/pinned keys resolves to the
    baseline default; the frontmatter metadata block is stripped from the body
    but the title + prose remain."""
    raw = (
        "---\n"
        "name: Some rule\n"
        "description: metadata only, no weight\n"
        "type: feedback\n"
        "---\n"
        "# Some rule\n\n"
        "Topical prose that carries the real signal.\n"
    )
    p = tmp_path / "feedback_fm.md"
    p.write_text(raw, encoding="utf-8")
    (doc,) = read_corpus_docs([p])
    assert doc.weight == BASELINE_WEIGHT
    assert doc.pinned is False
    # Metadata block stripped; title + prose retained.
    assert "description: metadata only" not in doc.body
    assert "Topical prose that carries the real signal." in doc.body
    assert doc.title == "Some rule"


def test_AC_FBM_W_3_empty_episode_merge_is_byte_identical() -> None:
    """The no-episode early-return returns the SAME corpus list object — no
    boost / partition / normalization runs (FBMU.2 byte-identical invariant)."""
    corpus = [
        {"path": "/a.md", "title": "a", "pointer": "a", "score": 9.0, "weight": 100, "pinned": True},
        {"path": "/b.md", "title": "b", "pointer": "b", "score": 1.0, "weight": 10, "pinned": False},
    ]
    merged = _merge_by_score(corpus, [], top_n=5)
    assert merged is corpus, (
        "no-episode path must return the corpus list unchanged — no weight "
        "boost or pinned partition may run on the byte-identical envelope"
    )
