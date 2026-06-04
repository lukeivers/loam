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

"""AC.PLATE.2 — the plate REUSES inc-4's prioritize ordering (no second
ranking).

Plan §6 AC.PLATE.2. Outcome: the plate's ordering + per-item reason are
inc-4's ``prioritize`` output reused — the top plate item is the top
``prioritize`` item among the filtered set, carrying the same transparent
plain-language reason. No second priority logic exists.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loam.primary_persona.keep_pace.plate import render_plate_block
from loam.primary_persona.keep_pace.prioritize import prioritize

from _wms4_store import make_item


def _filtered_set() -> list:
    # An unblocker (B, which C waits on) outranks an independent stale A —
    # the blocking-impact signal dominates (mirrors AC.WMS4.LIVE.1).
    a = make_item(
        "a",
        goal="tidy the independent backlog item",
        status="active",
        last_transition_at="2020-01-01T00:00:00+00:00",
    )
    b = make_item(
        "b",
        goal="build the shared foundation",
        status="active",
        edges_out=[("blocks", "c", None)],
    )
    c_waits = make_item(
        "c",
        goal="ship the feature on the foundation",
        status="active",
        edges_in=[("waits_on", "b", None)],
    )
    return [a, b, c_waits]


def test_AC_PLATE_2_top_item_matches_prioritize_top() -> None:
    now = datetime(2026, 6, 3, tzinfo=timezone.utc)
    items = _filtered_set()

    # The plate's surfaced ordering.
    block = render_plate_block(items=items, objectives_text="", now=now)
    first_line = next(
        (ln for ln in block.splitlines() if ln.strip().startswith("build")
         or "—" in ln),
        "",
    )

    # The independent prioritize call over the SAME filtered set.
    ranked = prioritize(items, now=now)
    top_goal = str(getattr(ranked[0].item, "goal", ""))
    top_reason = ranked[0].reason

    plate_lines = [ln for ln in block.splitlines() if ln.startswith("  ")]
    assert plate_lines, f"the plate must surface rows; block={block!r}"
    # The plate's top row is prioritize's top item + its reason.
    assert top_goal in plate_lines[0], (
        f"the plate top must be prioritize's top item; "
        f"plate_top={plate_lines[0]!r} prioritize_top={top_goal!r}"
    )
    assert top_reason in plate_lines[0], (
        f"the plate must carry prioritize's transparent reason verbatim; "
        f"plate_top={plate_lines[0]!r} reason={top_reason!r}"
    )
