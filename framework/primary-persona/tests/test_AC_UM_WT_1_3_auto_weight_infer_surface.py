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

"""AC.UM.WT.1/.2/.3 — FBM rule auto-weighting (D-N4.4).

AC.UM.WT.1: a weight is inferred + surfaced, NEVER silent-written.
AC.UM.WT.2: on confirm, the B1 ``weight:`` frontmatter mechanism carries
it (N4 adds no new weighting math).
AC.UM.WT.3: no-confirm => no change (the doc is byte-for-byte unchanged).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import interaction_model as im
from loam.primary_persona.keep_pace.corpus_index import (
    BASELINE_WEIGHT,
    read_corpus_docs,
)


def test_AC_UM_WT_1_infers_band_and_surfaces_only(tmp_path: Path) -> None:
    """suggest_weight infers a coarse band + builds a surface-for-confirm
    rationale; it writes NOTHING to disk."""
    doc = tmp_path / "rule.md"
    doc.write_text("# A load-bearing rule\n\nbody\n", encoding="utf-8")
    before = doc.read_text()
    s = im.suggest_weight(
        doc_path=doc, importance_signal="load-bearing safety rule"
    )
    assert s.band == "high"
    assert s.weight == im.WEIGHT_BANDS["high"]
    assert s.rationale  # a plain-language surface for confirm
    # NOTHING written — the surface is infer-only.
    assert doc.read_text() == before


def test_AC_UM_WT_1_bands_are_coarse() -> None:
    """The inference is coarse — low / normal / high, with normal == the
    B1 baseline no-op band."""
    assert im.infer_weight_band(importance_signal="critical core directive") == "high"
    assert im.infer_weight_band(importance_signal="just a nice-to-have") == "low"
    assert im.infer_weight_band(importance_signal="ordinary rule") == "normal"
    assert im.WEIGHT_BANDS["normal"] == BASELINE_WEIGHT  # the no-op band


def test_AC_UM_WT_2_confirm_writes_b1_frontmatter(tmp_path: Path) -> None:
    """On confirm, the weight lands as B1-format ``weight:`` frontmatter
    the existing corpus_index reader picks up (the B1 boost math applies
    unchanged)."""
    doc = tmp_path / "rule.md"
    doc.write_text("# A rule\n\nthe rule body prose\n", encoding="utf-8")
    s = im.suggest_weight(doc_path=doc, importance_signal="load-bearing")
    assert im.confirm_weight(doc_path=doc, weight=s.weight)
    # The B1 reader reads the confirmed weight back.
    docs = read_corpus_docs([doc])
    assert len(docs) == 1
    assert docs[0].weight == s.weight  # the high band value
    # The body prose is preserved (frontmatter is stripped for indexing).
    assert "the rule body prose" in docs[0].body


def test_AC_UM_WT_2_confirm_upserts_into_existing_frontmatter(
    tmp_path: Path,
) -> None:
    """A confirm on a doc that already has frontmatter upserts the
    ``weight:`` line, preserving the rest of the block."""
    doc = tmp_path / "rule.md"
    doc.write_text(
        "---\nname: a-rule\npinned: true\n---\n# A rule\n\nbody\n",
        encoding="utf-8",
    )
    assert im.confirm_weight(doc_path=doc, weight=80)
    docs = read_corpus_docs([doc])
    assert docs[0].weight == 80
    assert docs[0].pinned is True  # the existing pinned line preserved


def test_AC_UM_WT_3_no_confirm_is_no_op(tmp_path: Path) -> None:
    """An un-confirmed inferred weight leaves the doc byte-for-byte
    unchanged — declining the surface is a no-op (baseline weight=50)."""
    doc = tmp_path / "rule.md"
    original = "# A rule\n\nbody with no frontmatter\n"
    doc.write_text(original, encoding="utf-8")
    # Infer + surface, but NEVER confirm.
    im.suggest_weight(doc_path=doc, importance_signal="load-bearing critical")
    # The doc is byte-for-byte unchanged; the B1 reader sees the baseline.
    assert doc.read_text() == original
    docs = read_corpus_docs([doc])
    assert docs[0].weight == BASELINE_WEIGHT
    assert docs[0].pinned is False
