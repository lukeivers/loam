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

"""AC.PRI.3 — an explicit owner PIN/DEFER is a HARD override.

Plan §6 AC.PRI.3. Outcome: a pinned item/project ranks FIRST regardless
of its computed signals; a deferred item ranks LAST; removing the
pin/defer returns the item to its computed rank (architecture §4b — "the
user can always override").
"""

from __future__ import annotations

from datetime import datetime, timezone

from loam.primary_persona.keep_pace.prioritize import prioritize

from _wms4_store import make_item


_NOW = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_AC_PRI_3_pin_floats_target_above_computed_blend() -> None:
    """A pinned item floats first even though its computed signals are
    the weakest (a low-priority, edge-less, fresh, orphan item)."""
    weak = make_item("obj-weak", goal="the pinned chore", priority="proposed")
    strong = make_item("obj-strong", goal="the unblocker", priority="active",
                       edges_out=[("blocks", "obj-z", None)])
    z = make_item("obj-z", goal="downstream", priority="active",
                  edges_in=[("blocks", "obj-strong", None)])

    # Without a pin, the strong item leads.
    plain = [r.item.objective_id for r in prioritize([weak, strong, z], now=_NOW)]
    assert plain.index("obj-strong") < plain.index("obj-weak")

    # Pin the weak item — it floats first regardless of the blend.
    pinned = prioritize([weak, strong, z], pinned=frozenset({"obj-weak"}), now=_NOW)
    assert pinned[0].item.objective_id == "obj-weak", (
        f"the pinned item must rank first; order={[r.item.objective_id for r in pinned]}"
    )


def test_AC_PRI_3_pin_by_plain_language_floats_project() -> None:
    """A plain-language pin ("Money is the priority") floats every item
    bound to that project."""
    money1 = make_item("obj-m1", goal="invoice client", priority="proposed",
                      belongs_to_project="money")
    money2 = make_item("obj-m2", goal="chase payment", priority="proposed",
                      belongs_to_project="money")
    other = make_item("obj-o", goal="strong unblocker", priority="active",
                     edges_out=[("blocks", "obj-x", None)])
    x = make_item("obj-x", goal="downstream", priority="active",
                  edges_in=[("blocks", "obj-o", None)])

    ranked = prioritize(
        [money1, money2, other, x],
        pinned=frozenset({"money"}),
        now=_NOW,
    )
    top_two = {ranked[0].item.objective_id, ranked[1].item.objective_id}
    assert top_two == {"obj-m1", "obj-m2"}, (
        f"both Money items must float above the blend; order="
        f"{[r.item.objective_id for r in ranked]}"
    )


def test_AC_PRI_3_defer_demotes_target_below_blend() -> None:
    """A deferred item sinks last even though its computed signals are
    the strongest."""
    strong = make_item("obj-strong", goal="the unblocker", priority="active",
                       edges_out=[("blocks", "obj-z", None)])
    z = make_item("obj-z", goal="downstream", priority="active",
                  edges_in=[("blocks", "obj-strong", None)])
    weak = make_item("obj-weak", goal="minor task", priority="proposed")

    deferred = prioritize([strong, z, weak], deferred=frozenset({"obj-strong"}), now=_NOW)
    assert deferred[-1].item.objective_id == "obj-strong", (
        f"the deferred item must rank last; order="
        f"{[r.item.objective_id for r in deferred]}"
    )


def test_AC_PRI_3_removing_pin_returns_to_computed_rank() -> None:
    """Removing the pin returns the item to its computed rank (the
    override is not sticky)."""
    weak = make_item("obj-weak", goal="the chore", priority="proposed")
    strong = make_item("obj-strong", goal="the unblocker", priority="active",
                       edges_out=[("blocks", "obj-z", None)])
    z = make_item("obj-z", goal="downstream", priority="active",
                  edges_in=[("blocks", "obj-strong", None)])

    with_pin = [r.item.objective_id for r in
                prioritize([weak, strong, z], pinned=frozenset({"obj-weak"}), now=_NOW)]
    assert with_pin[0] == "obj-weak"

    without_pin = [r.item.objective_id for r in prioritize([weak, strong, z], now=_NOW)]
    # Back to the computed order: strong leads, weak is not first.
    assert without_pin[0] != "obj-weak"
    assert without_pin.index("obj-strong") < without_pin.index("obj-weak")
