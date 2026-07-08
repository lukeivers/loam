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

"""AC.RDP.2 — relevance-threshold recall, empty-OK.

Memory redesign S2 (design Stage 3). The discovered set is the records
AT/ABOVE a NAMED absolute relevance threshold, not a padded fixed count:
one relevant record surfaces one (never padded toward the count cap);
zero relevant surfaces empty (not a forced top-1).

The named default threshold is a CONSERVATIVE, deliberately-loose value
just above today's noise floor (owner ruling): tunable offline against
the standing telemetry, never a hot-path LLM.

Method-in-AC test: PASS — the AC pins the outcome (set = records above a
threshold; empty when none clears it), not the threshold value.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loam.primary_persona.keep_pace.retrieval import (
    EPISODE_MIN_RELEVANCE_SCORE,
    RELEVANCE_THRESHOLD,
    _merge_by_score,
)

_NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _episode_hit(pointer: str, score: float) -> dict:
    return {"pointer": pointer, "score": score, "_episode": True}


def test_AC_RDP_2_default_threshold_is_conservative_above_noise_floor() -> None:
    """The named default threshold is above the pure-noise floor (a real
    relevance gate) yet stays conservative (loose start; the owner's
    over-tighten asymmetry)."""
    assert RELEVANCE_THRESHOLD > EPISODE_MIN_RELEVANCE_SCORE, (
        "the relevance threshold must sit ABOVE the pure-noise floor so it is "
        "a relevance gate, not the noise floor"
    )
    # Loose: a genuine multi-term episode match scores multiple units on this
    # raw scale (verified against the live store ~2.9-5.2), so a conservative
    # default stays well below the genuine-match band.
    assert RELEVANCE_THRESHOLD <= 1.0, (
        "the day-one default must start LOOSE (well below the genuine-match "
        "band) so it cannot silently hide a relevant memory before offline tuning"
    )


def test_AC_RDP_2_one_relevant_surfaces_one_not_padded() -> None:
    """A single above-threshold record surfaces exactly one — not padded up
    toward the count cap with below-threshold near-misses."""
    episodes = [
        _episode_hit("the-relevant-one", 5.0),
        _episode_hit("near-miss-1", RELEVANCE_THRESHOLD / 2.0),
        _episode_hit("near-miss-2", RELEVANCE_THRESHOLD / 3.0),
        _episode_hit("near-miss-3", RELEVANCE_THRESHOLD / 4.0),
    ]
    merged = _merge_by_score([], episodes, top_n=5, now=_NOW)
    pointers = [h["pointer"] for h in merged]
    assert pointers == ["the-relevant-one"], (
        "exactly the one above-threshold record must surface, not a padded "
        f"top-N of near-misses; got {pointers}"
    )


def test_AC_RDP_2_zero_relevant_surfaces_empty() -> None:
    """When every matched record is below the threshold (but above the pure-
    noise floor — the populated regime), the discovered set is EMPTY, not a
    forced top-1."""
    # Both weak hits sit strictly BETWEEN the pure-noise floor and the
    # threshold, so the regime is "populated" (the threshold engages) yet
    # nothing clears the relevance bar — the empty-OK path. Values derived
    # from the levers so the test survives an offline threshold retune.
    _span = RELEVANCE_THRESHOLD - EPISODE_MIN_RELEVANCE_SCORE
    episodes = [
        _episode_hit("weak-a", EPISODE_MIN_RELEVANCE_SCORE + _span * 0.5),
        _episode_hit("weak-b", EPISODE_MIN_RELEVANCE_SCORE + _span * 0.25),
    ]
    # No corpus hit either → nothing relevant at all.
    merged = _merge_by_score([], episodes, top_n=5, now=_NOW)
    assert merged == [], (
        "zero above-threshold records must surface an EMPTY set, never a "
        f"forced top-1; got {[h['pointer'] for h in merged]}"
    )
