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

"""AC-FBM-FLOOR-1 (Slice B / B1) — the ABSOLUTE EPISODE RELEVANCE FLOOR.

In a POPULATED result set (at least one above-floor episode), an episode whose
RAW BM25 is below ``EPISODE_MIN_RELEVANCE_SCORE`` is dropped BEFORE the per-source
min-max normalization, so it cannot be min-max-promoted to ``1.0`` and out-rank a
genuine corpus feedback-rule (FM-4 closed on the episode side). The over-filter
SAFEGUARD: when NO episode clears the floor (the sparse / IDF-collapsed regime),
the floor self-disables and a lone relevant sub-floor episode still co-surfaces
(the sealed AC-FBM-RN-2 / AC.FBMU.1 behaviour is preserved).
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.retrieval import (
    EPISODE_MIN_RELEVANCE_SCORE,
    _merge_by_score,
)


def _corpus_hit(title: str, score: float) -> dict:
    return {"path": f"/x/{title}.md", "title": title, "pointer": title, "score": score}


def _episode_hit(pointer: str, score: float) -> dict:
    return {"pointer": pointer, "score": score, "_episode": True}


def test_AC_FBM_FLOOR_1_subfloor_episode_does_not_outrank_corpus() -> None:
    """Populated regime: a sub-floor noise episode is dropped so it cannot be
    min-max-promoted to out-rank a genuine corpus rule; the above-floor episode
    on the same query DOES still surface (the floor filters noise, not relevance)."""
    corpus = [_corpus_hit("c-real-rule", 30.0)]
    # Two episodes: one genuine match well above the floor, one pure-noise
    # zero-IDF hit below the floor. Without the floor, min-max would map the
    # noise episode (the EPISODE source's worst) to 0.0 — but the FM-4 harm is
    # the source's BEST being promoted; here we prove the sub-floor hit is gone
    # entirely so it can never be the source's best on a noisier query.
    episodes = [
        _episode_hit("ep-genuine", 12.0),
        _episode_hit("ep-noise", EPISODE_MIN_RELEVANCE_SCORE / 10.0),
    ]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    pointers = [h["pointer"] for h in merged]
    assert "ep-noise" not in pointers, (
        "a sub-floor episode must be dropped in the populated regime; "
        f"merged={pointers}"
    )
    # The genuine corpus rule AND the above-floor episode both surface.
    assert "c-real-rule" in pointers
    assert "ep-genuine" in pointers


def test_AC_FBM_FLOOR_1_subfloor_noise_cannot_be_promoted_above_corpus() -> None:
    """The FM-4 shape directly: the ONLY episode is a sub-floor noise hit, and a
    genuine above-floor episode also matches. The noise hit must not occupy a slot
    that min-max promotion would have handed it ahead of the corpus rule."""
    corpus = [_corpus_hit("c-real-rule", 30.0), _corpus_hit("c-second", 15.0)]
    episodes = [
        _episode_hit("ep-strong", 9.0),
        _episode_hit("ep-keyword-noise", 0.001),
    ]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    pointers = [h["pointer"] for h in merged]
    assert "ep-keyword-noise" not in pointers
    # The corpus rule still leads (it is the strongest hit and min-max keeps it
    # at the top); the noise episode is not min-max-promoted above it.
    assert pointers[0] == "c-real-rule"


def test_AC_FBM_FLOOR_1_safeguard_lone_sparse_episode_still_surfaces() -> None:
    """SAFEGUARD: in the sparse / IDF-collapsed regime (every episode raw ~0),
    the floor self-disables so a lone relevant episode is NOT over-filtered —
    the sealed AC-FBM-RN-2 behaviour (raw-0.0 episode co-surfaces at rank 2,
    ahead of the weaker corpus hit) is preserved exactly."""
    corpus = [_corpus_hit("c-big", 285.0), _corpus_hit("c-mid", 30.0)]
    episodes = [_episode_hit("ep-fresh", 0.0)]  # sparse-store raw BM25 ~0
    merged = _merge_by_score(corpus, episodes, top_n=5)
    pointers = [h["pointer"] for h in merged]
    assert "ep-fresh" in pointers, (
        "the floor must self-disable in the sparse regime — a lone relevant "
        f"episode must NOT be over-filtered; merged={pointers}"
    )
    # RN-2 ordering preserved: strongest corpus head, then the rescued episode.
    assert pointers[0] == "c-big"
    assert pointers[1] == "ep-fresh"


def test_AC_FBM_FLOOR_1_above_floor_episodes_all_survive() -> None:
    """When EVERY episode clears the floor, none is dropped (the floor only ever
    removes noise, never a relevant match)."""
    corpus = [_corpus_hit("c0", 20.0)]
    episodes = [_episode_hit(f"ep{i}", 5.0 + i) for i in range(3)]
    merged = _merge_by_score(corpus, episodes, top_n=5)
    pointers = [h["pointer"] for h in merged]
    for i in range(3):
        assert f"ep{i}" in pointers, f"above-floor episode ep{i} must survive"
