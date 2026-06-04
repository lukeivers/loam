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

"""AC.GOAL.4 — the lens fabricates no ladder.

Plan §6 AC.GOAL.4. Outcome: a work item appears under an objective ONLY
when a real alignment signal connects them; the lens never asserts a
goal->work link the data does not support (the honest-graph invariant,
mirroring AC.REL.4).
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

## litrpg-fiction-pipeline
status: active
objective: Produce the LitRPG series.
completion: seven books shipped.
detail-path: y.md
subgoals:
  - book-1-batch-production
"""


def test_AC_GOAL_4_unaligned_item_does_not_appear_under_a_goal() -> None:
    # The orphan mentions NO objective term — it must NOT be laddered
    # under either goal (it belongs only in the unattributed tail).
    items = [
        make_item("o1", goal="reorganize the garage shelving", status="active"),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    rev_line = next(
        (ln for ln in block.splitlines() if "revenue independence" in ln), ""
    )
    pipe_line = next(
        (ln for ln in block.splitlines() if "litrpg fiction pipeline" in ln),
        "",
    )
    assert "reorganize the garage shelving" not in rev_line
    assert "reorganize the garage shelving" not in pipe_line
    # Both goals are named as no-work (no fabricated ladder).
    assert "nothing is currently moving this goal" in rev_line
    assert "nothing is currently moving this goal" in pipe_line


def test_AC_GOAL_4_item_only_ladders_to_the_objective_it_mentions() -> None:
    """An item mentioning ONLY the revenue term does not also appear under
    the unrelated pipeline objective (no cross-fabrication)."""
    items = [
        make_item("o1", goal="grow revenue-independence assets", status="active"),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    pipe_line = next(
        (ln for ln in block.splitlines() if "litrpg fiction pipeline" in ln),
        "",
    )
    assert "grow revenue-independence assets" not in pipe_line
