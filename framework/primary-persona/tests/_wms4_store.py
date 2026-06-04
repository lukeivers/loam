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

"""Shared WMS-increment-4 test helpers.

Two kinds of fixture:

  - :func:`make_item` — a lightweight duck-typed work item for the PURE
    derivation unit tests (``prioritize``): it carries exactly the
    projection fields the derivation reads (goal / priority /
    last_transition_at / edges_out / edges_in / parent_id / status /
    belongs_to_project / objective_id) without standing up a store.

  - :func:`live_store` — a REAL ``ObjectiveTracker`` over a tmp DB plus
    helpers to create items + record edges through the store's OWN API.
    This is the substrate for the relational + outcome-altitude
    (AC.WMS4.LIVE.1) tests: NO pre-arranged surfacing/ranking state, the
    derivation + lens read the live queries (the production entry
    points).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import (
    ObjectiveSpec,
    ProseCriterion,
    TimeBound,
    WorkEdgeKind,
)


# ---------------------------------------------------------------------
# Lightweight duck-typed work item (pure derivation unit tests).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class _FakeEdge:
    edge_kind: str
    to_id: Optional[str] = None
    from_id: Optional[str] = None
    party: Optional[str] = None


@dataclass(frozen=True)
class _FakeStatus:
    value: str


@dataclass(frozen=True)
class _FakeItem:
    objective_id: str
    goal: str
    priority: Optional[str] = None
    last_transition_at: str = ""
    parent_id: Optional[str] = None
    belongs_to_project: Optional[str] = None
    status: Any = field(default_factory=lambda: _FakeStatus("active"))
    edges_out: tuple = ()
    edges_in: tuple = ()


def make_item(
    objective_id: str,
    *,
    goal: str,
    priority: Optional[str] = None,
    last_transition_at: str = "",
    parent_id: Optional[str] = None,
    belongs_to_project: Optional[str] = None,
    status: str = "active",
    edges_out: Optional[list[tuple]] = None,
    edges_in: Optional[list[tuple]] = None,
) -> _FakeItem:
    """Build a duck-typed work item carrying the projection fields the
    derivation reads. ``edges_out``/``edges_in`` are lists of
    ``(edge_kind, to_id_or_from_id, party)`` tuples."""
    eo = tuple(
        _FakeEdge(edge_kind=k, to_id=t, from_id=objective_id, party=p)
        for (k, t, p) in (edges_out or [])
    )
    ei = tuple(
        _FakeEdge(edge_kind=k, from_id=f, to_id=objective_id, party=p)
        for (k, f, p) in (edges_in or [])
    )
    return _FakeItem(
        objective_id=objective_id,
        goal=goal,
        priority=priority,
        last_transition_at=last_transition_at,
        parent_id=parent_id,
        belongs_to_project=belongs_to_project,
        status=_FakeStatus(status),
        edges_out=eo,
        edges_in=ei,
    )


def record_edge(item: _FakeItem, *, edge_kind: str, to_id=None, party=None) -> _FakeItem:
    """Return a copy of ``item`` with an added outgoing edge (pure-fn
    helper for the responsiveness unit test)."""
    new_out = item.edges_out + (
        _FakeEdge(edge_kind=edge_kind, to_id=to_id, from_id=item.objective_id, party=party),
    )
    return _FakeItem(
        objective_id=item.objective_id,
        goal=item.goal,
        priority=item.priority,
        last_transition_at=item.last_transition_at,
        parent_id=item.parent_id,
        belongs_to_project=item.belongs_to_project,
        status=item.status,
        edges_out=new_out,
        edges_in=item.edges_in,
    )


# ---------------------------------------------------------------------
# REAL store (relational + outcome-altitude tests).
# ---------------------------------------------------------------------


def live_store(db_path) -> ObjectiveTracker:
    """A real ``ObjectiveTracker`` over ``db_path`` (a tmp file)."""
    return ObjectiveTracker(db_path=db_path)


def fresh_factory(db_path):
    """A tracker_factory that opens a FRESH tracker per call against
    ``db_path`` — mirrors the production contract (the lens resolves a
    fresh tracker per turn and closes what it opened)."""
    return lambda: ObjectiveTracker(db_path=db_path)


def _spec(goal: str, *, priority: Optional[str] = None, parent_id: Optional[str] = None) -> ObjectiveSpec:
    return ObjectiveSpec(
        goal=goal,
        parent_id=parent_id,
        acceptance_criteria=(ProseCriterion(criterion_id="c1", prose="done"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
        priority=priority,
    )


async def make_open(
    tracker: ObjectiveTracker,
    goal: str,
    *,
    priority: Optional[str] = None,
    parent_id: Optional[str] = None,
    start: bool = True,
):
    """Create + (optionally) start a real open work item through the
    store's OWN API (no pre-arranged projection state)."""
    p = await tracker.create(_spec(goal, priority=priority, parent_id=parent_id))
    if start:
        await tracker.start(p.objective_id)
    return p


# Re-export the edge-kind enum for the live tests.
EDGE = WorkEdgeKind
