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

"""AC.RDP.5 — reversible via named levers.

Memory redesign S2 (design Stage 3). The relevance threshold, the
recency-prioritizer weight, and the count cap are NAMED tunable
constants; restoring their LEGACY (no-op) values reproduces the
pre-stage ranking byte-for-byte on a fixture the suites already cover.
This is the live-recall-behavior change's reversibility guarantee: a
single lever flip restores the prior surface.

Legacy no-op values:
  - relevance_threshold = EPISODE_MIN_RELEVANCE_SCORE  (the pre-stage
    noise floor — nothing is gated ABOVE the floor, so the set-determiner
    reverts to the count cap).
  - recency_weight = 0.0  (the recency factor is a constant 1.0 — no
    re-order; ordering reverts to the pure boosted-score order).
  - count cap = DEFAULT_TOP_N  (unchanged).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.retrieval import (
    DEFAULT_TOP_N,
    EPISODE_MIN_RELEVANCE_SCORE,
    RELEVANCE_THRESHOLD,
    _merge_by_score,
)

_NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _episode_hit(pointer: str, score: float, *, event_days_ago: float) -> dict:
    return {
        "pointer": pointer,
        "score": score,
        "_episode": True,
        "_event_time": (_NOW - timedelta(days=event_days_ago)).isoformat(),
    }


def _order(merged: list[dict]) -> list[str]:
    return [h["pointer"] for h in merged]


def test_AC_RDP_5_legacy_threshold_reproduces_pre_stage_set() -> None:
    """With the threshold lever at its legacy no-op value, a below-current-
    threshold record is RETAINED (pre-stage behaviour) — the new-behaviour
    default would have gated it out."""
    # A record between the noise floor and the current threshold, plus a
    # strong record so the regime is populated.
    below = EPISODE_MIN_RELEVANCE_SCORE + (RELEVANCE_THRESHOLD - EPISODE_MIN_RELEVANCE_SCORE) * 0.5
    episodes = [
        _episode_hit("strong", 5.0, event_days_ago=1),
        _episode_hit("below-threshold", below, event_days_ago=1),
    ]

    # NEW default levers: the below-threshold record is gated out.
    new_order = _order(_merge_by_score([], [dict(h) for h in episodes], top_n=DEFAULT_TOP_N, now=_NOW))
    assert "below-threshold" not in new_order, (
        f"the new default threshold must gate the below-threshold record; got {new_order}"
    )

    # LEGACY levers: the same record is retained (pre-stage set restored).
    legacy_order = _order(
        _merge_by_score(
            [],
            [dict(h) for h in episodes],
            top_n=DEFAULT_TOP_N,
            relevance_threshold=EPISODE_MIN_RELEVANCE_SCORE,
            recency_weight=0.0,
            now=_NOW,
        )
    )
    assert legacy_order == ["strong", "below-threshold"], (
        "legacy lever values must reproduce the pre-stage set + pure "
        f"boosted-score order; got {legacy_order}"
    )


def test_AC_RDP_5_legacy_recency_weight_reproduces_pre_stage_order() -> None:
    """With the recency-weight lever at 0.0, two equally-relevant records of
    different event-age keep the pre-stage order (arrival / boosted), with
    NO recency re-ordering."""
    episodes = [
        _episode_hit("older-first-arrival", 5.0, event_days_ago=40),
        _episode_hit("newer-second-arrival", 5.0, event_days_ago=1),
    ]

    # NEW default: recency re-orders the newer ahead.
    new_order = _order(_merge_by_score([], [dict(h) for h in episodes], top_n=DEFAULT_TOP_N, now=_NOW))
    assert new_order[0] == "newer-second-arrival", (
        f"the new default recency weight must re-order the newer ahead; got {new_order}"
    )

    # LEGACY weight 0.0: no recency re-order; equal-relevance ties keep
    # arrival order (the pre-stage stable sort).
    legacy_order = _order(
        _merge_by_score(
            [],
            [dict(h) for h in episodes],
            top_n=DEFAULT_TOP_N,
            relevance_threshold=EPISODE_MIN_RELEVANCE_SCORE,
            recency_weight=0.0,
            now=_NOW,
        )
    )
    assert legacy_order == ["older-first-arrival", "newer-second-arrival"], (
        "legacy recency weight must reproduce the pre-stage stable arrival "
        f"order; got {legacy_order}"
    )
