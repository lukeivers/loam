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

"""AC.ANL.PILEUP.1/.2/.3 — insight 1: where work is piling up / stalling.

Plan §6 AC.ANL.PILEUP.*:
  - .1 the most-accumulated group is correctly identified + named with the
    open count;
  - .2 the insight is TRANSPARENT — names WHY (count + how long it's sat,
    the supporting cycle-time phrase), never a bare score;
  - .3 an evenly-spread / nothing-stalled set produces NO fabricated
    hottest group (honest-empty).

Pure derivation over duck-typed projection items (the grouping +
staleness read off ``belongs_to_project`` / ``last_transition_at``).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.analytics import compute_pileup

from _wms4_store import make_item

_NOW = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


def _stale(days: int) -> str:
    return (_NOW - timedelta(days=days)).isoformat()


def test_AC_ANL_PILEUP_1_hottest_group_named_with_count() -> None:
    # Money holds five stalled open items; Personal holds one. Money is the
    # genuine pile-up.
    items = [
        make_item(f"m{i}", goal=f"money task {i}", belongs_to_project="money-independence",
                  status="active", last_transition_at=_stale(20))
        for i in range(5)
    ] + [
        make_item("p1", goal="personal task", belongs_to_project="personal-home",
                  status="active", last_transition_at=_stale(2)),
    ]
    result = compute_pileup(items, now=_NOW)
    assert result is not None, "the genuine pile-up must be identified"
    # Named in PLAIN language (slug de-slugged) with the open count.
    assert result.group == "money independence"
    assert result.open_count == 5


def test_AC_ANL_PILEUP_2_transparent_reason_with_supporting_age() -> None:
    items = [
        make_item(f"m{i}", goal=f"money task {i}", belongs_to_project="money",
                  status="active", last_transition_at=_stale(15))
        for i in range(4)
    ]
    result = compute_pileup(items, now=_NOW)
    assert result is not None
    sentence = result.sentence()
    # Transparent: names the count AND how long it's sat (the supporting
    # cycle-time phrase, D-ANL.5) — never a bare number/score.
    assert "4 open items" in sentence
    assert "hasn't moved" in sentence
    assert "week" in sentence  # ~15 days -> "about two weeks"
    # No black-box score / internal token in the reason.
    assert "score" not in sentence.lower()


def test_AC_ANL_PILEUP_3_even_spread_no_fabricated_hotspot() -> None:
    # Work spread evenly across groups, nothing stalled (all touched today).
    items = [
        make_item("a1", goal="a", belongs_to_project="alpha", status="active",
                  last_transition_at=_NOW.isoformat()),
        make_item("b1", goal="b", belongs_to_project="beta", status="active",
                  last_transition_at=_NOW.isoformat()),
        make_item("c1", goal="c", belongs_to_project="gamma", status="active",
                  last_transition_at=_NOW.isoformat()),
    ]
    assert compute_pileup(items, now=_NOW) is None, (
        "no group has enough accumulation/staleness — must not fabricate a hotspot"
    )


def test_AC_ANL_PILEUP_3_accumulated_but_fresh_is_not_a_pileup() -> None:
    # A group with many open items but ALL recently touched is NOT stalling
    # — pile-up requires both accumulation AND staleness.
    items = [
        make_item(f"m{i}", goal=f"t{i}", belongs_to_project="money", status="active",
                  last_transition_at=_NOW.isoformat())
        for i in range(6)
    ]
    assert compute_pileup(items, now=_NOW) is None, (
        "a freshly-moving group is not a stall, even when large"
    )
