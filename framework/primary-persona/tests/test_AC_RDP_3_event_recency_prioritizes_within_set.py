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

"""AC.RDP.3 — event-recency prioritizes WITHIN the discovered set.

Memory redesign S2 (design Stage 3). Among records that BOTH clear the
relevance threshold, the newer-by-EVENT-TIME is ordered ahead when
relevance is comparable (the owner's supersession example: the newest
"project complete" ahead of the oldest "project incomplete"). The
re-order is a BOUNDED re-weight over the already-discovered set — it can
NEVER promote a below-threshold record into the surfaced set.

Method-in-AC test: PASS — the AC pins the outcome (newer-first on
comparable relevance; a below-threshold near-miss stays out regardless
of recency), not the decay curve or the weight value.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.retrieval import (
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


def test_AC_RDP_3_newer_event_time_ordered_ahead_on_comparable_relevance() -> None:
    """Two equally-relevant discovered records of different event-age →
    the newer-by-event-time is ordered ahead (owner's project
    complete/incomplete example)."""
    episodes = [
        # Equal relevance; the "incomplete" record is OLDER, the "complete"
        # record is NEWER. Arrival order deliberately puts the OLDER first so
        # the assertion proves recency re-orders (not merely arrival order).
        _episode_hit("project-incomplete", 5.0, event_days_ago=40),
        _episode_hit("project-complete", 5.0, event_days_ago=1),
    ]
    merged = _merge_by_score([], episodes, top_n=5, now=_NOW)
    pointers = [h["pointer"] for h in merged]
    assert pointers == ["project-complete", "project-incomplete"], (
        "the newer-by-event-time record must be prioritized ahead of the "
        f"older one when relevance is comparable; got {pointers}"
    )


def test_AC_RDP_3_recency_never_resurrects_below_threshold_near_miss() -> None:
    """A below-threshold near-miss stays OUT of the surfaced set regardless
    of its recency — recency re-weights the discovered set, it does not
    determine membership."""
    episodes = [
        _episode_hit("relevant-old", 5.0, event_days_ago=40),
        # The near-miss is the NEWEST record but below the relevance
        # threshold — recency must not pull it into the set.
        _episode_hit("near-miss-newest", RELEVANCE_THRESHOLD / 5.0, event_days_ago=0),
    ]
    merged = _merge_by_score([], episodes, top_n=5, now=_NOW)
    pointers = [h["pointer"] for h in merged]
    assert "near-miss-newest" not in pointers, (
        "recency must NEVER resurrect a below-threshold record into the "
        f"surfaced set; got {pointers}"
    )
    assert pointers == ["relevant-old"]


def test_AC_RDP_3_reweight_is_bounded_cannot_leapfrog_much_stronger() -> None:
    """The recency re-weight is BOUNDED: a much-stronger-relevance older
    record is NOT leapfrogged by a much-weaker-but-newer one (recency
    reorders within comparable relevance, it does not override relevance)."""
    # Three episodes so per-source min-max spreads the two competitors onto
    # DISTINCT positive normalized scores (a 2-element source would zero the
    # loser and hide whether the recency bound — not min-max — does the work).
    # much-stronger-old normalizes to 1.0, much-weaker-new to ~0.56; the
    # bounded recency factor (>= 1 - weight) cannot close a >1.4x relevance gap.
    episodes = [
        _episode_hit("much-stronger-old", 10.0, event_days_ago=40),
        _episode_hit("much-weaker-new", 6.0, event_days_ago=0),
        _episode_hit("floor-filler", 1.0, event_days_ago=10),
    ]
    merged = _merge_by_score([], episodes, top_n=5, now=_NOW)
    pointers = [h["pointer"] for h in merged]
    assert pointers[0] == "much-stronger-old", (
        "a bounded recency re-weight must not let a much-weaker-but-newer "
        f"record leapfrog a much-stronger older one; got {pointers}"
    )
