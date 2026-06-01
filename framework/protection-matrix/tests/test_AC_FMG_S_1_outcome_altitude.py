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

"""★ AC.FMG-S.1 — OUTCOME-ALTITUDE: a real coverage-check at the PRODUCTION
entry-point.

``outcome-altitude: true``. This AC may NOT be satisfied by a unit test that
pre-seeds the manifest or stubs the guard set. It invokes the PRODUCTION
``loam guards`` entry-point through the unified ``loam`` CLI dispatcher
(``loam_cli.cli.main(["guards"])`` — the same resolution a real shell
invocation uses), with NO pre-arranged state, against the REAL installed
guard set (the shipped catalogue + the live tree). It asserts:

  (a) the verb succeeds (exit 0 — FORK F-2: the reporter never fails on gaps);
  (b) the floor invariant is asserted — EVERY ``class: floor`` row is checked
      for a default-on guard; and
  (c) every floor row lacking a default-on guard is emitted in the gap
      section.

(feedback_test_outcome_altitude_required: the entry-point must walk the real
tree; a STUB-class pre-seeded-manifest test does NOT satisfy this AC.)
"""

from __future__ import annotations

import io
from contextlib import redirect_stdout

from loam_cli.cli import main as loam_main

from loam.protection_matrix.check import run_coverage_check


def test_AC_FMG_S_1_production_entrypoint_real_guard_set_floor_invariant() -> None:
    """The real `loam guards` verb, no pre-arranged state, against the live
    tree: exits 0, asserts the floor invariant, and emits every uncovered
    floor row in the gap section."""
    # --- (a) the PRODUCTION entry-point through the unified dispatcher ---
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = loam_main(["guards"])  # no --catalogue, no --repo-root: REAL set.
    assert rc == 0, "the coverage reporter must exit 0 even with open gaps"
    output = buf.getvalue()

    # --- (b) the floor invariant: every floor row was checked ---
    # Re-derive the SAME real report the verb printed (no pre-seeding) to
    # assert against ground truth, then confirm the printed output agrees.
    report = run_coverage_check()
    assert report.floor_verdicts, "the real tree must carry floor-class rows"
    assert report.floor_invariant_checked, (
        "every floor-class row must be checked for a default-on guard"
    )
    # Every floor row is named in the real printed coverage section.
    assert "FLOOR-CLASS COVERAGE" in output
    for v in report.floor_verdicts:
        assert v.row.id in output, (
            f"floor row {v.row.id} not surfaced by the real verb output"
        )

    # --- (c) every uncovered floor row appears in the gap section ---
    assert "GAPS —" in output
    real_gaps = [v.row.id for v in report.gaps]
    assert real_gaps, (
        "given the Tier-0 row set, the real tree MUST surface floor gaps "
        "(an empty gap report would be a false-negative — plan §8)"
    )
    # The gap section of the printed output names each uncovered floor row.
    gap_section = output.split("GAPS —", 1)[1].split("=" * 70, 1)[0]
    for gid in real_gaps:
        assert gid in gap_section, (
            f"uncovered floor row {gid} missing from the printed gap section"
        )


def test_AC_FMG_S_1_no_divergence_in_the_real_shipped_catalogue() -> None:
    """The real run reconciles clean — no claimed guard is absent from the
    tree (the protection pillar does not hallucinate its own coverage)."""
    report = run_coverage_check()
    assert report.divergences == (), (
        "the shipped catalogue claims a guard the real tree lacks: "
        f"{[v.divergence_detail() for v in report.divergences]}"
    )
