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

"""AC.WMS7.LIVE.1 (OUTCOME-ALTITUDE, ``outcome-altitude:true``) — a REAL
work-item store with a REAL transition history → the live
``render_analytics_block`` production entry point produces all three
correct, plain-language, actionable insights through the live event log +
projection, with NO pre-arranged analytics/insight state and NO mocks at
the store/event-log boundary.

Plan §6 AC.WMS7.LIVE.1. Against a REAL objective-tracker store carrying a
REAL transition history — items created at different times, some advanced
to done, some left stalled, some blocked/waiting past the threshold,
intake outpacing completion in the window — invoking the live
``render_analytics_block`` renders:

  (a) a correct PILE-UP insight naming the genuinely-most-accumulated group
      with its plain-language reason (count + how long it's sat);
  (b) a correct STUCK insight naming the chronically-waiting item with what
      it waits on;
  (c) a correct COMPLETION-vs-INTAKE sentence derived over the event-log
      history in the window —

all plain-language, char-capped, zero internal vocabulary, with NO per-turn
registration. The store is REAL (its OWN API seeds it); only the reference
clock is injected (the method-default calibration seam, NOT a store mock) —
so the staleness/window thresholds bite against the real, recently-stamped
history.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.analytics import render_analytics_block

from _wms4_store import EDGE, fresh_factory, live_store, make_open

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import (
    ObjectiveSpec,
    ProseCriterion,
    TimeBound,
)


async def _make_open_in_project(
    tracker: ObjectiveTracker, goal: str, project: str
):
    """Create + start a real open item bound to a project (the pile-up
    grouping reads ``belongs_to_project`` off the live projection)."""
    spec = ObjectiveSpec(
        goal=goal,
        acceptance_criteria=(ProseCriterion(criterion_id="c1", prose="done"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
        belongs_to_project=project,
    )
    p = await tracker.create(spec)
    await tracker.start(p.objective_id)
    return p


async def test_AC_WMS7_LIVE_1_three_insights_live_no_pre_arranged_state(tmp_path) -> None:
    db = tmp_path / "objectives.db"

    # ---- Build a REAL store through its OWN API. NO pre-arranged
    # analytics / insight / ranking state. ----------------------------
    setup = live_store(db)
    try:
        # Money: FOUR open items, left stalled (the genuine pile-up group).
        for i in range(4):
            await _make_open_in_project(setup, f"money task {i}", "money-independence")
        # Personal: one open item (not a pile-up).
        await _make_open_in_project(setup, "fix the porch", "personal-home")

        # A chronically-waiting item: waits on an external party (Eric).
        launch = await make_open(setup, "the product launch")
        await setup.record_edge(
            launch.objective_id, edge_kind=EDGE.waits_on, party="Eric"
        )

        # Intake outpacing completion in the window: several captured, one
        # finished — all stamped at real "now" by the store.
        a = await make_open(setup, "captured and shipped")
        await setup.mark_achieved(a.objective_id, evidence="done")
        await make_open(setup, "another captured idea")
        await make_open(setup, "yet another captured idea")
    finally:
        setup.close()

    # The store stamped every transition at real "now". Evaluate analytics
    # against a reference clock 20 days AHEAD so the staleness (14d) +
    # chronic (7d) thresholds bite on the genuinely-older items — the store
    # + event log are REAL (no mocks at that boundary); only the clock is a
    # method-default parameter (the calibration seam).
    ref_now = datetime.now(timezone.utc) + timedelta(days=20)

    # The whole real history is one cohort stamped ~20 days before ref_now.
    # The 14-day staleness floor flags it as stalled/chronic; a 30-day
    # balance window (a calibratable method-default, D-ANL.6) captures the
    # same cohort's intake/completion — so all three insights derive over
    # the one REAL history through the live entry point.
    factory = fresh_factory(db)
    block = render_analytics_block(
        tracker_factory=factory, now=ref_now, window_days=30
    )

    assert block, f"analytics must render live; block={block!r}"

    # (a) PILE-UP — money is the genuinely-most-accumulated group, named in
    # plain language with its count + supporting age phrase.
    assert "money independence" in block, f"pile-up group must be named; {block!r}"
    assert "4 open items" in block, f"pile-up count must be named; {block!r}"
    assert "personal" not in block.lower(), (
        "the one-item group must NOT be flagged as a pile-up"
    )

    # (b) STUCK — the chronically-waiting launch, named with its party.
    assert "the product launch" in block, f"stuck item must be named; {block!r}"
    assert "Eric" in block, f"the stuck item's blocker must be named; {block!r}"

    # (c) BALANCE — capture-vs-finish over the window, derived over the
    # event-log history (the window is anchored on the reference clock; the
    # real events fall within it because we created them 20 days "before"
    # ref_now). Several captured, one finished.
    assert re.search(r"captured \d+", block.lower()), (
        f"balance sentence must name the capture count; {block!r}"
    )
    assert "finished" in block.lower(), f"balance must name finishes; {block!r}"

    # Plain-language + char-capped + zero internal vocabulary.
    assert len(block) <= 700, f"block must be capped; len={len(block)}"
    assert "obj-" not in block
    for token in ("belongs_to_project", "status_transitioned", "objective_created",
                  "waits_on", "last_transition_at", "money-independence"):
        assert token not in block, f"internal token leaked live: {token!r}"


async def test_AC_WMS7_LIVE_1_honest_empty_on_quiet_store(tmp_path) -> None:
    # A real store with a single fresh item + nothing stalled/stuck/finished:
    # the live entry point produces NO fabricated insight (honest-empty).
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        await make_open(setup, "one fresh thing")
    finally:
        setup.close()

    # Reference clock = real now (the item is fresh; nothing is chronic, no
    # pile-up). Balance WILL see one capture in the window — that is honest
    # (real activity), but there is no pile-up and nothing stuck.
    factory = fresh_factory(db)
    block = render_analytics_block(tracker_factory=factory)
    # The only honest signal is the single capture; no fabricated pile-up or
    # stuck line.
    assert "piling up" not in block.lower(), "no pile-up must be fabricated"
    assert "waiting" not in block.lower(), "nothing is chronically waiting"
