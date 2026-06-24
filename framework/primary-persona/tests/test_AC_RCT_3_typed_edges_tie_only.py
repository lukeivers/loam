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

"""AC.RCT.3 — the tie-breaker operates ONLY over deliberate typed edges
(supersedes / answers / continues), never statistical co-occurrence, and
is hub-corrected (IDF). It re-orders ONLY near-ties — never the primary
ranker.
"""

from __future__ import annotations

import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL.parent) not in sys.path:
    sys.path.insert(0, str(_EVAL.parent))

from eval import harness  # noqa: E402


def test_AC_RCT_3_edge_set_excludes_co_occurrence():
    split = harness.load_rct_split()
    assert split["typed_edges_only"] == ["supersedes", "answers", "continues"]
    assert "co_occurrence" in split["excludes"]
    assert "statistical_association" in split["excludes"]
    # Every edge in the frozen split is one of the typed kinds.
    typed = set(split["typed_edges_only"])
    for arm in ("train", "test"):
        for item in split[arm]:
            for _src, etype, _dst in item.get("edges", []):
                assert etype in typed, (
                    f"edge type {etype!r} is not a deliberate typed edge"
                )


def test_AC_RCT_3_hub_corrected_idf():
    # A hub referenced by everything is down-weighted relative to a
    # record referenced by a few distinct sources (IDF correction).
    candidates = ["hub", "specific", "other"]
    # 'hub' referenced by 3 distinct sources; 'specific' by 1.
    edges = [
        ["a", "answers", "hub"],
        ["b", "answers", "hub"],
        ["c", "answers", "hub"],
        ["a", "supersedes", "specific"],
    ]
    corrected = harness.reference_count_tiebreak(candidates, edges, hub_correct=True)
    raw = harness.reference_count_tiebreak(candidates, edges, hub_correct=False)
    # Raw in-degree puts hub strictly above specific.
    assert raw["hub"] > raw["specific"]
    # Hub-correction shrinks the hub's advantage (IDF down-weights it).
    raw_gap = raw["hub"] - raw["specific"]
    corrected_gap = corrected["hub"] - corrected["specific"]
    assert corrected_gap < raw_gap, (
        "IDF hub-correction must shrink a hub's reference-count advantage"
    )


def test_AC_RCT_3_no_op_when_no_edges():
    # With no typed edges, every score is 0 — the tie-breaker contributes
    # nothing (it is never the primary ranker).
    scores = harness.reference_count_tiebreak(["x", "y"], [], hub_correct=True)
    assert scores == {"x": 0.0, "y": 0.0}
