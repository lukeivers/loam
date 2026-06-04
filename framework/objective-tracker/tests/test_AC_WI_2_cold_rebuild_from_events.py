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

"""AC.WI.2 — full state (incl. edges + new fields) reconstructs from the
event log alone after a cold projection rebuild.

Plan §6 AC.WI.2. Outcome: single-source-of-truth preserved — no
out-of-log side state is load-bearing. Drop the projection cache, rebuild
from events, assert the work-item fields AND the active edge set
reconstruct identically.
"""

from __future__ import annotations

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import (
    ObjectiveSpec,
    ProseCriterion,
    TimeBound,
    WorkEdgeKind,
)


def _spec(goal: str, **over) -> ObjectiveSpec:
    base = dict(
        goal=goal,
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c1", prose="done"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
    )
    base.update(over)
    return ObjectiveSpec(**base)


async def test_AC_WI_2_fields_and_edges_rebuild_from_events(
    tracker: ObjectiveTracker,
) -> None:
    a = await tracker.create(
        _spec("a", belongs_to_project="loam", tagged_streams=("loam",), priority="active")
    )
    b = await tracker.create(_spec("b"))
    # Record an edge, then clear a different one to leave a non-trivial
    # active edge set after the fold.
    await tracker.record_edge(a.objective_id, edge_kind=WorkEdgeKind.blocks, to_id=b.objective_id)
    await tracker.record_edge(a.objective_id, edge_kind=WorkEdgeKind.relates_to, to_id=b.objective_id)
    await tracker.clear_edge(a.objective_id, edge_kind=WorkEdgeKind.relates_to, to_id=b.objective_id)

    # Cold rebuild: drop the cache, then re-read entirely from events.
    tracker.store.drop_projection()

    rebuilt_a = tracker.get(a.objective_id)
    assert rebuilt_a is not None
    assert rebuilt_a.belongs_to_project == "loam"
    assert rebuilt_a.tagged_streams == ("loam",)
    assert rebuilt_a.priority == "active"
    # Only the un-cleared `blocks` edge survives the fold.
    out_kinds = {e.edge_kind for e in rebuilt_a.edges_out}
    assert out_kinds == {WorkEdgeKind.blocks}
    assert all(e.to_id == b.objective_id for e in rebuilt_a.edges_out)

    # The edge surfaces on the `to` endpoint too, rebuilt from events.
    rebuilt_b = tracker.get(b.objective_id)
    assert rebuilt_b is not None
    in_kinds = {e.edge_kind for e in rebuilt_b.edges_in}
    assert in_kinds == {WorkEdgeKind.blocks}
