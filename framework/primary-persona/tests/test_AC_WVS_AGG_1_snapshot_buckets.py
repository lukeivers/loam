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

"""AC.WVS-AGG.1 — ONE aggregator snapshot distinguishes running-now /
queued / owner-pending / position, sourced from the existing tracker
projections + resolved cursor (NOT re-derived).

A snapshot built against a workspace whose tracker carries projections
in >=2 distinct states + an active cursor reflects each state in its
correct bucket. The state-distinctions derive from the sealed tracker
predicates; the aggregator is a reader, not a second tracker.

Plan: docs/plans/work-visibility-surface.md §5.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.work_visibility import build_snapshot

from _helpers_d40 import FakeTrackerClient, make_projection


def _tracker_in_three_states() -> FakeTrackerClient:
    """A fake tracker carrying active + proposed + owner_pending +
    a terminal (achieved) record (the terminal must NOT count)."""
    return FakeTrackerClient(
        query_result=(
            make_projection("obj-running-1", status="active"),
            make_projection("obj-running-2", status="active"),
            make_projection("obj-queued-1", status="proposed"),
            make_projection("obj-owner-1", status="owner_pending"),
            make_projection("obj-done-1", status="achieved"),
            make_projection("obj-dead-1", status="abandoned"),
        ),
    )


def test_AC_WVS_AGG_1_buckets_reflect_each_state(tmp_path: Path) -> None:
    """running_now / queued / owner_pending each carry the count of
    their state; terminal records are excluded."""
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=_tracker_in_three_states,
        stall_watchdog=None,
    )
    assert snapshot.running_now == 2, "two active objectives → running_now=2"
    assert snapshot.queued == 1, "one proposed objective → queued=1"
    assert snapshot.owner_pending == 1, "one owner_pending → owner_pending=1"
    # Terminal records (achieved / abandoned) are not work.
    assert snapshot.has_active_work is True


def test_AC_WVS_AGG_1_distinguishes_at_least_two_states(tmp_path: Path) -> None:
    """The snapshot distinguishes the buckets — two states present land
    in two distinct, non-conflated counts."""
    client = FakeTrackerClient(
        query_result=(
            make_projection("a", status="active"),
            make_projection("b", status="owner_pending"),
        ),
    )
    snapshot = build_snapshot(tmp_path, tracker_factory=lambda: client)
    assert snapshot.running_now == 1
    assert snapshot.owner_pending == 1
    assert snapshot.queued == 0


def test_AC_WVS_AGG_1_position_from_resolved_cursor(tmp_path: Path) -> None:
    """An active, resolvable cursor lands a known position in the
    snapshot — sourced from the sealed resolve_cursor, not re-derived."""
    from loam_cli.flows.cursor import Cursor, write_cursor

    cursor_path = tmp_path / "active.cursor.yaml"
    write_cursor(cursor_path, Cursor(flow="build", step="s1", branch_state="b"))

    class _Step:
        id = "s1"
        name = "first step"
        transitions: dict = {}

    class _Def:
        flow = "build"

        def get_step(self, sid: str):
            return _Step() if sid == "s1" else None

    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        cursor_path=cursor_path,
        flow_loader=lambda flow: _Def(),
    )
    assert snapshot.position_known is True
    assert snapshot.position_phrase is not None
    assert "first step" in snapshot.position_phrase


def test_AC_WVS_AGG_1_empty_tracker_no_active_work(tmp_path: Path) -> None:
    """An empty tracker (no records) yields zero buckets + no active
    work — the all-caught-up state, distinct from 'unknown'."""
    snapshot = build_snapshot(
        tmp_path, tracker_factory=lambda: FakeTrackerClient(query_result=())
    )
    assert snapshot.running_now == 0
    assert snapshot.queued == 0
    assert snapshot.owner_pending == 0
    assert snapshot.has_active_work is False
    assert snapshot.work_unknown is False
