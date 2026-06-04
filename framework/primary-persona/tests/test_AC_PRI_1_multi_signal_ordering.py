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

"""AC.PRI.1 — the prioritization produces a MULTI-SIGNAL ordering.

Plan §6 AC.PRI.1. Outcome: given two items equal on the existing
``tracker_context`` priority-key, the one that unblocks more downstream
work OR ladders up to a user-objective OR is staler ranks ahead — the
order is NOT determined by the single open-loop key alone.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.prioritize import prioritize

from _wms4_store import live_store, make_item, record_edge  # noqa: F401


_NOW = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)


def _fresh(days_ago: float = 0.0) -> str:
    return (_NOW - timedelta(days=days_ago)).isoformat()


def test_AC_PRI_1_blocking_impact_outranks_equal_priority_key() -> None:
    """Two items equal on the priority-key: the one that unblocks
    downstream work ranks ahead (blocking-impact is a real signal, not
    the open-loop key alone)."""
    # Both "active" (same priority-key). B unblocks C (a blocks edge);
    # A is independent.
    a = make_item("obj-a", goal="independent thing", priority="active")
    b = make_item("obj-b", goal="the unblocker", priority="active",
                  edges_out=[("blocks", "obj-c", None)])
    c = make_item("obj-c", goal="the blocked downstream", priority="active",
                  edges_in=[("blocks", "obj-b", None)])

    ranked = prioritize([a, b, c], now=_NOW)
    order = [r.item.objective_id for r in ranked]
    # B (unblocks C) ranks ahead of A (independent) despite equal key.
    assert order.index("obj-b") < order.index("obj-a"), (
        f"blocking-impact must lift B above the equally-keyed A; order={order}"
    )


def test_AC_PRI_1_goal_alignment_outranks_orphan() -> None:
    """Two items equal on the priority-key: the one laddering up to a
    user-objective ranks ahead of the orphan."""
    aligned = make_item("obj-aligned", goal="ship the revenue launch",
                        priority="active")
    orphan = make_item("obj-orphan", goal="some unrelated chore",
                       priority="active")
    ranked = prioritize(
        [orphan, aligned],
        aligned_terms=frozenset({"revenue"}),
        now=_NOW,
    )
    order = [r.item.objective_id for r in ranked]
    assert order.index("obj-aligned") < order.index("obj-orphan"), (
        f"goal-alignment must lift the aligned item above the orphan; order={order}"
    )


def test_AC_PRI_1_staleness_outranks_fresh_when_otherwise_equal() -> None:
    """Two items equal on the priority-key with no edges/alignment: the
    staler one ranks ahead (staleness is a real signal)."""
    stale = make_item("obj-stale", goal="languishing task",
                      priority="active", last_transition_at=_fresh(days_ago=30))
    fresh = make_item("obj-fresh", goal="just-touched task",
                      priority="active", last_transition_at=_fresh(days_ago=0))
    ranked = prioritize([fresh, stale], now=_NOW)
    order = [r.item.objective_id for r in ranked]
    assert order.index("obj-stale") < order.index("obj-fresh"), (
        f"staleness must lift the stale item above the fresh one; order={order}"
    )


def test_AC_PRI_1_not_determined_by_priority_key_alone() -> None:
    """A LOWER priority-key item that unblocks many can outrank a HIGHER
    priority-key independent item — proving the order is not the
    open-loop key alone."""
    # A: owner_pending (highest key) but independent.
    a = make_item("obj-a", goal="owner-pending but isolated",
                  priority="owner_pending")
    # B: proposed (lowest key) but unblocks two downstream items.
    b = make_item("obj-b", goal="proposed unblocker", priority="proposed",
                  edges_out=[("blocks", "obj-c", None), ("blocks", "obj-d", None)])
    c = make_item("obj-c", goal="downstream one", priority="proposed",
                  edges_in=[("blocks", "obj-b", None)])
    d = make_item("obj-d", goal="downstream two", priority="proposed",
                  edges_in=[("blocks", "obj-b", None)])
    ranked = prioritize([a, b, c, d], now=_NOW)
    order = [r.item.objective_id for r in ranked]
    assert order.index("obj-b") < order.index("obj-a"), (
        "the high-impact low-key item must be able to outrank the "
        f"high-key isolated item — order is not the key alone; order={order}"
    )
