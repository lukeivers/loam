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

"""AC.RDP.4 — injection-history is never a ranking signal (structural).

Memory redesign S2 (design Stage 3). No signal derived from how recently
or how often a record was previously INJECTED participates in discovery
or prioritization. Injecting a record on turn N does not raise its
discovery membership or its prioritization rank on turn N+1, holding
relevance + event-time fixed.

This locks the design's headline worry (injection-frequency self-
reinforcement) out structurally: the prioritizer keys on EVENT time
(valid_at / reference_time) only, and the merge carries no state between
calls.

Method-in-AC test: PASS — the AC pins the outcome (rank invariant to
prior injection, holding relevance + event-time fixed), not the mechanism.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.retrieval import _merge_by_score

_NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _episode_hit(pointer: str, score: float, *, event_days_ago: float) -> dict:
    return {
        "pointer": pointer,
        "score": score,
        "_episode": True,
        "_event_time": (_NOW - timedelta(days=event_days_ago)).isoformat(),
    }


def test_AC_RDP_4_repeated_merge_is_identical_no_carried_state() -> None:
    """Re-running the merge on identical inputs (turn N then turn N+1)
    yields an identical ordered set — the ranker carries no cross-turn
    state (no injection-history accumulation)."""
    episodes = [
        _episode_hit("rec-a", 5.0, event_days_ago=10),
        _episode_hit("rec-b", 4.0, event_days_ago=3),
        _episode_hit("rec-c", 3.0, event_days_ago=20),
    ]
    turn_n = [h["pointer"] for h in _merge_by_score([], list(episodes), top_n=5, now=_NOW)]
    turn_n_plus_1 = [
        h["pointer"] for h in _merge_by_score([], list(episodes), top_n=5, now=_NOW)
    ]
    assert turn_n == turn_n_plus_1, (
        "the ranking must be invariant across turns for identical inputs — no "
        f"injection-history may accumulate; N={turn_n} N+1={turn_n_plus_1}"
    )


def test_AC_RDP_4_prior_injection_marker_does_not_change_rank() -> None:
    """A record carrying an injection-history-shaped marker (as if it were
    injected last turn) ranks identically to the same record without it,
    holding relevance + event-time fixed — injection-history is ignored."""
    baseline = [
        _episode_hit("subject", 4.0, event_days_ago=10),
        _episode_hit("competitor", 4.0, event_days_ago=10),
    ]
    # Same two records, but "subject" now carries injection-history-shaped
    # fields (as a previously-injected record would). Relevance + event-time
    # are unchanged.
    with_history = [
        {
            **_episode_hit("subject", 4.0, event_days_ago=10),
            "_injected_count": 99,
            "_last_injected": _NOW.isoformat(),
            "activation": 5.0,
        },
        _episode_hit("competitor", 4.0, event_days_ago=10),
    ]
    base_order = [h["pointer"] for h in _merge_by_score([], baseline, top_n=5, now=_NOW)]
    hist_order = [h["pointer"] for h in _merge_by_score([], with_history, top_n=5, now=_NOW)]
    assert base_order == hist_order, (
        "an injection-history marker must not change the ranking; "
        f"base={base_order} with_history={hist_order}"
    )
