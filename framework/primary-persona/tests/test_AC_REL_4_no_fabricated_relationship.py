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

"""AC.REL.4 — no relationship is FABRICATED.

Plan §6 AC.REL.4. Outcome: an item with no recorded edges and no parent
surfaces no blocked/waiting/decomposition relationship; the surface
reports only relationships that exist in the graph (the honest-graph
invariant carried through surfacing).
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.relational import (
    render_relational_block,
    reset_cache,
)

from _wms4_store import fresh_factory, live_store, make_open


async def test_AC_REL_4_no_edges_no_parent_no_relationship_rows(tmp_path) -> None:
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        # Two independent items: no edges, no parents.
        await make_open(setup, "solo task one")
        await make_open(setup, "solo task two")
    finally:
        setup.close()

    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    # The items ARE unblocked-next (that is a real, true answer), but NO
    # blocked / waiting / decomposition relationship is fabricated.
    assert "blocked:" not in block, f"no blocked relationship may be invented; block={block!r}"
    assert "waiting on" not in block, f"no waiting relationship may be invented; block={block!r}"
    assert "part of:" not in block, f"no decomposition may be invented; block={block!r}"
    # The honest "next" answer still surfaces (the items are genuinely
    # unblocked).
    assert "solo task one" in block or "solo task two" in block


async def test_AC_REL_4_empty_store_renders_no_block(tmp_path) -> None:
    """An empty store (no work items) renders no block at all (fail-soft,
    nothing fabricated)."""
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    setup.close()  # empty store

    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    assert block == "", f"an empty store must render no block; block={block!r}"
