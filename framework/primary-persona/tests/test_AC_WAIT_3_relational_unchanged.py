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

"""AC.WAIT.3 — relational's rendered block is UNCHANGED by the extraction.

Plan §6 AC.WAIT.3. Outcome: ``relational.py``'s existing rendered block is
behaviour-preserving across the waiting-split extraction — the inc-4
AC.REL.2 surface renders identically (the regression fence). The inc-4
``test_AC_REL_2_*`` suite is the primary fence; this test asserts the
exact waiting-row strings the relational block produced before the
extraction still appear verbatim.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.relational import (
    render_relational_block,
    reset_cache,
)

from _wms4_store import EDGE, fresh_factory, live_store, make_open


async def test_AC_WAIT_3_relational_waiting_rows_render_verbatim(tmp_path) -> None:
    reset_cache()
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

    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    # The EXACT inc-4 relational waiting-row shape (byte-for-byte) — the
    # extraction is behaviour-preserving.
    assert "  waiting on you: review the draft and decide" in block, (
        f"relational's waiting-on-you row must be unchanged; block={block!r}"
    )
    assert "  waiting on others: the launch (on Eric)" in block, (
        f"relational's waiting-on-others row must be unchanged; block={block!r}"
    )
