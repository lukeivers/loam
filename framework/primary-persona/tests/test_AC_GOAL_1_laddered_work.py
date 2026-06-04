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

"""AC.GOAL.1 — the goals lens ladders open work under the right objective.

Plan §6 AC.GOAL.1. Outcome: given a real work-item set + a real
OBJECTIVES register with active objectives, the goals lens renders, per
active objective, the open work that advances it (laddered via the
existing alignment text-match), in ONE concise capped block.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.goals import render_goals_block

from _wms4_store import make_item

# A real two-objective register (mirrors the seeded shape) — the active
# objectives the work must ladder to.
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


def test_AC_GOAL_1_work_appears_under_the_right_objective() -> None:
    items = [
        make_item(
            "o1",
            goal="push the revenue-independence plan forward",
            status="active",
        ),
        make_item(
            "o2",
            goal="finish book-1-batch-production for the pipeline",
            status="active",
        ),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    assert block, f"the goals lens must render a block; block={block!r}"
    # Each item ladders under the objective whose term its goal mentions.
    lines = block.splitlines()
    rev_line = next((ln for ln in lines if "revenue independence" in ln), "")
    pipe_line = next(
        (ln for ln in lines if "litrpg fiction pipeline" in ln), ""
    )
    assert "push the revenue-independence plan forward" in rev_line, (
        f"revenue work must ladder under revenue-independence; block={block!r}"
    )
    assert "finish book-1-batch-production for the pipeline" in pipe_line, (
        f"pipeline work must ladder under the pipeline goal; block={block!r}"
    )


def test_AC_GOAL_1_subgoal_mention_ladders_to_its_objective() -> None:
    """An item mentioning a SUBGOAL label (not the slug) still ladders to
    its parent objective — the alignment terms include subgoal labels."""
    items = [
        make_item(
            "o1",
            goal="work on fiction-catalog-as-passive-asset",
            status="active",
        ),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    rev_line = next(
        (ln for ln in block.splitlines() if "revenue independence" in ln), ""
    )
    assert "fiction-catalog-as-passive-asset" in rev_line
