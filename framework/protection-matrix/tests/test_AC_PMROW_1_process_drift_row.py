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

"""AC.PMROW.1 — the FM.PROCESS-DRIFT row exists + binds a REAL guard.

The owed defined-workflow row is in the catalogue, schema-conformant, and its
``guard_ref`` resolves (via the production resolver, not a string compare) to
a real importable symbol on the merged defined-workflow re-injection guard —
the same real-guard-binding contract every guard-ref-required row obeys
(AC.FMG-CAT.2). A hallucinated guard_ref is exactly the failure the matrix
exists to prevent, so this asserts resolution against the real tree.
"""

from __future__ import annotations

from loam.protection_matrix.catalogue import load_catalogue
from loam.protection_matrix.derive import find_repo_root, resolve_guard_ref


def _row(row_id: str):
    cat = load_catalogue()
    matches = [r for r in cat.rows if r.id == row_id]
    assert matches, f"row {row_id} is absent from the catalogue"
    return matches[0]


def test_AC_PMROW_1_process_drift_row_present_and_schema_conformant() -> None:
    """FM.PROCESS-DRIFT exists, floor-class, with a guard-ref-required kind."""
    row = _row("FM.PROCESS-DRIFT")
    assert row.klass == "floor"
    assert row.guard_kind == "hook"
    assert row.guard_ref_required, (
        "a hook row must obligate a resolvable guard_ref"
    )
    assert row.guard_ref, "FM.PROCESS-DRIFT must carry a non-empty guard_ref"
    # Plain-language sanity: the row names the defined-workflow / flow drift.
    assert row.name
    assert row.description
    assert row.verification


def test_AC_PMROW_1_guard_ref_resolves_to_a_real_symbol() -> None:
    """The guard_ref resolves to a real path+symbol on the merged guard."""
    row = _row("FM.PROCESS-DRIFT")
    root = find_repo_root()
    res = resolve_guard_ref(row.id, row.guard_ref, root)
    assert res.resolved, (
        f"FM.PROCESS-DRIFT guard_ref does not resolve: {res.reason()} "
        f"(ref={row.guard_ref!r})"
    )
    # It binds the defined-workflow re-injection guard specifically.
    assert "flows/reinject.py" in row.guard_ref
    assert res.symbol_part is not None, (
        "the binding must name a symbol, not just a path"
    )
