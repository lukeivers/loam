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

"""AC.FBMT2.COCG.5 — spread is strictly capped at one hop.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.COCG.5:

    The graph is capped at strictly one hop. A two-hop reachable file
    (A→B→C, no direct A↔C edge) does NOT enter the result set on a
    query matching only A.

Verification (per plan-doc): seed A↔B and B↔C edges with no A↔C
edge; run a query lexically matching only A; assert file_C is NOT in
the result set; assert file_B IS in the result set (one hop from A).
"""

from __future__ import annotations

from loam.primary_persona.cocitation_graph import spread_one_hop


def test_AC_FBMT2_COCG_5_two_hop_neighbor_not_added() -> None:
    """A graph with A↔B and B↔C edges (no direct A↔C) — spreading from
    A returns ONLY B; C is two hops out and must NOT enter."""
    graph = {
        "/mem/A.md": {"/mem/B.md": 2.0},
        "/mem/B.md": {"/mem/A.md": 2.0, "/mem/C.md": 3.0},
        "/mem/C.md": {"/mem/B.md": 3.0},
    }
    candidates = [("/mem/A.md", 1.0)]
    additions = spread_one_hop(candidates, graph)
    # AC.FBMT2.COCG.5: B is one hop from A → enters. C is two hops out
    # → must NOT enter.
    assert "/mem/B.md" in additions, (
        f"B is one hop from A and MUST surface; got {additions}"
    )
    assert "/mem/C.md" not in additions, (
        f"AC.FBMT2.COCG.5: C is TWO hops from A (A→B→C) and must NOT "
        f"surface; got {additions}"
    )


def test_AC_FBMT2_COCG_5_one_hop_spread_includes_only_direct_neighbors() -> None:
    """A larger graph — confirm the spread set is exactly the direct
    neighbors of the candidate set, never their neighbors-of-neighbors."""
    graph = {
        "/A.md": {"/B.md": 1.0, "/D.md": 0.5},
        "/B.md": {"/A.md": 1.0, "/C.md": 1.0},
        "/C.md": {"/B.md": 1.0, "/E.md": 1.0},  # E is 2-hop from A
        "/D.md": {"/A.md": 0.5, "/F.md": 1.0},  # F is 2-hop from A
        "/E.md": {"/C.md": 1.0},
        "/F.md": {"/D.md": 1.0},
    }
    candidates = [("/A.md", 1.0)]
    additions = spread_one_hop(candidates, graph)
    # Direct neighbors of A: B, D — must surface.
    assert set(additions.keys()) == {"/B.md", "/D.md"}, (
        f"only direct (one-hop) neighbors of A must surface; got "
        f"{set(additions.keys())}"
    )
    # C, E, F are 2+ hops out and must be absent.
    for two_hop in ("/C.md", "/E.md", "/F.md"):
        assert two_hop not in additions, (
            f"AC.FBMT2.COCG.5: {two_hop} is 2+ hops from A and must "
            f"NOT enter; got {additions}"
        )


def test_AC_FBMT2_COCG_5_candidates_already_in_set_not_doubled() -> None:
    """When a neighbor of one candidate IS another candidate, the
    spread step does NOT re-add it (the candidate keeps its primary
    score). This is the COCG.5-adjacent guard against double-counting
    candidates as their own one-hop neighbors."""
    graph = {
        "/A.md": {"/B.md": 1.5},
        "/B.md": {"/A.md": 1.5},
    }
    candidates = [("/A.md", 1.0), ("/B.md", 2.0)]
    additions = spread_one_hop(candidates, graph)
    # Both A and B are in the candidate set; neither should appear in
    # additions (spread adds NEW files, not re-scores existing ones).
    assert additions == {}, (
        f"candidates already in the set must not appear in additions; "
        f"got {additions}"
    )
