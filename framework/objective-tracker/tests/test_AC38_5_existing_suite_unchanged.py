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

"""AC38.5 — Existing tracker test suite passes unchanged.

Plan: docs/rebuild/plans/amendment-38-objective-tracker-schema-widening.md
§4 AC38.5.

Outcome (paraphrased from the AC):

  - The pre-existing `objective-tracker/tests/` suite (D1–D9 + cross-
    cutting) passes after the widening lands without any test
    modification.
  - New tests under `test_AC38_*.py` are additive.
  - No pre-existing test edited.

The full-suite green check is the test runner itself (`pytest
tests/`); this file structurally asserts the file-list discipline:
the pre-existing test filenames are still present and no AC38 test
attempts to import a renamed predecessor.

Method choice: enumerate the baseline file set explicitly here so a
silent rename of a baseline test (which would silently regress
coverage) becomes a failed assertion at this layer.
"""

from __future__ import annotations

from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent

BASELINE_TEST_FILES = (
    "test_d1_objective_primitive.py",
    "test_d2_hierarchy.py",
    "test_d2b_parent_close.py",
    "test_d3_criterion_union.py",
    "test_d4_scope_binding.py",
    "test_d5_authored_by.py",
    "test_d6_odd_integration.py",
    "test_d7_otel_emission.py",
    "test_d8_upgrade_fidelity.py",
)


def test_AC38_5_baseline_test_files_present() -> None:
    """Every D1–D8 baseline test file still ships unrenamed."""
    for fname in BASELINE_TEST_FILES:
        assert (TESTS_DIR / fname).exists(), (
            f"Baseline test file vanished: {fname}. AC38.5 requires "
            f"the existing suite to ship unchanged."
        )


def test_AC38_5_amendment_test_files_present() -> None:
    """The new amendment-38 test files are present alongside the
    baseline suite — additive coverage, not replacement."""
    for ac in ("1_lifted_from_field", "2_round_trip_preservation",
               "3_query_projection_view", "4_d8_lifted_from_probes",
               "5_existing_suite_unchanged"):
        f = TESTS_DIR / f"test_AC38_{ac}.py"
        assert f.exists(), f"AC38 test file missing: {f.name}"


def test_AC38_5_seal_diff_test_present() -> None:
    """AC38.S sibling — the seal-diff test ships in this amendment
    (objective-tracker's first sealed-component sidecar surface)."""
    assert (TESTS_DIR / "test_no_sealed_amendments.py").exists(), (
        "Seal-diff test missing; AC38.S enforcement absent."
    )
