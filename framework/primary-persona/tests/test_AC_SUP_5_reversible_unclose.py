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

"""AC.SUP.5 — supersession is reversible: un-closing an interval (un-
marking) restores prior retrieval behaviour exactly. Retrieval keys
ONLY on interval state, so un-marking returns the record to the default
current view (the interval re-opens) and round-trips the original bytes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    _supersession_interval,
)
from loam.primary_persona.supersession import (
    mark_superseded,
    unmark_superseded,
)


def test_AC_SUP_5_unmark_reopens_interval(tmp_path: Path):
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    store.write_episode(
        name="turn/reversible",
        body="zebra quokka platypus narwhal",
        source_description="test",
        reference_time=datetime(2026, 5, 1, tzinfo=timezone.utc),
        source="message",
        group_id="g",
    )
    rec = list((memory_dir / "episodes" / "g").rglob("reversible.md"))[0]

    # Default view returns it (open interval).
    before = store.search(query="quokka platypus", group_ids=["g"], num_results=5)
    assert any("reversible.md" in ep["path"] for ep in before["episodes"])

    # Mark superseded → filtered from default view.
    mark_superseded(rec, "./successor.md", date="2026-06-01")
    _, vt = _supersession_interval(str(rec))
    assert vt == datetime(2026, 6, 1, tzinfo=timezone.utc)
    marked = store.search(query="quokka platypus", group_ids=["g"], num_results=5)
    assert not any("reversible.md" in ep["path"] for ep in marked["episodes"])

    # Un-mark → interval re-opens → restored to the default view.
    unmark_superseded(rec)
    vf, vt2 = _supersession_interval(str(rec))
    assert vt2 is None, "un-marking must re-open the interval"
    restored = store.search(query="quokka platypus", group_ids=["g"], num_results=5)
    assert any("reversible.md" in ep["path"] for ep in restored["episodes"]), (
        "un-marking must restore the record to the default current view"
    )
