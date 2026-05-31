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

"""AC-FBM-W-2 (FLOOR / SAFETY — load-bearing) — a ``pinned`` rule co-surfaces
in the retrieved set even at ~0 relevance, against a hyper-relevant episode;
it does NOT drop.

This is the property a MULTIPLIER ALONE cannot deliver. The same test proves
that: a multiplier-only variant of the scenario (the pinned rule given even the
MAXIMUM weight but NOT pinned) DOES drop out of top_n under the flood of
hyper-relevant hits, while the pinned (force-included) rule survives. The floor
is a hard force-include ahead of the relevance cut, not a big boost.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.corpus_index import WEIGHT_MAX
from loam.primary_persona.keep_pace.retrieval import _merge_by_score


def _corpus_hit(title: str, score: float, *, weight: int, pinned: bool) -> dict:
    return {
        "path": f"/x/{title}.md",
        "title": title,
        "pointer": title,
        "score": score,
        "weight": weight,
        "pinned": pinned,
    }


def _episode_hit(pointer: str, score: float) -> dict:
    return {"pointer": pointer, "score": score, "_episode": True}


def _scenario(*, pinned: bool):
    """The shared scenario: one critical rule at ~0 NORMALIZED relevance + a
    flood of hyper-relevant episodes + stronger corpus hits that, together,
    fill top_n on their own.

    The critical rule is the WEAKEST of several matched corpus hits, so
    per-source min-max normalization maps it to ~0.0 (the genuine ~0-relevance
    regime — a lone corpus hit would normalize to 1.0 and never test the floor;
    that is the subtlety this scenario captures). ``pinned`` toggles the floor
    on/off; with pinned=False the rule is given the MAXIMUM weight (the
    strongest a pure multiplier can do)."""
    critical = _corpus_hit(
        "critical-rule",
        0.0,  # weakest of the corpus hits => normalizes to 0.0 (~0 relevance)
        weight=WEIGHT_MAX,  # the most a multiplier alone could ever apply
        pinned=pinned,
    )
    # Stronger corpus hits so the critical rule is the min of its source
    # (normalizes to 0.0). These are NOT pinned and NOT weighted up.
    strong_corpus = [
        _corpus_hit(f"strong-c{i}", 200.0 - i * 10, weight=50, pinned=False)
        for i in range(3)
    ]
    # Hyper-relevant episodes — high relevance so a boosted-~0 rule cannot
    # compete on score, filling the remaining slots.
    episodes = [_episode_hit(f"hot-ep-{i}", 40.0 - i) for i in range(5)]
    return critical, strong_corpus, episodes


def test_AC_FBM_W_2_pinned_rule_survives_hyperrelevant_flood() -> None:
    """The pinned critical rule co-surfaces despite ~0 relevance against a
    top_n-filling flood of hyper-relevant episodes + stronger corpus hits."""
    critical, strong_corpus, episodes = _scenario(pinned=True)
    merged = _merge_by_score([critical] + strong_corpus, episodes, top_n=5)
    titles = [h.get("title") or h.get("pointer") for h in merged]
    assert "critical-rule" in titles, (
        "a pinned (hard-floor) rule must survive against a hyper-relevant "
        f"episode flood; got {titles}"
    )
    # Force-include places it at the FRONT, ahead of the relevance cut.
    assert merged[0].get("title") == "critical-rule"


def test_AC_FBM_W_2_multiplier_alone_drops_the_rule() -> None:
    """The demonstration the floor is necessary: the SAME rule at the MAXIMUM
    weight but NOT pinned DOES drop out of top_n — a multiplier cannot rescue
    a ~0-NORMALIZED-relevance rule (weight x ~0 ~= 0)."""
    critical, strong_corpus, episodes = _scenario(pinned=False)
    merged = _merge_by_score([critical] + strong_corpus, episodes, top_n=5)
    titles = [h.get("title") or h.get("pointer") for h in merged]
    assert "critical-rule" not in titles, (
        "the multiplier-only variant must DROP the ~0-relevance rule — this "
        "is exactly why the hard floor (force-include) is required, not a "
        f"big multiplier; got {titles}"
    )
    # The slots are taken by stronger corpus hits + hyper-relevant episodes;
    # the un-pinned ~0-normalized critical rule is squeezed out.
    assert len(merged) == 5
