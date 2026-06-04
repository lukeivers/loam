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

"""AC.REL.3 — the decomposition relationship (parent/child tree).

Plan §6 AC.REL.3. Outcome: the relational surface presents a child's
place under its parent, read off the EXISTING ``trace_to_root`` /
``parent_id`` tree, in plain language.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.relational import (
    render_relational_block,
    reset_cache,
)

from _wms4_store import fresh_factory, live_store, make_open


async def test_AC_REL_3_surfaces_child_under_parent(tmp_path) -> None:
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        parent = await make_open(setup, "ship the product launch")
        # A child under the parent (the decomposition tree).
        await make_open(
            setup, "write the launch email", parent_id=parent.objective_id
        )
    finally:
        setup.close()

    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    assert "part of: write the launch email → under ship the product launch" in block, (
        f"the decomposition tree must surface the child under the root; block={block!r}"
    )
