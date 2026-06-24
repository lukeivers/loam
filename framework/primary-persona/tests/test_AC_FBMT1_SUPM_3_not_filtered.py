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

"""AC.FBMT1.SUPM.3 — annotate-not-delete preserved under the SUP
validity-interval promotion (memory-supersession cycle).

PRECEDESSOR-CONTRACT MIGRATION: amendment-134 authored SUPM.3 as
"superseded files are demoted, NOT filtered" — visible-but-demoted in
the DEFAULT view. The memory-supersession cycle (plan §2) PROMOTES that
demote-not-filter penalty into a real validity-interval FILTER: the
DEFAULT current view now FILTERS the superseded record out (current-
over-stale, AC.SUP.1). The annotate-not-delete property SUPM.3 protects
(the record is never deleted; it stays reachable) is PRESERVED — it now
lives on the ``as_of`` HISTORY view, where the marked-but-in-window
record is still returned AND still demoted below an unmarked sibling by
``SUPERSEDED_PENALTY``. This test pins BOTH halves so the SUP filter
cannot silently become a delete.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


def _write_marked(store: FileMemoryStore, memory_dir: Path) -> Path:
    ref_time = datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc)
    store.write_episode(
        name="turn/superseded-strong-match",
        body=(
            "quokka platypus quokka platypus quokka platypus "
            "quokka platypus quokka platypus"
        ),
        source_description="test",
        reference_time=ref_time,
        source="message",
        group_id="testgroup",
    )
    sup_file = list((memory_dir / "episodes" / "testgroup").rglob("*.md"))
    assert sup_file
    sup_path = sup_file[0]
    text = sup_path.read_text(encoding="utf-8")
    # Mark superseded with an explicit close date → a concrete
    # validity interval [2026-05-21, 2026-06-01).
    annotated = text.replace(
        "group_id: testgroup\n",
        "group_id: testgroup\n"
        "superseded-by: ./other.md\n"
        "superseded-date: 2026-06-01T00:00:00+00:00\n",
    )
    sup_path.write_text(annotated, encoding="utf-8")
    return sup_path


def test_AC_FBMT1_SUPM_3_superseded_filtered_from_default_view(tmp_path: Path):
    """The DEFAULT current view FILTERS the superseded record out
    (AC.SUP.1 — the promotion of demote-not-filter into filter)."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    _write_marked(store, memory_dir)

    result = store.search(
        query="quokka platypus",
        group_ids=["testgroup"],
        num_results=5,
    )
    paths = [ep["path"] for ep in result["episodes"]]
    assert not any("superseded-strong-match.md" in p for p in paths), (
        "superseded record must be FILTERED from the default current "
        f"view (AC.SUP.1); paths returned: {paths}"
    )


def test_AC_FBMT1_SUPM_3_annotate_not_delete_reachable_via_as_of(tmp_path: Path):
    """The record is never deleted: an ``as_of`` query inside its
    validity window still returns it (AC.SUP.2 — filtering ≠ deletion;
    the annotate-not-delete property SUPM.3 protected)."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    _write_marked(store, memory_dir)

    as_of = datetime(2026, 5, 25, 0, 0, 0, tzinfo=timezone.utc)
    result = store.search(
        query="quokka platypus",
        group_ids=["testgroup"],
        num_results=5,
        as_of=as_of,
    )
    paths = [ep["path"] for ep in result["episodes"]]
    assert any("superseded-strong-match.md" in p for p in paths), (
        "the superseded record must remain reachable via an as_of query "
        f"inside its valid window (AC.SUP.2); paths returned: {paths}"
    )
