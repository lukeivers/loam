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

AC-FBM-RN update (fbm-rank-normalize slice): :func:`_merge_by_score` now
min-max-normalizes each source's raw scores onto a common ``[0, 1]`` scale
BEFORE the combined sort, so the two physical indexes' incompatible BM25
magnitudes (corpus ~15–285 vs episode 0–40, and ~0.0 for a sparse-store
episode) compete fairly — the AC-FBM-LIVE-2 fix. The cap, byte-budget, and
corpus-before-episode stable tie-break assertions below are UNCHANGED; only
the cross-source raw-magnitude ORDERING claims are restated to the
normalized contract (that ordering change IS the fix, not a weakening).
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
    # 5 corpus + 5 episode hits, each source on its own raw scale. The cap
    # still truncates the combined 10 to top_n=5.
    corpus = [_corpus_hit(f"c{i}", 10.0 - i) for i in range(5)]
    episodes = [_episode_hit(f"e{i}", 20.0 - i) for i in range(5)]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    assert len(merged) == 5, "merged set must not exceed top_n"
    # AC-FBM-RN: scores are min-max-normalized PER SOURCE before merging,
    # so raw magnitude no longer decides cross-source order. Both sources'
    # top hit normalizes to 1.0 (corpus c0 / episode e0), and because each
    # source spans 5 evenly-stepped scores the two normalized ladders
    # interleave 1.0, 1.0, 0.75, 0.75, 0.5 — so the top-5 holds hits from
    # BOTH sources, not all-episode. This is the fix: a relevant episode is
    # no longer buried under a higher-raw-magnitude corpus head (and vice
    # versa). The 1.0/1.0 tie keeps corpus-before-episode (stable arrival).
    assert any(h.get("_episode") for h in merged), "episode hit must surface"
    assert any(not h.get("_episode") for h in merged), "corpus hit must surface"
    assert merged[0]["pointer"] == "c0", (
        "the strongest corpus hit (norm 1.0) leads the 1.0/1.0 tie "
        "via the corpus-before-episode stable tie-break"
    )
    assert merged[1]["pointer"] == "e0", (
        "the strongest episode hit (norm 1.0) co-surfaces immediately "
        "after — the AC-FBM-LIVE-2 co-surface property"
    )


def test_AC_FBMU_3_merge_descending_normalized_deterministic() -> None:
    # AC-FBM-RN: order is by descending PER-SOURCE-NORMALIZED score, not raw.
    # corpus [c-low 1.0, c-high 9.0] -> norms [0.0, 1.0]; episode [e-mid 5.0]
    # single -> norm 1.0. Sorted desc-norm with stable tie-break:
    # c-high (1.0, corpus before episode), e-mid (1.0), c-low (0.0).
    corpus = [_corpus_hit("c-low", 1.0), _corpus_hit("c-high", 9.0)]
    episodes = [_episode_hit("e-mid", 5.0)]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    assert [h["pointer"] for h in merged] == ["c-high", "e-mid", "c-low"], (
        "merge must order by descending normalized score with a stable "
        "corpus-before-episode tie-break"
    )


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


def test_AC_FBM_RN_sparse_episode_at_raw_zero_co_surfaces() -> None:
    """AC-FBM-RN-1 (unit-level): a lone relevant episode whose raw BM25 is
    0.0 (the sparse-store / fresh-write regime — IDF collapses with few
    documents) still co-surfaces against a high-magnitude corpus head.

    Raw-score merge truncated it out entirely (0.0 < every corpus hit);
    min-max maps a source's sole hit to 1.0, so it competes at the top.
    This is the exact gap the live cold-walk surfaced (AC-FBM-LIVE-2)."""
    corpus = [_corpus_hit("c-big", 285.0), _corpus_hit("c-mid", 30.0)]
    episodes = [_episode_hit("ep-fresh", 0.0)]  # sparse-store raw BM25 ~0
    merged = _merge_by_score(corpus, episodes, top_n=5)
    assert any(h.get("_episode") for h in merged), (
        "a raw-0.0 relevant episode must still co-surface after normalize"
    )
    # The strongest corpus hit still leads (norm 1.0, corpus-first tie),
    # the episode co-surfaces (norm 1.0) ahead of the weaker corpus hit.
    assert merged[0]["pointer"] == "c-big"
    assert merged[1]["pointer"] == "ep-fresh"


def test_AC_FBM_RN_empty_episode_returns_corpus_unchanged() -> None:
    """AC-FBM-RN-2 / AC.FBMU.2 invariant: no episode hits => the corpus
    list is returned UNCHANGED (same objects, no normalization) so the
    no-regression byte-identical envelope holds."""
    corpus = [_corpus_hit("c0", 9.0), _corpus_hit("c1", 1.0)]
    merged = _merge_by_score(corpus, [], top_n=5)
    assert merged is corpus, "empty-episode path must return corpus unchanged"
