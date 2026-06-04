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

"""AC.SURF.2 — bounded per-turn cost via the Slice-D TTL cache.

Plan §6 AC.SURF.2. Outcome: the lens render reuses the Slice-D per-turn
TTL/caching discipline so the per-turn cost is bounded; it does not
introduce a per-turn latency regression beyond the existing keep-pace
contributor budget.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.relational import (
    _RELATIONAL_TTL_SECONDS,
    render_relational_block,
    reset_cache,
)

from _wms4_store import fresh_factory, live_store, make_open


async def test_AC_SURF_2_within_ttl_window_is_a_cache_hit(tmp_path) -> None:
    """Two renders within the TTL window resolve the tracker only ONCE
    (the second is a cache hit) — the per-turn cost is bounded."""
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        await make_open(setup, "the one task")
    finally:
        setup.close()

    calls = {"n": 0}

    def counting_factory():
        calls["n"] += 1
        return fresh_factory(db)()

    first = render_relational_block(
        tracker_factory=counting_factory, objectives_text="", now=100.0
    )
    second = render_relational_block(
        tracker_factory=counting_factory, objectives_text="",
        now=100.0 + _RELATIONAL_TTL_SECONDS / 2,
    )
    assert first == second
    assert calls["n"] == 1, (
        "a render within the TTL window must be a cache hit (the tracker "
        f"is resolved once, not per-turn); factory calls={calls['n']}"
    )


async def test_AC_SURF_2_past_ttl_window_re_derives(tmp_path) -> None:
    """Past the TTL window the lens re-derives (fresh state surfaces) —
    the cache is a bound, not a staleness trap."""
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        await make_open(setup, "the one task")
    finally:
        setup.close()

    calls = {"n": 0}

    def counting_factory():
        calls["n"] += 1
        return fresh_factory(db)()

    render_relational_block(
        tracker_factory=counting_factory, objectives_text="", now=0.0
    )
    render_relational_block(
        tracker_factory=counting_factory, objectives_text="",
        now=_RELATIONAL_TTL_SECONDS + 1.0,
    )
    assert calls["n"] == 2, (
        "past the TTL window the lens must re-derive (resolve the tracker "
        f"again); factory calls={calls['n']}"
    )
