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

"""AC.KP5.3 — the register's index surface loads within the hot
byte-budget (~20KB headroom target); detail lives in the detail-path,
not inlined."""

from __future__ import annotations

from loam.primary_persona.keep_pace import objectives as obj


def test_AC_KP5_3_seed_under_hot_budget() -> None:
    size = obj.register_index_bytes(obj.SEEDED_OBJECTIVES)
    assert size <= obj.HOT_INDEX_BUDGET_BYTES, (
        f"register index {size}B exceeds hot budget "
        f"{obj.HOT_INDEX_BUDGET_BYTES}B — detail leaked into the index?"
    )


def test_AC_KP5_3_budget_catches_inlined_detail() -> None:
    # If a future edit inlined a multi-KB detail body into an entry's
    # objective text, the byte guard catches it. Simulate by crafting a
    # bloated entry and asserting the guard would trip.
    bloated = obj.Objective(
        slug="bloated",
        status="active",
        objective="x" * (obj.HOT_INDEX_BUDGET_BYTES + 1),
        completion="c",
        detail_path="d",
    )
    size = obj.register_index_bytes([bloated])
    assert size > obj.HOT_INDEX_BUDGET_BYTES
