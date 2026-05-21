"""AC.DTCO.2 — the plan-doc archive (``_stage_plan_doc_archive``)
runs only after the dirty-tree gate passes; source-level
verification by line-order grep on ``_finalize``.

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope B: F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE).

Regression-guard: AC.DTCO.1 verifies the behavior (halt leaves
files at original locations); AC.DTCO.2 verifies the source-order
that mechanism relies on, so a future edit that accidentally
reverts the ordering is caught immediately by a unit test rather
than only at halt time.
"""

from __future__ import annotations

import inspect

from loam_amend.commands import seal as seal_mod


def test_AC_DTCO_2_stage_plan_doc_archive_appears_after_dirty_check():
    """In ``_finalize``, the line numbers of ``_working_tree_dirty(``
    and ``_stage_plan_doc_archive(`` call sites must satisfy
    dirty_check_line < archive_line."""
    src = inspect.getsource(seal_mod._finalize)
    lines = src.splitlines()

    dirty_check_line = None
    archive_line = None
    for i, line in enumerate(lines):
        if "_working_tree_dirty(" in line and dirty_check_line is None:
            dirty_check_line = i
        if "_stage_plan_doc_archive(" in line and archive_line is None:
            archive_line = i

    assert dirty_check_line is not None, (
        "no _working_tree_dirty(...) call found in _finalize"
    )
    assert archive_line is not None, (
        "no _stage_plan_doc_archive(...) call found in _finalize"
    )
    assert dirty_check_line < archive_line, (
        f"_finalize must invoke _working_tree_dirty BEFORE "
        f"_stage_plan_doc_archive (got dirty_check at line "
        f"{dirty_check_line}, archive at line {archive_line}). "
        f"Amendment #138 Scope B revised this order to ensure halts "
        f"leave the working tree pristine."
    )
