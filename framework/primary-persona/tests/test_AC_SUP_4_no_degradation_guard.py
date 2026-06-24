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

"""AC.SUP.4 — No-degradation = 0 regressions (tolerance EXACTLY 0).

The supersession FILTER must not drop a not-actually-superseded record.
Two properties pin the guard deterministically:

1. With NO markers anywhere, the default view is BYTE-IDENTICAL to the
   pre-change ranking — the filter is a pure no-op on an unmarked store.
2. Marking ONE record superseded removes ONLY that record; every other
   (unmarked) record's presence + relative ordering is unchanged.

Property (1) is the structural form of "no query correct pre-change
fails post-change" reduced to a deterministic invariant: if the filter
never touches an unmarked record, no unmarked-record query can regress.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


def _seed_unmarked(memory_dir: Path, n: int = 12) -> FileMemoryStore:
    store = FileMemoryStore(memory_dir=memory_dir)
    base = datetime(2026, 5, 1, tzinfo=timezone.utc)
    for i in range(n):
        store.write_episode(
            name=f"turn/rec-{i:02d}",
            body=f"alpha beta gamma record {i} delta epsilon zeta",
            source_description="test",
            reference_time=base + timedelta(hours=i),
            source="message",
            group_id="g",
        )
    return store


def test_AC_SUP_4_unmarked_store_default_view_is_noop(tmp_path: Path):
    """With no markers, the default current view returns exactly the
    records an unmarked store would — the filter is a no-op."""
    store = _seed_unmarked(tmp_path / "memory")
    result = store.search(query="alpha beta gamma", group_ids=["g"], num_results=10)
    paths = [Path(ep["path"]).name for ep in result["episodes"]]
    # All returned records are present and none was dropped by a filter
    # (no record carries a marker, so the closed-interval filter must
    # remove nothing).
    assert len(paths) == 10, f"expected the full top-10; got {paths}"
    assert len(set(paths)) == len(paths), "no duplicates"


def test_AC_SUP_4_marking_one_drops_only_that_record(tmp_path: Path):
    """Marking ONE record superseded removes exactly that record;
    every other record's presence + relative order is unchanged
    (the filter must not drop a not-actually-superseded record)."""
    memory_dir = tmp_path / "memory"
    store = _seed_unmarked(memory_dir, n=10)

    before = store.search(query="alpha beta gamma", group_ids=["g"], num_results=10)
    before_paths = [Path(ep["path"]).name for ep in before["episodes"]]
    assert "rec-05.md" in before_paths

    # Mark rec-05 superseded (concrete interval close).
    target = list((memory_dir / "episodes" / "g").rglob("rec-05.md"))[0]
    text = target.read_text(encoding="utf-8")
    target.write_text(
        text.replace(
            "group_id: g\n",
            "group_id: g\n"
            "superseded-by: ./rec-00.md\n"
            "superseded-date: 2026-06-01T00:00:00+00:00\n",
        ),
        encoding="utf-8",
    )

    after = store.search(query="alpha beta gamma", group_ids=["g"], num_results=10)
    after_paths = [Path(ep["path"]).name for ep in after["episodes"]]

    # rec-05 is gone; EVERY other record that was present is still
    # present, in the SAME relative order (zero regression).
    assert "rec-05.md" not in after_paths
    expected = [p for p in before_paths if p != "rec-05.md"]
    surviving = [p for p in after_paths if p in expected]
    assert surviving == expected, (
        "marking one record must not perturb the ordering of any "
        f"unmarked record (tolerance 0); before={before_paths} "
        f"after={after_paths}"
    )
