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

"""AC.LENS.1 — each lens renders ONE concise capped fail-soft block.

Plan §6 AC.LENS.1. Outcome: each of the three lenses renders ONE concise
block within the Slice-D char cap, fail-soft (any boundary error -> empty
block, the render proceeds), composing the same cap discipline the sealed
lenses use — not three new walls of text.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.keep_pace.goals import (
    _GOALS_BLOCK_CHAR_CAP,
    render_goals_block,
)
from loam.primary_persona.keep_pace.plate import (
    _PLATE_BLOCK_CHAR_CAP,
    render_plate_block,
)
from loam.primary_persona.keep_pace.waiting_on import (
    _WAITING_ON_BLOCK_CHAR_CAP,
    render_waiting_on_block,
)

from _wms4_store import make_item

_OBJECTIVES = """# user-objectives

## revenue-independence
status: active
objective: Build financial independence.
completion: done.
detail-path: x.md
subgoals:
  - fiction-catalog-as-passive-asset
"""


def test_AC_LENS_1_goals_block_within_cap() -> None:
    # Many advancing items — the block stays within the cap (one concise
    # block, not a wall).
    items = [
        make_item(f"o{i}", goal=f"revenue-independence task number {i}", status="active")
        for i in range(40)
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    assert block
    assert len(block) <= _GOALS_BLOCK_CHAR_CAP


def test_AC_LENS_1_plate_block_within_cap() -> None:
    items = [
        make_item(f"o{i}", goal=f"active plate task number {i}", status="active")
        for i in range(40)
    ]
    block = render_plate_block(items=items, objectives_text="")
    assert block
    assert len(block) <= _PLATE_BLOCK_CHAR_CAP


def test_AC_LENS_1_lenses_failsoft_on_a_raising_factory() -> None:
    """A boundary error inside the render returns ``""`` (no block), never
    raises — the render proceeds."""

    def _raise():
        raise RuntimeError("store boundary blew up")

    assert render_goals_block(
        objectives_text=_OBJECTIVES, tracker_factory=_raise
    ) == ""
    assert render_plate_block(
        objectives_text="", tracker_factory=_raise
    ) == ""
    assert render_waiting_on_block(tracker_factory=_raise) == ""


@pytest.mark.parametrize("cap", [_GOALS_BLOCK_CHAR_CAP, _PLATE_BLOCK_CHAR_CAP, _WAITING_ON_BLOCK_CHAR_CAP])
def test_AC_LENS_1_caps_are_slice_d_sized(cap: int) -> None:
    # All three lenses share the Slice-D concise-block cap (600), not a
    # wall-of-text budget.
    assert cap == 600
