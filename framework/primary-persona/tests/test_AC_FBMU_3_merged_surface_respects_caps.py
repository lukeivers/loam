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

"""AC.FBMU.3 — the merged surface respects the existing top-N <= 5 +
byte-budget caps; episode hits do not blow the budget; truncation is
deterministic.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.retrieval import (
    INJECTION_CHAR_CAP,
    _merge_by_score,
    _render_injection,
)


def _corpus_hit(title: str, score: float) -> dict:
    return {"path": f"/x/{title}.md", "title": title, "pointer": title, "score": score}


def _episode_hit(pointer: str, score: float) -> dict:
    return {"pointer": pointer, "score": score, "_episode": True}


def test_AC_FBMU_3_merge_caps_at_top_n() -> None:
    corpus = [_corpus_hit(f"c{i}", 10.0 - i) for i in range(5)]
    episodes = [_episode_hit(f"e{i}", 20.0 - i) for i in range(5)]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    assert len(merged) == 5, "merged set must not exceed top_n"
    # Highest-scored hits win — the 5 episode hits (scores 16-20) outrank
    # the corpus hits (scores 6-10).
    assert all(h.get("_episode") for h in merged)


def test_AC_FBMU_3_merge_descending_score_deterministic() -> None:
    corpus = [_corpus_hit("c-low", 1.0), _corpus_hit("c-high", 9.0)]
    episodes = [_episode_hit("e-mid", 5.0)]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    scores = [h["score"] for h in merged]
    assert scores == sorted(scores, reverse=True), "merge not score-ordered"
    assert merged[0]["pointer"] == "c-high"
    assert merged[-1]["pointer"] == "c-low"


def test_AC_FBMU_3_equal_score_stable_corpus_before_episode() -> None:
    """Equal-scored hits keep arrival order (corpus before episode) —
    deterministic truncation."""
    corpus = [_corpus_hit("c-eq", 3.0)]
    episodes = [_episode_hit("e-eq", 3.0)]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    assert merged[0]["pointer"] == "c-eq"
    assert merged[1]["pointer"] == "e-eq"


def test_AC_FBMU_3_render_respects_byte_budget() -> None:
    """Many episode pointers cannot blow the INJECTION_CHAR_CAP byte
    budget — the rendered block is capped."""
    episodes = [_episode_hit("x" * 400, 5.0 - i * 0.01) for i in range(5)]
    merged = _merge_by_score([], episodes, top_n=5)
    block = _render_injection(merged, cap=INJECTION_CHAR_CAP)
    assert len(block) <= INJECTION_CHAR_CAP
