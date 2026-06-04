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

"""AC.REL.2 — waiting-on-ME vs waiting-on-OTHERS.

Plan §6 AC.REL.2. Outcome: the relational surface distinguishes "waiting
on ME" (``owner_pending``) from "waiting on OTHERS" (an external-party
``waits_on``), reported in plain language ("waiting on Eric" vs "waiting
on you").
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.relational import (
    render_relational_block,
    reset_cache,
)

from _wms4_store import EDGE, fresh_factory, live_store, make_open


async def test_AC_REL_2_splits_waiting_on_me_from_waiting_on_others(tmp_path) -> None:
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        # An item shipped + awaiting the owner's call (waiting on ME).
        mine = await make_open(setup, "review the draft and decide")
        await setup.mark_owner_pending(mine.objective_id, evidence="needs your call")
        # An item waiting on an external party (waiting on OTHERS).
        theirs = await make_open(setup, "the launch")
        await setup.record_edge(
            theirs.objective_id, edge_kind=EDGE.waits_on, party="Eric"
        )
    finally:
        setup.close()

    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    assert "waiting on you: review the draft and decide" in block, (
        f"owner_pending must surface as waiting-on-you; block={block!r}"
    )
    assert "waiting on others: the launch (on Eric)" in block, (
        f"the external-party wait must surface as waiting-on-others; block={block!r}"
    )


async def test_AC_REL_2_external_party_named_in_plain_language(tmp_path) -> None:
    """The external party is named ("Eric"), not an internal id/enum."""
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        item = await make_open(setup, "the partnership deal")
        await setup.record_edge(
            item.objective_id, edge_kind=EDGE.waits_on, party="Jo-Anna"
        )
    finally:
        setup.close()

    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    assert "Jo-Anna" in block
    assert "waits_on" not in block  # no enum leak
    assert "owner_pending" not in block
