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

"""AC.WI.EDGE.1 — blocks/waits-on/relates-to edges recordable, surface on
both endpoints, clearable, gone after clearing.

Plan §6 AC.WI.EDGE.1. Outcome: the relational graph memory has no concept
of exists + is mutable; a waits-on may name an external party.
"""

from __future__ import annotations

import pytest

from loam.objective_tracker.errors import UnresolvedObjectiveError
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


@pytest.mark.parametrize(
    "kind",
    [WorkEdgeKind.blocks, WorkEdgeKind.waits_on, WorkEdgeKind.relates_to],
)
async def test_AC_WI_EDGE_1_item_edge_surfaces_on_both_endpoints(
    tracker: ObjectiveTracker, kind: WorkEdgeKind
) -> None:
    a = await tracker.create(_spec("a"))
    b = await tracker.create(_spec("b"))

    await tracker.record_edge(a.objective_id, edge_kind=kind, to_id=b.objective_id)

    pa = tracker.get(a.objective_id)
    pb = tracker.get(b.objective_id)
    assert pa is not None and pb is not None
    # Surfaces as an OUTGOING edge on `a`.
    assert any(
        e.edge_kind == kind and e.to_id == b.objective_id for e in pa.edges_out
    )
    # Surfaces as an INCOMING edge on `b` (the same edge, both endpoints).
    assert any(
        e.edge_kind == kind and e.from_id == a.objective_id for e in pb.edges_in
    )


async def test_AC_WI_EDGE_1_waits_on_external_party(
    tracker: ObjectiveTracker,
) -> None:
    """A waits-on edge may name an external party (no `to` item)."""
    a = await tracker.create(_spec("the launch"))
    await tracker.record_edge(
        a.objective_id, edge_kind=WorkEdgeKind.waits_on, party="Eric"
    )
    pa = tracker.get(a.objective_id)
    assert pa is not None
    waits = [e for e in pa.edges_out if e.edge_kind == WorkEdgeKind.waits_on]
    assert len(waits) == 1
    assert waits[0].party == "Eric"
    assert waits[0].to_id is None


async def test_AC_WI_EDGE_1_clear_removes_edge_from_both_endpoints(
    tracker: ObjectiveTracker,
) -> None:
    a = await tracker.create(_spec("a"))
    b = await tracker.create(_spec("b"))
    await tracker.record_edge(
        a.objective_id, edge_kind=WorkEdgeKind.blocks, to_id=b.objective_id
    )
    await tracker.clear_edge(
        a.objective_id, edge_kind=WorkEdgeKind.blocks, to_id=b.objective_id
    )

    pa = tracker.get(a.objective_id)
    pb = tracker.get(b.objective_id)
    assert pa is not None and pb is not None
    assert pa.edges_out == ()
    assert pb.edges_in == ()


async def test_AC_WI_EDGE_1_edge_to_nonexistent_item_raises(
    tracker: ObjectiveTracker,
) -> None:
    """An item-to-item edge whose `to` does not exist raises (no edge
    fabrication against a non-existent item)."""
    a = await tracker.create(_spec("a"))
    with pytest.raises(UnresolvedObjectiveError):
        await tracker.record_edge(
            a.objective_id, edge_kind=WorkEdgeKind.blocks, to_id="obj-does-not-exist"
        )
