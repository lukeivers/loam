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

"""AC.FBMT2.COCG.1 — Anderson HAM/ACT-R edge-weight formula.

Per plan-doc ``amendment-135-fbm-tier2-retrieval-mechanics.md`` §4
AC.FBMT2.COCG.1:

    A co-citation graph is built from the access log (and at
    retroactive-seed time, from existing memory-write log entries +
    agent-transcript files). Edge weight matches the Anderson
    HAM/ACT-R functional form: ``S_ji = log(P(file_i | file_j) /
    P(file_i))`` computed from co-occurrence counts, floored at a
    small epsilon to avoid ``log(0)``.

Verification (per plan-doc): seed a synthetic access log + transcript
corpus with known co-occurrence counts; build the graph; assert each
edge weight equals the expected ``log(P(i|j)/P(i))`` to within 1e-9
tolerance; assert never-co-occurring pairs map to the epsilon floor
(not ``-inf`` / not raised).
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from loam.primary_persona.cocitation_graph import (
    EDGE_WEIGHT_EPSILON,
    build_cocitation_graph,
    edge_weight,
)


def test_AC_FBMT2_COCG_1_two_file_pair_co_occurring() -> None:
    """Two files that co-occur in the access window emit an edge whose
    weight matches ``log((C_ij * N) / (N_i * N_j))``."""
    now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    # File A: 3 accesses; File B: 2 accesses; all within 60s — every
    # cross-file pair co-occurs once per pair-position in the stream.
    events_by_file = {
        "/mem/A.md": [
            now,
            now + timedelta(seconds=10),
            now + timedelta(seconds=20),
        ],
        "/mem/B.md": [
            now + timedelta(seconds=5),
            now + timedelta(seconds=25),
        ],
    }
    graph = build_cocitation_graph(events_by_file, window_seconds=60.0)
    # Expected counts:
    #   N_total = 5 (3 + 2)
    #   N_A = 3, N_B = 2
    #   C_AB = forward-window cross-file pair count.
    #          stream order (by ts): A(0), B(5), A(10), A(20), B(25)
    #          Forward i<j cross-file pairs (skip same-file):
    #            (A0,B5), (A0,B25), (B5,A10), (B5,A20),
    #            (A10,B25), (A20,B25) → 6 cross pairs.
    #          Each pair-event increments both cooccur[(A,B)] and
    #          cooccur[(B,A)] by 1, so c_AB = c_BA = 6.
    # Weight formula: S = log((C_ij * N) / (N_i * N_j))
    #   S_AB = log((6 * 5) / (3 * 2)) = log(30/6) = log(5)
    expected = math.log((6 * 5) / (3 * 2))
    assert "/mem/A.md" in graph
    assert "/mem/B.md" in graph["/mem/A.md"]
    assert abs(graph["/mem/A.md"]["/mem/B.md"] - expected) < 1e-9, (
        f"S_AB must match log((C*N)/(N_i*N_j)); "
        f"got {graph['/mem/A.md']['/mem/B.md']}, expected {expected}"
    )
    assert abs(graph["/mem/B.md"]["/mem/A.md"] - expected) < 1e-9


def test_AC_FBMT2_COCG_1_never_co_occurring_returns_epsilon_floor() -> None:
    """A pair of files that never co-occur (separate access windows)
    maps to the epsilon floor on :func:`edge_weight` lookup, not to
    ``-inf``, not raised."""
    now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    # File A and File B accessed days apart — outside any reasonable
    # co-occurrence window.
    events_by_file = {
        "/mem/A.md": [now],
        "/mem/B.md": [now + timedelta(days=2)],
    }
    graph = build_cocitation_graph(events_by_file, window_seconds=60.0)
    # No edge → epsilon-floor lookup must return a finite log(epsilon).
    w = edge_weight(graph, "/mem/A.md", "/mem/B.md")
    expected_floor = math.log(EDGE_WEIGHT_EPSILON)
    assert abs(w - expected_floor) < 1e-9, (
        f"never-co-occurring pair must map to log(epsilon); "
        f"got {w}, expected {expected_floor}"
    )
    # A lookup on a missing source file also maps to the floor.
    w2 = edge_weight(graph, "/mem/never-seen.md", "/mem/A.md")
    assert abs(w2 - expected_floor) < 1e-9
    # Not -inf, not NaN — finite floor.
    assert math.isfinite(w) and math.isfinite(w2)


def test_AC_FBMT2_COCG_1_empty_input_returns_empty_graph() -> None:
    """An empty events_by_file dict produces an empty graph (no edges,
    no errors). Composes with AC.FBMT2.COCG.4."""
    graph = build_cocitation_graph({})
    assert graph == {}


def test_AC_FBMT2_COCG_1_outside_window_no_edge() -> None:
    """Two file events whose ts-delta exceeds the window do NOT
    contribute a co-occurrence. The edge is absent (epsilon-floor on
    lookup)."""
    now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)
    events_by_file = {
        "/mem/A.md": [now],
        "/mem/B.md": [now + timedelta(seconds=120)],
    }
    graph = build_cocitation_graph(events_by_file, window_seconds=60.0)
    # The two events are 120s apart; window is 60s → no edge.
    assert "/mem/A.md" not in graph or "/mem/B.md" not in graph.get(
        "/mem/A.md", {}
    )
    w = edge_weight(graph, "/mem/A.md", "/mem/B.md")
    assert abs(w - math.log(EDGE_WEIGHT_EPSILON)) < 1e-9
