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

"""AC.WVS-FRESH.1 — the surface is self-maintaining: it reflects the
CURRENT work-state without the user asking. After a work-state change,
the surface reflects the new state on the next refresh event — no user
pull required.

Drives presenter (a) (the generated status file) and the shared
aggregator: mutate work-state, fire the refresh entry-point, assert the
surface content changed to match.

Plan: docs/plans/work-visibility-surface.md §5.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.work_visibility_presenters import (
    regenerate_status_file,
    status_file_path,
)

from _helpers_d40 import FakeTrackerClient, make_projection


class _MutableTracker:
    """A tracker whose projection view changes between calls (simulating
    a real work-state change between two refresh events)."""

    def __init__(self) -> None:
        self._state: tuple = ()

    def set_state(self, projections: tuple) -> None:
        self._state = projections

    def query_projection_view(self, filter=None):
        return self._state

    def close(self):
        pass


def test_AC_WVS_FRESH_1_file_reflects_state_change(tmp_path: Path) -> None:
    """A work-state change, followed by a refresh, updates the openable
    file — no user pull."""
    backing = _MutableTracker()

    # First refresh: nothing running.
    backing.set_state(())
    path = regenerate_status_file(tmp_path, tracker_factory=lambda: backing)
    assert path == status_file_path(tmp_path)
    first = path.read_text(encoding="utf-8")
    assert "nothing is in progress" in first.lower()

    # Work-state changes: two things now running + one waiting on owner.
    backing.set_state(
        (
            make_projection("a", status="active"),
            make_projection("b", status="active"),
            make_projection("c", status="owner_pending"),
        )
    )
    # Next refresh event.
    regenerate_status_file(tmp_path, tracker_factory=lambda: backing)
    second = path.read_text(encoding="utf-8")

    assert second != first, "AC.WVS-FRESH.1 — the surface must change"
    assert "working on 2" in second.lower()
    assert "waiting on you" in second.lower()


def test_AC_WVS_FRESH_1_file_written_under_loam(tmp_path: Path) -> None:
    """The generated file lives under the gitignored .loam/ user-state
    home (durable, openable, per-workspace)."""
    path = regenerate_status_file(
        tmp_path, tracker_factory=lambda: FakeTrackerClient(query_result=())
    )
    assert path.exists()
    assert ".loam" in path.parts
    assert path.name == "status.txt"
