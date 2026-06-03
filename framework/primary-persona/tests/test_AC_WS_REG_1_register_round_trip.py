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

"""AC.WS.REG.1 — the stream register loads from a user-scope file into a
list of streams, each carrying slug / attention / bound projects /
optional nest-parent / detail-path; round-trips render->load unchanged."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws


def test_AC_WS_REG_1_header_names_work_streams() -> None:
    text = ws.render_register(ws.SEEDED_WORK_STREAMS)
    assert text.startswith("# work-streams"), (
        "register header must name it work-streams (sibling to user-objectives)"
    )


def test_AC_WS_REG_1_each_entry_carries_full_schema() -> None:
    text = ws.render_register(ws.SEEDED_WORK_STREAMS)
    loaded = ws.load_streams(text)
    assert loaded, "register must round-trip through the loader"
    for s in loaded:
        assert s.slug
        assert s.attention in ws.VALID_ATTENTION
        assert s.objective
        assert s.detail_path  # detail lives in the linked file (index/detail)


def test_AC_WS_REG_1_round_trips_unchanged() -> None:
    text = ws.render_register(ws.SEEDED_WORK_STREAMS)
    loaded = ws.load_streams(text)
    assert len(loaded) == len(ws.SEEDED_WORK_STREAMS)
    by_slug = {s.slug: s for s in loaded}
    for seed in ws.SEEDED_WORK_STREAMS:
        got = by_slug[seed.slug]
        assert got.attention == seed.attention
        assert got.objective == seed.objective
        assert got.projects == seed.projects  # bound projects round-trip
        assert got.nest_under == seed.nest_under
        assert got.subgoals == seed.subgoals
        assert got.backlog == seed.backlog
        assert got.detail_path == seed.detail_path


def test_AC_WS_REG_1_detail_not_inlined_only_pointer() -> None:
    # Index/detail shape: the register carries the detail-path pointer,
    # not the detail body. A sanity floor: the index is small.
    text = ws.render_register(ws.SEEDED_WORK_STREAMS)
    for s in ws.SEEDED_WORK_STREAMS:
        assert s.detail_path in text
    assert ws.register_index_bytes(ws.SEEDED_WORK_STREAMS) < ws.HOT_INDEX_BUDGET_BYTES


def test_AC_WS_REG_1_user_scope_seed_round_trips(tmp_path) -> None:
    # The user-scope seed step writes the register; loading it back yields
    # the same streams (no live-file dependency — a tmp claude_home).
    home = tmp_path / ".claude"
    path = ws.seed_user_scope_register(claude_home=home)
    assert path.exists()
    loaded = ws.load_user_scope_register(claude_home=home)
    assert {s.slug for s in loaded} == {s.slug for s in ws.SEEDED_WORK_STREAMS}


def test_AC_WS_REG_1_absent_file_falls_back_to_seed(tmp_path) -> None:
    # No live file => the in-source seed is the floor (lets AC.WS.LIVE.1
    # surface with no pre-arranged state).
    home = tmp_path / "empty-home"
    loaded = ws.load_user_scope_register(claude_home=home)
    assert {s.slug for s in loaded} == {s.slug for s in ws.SEEDED_WORK_STREAMS}
