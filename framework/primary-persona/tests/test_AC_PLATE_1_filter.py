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

"""AC.PLATE.1 — the on-my-plate filter is correct (D-WMS5.6).

Plan §6 AC.PLATE.1. Outcome: the lens renders exactly the items matching
the D-WMS5.6 filter — active/owner_pending, NOT blocked, NOT waiting on an
external party, NOT deferred, NOT proposed. A blocked item and a
waiting-on-others item do NOT appear on the plate.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.plate import render_plate_block

from _wms4_store import make_item


def test_AC_PLATE_1_filter_includes_only_actionable_items() -> None:
    items = [
        make_item("a", goal="write the launch email", status="active"),
        make_item("p", goal="decide the launch date", status="owner_pending"),
        make_item("b", goal="ship the blocked feature", status="blocked"),
        make_item("prop", goal="maybe explore a new market", status="proposed"),
        # Waiting on an external party — off the plate.
        make_item(
            "w",
            goal="wait for the vendor quote",
            status="active",
            edges_out=[("waits_on", None, "Vendor")],
        ),
    ]
    block = render_plate_block(items=items, objectives_text="")
    assert block, f"the plate must render a block; block={block!r}"

    # On the plate: active + owner_pending, non-blocked, non-waiting.
    assert "write the launch email" in block
    assert "decide the launch date" in block

    # Off the plate: blocked, proposed, waiting-on-others.
    assert "ship the blocked feature" not in block, "blocked item must be off the plate"
    assert "maybe explore a new market" not in block, "proposed item must be off the plate"
    assert "wait for the vendor quote" not in block, (
        "an item waiting on an external party must be off the plate"
    )


def test_AC_PLATE_1_deferred_item_is_off_the_plate() -> None:
    items = [
        make_item("a", goal="active focus task", status="active"),
        make_item("d", goal="the deferred side project", status="active"),
    ]
    # An explicit owner defer matching the side-project goal text.
    block = render_plate_block(
        items=items,
        objectives_text="",
        deferred=frozenset({"deferred side project"}),
    )
    assert "active focus task" in block
    assert "the deferred side project" not in block, (
        "an explicitly-deferred item must be off the plate"
    )
