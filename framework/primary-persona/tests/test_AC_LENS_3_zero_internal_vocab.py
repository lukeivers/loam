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

"""AC.LENS.3 — every render carries zero internal vocabulary.

Plan §6 AC.LENS.3. Outcome: no IDs, SHAs, paths, slugs (raw), lifecycle
enums, or numeric scores reach the rendered text — across all three
lenses (the zero-internal-vocab HARD invariant).
"""

from __future__ import annotations

import re

from loam.primary_persona.keep_pace.goals import render_goals_block
from loam.primary_persona.keep_pace.plate import render_plate_block
from loam.primary_persona.keep_pace.waiting_on import render_waiting_on_block

from _wms4_store import EDGE, fresh_factory, live_store, make_item, make_open

_OBJECTIVES = """# user-objectives

## revenue-independence
status: active
objective: Build financial independence.
completion: done.
detail-path: x.md
subgoals:
  - fiction-catalog-as-passive-asset
"""

# Lifecycle enums / internal tokens that must never reach a render.
_FORBIDDEN = ("owner_pending", "waits_on", "blocks", "obj-", "objective_id", "status=")


def _assert_clean(block: str) -> None:
    for token in _FORBIDDEN:
        assert token not in block, f"internal token {token!r} leaked; block={block!r}"
    # No raw numeric score.
    assert not re.search(r"\b\d+\.\d+\b", block), f"numeric score leaked; block={block!r}"


def test_AC_LENS_3_goals_zero_internal_vocab() -> None:
    items = [
        make_item("obj-123", goal="advance revenue-independence", status="active"),
        make_item("obj-456", goal="an unattributed orphan", status="active"),
    ]
    block = render_goals_block(items=items, objectives_text=_OBJECTIVES)
    _assert_clean(block)


def test_AC_LENS_3_plate_zero_internal_vocab() -> None:
    items = [
        make_item("obj-789", goal="write the launch email", status="active"),
        make_item("obj-790", goal="decide the launch date", status="owner_pending"),
    ]
    block = render_plate_block(items=items, objectives_text="")
    _assert_clean(block)


async def test_AC_LENS_3_waiting_on_zero_internal_vocab(tmp_path) -> None:
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        mine = await make_open(setup, "review the draft and decide")
        await setup.mark_owner_pending(mine.objective_id, evidence="needs your call")
        theirs = await make_open(setup, "the launch")
        await setup.record_edge(
            theirs.objective_id, edge_kind=EDGE.waits_on, party="Eric"
        )
    finally:
        setup.close()
    block = render_waiting_on_block(tracker_factory=fresh_factory(db))
    _assert_clean(block)
