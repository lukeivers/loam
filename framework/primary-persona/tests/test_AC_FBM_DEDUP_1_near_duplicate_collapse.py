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

"""AC-FBM-DEDUP-1 (Slice B / B2) — near-duplicate collapse.

When two retrieved hits share more than ``DEDUP_JACCARD_THRESHOLD`` (0.85)
token-set Jaccard, only one occupies a top-N slot and the freed slot is filled
by the next DISTINCT hit downstream. Distinct hits are never collapsed (the
conservative side — over-collapsing distinct context is the named risk).
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.retrieval import (
    DEDUP_JACCARD_THRESHOLD,
    _is_near_duplicate,
    _merge_by_score,
)


def _corpus_hit(title: str, pointer: str, score: float) -> dict:
    return {"path": f"/x/{title}.md", "title": title, "pointer": pointer, "score": score}


def _episode_hit(pointer: str, score: float) -> dict:
    return {"pointer": pointer, "score": score, "_episode": True}


def test_AC_FBM_DEDUP_1_jaccard_threshold_semantics() -> None:
    """The Jaccard helper fires only ABOVE the threshold; an identical set is a
    duplicate, a half-overlapping set is not, and two empty sets are not."""
    a = frozenset({"alpha", "beta", "gamma", "delta", "epsilon"})
    # Identical -> Jaccard 1.0 > 0.85 -> duplicate.
    assert _is_near_duplicate(a, a, threshold=DEDUP_JACCARD_THRESHOLD)
    # 3/5 overlap on the union of 7 -> Jaccard ~0.43 -> NOT a duplicate.
    b = frozenset({"alpha", "beta", "gamma", "zeta", "eta"})
    assert not _is_near_duplicate(a, b, threshold=DEDUP_JACCARD_THRESHOLD)
    # Two empty token-sets are not duplicates (fail toward keeping distinct).
    assert not _is_near_duplicate(
        frozenset(), frozenset(), threshold=DEDUP_JACCARD_THRESHOLD
    )


def test_AC_FBM_DEDUP_1_near_dup_pair_collapses_freed_slot_filled() -> None:
    """Two near-identical episodes collapse to ONE top-N slot; a third DISTINCT
    hit that would otherwise have been below the top-N cut now appears in the
    freed slot."""
    # A shared near-identical opening (>0.85 Jaccard) on two episodes, plus a
    # distinct third episode. top_n=2 forces the freed-slot behaviour: without
    # dedup the two near-dups would take both slots and the distinct hit would
    # be cut. The shared opening is long (the real-store near-dups share a
    # multi-sentence opening) so a single trailing-word difference clears 0.85.
    shared = (
        "we confirmed the litrpg canon store is the established source of "
        "narrative truth for every production pipeline chapter continuity check "
        "before the editor sweep today"
    )
    near_dup_a = shared + " exactly"
    near_dup_b = shared + " precisely"
    distinct = "the chapter loop policy retries on a continuity regression"
    episodes = [
        _episode_hit(near_dup_a, 10.0),
        _episode_hit(near_dup_b, 9.0),
        _episode_hit(distinct, 8.0),
    ]
    merged = _merge_by_score([], episodes, top_n=2)
    pointers = [h["pointer"] for h in merged]
    # Exactly one of the near-dup pair occupies a slot.
    n_neardup = sum(1 for p in pointers if p in (near_dup_a, near_dup_b))
    assert n_neardup == 1, f"near-dup pair must collapse to one slot; got {pointers}"
    # The higher-scored member is the one kept.
    assert near_dup_a in pointers, "the higher-ranked near-dup member is kept"
    # The freed slot is filled by the next distinct hit.
    assert distinct in pointers, (
        f"the distinct hit must fill the freed slot; got {pointers}"
    )


def test_AC_FBM_DEDUP_1_distinct_hits_never_collapsed() -> None:
    """Two genuinely-distinct hits that merely share some vocabulary (Jaccard
    well below 0.85) are BOTH kept — the conservative no-over-collapse property."""
    episodes = [
        _episode_hit("the litrpg canon store source of truth for chapters", 10.0),
        _episode_hit("the telegram outage self-heal direct-send curl recipe", 9.0),
    ]
    merged = _merge_by_score([], episodes, top_n=5)
    pointers = [h["pointer"] for h in merged]
    assert len(pointers) == 2, f"distinct hits must not collapse; got {pointers}"
