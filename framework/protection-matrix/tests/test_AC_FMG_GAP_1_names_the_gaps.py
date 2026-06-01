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

"""AC.FMG-GAP.1 — the coverage check NAMES the gaps.

A run against the actual guard set emits, as a distinct section of its
output, the floor-class failure modes whose default_on != YES (the gaps). The
list is non-empty iff such modes exist in the manifest. The gaps are the
deliverable (FORK F-3: ship all five floor-class gaps; under-reporting is the
hallucination failure applied to loam's own coverage).
"""

from __future__ import annotations

from pathlib import Path

from loam.protection_matrix.check import render_report, run_coverage_check

# The five floor-class gaps FORK F-3 rules must be present + visible.
EXPECTED_FLOOR_GAPS = {
    "FM.NARRATION-NOT-ACTION",
    "FM.ENV-PERCEPTION-MVC",
    "FM.PROCESS-DRIFT-UNDER-PRESSURE",
    "FM.BUILT-NE-LIVE",
    "FM.DESTRUCTIVE-PRUNE",
}


def test_gap_section_is_distinct_and_names_the_floor_gaps() -> None:
    report = run_coverage_check()
    text = render_report(report)
    assert "GAPS —" in text, "the report must carry a distinct GAP section"
    gap_ids = {v.row.id for v in report.gaps}
    # Every gap is floor-class with default_on != YES (the derived invariant).
    for v in report.gaps:
        assert v.row.is_floor
        assert v.row.default_on != "YES"
        assert v.row.id in text  # named in the rendered output.


def test_all_five_fork_f3_floor_gaps_are_present_and_visible() -> None:
    """FORK F-3: all five floor-class gaps ship as visible rows, not omissions."""
    report = run_coverage_check()
    gap_ids = {v.row.id for v in report.gaps}
    missing = EXPECTED_FLOOR_GAPS - gap_ids
    assert not missing, (
        f"FORK F-3 floor gaps missing from the gap report (under-reporting "
        f"is the recursive FM.HALLUCINATION failure): {missing}"
    )


def test_gap_list_is_nonempty_iff_floor_modes_lack_default_on_guards() -> None:
    report = run_coverage_check()
    has_uncovered_floor = any(
        v.row.is_floor and v.row.default_on != "YES" for v in report.verdicts
    )
    assert bool(report.gaps) == has_uncovered_floor


def test_a_fully_covered_manifest_reports_no_gaps(tmp_path: Path) -> None:
    """Empty-gap path: a manifest whose only floor row is default-on YES."""
    covered = tmp_path / "covered.yaml"
    covered.write_text(
        "schema_version: 1\n"
        "rows:\n"
        "  - id: FM.COVERED\n"
        "    name: covered\n"
        "    description: d\n"
        "    source: s\n"
        "    guard: the boundary gate\n"
        "    guard_kind: release-gate\n"
        "    guard_ref: framework/tools/loam/src/loam_cli/release/gates.py:check_boundary_respected\n"
        "    default_on: YES\n"
        "    class: floor\n"
        "    proportionality_note: ''\n"
        "    verification: v\n",
        encoding="utf-8",
    )
    report = run_coverage_check(catalogue_path=covered)
    assert report.gaps == ()
    assert "GAPS — none" in render_report(report)
