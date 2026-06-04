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

"""AC.PRI.5 — the signal WEIGHTING is calibrate-on-use, not hard-coded.

Plan §6 AC.PRI.5. Outcome: changing the weight set changes the resulting
order (a configuration/tuning surface, not a code edit), so the
prioritization can be tuned to the user over time (WMS-D5 / Lens-4 — no
imported magic number).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loam.primary_persona.keep_pace.prioritize import (
    BLOCKING_IMPACT_WEIGHT,
    DEFAULT_SIGNAL_WEIGHTS,
    STALENESS_WEIGHT,
    prioritize,
)

from _wms4_store import make_item


_NOW = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)


def test_AC_PRI_5_changing_weights_changes_the_order() -> None:
    """The SAME items, two weight sets, two orders — no code edit between
    them. An unblock-many item vs a very-stale item: which leads depends
    on the weights."""
    unblocker = make_item("obj-unblock", goal="unblocks downstream", priority="active",
                          edges_out=[("blocks", "obj-c", None)],
                          last_transition_at=_NOW.isoformat())
    c = make_item("obj-c", goal="downstream", priority="active",
                  edges_in=[("blocks", "obj-unblock", None)])
    stale = make_item("obj-stale", goal="ancient task", priority="active",
                      last_transition_at=(_NOW - timedelta(days=90)).isoformat())

    items = [unblocker, c, stale]

    # Weights favouring blocking-impact: the unblocker leads.
    impact_first = prioritize(
        items,
        weights={BLOCKING_IMPACT_WEIGHT: 10.0, STALENESS_WEIGHT: 0.1},
        now=_NOW,
    )
    impact_order = [r.item.objective_id for r in impact_first]

    # Weights favouring staleness: the ancient task leads.
    staleness_first = prioritize(
        items,
        weights={BLOCKING_IMPACT_WEIGHT: 0.1, STALENESS_WEIGHT: 10.0},
        now=_NOW,
    )
    staleness_order = [r.item.objective_id for r in staleness_first]

    assert impact_order.index("obj-unblock") < impact_order.index("obj-stale")
    assert staleness_order.index("obj-stale") < staleness_order.index("obj-unblock")
    assert impact_order != staleness_order, (
        "changing the weight set must change the resulting order "
        f"(impact={impact_order}, staleness={staleness_order})"
    )


def test_AC_PRI_5_default_weights_are_a_mutable_tuning_surface() -> None:
    """The default weights are a named, mutable mapping (a tuning
    surface), NOT an imported magic constant baked into the blend."""
    assert isinstance(DEFAULT_SIGNAL_WEIGHTS, dict)
    assert DEFAULT_SIGNAL_WEIGHTS, "the weight set must be non-empty"
    # Every value is a tunable number, not a sentinel.
    assert all(isinstance(v, (int, float)) for v in DEFAULT_SIGNAL_WEIGHTS.values())
    # The blend reads the weight set: a partial override merges over the
    # defaults (callers tune one signal without restating all of them).
    item = make_item("obj-a", goal="task a", priority="active")
    # An override of one weight is accepted (merge semantics) and does
    # not raise — the calibration surface is partial-override-friendly.
    ranked = prioritize([item], weights={STALENESS_WEIGHT: 5.0}, now=_NOW)
    assert len(ranked) == 1
