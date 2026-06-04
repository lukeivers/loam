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

"""AC.PLATE.3 — no score reaches the surface; every item has a plain reason.

Plan §6 AC.PLATE.3. Outcome: no numeric score reaches the surface; every
plate item carries a plain-language reason (inherited from ``prioritize``
— the AC.PRI.4 invariant holds through the plate lens).
"""

from __future__ import annotations

import re

from loam.primary_persona.keep_pace.plate import render_plate_block

from _wms4_store import make_item


def test_AC_PLATE_3_no_numeric_score_every_item_has_a_reason() -> None:
    items = [
        make_item("a", goal="write the launch email", status="active"),
        make_item("p", goal="decide the launch date", status="owner_pending"),
    ]
    block = render_plate_block(items=items, objectives_text="")

    # No black-box numeric score leaks to the surface.
    assert not re.search(r"\b\d+\.\d+\b", block), (
        f"no raw numeric score may surface; block={block!r}"
    )
    # Every plate row carries a plain-language reason (the " — <reason>").
    rows = [ln for ln in block.splitlines() if ln.startswith("  ")]
    assert rows, f"the plate must surface rows; block={block!r}"
    for row in rows:
        assert " — " in row, (
            f"every plate item must carry a plain-language reason; row={row!r}"
        )
        # No internal id / lifecycle enum leaks.
        assert "obj-" not in row
        assert "owner_pending" not in row
        assert "status=" not in row
