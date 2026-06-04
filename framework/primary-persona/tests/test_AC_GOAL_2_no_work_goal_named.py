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

"""AC.GOAL.2 — an objective with no advancing work is NAMED.

Plan §6 AC.GOAL.2. Outcome: an active objective with NO work moving it
surfaces explicitly as "nothing is currently moving this goal" — never
silently omitted (the "what goals have no work" architecture
requirement).
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


def test_AC_GOAL_2_objective_with_no_work_is_named() -> None:
    # Only revenue work exists; the pipeline goal has nothing moving it.
    items = [
        make_item(
            "o1",
            goal="advance revenue-independence this week",
            status="active",
        ),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    pipe_line = next(
        (
            ln
            for ln in block.splitlines()
            if "litrpg fiction pipeline" in ln
        ),
        "",
    )
    assert pipe_line, (
        f"the no-work goal must still appear, never be omitted; block={block!r}"
    )
    assert "nothing is currently moving this goal" in pipe_line, (
        f"a no-work goal must be NAMED as such; line={pipe_line!r}"
    )
