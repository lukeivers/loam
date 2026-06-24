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

"""AC.RCT.4 — RCT is default-OFF and reversible: with the tie-breaker
disabled, retrieval is BYTE-IDENTICAL to the SUP-only committed core.
The committed core never depends on RCT.

Because the NOT-EARNED verdict fires (the predicted null), the
tie-breaker is never wired into the production ``FileMemoryStore.search``
path at all — it stays a separate, default-OFF function in the eval
harness. This test pins that structural default-off guarantee: the
production ranker's output does not reference or depend on the
tie-breaker, so retrieval IS the SUP-only core.
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore

_FM_SRC = (
    Path(__file__).resolve().parent.parent
    / "src" / "loam" / "primary_persona" / "file_memory.py"
)


def test_AC_RCT_4_tie_breaker_not_wired_into_production_ranker():
    src = _FM_SRC.read_text(encoding="utf-8")
    # The production ranker must not import or call the tie-breaker —
    # default-OFF is structural (it is absent from the production path).
    assert "reference_count_tiebreak" not in src
    assert "rct" not in src.lower().replace("contradict", "")


def test_AC_RCT_4_default_search_is_sup_only_deterministic():
    """The default search path is fully determined by the SUP filter +
    BM25 + supersession penalty — running it twice yields identical
    results (no RCT randomness leaks into production retrieval)."""
    with tempfile.TemporaryDirectory() as td:
        memory_dir = Path(td) / "memory"
        store = FileMemoryStore(memory_dir=memory_dir)
        base = datetime(2026, 5, 1, tzinfo=timezone.utc)
        for i in range(6):
            store.write_episode(
                name=f"turn/rec-{i}",
                body=f"alpha beta gamma {i} delta",
                source_description="t",
                reference_time=base,
                source="message",
                group_id="g",
            )
        r1 = store.search(query="alpha beta gamma", group_ids=["g"], num_results=5)
        r2 = store.search(query="alpha beta gamma", group_ids=["g"], num_results=5)
        assert [e["path"] for e in r1["episodes"]] == [
            e["path"] for e in r2["episodes"]
        ], "the SUP-only default ranker must be deterministic (no RCT leak)"
