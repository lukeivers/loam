"""AC.SDC.3 — the meta-check is green on the current tree (zero-FP gate).

Plan: ``docs/plans/shared-doc-guard-floor-coverage.md`` §4.

Evaluated against the floor this cycle registers (the real
``docs/plans/guard-floor.yaml`` resolved on the sealed tree), the meta-check
returns ZERO violations — every file-level universal-admitted doc's
content-guards are floored. This is a HARD gate: the meta-check is itself a
floor member (AC.SDC.4), so a false positive here would break every seal.
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.guard_floor import discover_guard_floor
from loam_amend.shared_doc_coverage import find_uncovered_shared_doc_guards

REPO_ROOT = Path(__file__).resolve().parents[5]


def test_current_tree_has_no_uncovered_shared_doc_guards() -> None:
    floor = discover_guard_floor(REPO_ROOT)
    violations = find_uncovered_shared_doc_guards(REPO_ROOT, floor)
    assert violations == [], (
        "shared-doc guards not covered by the current floor:\n"
        + "\n".join(f"  {v.doc} -> {v.guard_test}" for v in violations)
    )
