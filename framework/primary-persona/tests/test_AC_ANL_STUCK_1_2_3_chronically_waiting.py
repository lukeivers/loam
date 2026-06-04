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

"""AC.ANL.STUCK.1/.2/.3 — insight 2: chronically blocked / waiting items.

Plan §6 AC.ANL.STUCK.*:
  - .1 items blocked / externally-waiting PAST the threshold surface, named
    with what they wait on, in plain language;
  - .2 items blocked/waiting BELOW the threshold do NOT surface (chronic-
    not-all — the forgotten-waiting nudge, not a dump);
  - .3 nothing chronically stuck -> honest empty.

Pure derivation over duck-typed projection items (status + waits_on edge +
last_transition_at).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.analytics import compute_stuck

from _wms4_store import make_item

_NOW = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


def _aged(days: int) -> str:
    return (_NOW - timedelta(days=days)).isoformat()


def test_AC_ANL_STUCK_1_external_wait_named_with_party() -> None:
    items = [
        make_item("launch", goal="the launch", status="active",
                  last_transition_at=_aged(9),
                  edges_out=[("waits_on", None, "Eric")]),
    ]
    stuck = compute_stuck(items, now=_NOW)
    assert len(stuck) == 1
    phrase = stuck[0].phrase()
    assert "the launch" in phrase
    assert "Eric" in phrase  # named with what it waits on
    assert "waiting" in phrase


def test_AC_ANL_STUCK_1_blocked_status_past_threshold_surfaces() -> None:
    items = [
        make_item("b", goal="the blocked thing", status="blocked",
                  last_transition_at=_aged(30)),
    ]
    stuck = compute_stuck(items, now=_NOW)
    assert len(stuck) == 1
    assert "the blocked thing" in stuck[0].phrase()


def test_AC_ANL_STUCK_2_recent_block_below_threshold_excluded() -> None:
    # Blocked / waiting but only 2 days — normal, NOT chronic. Must not
    # surface (AC.ANL.STUCK.2).
    items = [
        make_item("recent_block", goal="just got blocked", status="blocked",
                  last_transition_at=_aged(2)),
        make_item("recent_wait", goal="just started waiting", status="active",
                  last_transition_at=_aged(1),
                  edges_out=[("waits_on", None, "Sam")]),
    ]
    assert compute_stuck(items, now=_NOW) == [], (
        "recently-blocked/waiting items are normal and must not surface"
    )


def test_AC_ANL_STUCK_2_chronic_only_mixed_set() -> None:
    items = [
        make_item("chronic", goal="the chronic one", status="blocked",
                  last_transition_at=_aged(20)),
        make_item("recent", goal="the recent one", status="blocked",
                  last_transition_at=_aged(1)),
    ]
    stuck = compute_stuck(items, now=_NOW)
    goals = [s.goal for s in stuck]
    assert "the chronic one" in goals
    assert "the recent one" not in goals


def test_AC_ANL_STUCK_3_nothing_chronic_is_honest_empty() -> None:
    items = [
        make_item("ok", goal="moving along", status="active",
                  last_transition_at=_aged(1)),
    ]
    assert compute_stuck(items, now=_NOW) == []
