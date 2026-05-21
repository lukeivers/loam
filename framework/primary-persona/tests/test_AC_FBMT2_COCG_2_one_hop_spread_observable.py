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

"""AC.FBMT2.COCG.2 — one-hop spreading activation observable.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.COCG.2:

    At retrieval time, when BM25 produces a candidate set C, the
    ranker adds to the returned result set every one-hop neighbor n
    of c ∈ C scored as ``score(c) × S_cn``, capped at one hop.
    Concretely: the F-PHRASING cure is observable — a query whose
    tokens appear in file_A but not file_B, where the co-citation
    graph has a strong A↔B edge, surfaces file_B in the result even
    though pure BM25 would have missed it.

Verification (per plan-doc): seed the graph with a strong A↔B edge;
construct a query that lexically matches A but not B; assert file_B
appears in the result set; assert its score is ``score(A) × S_AB``.

This test exercises BOTH the spread step in isolation (via
:func:`spread_one_hop` direct call to anchor the formula) AND the
end-to-end ranker (via :class:`FileMemoryStore` to verify the
production composition surfaces the neighbor).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.access_log import append_access_event
from loam.primary_persona.cocitation_graph import spread_one_hop
from loam.primary_persona.file_memory import FileMemoryStore


def test_AC_FBMT2_COCG_2_spread_score_equals_candidate_times_edge() -> None:
    """The neighbor's spread score equals ``score(c) × S_cn``."""
    graph = {
        "/mem/A.md": {"/mem/B.md": 2.5},
        "/mem/B.md": {"/mem/A.md": 2.5},
    }
    candidates = [("/mem/A.md", 4.0)]
    additions = spread_one_hop(candidates, graph)
    assert "/mem/B.md" in additions
    # AC.FBMT2.COCG.2: spread_score = score(c) × S_cn = 4.0 × 2.5 = 10.0.
    assert abs(additions["/mem/B.md"] - 10.0) < 1e-9


def test_AC_FBMT2_COCG_2_neighbor_surfaces_via_ranker(tmp_path: Path) -> None:
    """End-to-end: a query lexically matching only A returns B in the
    result set when the graph has a strong A↔B edge — the F-PHRASING
    cure observable per plan-doc."""
    memory_dir = tmp_path / "mem"
    store = FileMemoryStore(memory_dir=memory_dir)
    now = datetime.now(timezone.utc)

    # File A: lexically matches the query terms.
    store.write_episode(
        name="turn/a-lexically-matched",
        body="alpha beta gamma the query terms",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )
    # File B: does NOT lexically match the query — only surfaces via
    # the co-citation spread.
    store.write_episode(
        name="turn/b-phrasing-mismatch",
        body="entirely different tokens here xenon yttrium zinc",
        source_description="t",
        reference_time=now,
        source="message",
        group_id="ws",
    )

    a_path = next((memory_dir / "episodes" / "ws").rglob("a-lexically-matched.md"))
    b_path = next((memory_dir / "episodes" / "ws").rglob("b-phrasing-mismatch.md"))

    # Seed the access log with many A↔B co-occurring events to drive a
    # positive edge weight. The events must fall inside the
    # COOCCUR_WINDOW_SECONDS window (default 1800s).
    for i in range(15):
        ts_a = now - timedelta(seconds=i * 60)
        ts_b = now - timedelta(seconds=i * 60 + 5)
        append_access_event(
            memory_dir, file=str(a_path), ts=ts_a, op="read"
        )
        append_access_event(
            memory_dir, file=str(b_path), ts=ts_b, op="read"
        )

    # Query that lexically matches only A.
    result = store.search(
        query="alpha beta gamma query terms",
        group_ids=["ws"],
        num_results=5,
    )
    names = [e["name"] for e in result["episodes"]]
    # AC.FBMT2.COCG.2: B must surface via spread despite NO lexical match.
    assert "turn/b-phrasing-mismatch" in names, (
        f"AC.FBMT2.COCG.2 F-PHRASING cure: file B must surface via "
        f"one-hop spread from A; got {names}"
    )
