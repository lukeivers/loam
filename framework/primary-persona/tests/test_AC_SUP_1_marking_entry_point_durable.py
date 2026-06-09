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

"""AC.SUP.1 — a production entry point durably marks a corpus document
superseded-by a named successor using the existing ``superseded-by``
marker convention; the mark is on-disk, machine-readable, and carries
date + successor pointer.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.supersession import (
    mark_superseded,
    read_supersession,
)


def test_AC_SUP_1_mark_doc_without_frontmatter(tmp_path: Path) -> None:
    doc = tmp_path / "feedback_old_rule.md"
    doc.write_text(
        "# Old rule\n\nNever do the thing without checking.\n",
        encoding="utf-8",
    )
    mark_superseded(doc, "feedback_new_rule.md", date="2026-06-09")

    # Durable: a FRESH read of the on-disk bytes carries the mark.
    on_disk = doc.read_text(encoding="utf-8")
    assert "superseded-by: feedback_new_rule.md" in on_disk
    assert "superseded-date: 2026-06-09" in on_disk

    # Machine-readable round-trip with date + successor.
    mark = read_supersession(doc)
    assert mark == {
        "superseded-by": "feedback_new_rule.md",
        "superseded-date": "2026-06-09",
    }


def test_AC_SUP_1_mark_doc_with_existing_frontmatter(tmp_path: Path) -> None:
    """A doc that already carries frontmatter (weight/pinned) keeps its
    other keys; the marker extends the block (re-marking replaces a
    prior marker, not duplicates it)."""
    doc = tmp_path / "feedback_weighted_rule.md"
    doc.write_text(
        "---\nweight: 80\npinned: false\n---\n# Weighted rule\n\nbody\n",
        encoding="utf-8",
    )
    mark_superseded(doc, "feedback_first.md", date="2026-06-01")
    mark_superseded(doc, "feedback_second.md", date="2026-06-09")

    text = doc.read_text(encoding="utf-8")
    assert "weight: 80" in text
    assert "pinned: false" in text
    assert text.count("superseded-by:") == 1, "re-marking must replace"
    mark = read_supersession(doc)
    assert mark["superseded-by"] == "feedback_second.md"
    assert mark["superseded-date"] == "2026-06-09"


def test_AC_SUP_1_default_date_is_today(tmp_path: Path) -> None:
    from datetime import date as _date

    doc = tmp_path / "rule.md"
    doc.write_text("# Rule\n\nbody\n", encoding="utf-8")
    mark_superseded(doc, "newer.md")
    mark = read_supersession(doc)
    assert mark["superseded-date"] == _date.today().isoformat()


def test_AC_SUP_1_unmarked_or_missing_reads_none(tmp_path: Path) -> None:
    doc = tmp_path / "plain.md"
    doc.write_text("# Plain\n\nbody\n", encoding="utf-8")
    assert read_supersession(doc) is None
    assert read_supersession(tmp_path / "missing.md") is None
