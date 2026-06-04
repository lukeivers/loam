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

"""AC.WI.EDGE.3 — no edge fabricated where none was recorded.

Plan §6 AC.WI.EDGE.3. Outcome: querying a work item with no recorded
edges returns no edges; a project binding to an unregistered FBM project
does NOT synthesize a blocks/waits-on relationship (the honest-graph
invariant).
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


async def test_AC_WI_EDGE_3_no_edges_when_none_recorded(
    tracker: ObjectiveTracker,
) -> None:
    p = await tracker.create(_spec("lonely item"))
    proj = tracker.get(p.objective_id)
    assert proj is not None
    assert proj.edges_out == ()
    assert proj.edges_in == ()


async def test_AC_WI_EDGE_3_project_binding_synthesizes_no_edge(
    tracker: ObjectiveTracker,
) -> None:
    """An item bound to an (even unregistered) project gains NO edge — the
    project binding is a field, not a relationship."""
    p = await tracker.create(
        _spec("bound to nowhere", belongs_to_project="a-project-with-no-fbm-spec")
    )
    proj = tracker.get(p.objective_id)
    assert proj is not None
    assert proj.belongs_to_project == "a-project-with-no-fbm-spec"
    assert proj.edges_out == ()
    assert proj.edges_in == ()


async def test_AC_WI_EDGE_3_clearing_absent_edge_is_noop(
    tracker: ObjectiveTracker,
) -> None:
    """Clearing an edge that was never recorded fabricates nothing and
    raises nothing (idempotent)."""
    a = await tracker.create(_spec("a"))
    b = await tracker.create(_spec("b"))
    await tracker.clear_edge(
        a.objective_id, edge_kind=WorkEdgeKind.blocks, to_id=b.objective_id
    )
    pa = tracker.get(a.objective_id)
    assert pa is not None
    assert pa.edges_out == ()
