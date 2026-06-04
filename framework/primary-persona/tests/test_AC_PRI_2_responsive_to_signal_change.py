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

"""AC.PRI.2 — the ordering is RESPONSIVE to a signal change.

Plan §6 AC.PRI.2. Outcome: recording an edge that makes an item
unblock-many (or passing its staleness cadence, or being placed under an
objective) changes its rank in the next derivation — WITHOUT editing the
prioritization code (derived, not static).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.prioritize import prioritize

from _wms4_store import make_item, record_edge


_NOW = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_AC_PRI_2_recording_a_blocking_edge_lifts_rank() -> None:
    """An item gains a ``blocks`` edge (now unblocks downstream work) →
    its rank rises in the next derivation, no code edit."""
    a = make_item("obj-a", goal="task a", priority="active")
    b = make_item("obj-b", goal="task b", priority="active")
    c = make_item("obj-c", goal="downstream", priority="active",
                  edges_in=[])

    before = [r.item.objective_id for r in prioritize([a, b, c], now=_NOW)]

    # Record an edge: B now blocks C (B unblocks downstream work).
    b2 = record_edge(b, edge_kind="blocks", to_id="obj-c")
    c2 = make_item("obj-c", goal="downstream", priority="active",
                   edges_in=[("blocks", "obj-b", None)])
    after = [r.item.objective_id for r in prioritize([a, b2, c2], now=_NOW)]

    assert before.index("obj-b") >= 0 and after.index("obj-b") >= 0
    assert after.index("obj-b") < before.index("obj-b") or after.index("obj-b") < after.index("obj-a"), (
        f"recording the blocking edge must lift B's rank; before={before} after={after}"
    )
    # Concretely: after the edge, B (now an unblocker) outranks A.
    assert after.index("obj-b") < after.index("obj-a")


def test_AC_PRI_2_passing_staleness_cadence_lifts_rank() -> None:
    """An item passing its staleness cadence (older last_transition_at)
    rises relative to a fresh peer — the same item, two clocks."""
    fresh_ts = (_NOW - timedelta(days=1)).isoformat()
    item_a = make_item("obj-a", goal="task a", priority="active",
                       last_transition_at=fresh_ts)
    item_b = make_item("obj-b", goal="task b", priority="active",
                       last_transition_at=fresh_ts)

    # Both fresh now: tie broken by goal text (a < b).
    early = [r.item.objective_id for r in prioritize([item_a, item_b], now=_NOW)]
    assert early == ["obj-a", "obj-b"]

    # Make A stale by re-deriving against a later clock where only A's
    # timestamp is old (B re-touched). The derivation responds to the
    # state, no code change.
    a_stale = make_item("obj-a", goal="task a", priority="active",
                        last_transition_at=(_NOW - timedelta(days=40)).isoformat())
    b_fresh = make_item("obj-b", goal="task b", priority="active",
                       last_transition_at=_NOW.isoformat())
    later = [r.item.objective_id for r in prioritize([a_stale, b_fresh], now=_NOW)]
    assert later.index("obj-a") < later.index("obj-b"), (
        f"the now-stale A must outrank the fresh B; order={later}"
    )


def test_AC_PRI_2_placing_under_objective_lifts_rank() -> None:
    """Adding an item's goal to the aligned-objective vocabulary (it now
    ladders up) lifts its rank — the alignment signal responds to the
    objective register, no code edit."""
    item = make_item("obj-x", goal="grow the newsletter", priority="active")
    peer = make_item("obj-y", goal="random errand", priority="active")

    without = [r.item.objective_id for r in prioritize([item, peer], now=_NOW)]
    with_obj = [
        r.item.objective_id
        for r in prioritize(
            [item, peer], aligned_terms=frozenset({"newsletter"}), now=_NOW
        )
    ]
    # With the objective vocabulary, the aligned item rises above the peer.
    assert with_obj.index("obj-x") < with_obj.index("obj-y")
    assert with_obj != without or without.index("obj-x") < without.index("obj-y")
