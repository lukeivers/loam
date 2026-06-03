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

"""AC.WVS-MR.1 (Slice E) — the work-visibility snapshot reflects EVERY
registered project's ground-truth build state (loam + Cairn), not just
loam.

A snapshot built with a project-state reader covering two projects
carries a COUNT-level ``ProjectStateSummary`` for BOTH, each with its own
built/total counts derived from ITS spec; the rendered surface names both
projects' build state in plain language.

Plan: docs/plans/fbm-multi-repo-work-visibility.md §5.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.work_visibility import (
    ProjectStateSummary,
    build_snapshot,
    render_surface,
)

from _helpers_d40 import FakeTrackerClient


def _two_project_reader() -> tuple[ProjectStateSummary, ...]:
    # A reader covering two registered projects with distinct counts —
    # each from ITS own spec (loam fully built, cairn fully built but a
    # different module count).
    return (
        ProjectStateSummary(name="loam", built=18, total=18),
        ProjectStateSummary(name="cairn", built=5, total=5),
    )


def test_AC_WVS_MR_1_snapshot_carries_both_project_buckets(
    tmp_path: Path,
) -> None:
    """The snapshot carries a per-project bucket for BOTH registered
    projects, each with its own built/total counts."""
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        project_state_reader=_two_project_reader,
    )
    names = {p.name for p in snapshot.project_states}
    assert names == {"loam", "cairn"}
    by_name = {p.name: p for p in snapshot.project_states}
    assert by_name["loam"].built == 18 and by_name["loam"].total == 18
    assert by_name["cairn"].built == 5 and by_name["cairn"].total == 5
    assert snapshot.project_states_unknown is False


def test_AC_WVS_MR_1_render_names_both_projects(tmp_path: Path) -> None:
    """The rendered surface names BOTH projects' build state in plain
    language (count lines, one per project)."""
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        project_state_reader=_two_project_reader,
    )
    surface = render_surface(snapshot)
    lower = surface.lower()
    assert "project loam" in lower
    assert "project cairn" in lower
    # COUNT-level plain phrasing (built / pieces), not a module dump.
    assert "18 of 18 pieces built" in lower
    assert "5 of 5 pieces built" in lower


def test_AC_WVS_MR_1_distinct_counts_per_spec(tmp_path: Path) -> None:
    """Each project's counts come from ITS own summary — a project that
    is partially built shows its own built<total, not loam's."""

    def _reader() -> tuple[ProjectStateSummary, ...]:
        return (
            ProjectStateSummary(name="loam", built=10, total=12),
            ProjectStateSummary(name="cairn", built=5, total=5),
        )

    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        project_state_reader=_reader,
    )
    by_name = {p.name: p for p in snapshot.project_states}
    assert by_name["loam"].built == 10 and by_name["loam"].total == 12
    assert by_name["cairn"].built == 5 and by_name["cairn"].total == 5
    surface = render_surface(snapshot).lower()
    assert "10 of 12 pieces built" in surface
    assert "5 of 5 pieces built" in surface
