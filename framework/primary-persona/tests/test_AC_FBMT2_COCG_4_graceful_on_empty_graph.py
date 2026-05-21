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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.FBMT2.COCG.4 — graceful on empty graph.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.COCG.4:

    A workspace with an empty graph (fresh workspace; no co-occurrences
    yet) returns BM25 + activation results unchanged (no spread
    contribution). The spreading-activation step degrades to neutral
    when no graph exists.

Verification (per plan-doc): run the retrieval contributor against a
workspace whose access log exists but contains no co-occurring touches;
assert the result set is exactly the BM25 × activation result (no
neighbors added); assert no error or warning.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.access_log import append_access_event
from loam.primary_persona.cocitation_graph import spread_one_hop
from loam.primary_persona.file_memory import FileMemoryStore


def test_AC_FBMT2_COCG_4_spread_on_empty_graph_returns_empty() -> None:
    """:func:`spread_one_hop` against an empty graph returns an empty
    addition dict."""
    candidates = [("/mem/A.md", 1.0), ("/mem/B.md", 0.5)]
    assert spread_one_hop(candidates, {}) == {}


def test_AC_FBMT2_COCG_4_spread_on_empty_candidates_returns_empty() -> None:
    """:func:`spread_one_hop` with no candidates returns an empty
    addition dict (no candidates → nothing to spread from)."""
    graph = {"/mem/A.md": {"/mem/B.md": 1.0}}
    assert spread_one_hop([], graph) == {}


def test_AC_FBMT2_COCG_4_ranker_returns_bm25_only_on_empty_graph(
    tmp_path: Path,
) -> None:
    """When the access log has NO co-occurring touches (each file's
    accesses are days apart), the graph is empty and the ranker
    surfaces the BM25 result unchanged — no spread contribution, no
    spurious neighbors."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)

    # File A: lexically matches; will be touched once.
    store.write_episode(
        name="turn/a",
        body="alpha beta gamma query terms",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # File B: does NOT match the query; only one touch, far in the past.
    store.write_episode(
        name="turn/b",
        body="entirely different topic words zinc yttrium",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )

    a_path = next((memory_dir / "episodes" / "ws").rglob("a.md"))
    b_path = next((memory_dir / "episodes" / "ws").rglob("b.md"))

    # Seed access events with timestamps DAYS APART → outside the
    # COOCCUR_WINDOW_SECONDS window → no co-occurrence → empty graph.
    append_access_event(
        memory_dir,
        file=str(a_path),
        ts=now.replace(year=2026, month=4, day=1),
        op="read",
    )
    append_access_event(
        memory_dir,
        file=str(b_path),
        ts=now.replace(year=2026, month=5, day=21),
        op="read",
    )

    result = store.search(
        query="alpha beta gamma query", group_ids=["ws"], num_results=5
    )
    names = [e["name"] for e in result["episodes"]]
    # AC.FBMT2.COCG.4: only A surfaces (the BM25 hit); no spread brings
    # B in despite both files being touched, because they don't co-occur.
    assert "turn/a" in names
    assert "turn/b" not in names, (
        f"empty graph must NOT contribute neighbors via spread; got {names}"
    )
