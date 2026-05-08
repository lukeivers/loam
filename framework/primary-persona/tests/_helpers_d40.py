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

"""Shared test helpers for the amendment #40 tracker-context AC suite.

Not a test module — pytest discovers tests by ``test_*`` prefix on
function names, so a module with no ``test_`` functions is inert.

Provides:

- ``FakeTrackerClient`` — Protocol-compatible stub recording calls,
  configurable ``query_projection_view`` results, configurable error
  injection (mirrors ``_helpers_d7.FakeMemoryClient`` shape).
- ``FakeProjection`` — minimal duck-typed projection holding the
  ``objective_id``, ``goal``, ``status``, ``parent_id`` fields the
  contributor reads.
- ``seed_value_prop_tree(db_path)`` — runs a real
  ``objective_tracker.ObjectiveTracker`` in-process to seed a value-
  prop-rooted tree with a small set of descendants so AC40 tests can
  hit a real DB without depending on workspace-bootstrap. The seeded
  shape mirrors amendment #39's contract (root id ``value-prop-root``,
  ``authored_by="user"``, ``LiftedFrom`` set).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---- FakeProjection / FakeTrackerClient ----------------------------


@dataclass(frozen=True)
class FakeStatus:
    """Duck-typed enum-like object — has a ``.value`` attribute."""

    value: str


@dataclass(frozen=True)
class FakeProjection:
    """Minimal projection shape the tracker-context contributor reads.

    Exposes ``.objective_id``, ``.goal``, ``.status`` (an object whose
    ``.value`` is a string), and ``.parent_id``. Sufficient for every
    code path the contributor exercises; the real
    ``ObjectiveProjection`` shape is a strict superset.
    """

    objective_id: str
    goal: str
    status: FakeStatus
    parent_id: str | None


@dataclass
class FakeTrackerClient:
    """Protocol-compatible stub for ``TrackerClient`` in AC tests.

    Records every call. ``query_projection_view`` returns
    ``query_result``; ``trace_to_root`` returns the value of
    ``trace_map`` (objective_id → list[FakeProjection]). Both methods
    raise ``query_raises`` / ``trace_raises`` if set, mirroring the
    ``FakeMemoryClient`` error-injection shape.
    """

    query_result: tuple[FakeProjection, ...] = ()
    query_raises: BaseException | None = None
    trace_map: dict[str, list[FakeProjection]] = field(default_factory=dict)
    trace_raises: BaseException | None = None
    trace_raises_for_id: dict[str, BaseException] = field(default_factory=dict)
    close_calls: list[None] = field(default_factory=list)
    query_calls: list[Any] = field(default_factory=list)
    trace_calls: list[str] = field(default_factory=list)

    def query_projection_view(
        self, filter: Any | None = None
    ) -> tuple[FakeProjection, ...]:
        self.query_calls.append(filter)
        if self.query_raises is not None:
            raise self.query_raises
        return self.query_result

    def trace_to_root(self, objective_id: str) -> list[FakeProjection]:
        self.trace_calls.append(objective_id)
        per_id_exc = self.trace_raises_for_id.get(objective_id)
        if per_id_exc is not None:
            raise per_id_exc
        if self.trace_raises is not None:
            raise self.trace_raises
        return list(self.trace_map.get(objective_id, []))

    def close(self) -> None:
        self.close_calls.append(None)


def make_projection(
    objective_id: str,
    *,
    goal: str = "",
    status: str = "active",
    parent_id: str | None = None,
) -> FakeProjection:
    """Sugar to construct a FakeProjection."""
    return FakeProjection(
        objective_id=objective_id,
        goal=goal or f"goal-{objective_id}",
        status=FakeStatus(value=status),
        parent_id=parent_id,
    )


# ---- live-tracker seeding ------------------------------------------


VALUE_PROP_ROOT_ID = "value-prop-root"


def seed_value_prop_tree(db_path: Path) -> dict[str, Any]:
    """Seed a real ``objective_tracker.ObjectiveTracker`` at ``db_path``.

    Returns a dict with the seeded objective IDs. Mirrors amendment
    #39's contract: root with ``authored_by="user"``, ``parent_id=None``,
    two prose criteria (AC.PO.1 + AC.PO.2), evergreen time-bound,
    ``LiftedFrom(source_doc="docs/VALUE_PROPOSITION.md",
    source_ac="prime")``. One spec-tier descendant for the live-tree
    tests (we don't need three; the contributor walks them
    structurally).

    Raises if objective_tracker is not importable. Tests that need a
    pure-Protocol shape should use ``FakeTrackerClient`` instead.
    """
    from loam.objective_tracker import (
        LiftedFrom,
        ObjectiveSpec,
        ObjectiveTracker,
        ProseCriterion,
        TimeBound,
    )

    db_path.parent.mkdir(parents=True, exist_ok=True)
    tracker = ObjectiveTracker(db_path)
    try:
        root_spec = ObjectiveSpec(
            goal="<value-prop root for tests>",
            parent_id=None,
            acceptance_criteria=(
                ProseCriterion(
                    criterion_id="ac-po-1",
                    description="AC.PO.1",
                    prose="primary-persona translation-burden test",
                ),
                ProseCriterion(
                    criterion_id="ac-po-2",
                    description="AC.PO.2",
                    prose="harness toolkit test",
                ),
            ),
            time_bound=TimeBound(evergreen=True, review_cadence="amendment-driven"),
            authored_by="user",
            lifted_from=LiftedFrom(
                source_doc="docs/VALUE_PROPOSITION.md",
                source_ac="prime",
            ),
        )
        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
            tracker.create(root_spec, objective_id=VALUE_PROP_ROOT_ID)
        )

        descendant_spec = ObjectiveSpec(
            goal="<spec-v1.0 descendant for tests>",
            parent_id=VALUE_PROP_ROOT_ID,
            acceptance_criteria=(
                ProseCriterion(
                    criterion_id="d1",
                    description="d1",
                    prose="descendant criterion",
                ),
            ),
            time_bound=TimeBound(evergreen=True, review_cadence="amendment-driven"),
            authored_by="user",
            lifted_from=LiftedFrom(
                source_doc="docs/spec/loam-objectives-spec.md",
                source_ac="v1.0",
            ),
        )
        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
            tracker.create(descendant_spec, objective_id="spec-v1.0")
        )
    finally:
        tracker.close()

    return {
        "root_id": VALUE_PROP_ROOT_ID,
        "descendant_id": "spec-v1.0",
        "db_path": db_path,
    }


def start_objective(db_path: Path, objective_id: str) -> None:
    """Helper: open a tracker at ``db_path`` and transition
    ``objective_id`` from ``proposed`` to ``active`` (i.e. start it)."""
    from loam.objective_tracker import ObjectiveTracker

    tracker = ObjectiveTracker(db_path)
    try:
        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
            tracker.start(objective_id)
        )
    finally:
        tracker.close()
