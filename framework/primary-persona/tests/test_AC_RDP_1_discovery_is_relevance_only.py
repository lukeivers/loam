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

"""AC.RDP.1 — discovery is relevance-only (the locked invariant).

Memory redesign S2 (design Stage 3). Whether a record ENTERS the
discovered set is decided by topical relevance (the raw BM25 relevance)
ALONE; neither event-time nor injection-history changes set MEMBERSHIP.

Outcome (plan §4 AC.RDP.1): a strongly-relevant OLD record + a
weakly-relevant RECENT record — the strongly-relevant one is discovered,
the weakly-relevant one is not — and the discovered SET is invariant to
swapping their event-times. This locks the "discovery is relevance-only"
guarantee so a future change cannot re-wire event-recency into discovery.

Method-in-AC test: PASS — the AC pins the outcome (membership decided by
relevance, invariant to event-time), not the scoring curve.
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


def _members(merged: list[dict]) -> set[str]:
    return {h["pointer"] for h in merged}


def test_AC_RDP_1_strong_old_discovered_weak_recent_not() -> None:
    """A strongly-relevant OLD episode is discovered; a weakly-relevant
    RECENT episode (below the relevance threshold) is not."""
    episodes = [
        _episode_hit("strong-old", 5.0, event_days_ago=40),
        _episode_hit("weak-recent", RELEVANCE_THRESHOLD / 5.0, event_days_ago=0),
    ]
    merged = _merge_by_score([], episodes, top_n=5, now=_NOW)
    members = _members(merged)
    assert "strong-old" in members, (
        "a strongly-relevant record must be discovered regardless of age; "
        f"members={members}"
    )
    assert "weak-recent" not in members, (
        "a weakly-relevant (below-threshold) record must NOT be discovered "
        f"even when it is the most recent; members={members}"
    )


def test_AC_RDP_1_membership_invariant_to_event_time_swap() -> None:
    """Swapping the two records' event-times does not change WHICH records
    are discovered — event-time is not a discovery signal."""
    base = [
        _episode_hit("A-strong", 5.0, event_days_ago=40),
        _episode_hit("B-weak", RELEVANCE_THRESHOLD / 5.0, event_days_ago=0),
    ]
    swapped = [
        _episode_hit("A-strong", 5.0, event_days_ago=0),
        _episode_hit("B-weak", RELEVANCE_THRESHOLD / 5.0, event_days_ago=40),
    ]
    base_members = _members(_merge_by_score([], base, top_n=5, now=_NOW))
    swapped_members = _members(_merge_by_score([], swapped, top_n=5, now=_NOW))
    assert base_members == swapped_members == {"A-strong"}, (
        "discovered-set membership must be invariant to event-time; "
        f"base={base_members} swapped={swapped_members}"
    )
