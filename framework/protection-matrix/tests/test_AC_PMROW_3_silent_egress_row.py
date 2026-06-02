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

"""AC.PMROW.3/.4/.5 — the FM.SILENT-EGRESS floor row.

Documents the silent off-machine data-egress failure mode: "loam sends a
user's data / files off their machine for troubleshooting or analytics WITHOUT
explicit, transparent, per-item user consent." Modelled on the
FM.COMMS-PATH-DEAD precedent (a documented floor gap whose guard is named but
not yet default-on-bound) — but the named guard here (the egress-consent gate)
is DESIGNED-not-yet-built, so it has no symbol to resolve. The row therefore
carries the schema's legitimate unbuilt-guard shape (``guard_kind: none``,
empty ``guard_ref``, ``default_on: NONE``) so it records an HONEST floor gap
rather than a hallucinated guard binding — the protection pillar must not
invent coverage it does not have.

  * AC.PMROW.3 — the row exists + is schema-conformant + is NOT a divergence
    (its empty guard_ref is legitimate for its guard_kind).
  * AC.PMROW.4 — the row surfaces as a visible floor GAP (not silently
    omitted).
  * AC.PMROW.5 (outcome-altitude) — a real ``load_catalogue()`` +
    ``run_coverage_check()`` at the production entry-point, no pre-arranged
    state: the row parses, adds zero new divergence, and appears among the
    live coverage gaps.
"""

from __future__ import annotations

from loam.protection_matrix.catalogue import load_catalogue
from loam.protection_matrix.check import render_report, run_coverage_check


_ROW_ID = "FM.SILENT-EGRESS"


def _row(row_id: str):
    cat = load_catalogue()
    matches = [r for r in cat.rows if r.id == row_id]
    assert matches, f"row {row_id} is absent from the catalogue"
    return matches[0]


def test_AC_PMROW_3_silent_egress_row_present_and_schema_conformant() -> None:
    """FM.SILENT-EGRESS exists, floor-class, with a legitimate empty ref."""
    row = _row(_ROW_ID)
    assert row.klass == "floor"
    # The named guard (egress-consent gate) is designed-not-yet-built → no
    # symbol → the unbuilt-guard shape: a kind that does NOT obligate a
    # resolvable guard_ref, with an empty ref (NOT a hallucinated binding).
    assert row.guard_kind == "none"
    assert not row.guard_ref_required
    assert row.guard_ref == "", (
        "the unbuilt egress-consent gate has no symbol — the ref must be "
        "empty, never a hallucinated binding"
    )
    assert row.default_on == "NONE"
    # Every other required field is present + meaningful.
    assert row.name
    assert row.description
    assert row.source
    assert row.guard  # names the future egress-consent gate
    assert row.verification


def test_AC_PMROW_3_silent_egress_row_is_not_a_divergence() -> None:
    """The empty-ref row is NOT flagged as a claimed-but-absent over-claim.

    A divergence is a row whose kind OBLIGATES a resolvable guard_ref but whose
    ref does not resolve. FM.SILENT-EGRESS uses a non-obligating kind with an
    empty ref, so it must not appear in the divergence set — the honest gap is
    recorded without the matrix hallucinating coverage.
    """
    report = run_coverage_check()
    diverged = {v.row.id for v in report.divergences}
    assert _ROW_ID not in diverged, (
        f"{_ROW_ID} must not be a divergence — its empty guard_ref is "
        f"legitimate for guard_kind 'none'"
    )


def test_AC_PMROW_4_silent_egress_surfaces_as_a_visible_floor_gap() -> None:
    """The row is named in the distinct GAP section (not silently omitted)."""
    report = run_coverage_check()
    gap_ids = {v.row.id for v in report.gaps}
    assert _ROW_ID in gap_ids, (
        f"{_ROW_ID} is floor-class with default_on != YES — it must surface "
        f"as a gap (under-reporting is the recursive FM.HALLUCINATION failure)"
    )
    text = render_report(report)
    assert "GAPS —" in text
    assert _ROW_ID in text


def test_AC_PMROW_5_outcome_altitude_real_load_and_coverage() -> None:
    """Outcome-altitude: real shipped-catalogue load + live coverage check.

    No pre-arranged state — ``load_catalogue()`` over the shipped file and
    ``run_coverage_check()`` over the shipped catalogue + the live tree.
    """
    # Real load of the shipped catalogue parses the row.
    cat = load_catalogue()
    assert any(r.id == _ROW_ID for r in cat.rows)
    # Real coverage check over ground truth: the row is a gap, not a divergence.
    report = run_coverage_check()
    assert _ROW_ID in {v.row.id for v in report.gaps}
    assert _ROW_ID not in {v.row.id for v in report.divergences}
