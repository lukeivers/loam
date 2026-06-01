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

"""AC.FMG-CHECK.2 — the check derives the guard set from GROUND TRUTH, not the
manifest's own claim.

For a guard the manifest claims exists, the check confirms it is actually
present in the tree (path+symbol resolution / release-gate membership); a
manifest claim that contradicts ground truth is reported as a divergence.
Mirrors the substrate-audit comparator (manifest-claim vs wired-reality).
"""

from __future__ import annotations

from pathlib import Path

from loam.protection_matrix.check import run_coverage_check
from loam.protection_matrix.derive import find_repo_root, resolve_guard_ref


def test_a_real_release_gate_symbol_resolves_against_ground_truth() -> None:
    """A claimed release-gate guard resolves to the real ALL_GATES member."""
    root = find_repo_root()
    res = resolve_guard_ref(
        "FM.BOUNDARY-VIOLATION",
        "framework/tools/loam/src/loam_cli/release/gates.py:check_boundary_respected",
        root,
    )
    assert res.resolved
    assert res.symbol_part == "check_boundary_respected"


def test_a_fabricated_symbol_does_not_resolve() -> None:
    """A symbol absent from the real file is ground-truth-false."""
    root = find_repo_root()
    res = resolve_guard_ref(
        "FM.FAKE",
        "framework/tools/loam/src/loam_cli/release/gates.py:check_DOES_NOT_EXIST",
        root,
    )
    assert not res.resolved
    assert res.path_exists  # the file is real...
    assert res.symbol_defined is False  # ...but the symbol is not.


def test_a_manifest_over_claim_is_flagged_as_divergence(tmp_path: Path) -> None:
    """A manifest that claims default_on:YES via an absent guard is flagged.

    The reconcile keys off GROUND TRUTH: the row asserts a hook guard, but the
    referenced file does not exist, so the check reports a divergence rather
    than trusting the manifest's own claim.
    """
    over = tmp_path / "over-claim.yaml"
    over.write_text(
        "schema_version: 1\n"
        "rows:\n"
        "  - id: FM.OVERCLAIM\n"
        "    name: over\n"
        "    description: d\n"
        "    source: s\n"
        "    guard: a hook that is not wired\n"
        "    guard_kind: hook\n"
        "    guard_ref: framework/safety-layer/hooks/this_hook_does_not_exist.py\n"
        "    default_on: YES\n"
        "    class: floor\n"
        "    proportionality_note: ''\n"
        "    verification: v\n",
        encoding="utf-8",
    )
    report = run_coverage_check(catalogue_path=over)
    diverged = {v.row.id for v in report.divergences}
    assert "FM.OVERCLAIM" in diverged
