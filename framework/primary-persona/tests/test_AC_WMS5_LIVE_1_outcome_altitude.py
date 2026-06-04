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

"""AC.WMS5.LIVE.1 (OUTCOME-ALTITUDE, ``outcome-altitude:true``) — a REAL
store with no pre-arranged state → all three lenses render the right view
through the live production entry points, and waiting-on is produced by
the SAME shared helper relational calls.

Plan §6 AC.WMS5.LIVE.1. Against a REAL objective-tracker store carrying a
REAL set of work items (a dependency chain, items laddering to real
objectives, an ``owner_pending`` item, an external-party wait) with NO
pre-arranged lens / ladder / ranking state, invoking each of the three
lenses' LIVE production entry points renders the correct view:

  - goals: ladders the right work under the right objective AND names a
    no-work goal;
  - on-my-plate: surfaces the right top item with prioritize's reason and
    EXCLUDES the blocked + waiting-on-others items;
  - waiting-on: splits on-me vs on-others — produced by the SAME shared
    ``compute_waiting_split`` helper ``relational.py`` calls.

Exercised through the real entry points, no mocks at the store boundary.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.goals import render_goals_block
from loam.primary_persona.keep_pace.plate import render_plate_block
from loam.primary_persona.keep_pace.relational import (
    render_relational_block,
    reset_cache,
)
from loam.primary_persona.keep_pace.waiting_on import render_waiting_on_block

from _wms4_store import EDGE, fresh_factory, live_store, make_open

# A real two-objective register: one objective has advancing work, the
# other has NONE (the no-work-goal case).
_OBJECTIVES = """# user-objectives

## revenue-independence
status: active
objective: Build financial independence.
completion: passive income covers the floor.
detail-path: x.md
subgoals:
  - shared-foundation

## litrpg-fiction-pipeline
status: active
objective: Produce the LitRPG series.
completion: seven books shipped.
detail-path: y.md
subgoals:
  - book-1-batch-production
"""


async def test_AC_WMS5_LIVE_1_three_lenses_live_no_pre_arranged_state(tmp_path) -> None:
    reset_cache()
    db = tmp_path / "objectives.db"

    # Build a REAL store through the store's OWN API. NO pre-arranged
    # ladder / ranking / surfacing state.
    setup = live_store(db)
    try:
        # B — the unblocker; its goal mentions the revenue-independence
        # subgoal "shared-foundation" so it ladders to that objective.
        b = await make_open(setup, "build the shared-foundation for revenue")
        # C — the blocked downstream item: C waits on B, B blocks C.
        c = await make_open(setup, "ship the feature on the foundation")
        await setup.record_edge(
            c.objective_id, edge_kind=EDGE.waits_on, to_id=b.objective_id
        )
        await setup.record_edge(
            b.objective_id, edge_kind=EDGE.blocks, to_id=c.objective_id
        )
        # A decision the owner owes (owner_pending) — on the plate + on the
        # waiting-on-me side.
        d = await make_open(setup, "decide the revenue-independence pricing")
        await setup.mark_owner_pending(d.objective_id, evidence="needs your call")
        # An external-party wait — off the plate, on the waiting-on-others
        # side.
        w = await make_open(setup, "the partner integration")
        await setup.record_edge(
            w.objective_id, edge_kind=EDGE.waits_on, party="Acme"
        )
    finally:
        setup.close()

    factory = fresh_factory(db)

    # ---- GOALS lens (live) ------------------------------------------
    goals_block = render_goals_block(
        objectives_text=_OBJECTIVES, tracker_factory=factory
    )
    assert goals_block, f"goals lens must render live; block={goals_block!r}"
    rev_line = next(
        (ln for ln in goals_block.splitlines() if "revenue independence" in ln),
        "",
    )
    # The right work ladders under revenue-independence (via the subgoal).
    assert "build the shared-foundation for revenue" in rev_line, (
        f"the right work must ladder under revenue-independence; "
        f"block={goals_block!r}"
    )
    # The pipeline objective has NO advancing work — named as such.
    pipe_line = next(
        (ln for ln in goals_block.splitlines() if "litrpg fiction pipeline" in ln),
        "",
    )
    assert "nothing is currently moving this goal" in pipe_line, (
        f"the no-work goal must be named; block={goals_block!r}"
    )

    # ---- ON-MY-PLATE lens (live) ------------------------------------
    plate_block = render_plate_block(
        objectives_text=_OBJECTIVES, tracker_factory=factory
    )
    assert plate_block, f"plate lens must render live; block={plate_block!r}"
    plate_rows = [ln for ln in plate_block.splitlines() if ln.startswith("  ")]
    # The top plate item is the unblocker B, carrying prioritize's reason.
    assert "build the shared-foundation for revenue" in plate_rows[0], (
        f"the unblocker must be the top plate item; rows={plate_rows!r}"
    )
    assert "waiting on it" in plate_rows[0].lower(), (
        f"the plate must carry prioritize's transparent reason; "
        f"top={plate_rows[0]!r}"
    )
    # The blocked downstream C and the external-party wait are OFF the plate.
    assert "ship the feature on the foundation" not in plate_block, (
        "the blocked item must be off the plate"
    )
    assert "the partner integration" not in plate_block, (
        "the waiting-on-others item must be off the plate"
    )
    # The owner_pending decision IS on the plate (D-WMS5.6).
    assert "decide the revenue-independence pricing" in plate_block

    # ---- WAITING-ON lens (live) -------------------------------------
    waiting_block = render_waiting_on_block(tracker_factory=factory)
    assert waiting_block, f"waiting-on lens must render live; block={waiting_block!r}"
    # On-me: the owner_pending decision.
    assert "decide the revenue-independence pricing" in waiting_block
    # On-others: the external-party wait, party named.
    assert "the partner integration" in waiting_block
    assert "Acme" in waiting_block

    # ---- The reconciliation: SAME shared helper as relational -------
    # The relational block computes the SAME on-me / on-others split via
    # the shared compute_waiting_split helper. The standalone lens's split
    # MUST agree with relational's (no duplicated, divergent surfacing).
    reset_cache()
    rel_block = render_relational_block(
        tracker_factory=factory, objectives_text=_OBJECTIVES
    )
    # relational surfaces the same on-me item ("waiting on you: ...") and
    # the same on-others party ("waiting on others: ... (on Acme)").
    assert "waiting on you: decide the revenue-independence pricing" in rel_block
    assert "waiting on others: the partner integration (on Acme)" in rel_block
