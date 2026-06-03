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

"""AC.PMROW.6/.7/.8/.9 — the FM.DROPPED-OPEN-LOOPS floor row.

Documents a genuine, currently-uncatalogued failure mode (owner-prompted,
Telegram 13573): "the assistant DROPS ITS OWN OPEN LOOPS — deferred work,
follow-ups, and rechecks it intended to revisit are never revisited; it acts
only when prompted and silently forgets its outstanding obligations."

Coverage is HONESTLY PARTIAL. The named guard — the persona
self-scheduled-recheck mechanism (task #79) — has its first instance LIVE, but
that instance lives in the OPERATOR's personal environment (launchd jobs), NOT
in canonical loam; the reusable, productized, default-on self-recheck SKILL +
pending-rechecks register is SCOPED, not yet built. There is therefore no
symbol in the loam tree to resolve, so the row takes the FM.SILENT-EGRESS
unbuilt-guard shape (``guard_kind: none``, empty ``guard_ref``,
``default_on: NONE``) — an HONEST floor gap, NOT a hallucinated full-coverage
claim (the protection pillar must not invent coverage it does not have).

  * AC.PMROW.6 — the row exists + is schema-conformant + its empty guard_ref
    is legitimate for its guard_kind.
  * AC.PMROW.7 — the row is NOT a divergence (no over-claim).
  * AC.PMROW.8 — the row surfaces as a visible floor GAP (not silently
    omitted).
  * AC.PMROW.9 (outcome-altitude) — a real ``load_catalogue()`` +
    ``run_coverage_check()`` at the production entry-point, no pre-arranged
    state: the row parses, adds zero new divergence, appears among the live
    coverage gaps, and the coverage is honest-partial (guard text names both
    the live instance and the not-yet-built productized capability;
    ``default_on != "YES"``).
"""

from __future__ import annotations

from loam.protection_matrix.catalogue import load_catalogue
from loam.protection_matrix.check import render_report, run_coverage_check


_ROW_ID = "FM.DROPPED-OPEN-LOOPS"


def _row(row_id: str):
    cat = load_catalogue()
    matches = [r for r in cat.rows if r.id == row_id]
    assert matches, f"row {row_id} is absent from the catalogue"
    return matches[0]


def test_AC_PMROW_6_dropped_open_loops_row_present_and_schema_conformant() -> None:
    """FM.DROPPED-OPEN-LOOPS exists, floor-class, with a legitimate empty ref."""
    row = _row(_ROW_ID)
    assert row.klass == "floor"
    # The named guard (the self-recheck SKILL + register) is scoped-not-yet-built
    # in the canonical tree → no symbol → the unbuilt-guard shape: a kind that
    # does NOT obligate a resolvable guard_ref, with an empty ref (NOT a
    # hallucinated binding).
    assert row.guard_kind == "none"
    assert not row.guard_ref_required
    assert row.guard_ref == "", (
        "the not-yet-built self-recheck capability has no symbol in the "
        "canonical tree — the ref must be empty, never a hallucinated binding"
    )
    assert row.default_on == "NONE"
    # Every other required field is present + meaningful.
    assert row.name
    assert row.description
    assert row.source
    assert row.guard  # names the task-#79 mechanism + the future SKILL/register
    assert row.verification


def test_AC_PMROW_6_coverage_is_honestly_partial_not_overclaimed() -> None:
    """The row records HONEST PARTIAL coverage, not a faked full-coverage claim.

    The value of the matrix is that it does not pretend protection that isn't
    there. The guard text must name BOTH the live instance (task #79) AND the
    not-yet-built productized capability; the row must NOT claim default-on.
    """
    row = _row(_ROW_ID)
    guard = row.guard.lower()
    verification = row.verification.lower()
    # Names the live first instance.
    assert "live" in guard
    assert "task #79" in row.guard
    # Names the not-yet-built reusable capability (the honest partial).
    assert "not yet built" in guard
    assert ("skill" in guard) and ("register" in guard)
    # And does NOT overclaim coverage.
    assert row.default_on != "YES"
    assert "not yet built" in verification or "scoped" in verification


def test_AC_PMROW_7_dropped_open_loops_row_is_not_a_divergence() -> None:
    """The empty-ref row is NOT flagged as a claimed-but-absent over-claim.

    A divergence is a row whose kind OBLIGATES a resolvable guard_ref but whose
    ref does not resolve. FM.DROPPED-OPEN-LOOPS uses a non-obligating kind with
    an empty ref, so it must not appear in the divergence set — the honest gap
    is recorded without the matrix hallucinating coverage.
    """
    report = run_coverage_check()
    diverged = {v.row.id for v in report.divergences}
    assert _ROW_ID not in diverged, (
        f"{_ROW_ID} must not be a divergence — its empty guard_ref is "
        f"legitimate for guard_kind 'none'"
    )


def test_AC_PMROW_8_dropped_open_loops_surfaces_as_a_visible_floor_gap() -> None:
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


def test_AC_PMROW_9_outcome_altitude_real_load_and_coverage() -> None:
    """Outcome-altitude: real shipped-catalogue load + live coverage check.

    No pre-arranged state — ``load_catalogue()`` over the shipped file and
    ``run_coverage_check()`` over the shipped catalogue + the live tree: the
    row parses, adds zero new divergence, appears among the live gaps, and the
    coverage is honest-partial (default_on != YES).
    """
    # Real load of the shipped catalogue parses the row.
    cat = load_catalogue()
    matches = [r for r in cat.rows if r.id == _ROW_ID]
    assert matches, f"{_ROW_ID} absent from the shipped catalogue"
    row = matches[0]
    assert row.default_on != "YES", "honest-partial: the row must not overclaim"
    # Real coverage check over ground truth: the row is a gap, not a divergence.
    report = run_coverage_check()
    assert _ROW_ID in {v.row.id for v in report.gaps}
    assert _ROW_ID not in {v.row.id for v in report.divergences}
