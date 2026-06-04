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

"""AC.SURF.1 — ONE concise capped fail-soft block at the turn seat.

Plan §6 AC.SURF.1. Outcome: the relational lens renders as ONE concise
block within a hard character cap (the Slice-D 600-char discipline),
composing the prioritized next-thing + reason + the relational answers;
fail-soft (any boundary error or no-content render returns no block);
registered as a ``TriggerKind.turn`` keep-pace contributor (the same seat
the projects/intake contributors use).
"""

from __future__ import annotations

from loam.primary_persona.context_composer import (
    ComposedContextPayload,
    TriggerKind,
)
from loam.primary_persona.keep_pace.relational import (
    _RELATIONAL_BLOCK_CHAR_CAP,
    build_relational_contributor,
    register_relational_contributor,
    render_relational_block,
    reset_cache,
)

from _wms4_store import EDGE, fresh_factory, live_store, make_open


async def test_AC_SURF_1_block_is_within_char_cap(tmp_path) -> None:
    """Even with many items + edges, the block is hard-capped (one
    concise block, not a wall of text)."""
    reset_cache()
    db = tmp_path / "objectives.db"
    setup = live_store(db)
    try:
        prev = None
        for i in range(12):
            item = await make_open(setup, f"work item number {i} with a longish goal text")
            if prev is not None:
                await setup.record_edge(
                    item.objective_id, edge_kind=EDGE.waits_on, to_id=prev.objective_id
                )
            prev = item
    finally:
        setup.close()

    block = render_relational_block(
        tracker_factory=fresh_factory(db), objectives_text=""
    )
    assert block, "the block must render with content"
    assert len(block) <= _RELATIONAL_BLOCK_CHAR_CAP, (
        f"the block must be within the {_RELATIONAL_BLOCK_CHAR_CAP}-char cap; "
        f"got {len(block)}"
    )


def test_AC_SURF_1_failsoft_returns_empty_on_factory_error() -> None:
    """A raising tracker_factory yields no block (fail-soft), never an
    exception out of the contributor."""
    reset_cache()

    def _boom():
        raise RuntimeError("tracker unavailable")

    contributor = build_relational_contributor(tracker_factory=_boom)
    assert contributor({}) == "", "a boundary error must fail-soft to no block"


def test_AC_SURF_1_registers_at_turn_seat() -> None:
    """The contributor registers as a TriggerKind.turn contributor named
    'relational' — the same seat the projects/intake lenses use."""
    reset_cache()
    composer = ComposedContextPayload(session_builder=lambda root: {})
    register_relational_contributor(
        composer, tracker_factory=lambda: None  # no store => empty render
    )
    turn = composer.contributors(trigger_kind=TriggerKind.turn)
    names = [c.name for c in turn]
    assert "relational" in names, f"the relational lens must register at the turn seat; {names}"
    assert names.count("relational") == 1, "no double-register"


def test_AC_SURF_1_no_store_renders_no_block() -> None:
    """A None-tracker (no store wired) renders no block (fail-soft)."""
    reset_cache()
    block = render_relational_block(tracker_factory=lambda: None, objectives_text="")
    assert block == ""


def test_AC_SURF_1_production_composer_registers_relational(tmp_path) -> None:
    """The PRODUCTION (client-None) composer registers the relational
    turn contributor live — the lens is wired, not merely registerable
    (mirrors the projects/work-streams production-registration ACs)."""
    from loam.primary_persona.session_start_emitter import build_session_composer

    ws = tmp_path / "myws"
    ws.mkdir()
    composer = build_session_composer(
        ws,
        memory_client_factory=lambda _root: None,  # production client-None branch
        register_tracker=False,
    )
    names = [c.name for c in composer.contributors(trigger_kind=TriggerKind.turn)]
    assert "relational" in names, (
        f"the production composer must register the relational lens at the "
        f"turn seat; registered turn contributors: {names}"
    )
    assert names.count("relational") == 1, "no double-register"
