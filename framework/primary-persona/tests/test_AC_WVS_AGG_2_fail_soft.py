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

"""AC.WVS-AGG.2 — every source read is fail-soft: a missing / broken /
UNRESOLVED source degrades that part of the snapshot to "unknown" and
NEVER breaks the snapshot or the host hook (exit 0).

Each source is removed / corrupted in turn; the aggregator still
returns a snapshot, with the broken part marked unknown, and the
surface still renders.

Plan: docs/plans/work-visibility-surface.md §5.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.work_visibility import (
    HEALTH_UNKNOWN,
    build_snapshot,
    render_surface,
)

from _helpers_d40 import FakeTrackerClient, make_projection


def test_AC_WVS_AGG_2_absent_tracker_db_marks_work_unknown(tmp_path: Path) -> None:
    """No tracker DB on disk (and no injected factory) → work_unknown,
    snapshot still returns, surface still renders."""
    # No tracker_factory → the aggregator resolves the workspace DB path,
    # which does not exist under a fresh tmp workspace.
    snapshot = build_snapshot(tmp_path)
    assert snapshot.work_unknown is True
    # The snapshot still returns and renders (no crash).
    text = render_surface(snapshot)
    assert text


def test_AC_WVS_AGG_2_tracker_open_failure_marks_work_unknown(
    tmp_path: Path,
) -> None:
    """A tracker factory that raises → work_unknown, no exception
    propagates."""

    def _boom():
        raise RuntimeError("tracker open failed")

    snapshot = build_snapshot(tmp_path, tracker_factory=_boom)
    assert snapshot.work_unknown is True
    assert snapshot.running_now == 0


def test_AC_WVS_AGG_2_query_error_marks_work_unknown(tmp_path: Path) -> None:
    """A tracker whose query raises → work_unknown."""
    client = FakeTrackerClient(query_raises=RuntimeError("query failed"))
    snapshot = build_snapshot(tmp_path, tracker_factory=lambda: client)
    assert snapshot.work_unknown is True


def test_AC_WVS_AGG_2_unresolved_cursor_is_not_a_false_position(
    tmp_path: Path,
) -> None:
    """A cursor naming a step that no longer exists resolves UNRESOLVED
    → position_known False, NOT a false position; not marked unknown
    (we successfully determined it is unresolved)."""
    from loam_cli.flows.cursor import Cursor, write_cursor

    cursor_path = tmp_path / "stale.cursor.yaml"
    write_cursor(cursor_path, Cursor(flow="build", step="gone", branch_state=""))

    class _Def:
        flow = "build"

        def get_step(self, sid: str):
            return None  # step vanished → UNRESOLVED

    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        cursor_path=cursor_path,
        flow_loader=lambda flow: _Def(),
    )
    assert snapshot.position_known is False
    assert snapshot.position_phrase is None


def test_AC_WVS_AGG_2_corrupt_cursor_file_marks_position(tmp_path: Path) -> None:
    """A corrupt cursor file (read_cursor returns None) → no resolved
    position, snapshot still returns."""
    cursor_path = tmp_path / "corrupt.cursor.yaml"
    cursor_path.write_text(":\n:not yaml:\n  - [", encoding="utf-8")
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        cursor_path=cursor_path,
    )
    assert snapshot.position_known is False


def test_AC_WVS_AGG_2_absent_watchdog_marks_health_unknown(tmp_path: Path) -> None:
    """No watchdog → health unknown (never a false 'ok')."""
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        stall_watchdog=None,
    )
    assert snapshot.health == HEALTH_UNKNOWN
    assert snapshot.health_unknown is True


def test_AC_WVS_AGG_2_broken_watchdog_marks_health_unknown(tmp_path: Path) -> None:
    """A watchdog whose evaluate path raises → health unknown, no
    exception propagates."""

    class _BoomWatchdog:
        def seconds_since_progress(self):
            raise RuntimeError("watchdog boom")

        def is_stuck(self):
            raise RuntimeError("watchdog boom")

    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        stall_watchdog=_BoomWatchdog(),
    )
    assert snapshot.health == HEALTH_UNKNOWN
    assert snapshot.health_unknown is True


def test_AC_WVS_AGG_2_all_sources_broken_still_renders(tmp_path: Path) -> None:
    """Every source broken at once → the snapshot still returns and the
    surface still renders (the host hook is never broken)."""

    def _boom_tracker():
        raise RuntimeError("boom")

    class _BoomWatchdog:
        def seconds_since_progress(self):
            raise RuntimeError("boom")

        def is_stuck(self):
            raise RuntimeError("boom")

    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=_boom_tracker,
        stall_watchdog=_BoomWatchdog(),
    )
    assert snapshot.work_unknown is True
    assert snapshot.health_unknown is True
    text = render_surface(snapshot)
    assert text  # always renders
