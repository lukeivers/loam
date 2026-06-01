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

"""AC.PMROW.2 — FM.COMMS-PATH-DEAD row + the narration-row fold.

Two bindings this cycle lands:

  * FM.COMMS-PATH-DEAD exists, schema-conformant, with a ``guard_ref`` that
    resolves (via the production resolver) to a real importable symbol on the
    merged self-recovery watchdog / comms-liveness guard.

  * the FM.NARRATION-NOT-ACTION row, formerly an empty-ref persona-discipline
    gap, now binds the self-recovery distress-detector symbol — its guard_ref
    resolves to the real distress-classifier on the inbound path.

A guard_ref that does not resolve is the matrix hallucinating its own
coverage, so both are asserted against the real tree via the production
resolver.
"""

from __future__ import annotations

from loam.protection_matrix.catalogue import load_catalogue
from loam.protection_matrix.derive import find_repo_root, resolve_guard_ref


def _row(row_id: str):
    cat = load_catalogue()
    matches = [r for r in cat.rows if r.id == row_id]
    assert matches, f"row {row_id} is absent from the catalogue"
    return matches[0]


def test_AC_PMROW_2_comms_path_dead_row_present_and_schema_conformant() -> None:
    """FM.COMMS-PATH-DEAD exists, floor-class, guard-ref-required kind."""
    row = _row("FM.COMMS-PATH-DEAD")
    assert row.klass == "floor"
    assert row.guard_kind == "hook"
    assert row.guard_ref_required
    assert row.guard_ref, "FM.COMMS-PATH-DEAD must carry a non-empty guard_ref"
    assert row.name
    assert row.description
    assert row.verification


def test_AC_PMROW_2_comms_path_dead_guard_ref_resolves() -> None:
    """The comms-path-dead guard_ref resolves to a real watchdog symbol."""
    row = _row("FM.COMMS-PATH-DEAD")
    root = find_repo_root()
    res = resolve_guard_ref(row.id, row.guard_ref, root)
    assert res.resolved, (
        f"FM.COMMS-PATH-DEAD guard_ref does not resolve: {res.reason()} "
        f"(ref={row.guard_ref!r})"
    )
    assert "self_correction/watchdog.py" in row.guard_ref
    assert res.symbol_part is not None


def test_AC_PMROW_2_narration_row_folded_to_distress_detector() -> None:
    """The narration row's guard now resolves to the distress-detector symbol.

    Formerly an empty-ref persona-discipline gap; the fold binds it to the
    real inbound distress classifier (its unfulfilled-claim class catches the
    narration-not-action distress shape).
    """
    row = _row("FM.NARRATION-NOT-ACTION")
    assert row.guard_ref, (
        "the narration row's guard_ref must no longer be empty after the fold"
    )
    assert row.guard_ref_required, (
        "the folded row binds a hook guard, so its ref must be resolvable"
    )
    assert "distress_detector.py" in row.guard_ref
    root = find_repo_root()
    res = resolve_guard_ref(row.id, row.guard_ref, root)
    assert res.resolved, (
        f"narration-row distress-detector guard_ref does not resolve: "
        f"{res.reason()} (ref={row.guard_ref!r})"
    )
    assert res.symbol_part is not None
