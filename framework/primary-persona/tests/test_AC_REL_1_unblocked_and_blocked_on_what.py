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

"""AC.REL.1 — unblocked-next + blocked-on-what off the REAL edge graph.

Plan §6 AC.REL.1. Outcome: the relational surface answers "what is
unblocked and ready to do next" and "what is blocked and ON WHAT" from
the EXISTING edge graph + queries; recording/clearing an edge changes
the answer.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.relational import (
    render_relational_block,
    reset_cache,
)

from _wms4_store import EDGE, live_store, make_open


async def test_AC_REL_1_unblocked_and_blocked_answers_off_real_graph(tmp_path) -> None:
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        blocker = await make_open(setup, "do the foundation first")
        waiter = await make_open(setup, "build on the foundation")
        await setup.record_edge(
            waiter.objective_id, edge_kind=EDGE.waits_on, to_id=blocker.objective_id
        )
    finally:
        setup.close()

    # The lens resolves a FRESH tracker per turn (the production factory
    # contract — the lens closes what the factory opened).
    block = render_relational_block(
        tracker_factory=lambda: live_store(db), objectives_text=""
    )
    # "next" surfaces the unblocked item (the foundation), and the
    # blocked item is named with what it waits on.
    assert "do the foundation first" in block
    assert "blocked: build on the foundation" in block
    assert "waiting on do the foundation first" in block


async def test_AC_REL_1_clearing_an_edge_changes_the_answer(tmp_path) -> None:
    """Recording then clearing the blocking edge changes the surface —
    the answer reflects the real (mutable) graph."""
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        blocker = await make_open(setup, "ship the api")
        waiter = await make_open(setup, "write the docs")
        await setup.record_edge(
            waiter.objective_id, edge_kind=EDGE.waits_on, to_id=blocker.objective_id
        )
    finally:
        setup.close()

    with_edge = render_relational_block(
        tracker_factory=lambda: live_store(db), objectives_text="", now=0.0
    )
    assert "blocked: write the docs" in with_edge

    # Clear the edge: the docs item is no longer blocked.
    setup = live_store(db)
    try:
        await setup.clear_edge(
            waiter.objective_id, edge_kind=EDGE.waits_on, to_id=blocker.objective_id
        )
    finally:
        setup.close()
    without_edge = render_relational_block(
        tracker_factory=lambda: live_store(db), objectives_text="", now=1000.0
    )
    assert "blocked: write the docs" not in without_edge, (
        "clearing the edge must remove the blocked answer; "
        f"block={without_edge!r}"
    )
