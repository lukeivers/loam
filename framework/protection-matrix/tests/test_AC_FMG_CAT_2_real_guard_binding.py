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

"""AC.FMG-CAT.2 — every row binds to a REAL, citable guard or an explicit gap.

For every row whose guard_kind is not none/persona-discipline, the guard_ref
resolves to a path+symbol that exists in the tree at check-time. No row may
claim a guard that isn't there; an unresolved guard is reported as a
divergence (no invented guards — the protection pillar must not hallucinate
its own coverage).
"""

from __future__ import annotations

from pathlib import Path

from loam.protection_matrix.catalogue import load_catalogue
from loam.protection_matrix.check import run_coverage_check
from loam.protection_matrix.derive import find_repo_root, resolve_guard_ref


def test_every_guard_ref_required_row_resolves_against_the_real_tree() -> None:
    """Every hook/gate/comparator/memory row's guard_ref resolves for real."""
    cat = load_catalogue()
    root = find_repo_root()
    unresolved = []
    for row in cat.rows:
        if not row.guard_ref_required:
            continue
        res = resolve_guard_ref(row.id, row.guard_ref, root)
        if not res.resolved:
            unresolved.append((row.id, res.reason()))
    assert unresolved == [], (
        f"rows claiming a guard the tree does not carry: {unresolved}"
    )


def test_no_invented_guards_shipped_catalogue_has_zero_divergences() -> None:
    """The shipped catalogue over-claims NOTHING — zero divergences."""
    report = run_coverage_check()
    assert report.divergences == (), (
        "shipped catalogue claims a guard the real tree does not carry: "
        f"{[v.divergence_detail() for v in report.divergences]}"
    )


def test_an_absent_guard_is_reported_as_a_divergence(tmp_path: Path) -> None:
    """A row claiming a guard the tree lacks is flagged (not silently passed)."""
    bad = tmp_path / "claims-absent-guard.yaml"
    bad.write_text(
        "schema_version: 1\n"
        "rows:\n"
        "  - id: FM.PHANTOM\n"
        "    name: phantom\n"
        "    description: d\n"
        "    source: s\n"
        "    guard: a guard that does not exist\n"
        "    guard_kind: release-gate\n"
        "    guard_ref: framework/tools/loam/src/loam_cli/release/gates.py:check_NONEXISTENT\n"
        "    default_on: YES\n"
        "    class: floor\n"
        "    proportionality_note: ''\n"
        "    verification: v\n",
        encoding="utf-8",
    )
    report = run_coverage_check(catalogue_path=bad)
    ids = {v.row.id for v in report.divergences}
    assert "FM.PHANTOM" in ids
