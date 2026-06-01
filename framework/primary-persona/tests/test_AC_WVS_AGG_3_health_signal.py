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

"""AC.WVS-AGG.3 — the snapshot carries a watchdog-sourced health signal
so the surface answers "is it stuck?", not just "what's there?".

A watchdog reporting a stuck condition produces a non-healthy snapshot;
a clean watchdog produces healthy. The signal is sourced from the
sealed ``evaluate_stall`` surface (read across the fence, not
re-implemented).

Plan: docs/plans/work-visibility-surface.md §5.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.work_visibility import (
    HEALTH_OK,
    HEALTH_STUCK,
    build_snapshot,
)
from loam.self_correction.watchdog import StallWatchdog

from _helpers_d40 import FakeTrackerClient


def _watchdog_with_clock(start: float, now: float, threshold: float) -> StallWatchdog:
    """A StallWatchdog with an injected mutable clock; beats at ``start``
    (recording the heartbeat), then the clock advances to ``now`` so
    every subsequent read sees elapsed = now - start. The clock is a
    mutable holder (not a one-shot iterator): ``is_stuck`` /
    ``seconds_since_progress`` may each read the clock, so it must be
    stable across repeated calls."""
    holder = {"t": start}
    wd = StallWatchdog(
        stall_threshold_seconds=threshold,
        clock=lambda: holder["t"],
    )
    wd.beat()  # records heartbeat at ``start``
    holder["t"] = now  # advance the clock for all subsequent reads
    return wd


def test_AC_WVS_AGG_3_stuck_watchdog_yields_stuck_health(tmp_path: Path) -> None:
    """A watchdog whose heartbeat is older than the threshold → the
    snapshot health is STUCK."""
    wd = _watchdog_with_clock(start=0.0, now=600.0, threshold=300.0)
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        stall_watchdog=wd,
    )
    assert snapshot.health == HEALTH_STUCK
    assert snapshot.health_unknown is False


def test_AC_WVS_AGG_3_healthy_watchdog_yields_ok_health(tmp_path: Path) -> None:
    """A watchdog beating within the threshold → the snapshot health is
    OK (the 'is it stuck?' answer is 'no')."""
    wd = _watchdog_with_clock(start=0.0, now=10.0, threshold=300.0)
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        stall_watchdog=wd,
    )
    assert snapshot.health == HEALTH_OK
    assert snapshot.health_unknown is False
