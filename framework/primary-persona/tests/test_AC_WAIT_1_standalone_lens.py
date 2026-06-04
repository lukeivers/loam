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

"""AC.WAIT.1 — the waiting-on lens renders the on-me/on-others split as a
standalone named view.

Plan §6 AC.WAIT.1. Outcome: given a real store, the waiting-on lens
renders the on-me (``owner_pending``/internal) vs on-others
(external-party) split as a standalone named view, in ONE concise capped
block.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.waiting_on import render_waiting_on_block

from _wms4_store import EDGE, fresh_factory, live_store, make_open


async def test_AC_WAIT_1_standalone_split_renders(tmp_path) -> None:
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
    assert block, f"the standalone waiting-on lens must render; block={block!r}"
    # On-me side: the owner_pending item.
    assert "review the draft and decide" in block
    # On-others side: the external-party wait, party named in plain language.
    assert "the launch" in block
    assert "Eric" in block
    # Zero internal vocab.
    assert "owner_pending" not in block
    assert "waits_on" not in block


async def test_AC_WAIT_1_empty_store_renders_no_block(tmp_path) -> None:
    """No waits → no block (the graceful-empty contract)."""
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        await make_open(setup, "an ordinary active task")
    finally:
        setup.close()
    block = render_waiting_on_block(tracker_factory=fresh_factory(db))
    assert block == "", f"no waits must render no block; block={block!r}"
