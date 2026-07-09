"""AC.SDC.4 — the shared-doc-coverage meta-check is itself a floor member.

Plan: ``docs/plans/shared-doc-guard-floor-coverage.md`` §2 (D-SDC.META-FLOORED).

The meta-check runs at every seal via the guard-floor sweep and cannot be
skipped by a component whose fence excludes it — the anti-rot closure. This
test IS the meta-check's test cohort, so its own path resolving to a floor
member proves the cohort is swept every seal.
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.guard_floor import discover_guard_floor
from loam_amend.shared_doc_coverage import _is_floored

REPO_ROOT = Path(__file__).resolve().parents[5]


def test_this_metacheck_cohort_is_a_floor_member() -> None:
    this_test = str(Path(__file__).resolve().relative_to(REPO_ROOT))
    floor = discover_guard_floor(REPO_ROOT)
    assert _is_floored(this_test, floor), (
        f"the shared-doc-coverage meta-check ({this_test}) is not a "
        "guard-floor member — it would not run at every seal"
    )
