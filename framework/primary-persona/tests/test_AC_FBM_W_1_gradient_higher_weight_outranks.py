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

"""AC-FBM-W-1 (GRADIENT) — at comparable relevance, a higher-weighted rule
out-ranks a lower-weighted one.

The rule-weighting slice (B1) is the safety-pair for rank-normalize: it adds a
per-rule importance gradient so importance — not just relevance — shapes the
merged surface. This AC proves the gradient: two corpus hits with EQUAL raw
relevance but DIFFERENT declared weights surface in weight order. The boost is
``norm * (weight / BASELINE_WEIGHT)``, so a higher-weighted rule wins a
relevance tie.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.corpus_index import BASELINE_WEIGHT
from loam.primary_persona.keep_pace.retrieval import _merge_by_score


def _corpus_hit(title: str, score: float, *, weight: int) -> dict:
    return {
        "path": f"/x/{title}.md",
        "title": title,
        "pointer": title,
        "score": score,
        "weight": weight,
        "pinned": False,
    }


def _episode_hit(pointer: str, score: float) -> dict:
    return {"pointer": pointer, "score": score, "_episode": True}


def test_AC_FBM_W_1_higher_weight_outranks_at_equal_relevance() -> None:
    """Two corpus hits at the SAME raw relevance but different weights:
    the higher-weighted one surfaces first.

    Both corpus hits share a raw score so min-max normalizes both to the same
    value; only the weight breaks the tie. (An episode is present so the merge
    path — not the byte-identical early-return — runs.)"""
    # Equal raw relevance for both corpus rules; one high-weight, one low.
    high = _corpus_hit("high-weight-rule", 10.0, weight=100)
    low = _corpus_hit("low-weight-rule", 10.0, weight=10)
    # An episode so episode_hits is non-empty (merge path, not early-return).
    episodes = [_episode_hit("an-episode", 5.0)]
    # Arrival order puts the LOW-weight rule first to prove the boost — not
    # arrival order — decides the cross-weight ordering.
    merged = _merge_by_score([low, high], episodes, top_n=5)
    titles = [h.get("title") for h in merged if not h.get("_episode")]
    assert titles[0] == "high-weight-rule", (
        "the higher-weighted rule must out-rank the equally-relevant "
        f"lower-weighted rule; got corpus order {titles}"
    )
    assert titles[1] == "low-weight-rule"


def test_AC_FBM_W_1_baseline_weight_is_noop() -> None:
    """A rule at BASELINE_WEIGHT boosts by exactly 1.0 (no-op) — so a corpus
    where no doc declares a weight orders exactly as rank-normalize alone
    (the AC-FBM-W-3 no-regression hinge, proven at the math level here)."""
    a = _corpus_hit("a", 9.0, weight=BASELINE_WEIGHT)
    b = _corpus_hit("b", 1.0, weight=BASELINE_WEIGHT)
    episodes = [_episode_hit("e", 5.0)]
    merged = _merge_by_score([a, b], episodes, top_n=5)
    corpus_order = [h.get("title") for h in merged if not h.get("_episode")]
    # a (norm 1.0) before b (norm 0.0) — pure relevance order, weight no-op.
    assert corpus_order == ["a", "b"]
