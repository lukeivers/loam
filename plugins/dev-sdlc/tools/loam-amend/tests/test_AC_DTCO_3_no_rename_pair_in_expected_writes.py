"""AC.DTCO.3 — the ``expected_writes`` set computed before the
dirty-tree gate no longer includes the plan-doc / manifest rename
pair (those paths haven't moved when the gate runs).

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope B: F-SEAL-DIRTY-TREE-CHECK-AFTER-PLAN-ARCHIVE).

The pre-amendment-#138 code at lines 689-697 iterated
``archive_renames`` and admitted both old + new paths into
``expected_writes`` so the staged-by-``git mv`` rename pair did not
trigger the dirty filter. Post-amendment, the rename happens
AFTER the gate, so the filter is unnecessary — and an
``archive_renames``-based filter sitting before the gate would be
populated only with the pre-archive paths (i.e., it would do
nothing).

This test verifies the filter is gone (source-level grep).
"""

from __future__ import annotations

import inspect

from loam_amend.commands import seal as seal_mod


def test_AC_DTCO_3_archive_renames_filter_removed_from_finalize():
    """The pre-amendment-#138 ``for old_path, new_path in
    archive_renames`` loop must be absent from ``_finalize``. Its
    purpose was to admit staged-rename paths into the dirty-tree
    filter; after the reorder, the staging happens after the gate
    so the filter is unnecessary."""
    src = inspect.getsource(seal_mod._finalize)
    assert "archive_renames" not in src, (
        "the ``archive_renames`` list (and the loop that populated "
        "the rename-pair into ``expected_writes``) must be removed "
        "from _finalize per amendment #138 Scope B (AC.DTCO.3). "
        "The rename happens after the dirty-tree gate now, so the "
        "filter is unnecessary."
    )
