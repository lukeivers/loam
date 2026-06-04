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

"""AC.GOAL.3 — open work laddering to no objective is not silently dropped.

Plan §6 AC.GOAL.3. Outcome: open work that ladders to NO objective
surfaces as an "unattributed open work" tail (the derivation-cost
mitigation) — no work item vanishes from the union of (laddered +
unattributed).
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.goals import render_goals_block

from _wms4_store import make_item

_OBJECTIVES = """# user-objectives

## revenue-independence
status: active
objective: Build financial independence.
completion: passive income covers the floor.
detail-path: x.md
subgoals:
  - fiction-catalog-as-passive-asset
"""


def test_AC_GOAL_3_unattributed_open_work_surfaces() -> None:
    items = [
        make_item("o1", goal="advance revenue-independence", status="active"),
        # An orphan whose goal text mentions no objective term.
        make_item("o2", goal="fix the leaky kitchen faucet", status="active"),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    assert "not tied to a goal yet" in block, (
        f"unattributed open work must surface as a tail; block={block!r}"
    )
    assert "fix the leaky kitchen faucet" in block, (
        f"the orphan item must not vanish; block={block!r}"
    )


def test_AC_GOAL_3_no_open_item_vanishes_from_the_union() -> None:
    """Every open item appears EITHER laddered under an objective OR in the
    unattributed tail — the union covers all open work."""
    items = [
        make_item("o1", goal="advance revenue-independence", status="active"),
        make_item("o2", goal="paint the back fence", status="active"),
        make_item("o3", goal="call the insurance company", status="active"),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    for goal in (
        "advance revenue-independence",
        "paint the back fence",
        "call the insurance company",
    ):
        assert goal in block, (
            f"open item {goal!r} vanished from the union; block={block!r}"
        )
