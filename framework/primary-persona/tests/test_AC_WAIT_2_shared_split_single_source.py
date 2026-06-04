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

"""AC.WAIT.2 — the split is computed by ONE shared helper, two call sites.

Plan §6 AC.WAIT.2. Outcome: the on-me/on-others split is computed by the
SAME logic ``relational.py`` uses — a single shared helper produces both
``relational.py``'s waiting rows AND the standalone lens's rows; there is
NO second waiting-on implementation. Verifiable: exactly one function
computes the split; both call sites consume it.
"""

from __future__ import annotations

import inspect

from loam.primary_persona.keep_pace import relational, waiting_on
from loam.primary_persona.keep_pace import waiting_split
from loam.primary_persona.keep_pace.waiting_split import (
    WaitingSplit,
    compute_waiting_split,
)

from _wms4_store import make_item


def test_AC_WAIT_2_both_call_sites_import_the_shared_helper() -> None:
    # relational.py's waiting rows are produced via the shared helper.
    rel_src = inspect.getsource(relational._waiting_rows)
    assert "compute_waiting_split" in rel_src, (
        "relational._waiting_rows must call the shared compute_waiting_split"
    )
    assert "waiting_rows_from_split" in rel_src, (
        "relational must render via the shared split-to-rows helper"
    )

    # The standalone lens calls the SAME shared helper.
    wo_src = inspect.getsource(waiting_on.render_waiting_on_block)
    assert "compute_waiting_split" in wo_src, (
        "the standalone lens must call the shared compute_waiting_split"
    )


def test_AC_WAIT_2_no_second_owner_pending_split_in_either_module() -> None:
    """Neither module re-implements the owner_pending / external-party
    split inline — the only computation lives in waiting_split.py."""
    for mod in (relational, waiting_on):
        src = inspect.getsource(mod)
        # The split's defining predicate (owner_pending status read) must
        # NOT be re-implemented in the consuming modules.
        assert 'status' not in src or '== "owner_pending"' not in src, (
            f"{mod.__name__} must not re-implement the owner_pending split; "
            f"the split lives only in waiting_split.py"
        )


def test_AC_WAIT_2_shared_helper_is_the_single_computation() -> None:
    """The shared helper produces the structured split both sites consume.
    A pure call over a fixture set returns the on-me / on-others split."""

    class _Tracker:
        def waiting_on_other(self):
            return [
                make_item(
                    "x",
                    goal="vendor task",
                    edges_out=[("waits_on", None, "Vendor")],
                )
            ]

    open_items = [
        make_item("p", goal="decide the thing", status="owner_pending"),
        make_item("a", goal="ordinary active", status="active"),
    ]
    split = compute_waiting_split(_Tracker(), open_items)
    assert isinstance(split, WaitingSplit)
    assert split.mine == ["decide the thing"]
    assert split.others == ["vendor task (on Vendor)"]
