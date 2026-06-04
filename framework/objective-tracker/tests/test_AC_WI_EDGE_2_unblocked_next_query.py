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

"""AC.WI.EDGE.2 — the unblocked-next query.

Plan §6 AC.WI.EDGE.2. Outcome: given work items with waits-on/blocks
edges, a query returns the items NOT waiting on any unresolved blocker
(the "next unblocked thing"); an item waiting on an external party is
reported as waiting-on-other, NOT as next.
"""

from __future__ import annotations

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import (
    ObjectiveSpec,
    ProseCriterion,
    TimeBound,
    WorkEdgeKind,
)


def _spec(goal: str) -> ObjectiveSpec:
    return ObjectiveSpec(
        goal=goal,
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c1", prose="done"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
    )


async def _make_open(tracker: ObjectiveTracker, goal: str):
    p = await tracker.create(_spec(goal))
    await tracker.start(p.objective_id)
    return p


async def test_AC_WI_EDGE_2_waits_on_unresolved_blocker_is_not_next(
    tracker: ObjectiveTracker,
) -> None:
    blocker = await _make_open(tracker, "do first")
    waiter = await _make_open(tracker, "do after")
    await tracker.record_edge(
        waiter.objective_id, edge_kind=WorkEdgeKind.waits_on, to_id=blocker.objective_id
    )

    ids = {p.objective_id for p in tracker.unblocked_next()}
    assert blocker.objective_id in ids  # the blocker itself is unblocked
    assert waiter.objective_id not in ids  # waiting on an unresolved item


async def test_AC_WI_EDGE_2_resolved_blocker_unblocks_the_waiter(
    tracker: ObjectiveTracker,
) -> None:
    blocker = await _make_open(tracker, "do first")
    waiter = await _make_open(tracker, "do after")
    await tracker.record_edge(
        waiter.objective_id, edge_kind=WorkEdgeKind.waits_on, to_id=blocker.objective_id
    )
    # Resolve the blocker — the waiter is now unblocked (a terminal
    # blocker no longer blocks).
    await tracker.evaluate_criterion(
        blocker.objective_id, criterion_id="c1", result="met"
    )
    await tracker.mark_achieved(blocker.objective_id, evidence="done")

    ids = {p.objective_id for p in tracker.unblocked_next()}
    assert waiter.objective_id in ids


async def test_AC_WI_EDGE_2_blocks_edge_inverse_direction(
    tracker: ObjectiveTracker,
) -> None:
    """An item that is the TARGET of an active `blocks` edge from an open
    item is not next (the blocks-direction inverse of waits-on)."""
    blocker = await _make_open(tracker, "blocker")
    blocked = await _make_open(tracker, "blocked thing")
    await tracker.record_edge(
        blocker.objective_id, edge_kind=WorkEdgeKind.blocks, to_id=blocked.objective_id
    )
    ids = {p.objective_id for p in tracker.unblocked_next()}
    assert blocker.objective_id in ids
    assert blocked.objective_id not in ids


async def test_AC_WI_EDGE_2_external_party_is_waiting_on_other_not_next(
    tracker: ObjectiveTracker,
) -> None:
    eric_wait = await _make_open(tracker, "the launch (waits on Eric)")
    free = await _make_open(tracker, "free work")
    await tracker.record_edge(
        eric_wait.objective_id, edge_kind=WorkEdgeKind.waits_on, party="Eric"
    )

    next_ids = {p.objective_id for p in tracker.unblocked_next()}
    other_ids = {p.objective_id for p in tracker.waiting_on_other()}

    assert free.objective_id in next_ids
    assert eric_wait.objective_id not in next_ids  # waiting on a party
    assert eric_wait.objective_id in other_ids  # reported as waiting-on-other
