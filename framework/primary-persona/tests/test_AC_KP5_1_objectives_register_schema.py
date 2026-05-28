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

"""AC.KP5.1 — OBJECTIVES.md exists at user-scope with the index/detail
schema; header names the register ``user-objectives`` (Surface #6)."""

from __future__ import annotations

from loam.primary_persona.keep_pace import objectives as obj


def test_AC_KP5_1_header_names_user_objectives() -> None:
    text = obj.render_register(obj.SEEDED_OBJECTIVES)
    assert text.startswith("# user-objectives"), (
        "register header must name it user-objectives (Surface #6, "
        "distinct from dev-ODD)"
    )


def test_AC_KP5_1_each_entry_carries_full_schema() -> None:
    text = obj.render_register(obj.SEEDED_OBJECTIVES)
    loaded = obj.load_objectives(text)
    assert loaded, "register must round-trip through the loader"
    for o in loaded:
        assert o.slug
        assert o.status in obj.VALID_STATUSES
        assert o.last_touched  # bookkeeping field present
        assert o.cadence
        assert o.objective
        assert o.completion  # completion criterion
        assert o.subgoals  # subgoal state
        assert o.detail_path  # detail lives in the linked file


def test_AC_KP5_1_detail_not_inlined_only_pointer() -> None:
    # Index/detail shape: the register carries the detail-path pointer,
    # NOT the detail body. The seeded detail docs' bodies must not be
    # inlined into the rendered index.
    text = obj.render_register(obj.SEEDED_OBJECTIVES)
    for o in obj.SEEDED_OBJECTIVES:
        assert o.detail_path in text  # the pointer is present
    # A sanity floor: the index is small (detail lives elsewhere).
    assert len(text) < obj.HOT_INDEX_BUDGET_BYTES


def test_AC_KP5_1_loader_round_trips() -> None:
    text = obj.render_register(obj.SEEDED_OBJECTIVES)
    loaded = obj.load_objectives(text)
    assert len(loaded) == len(obj.SEEDED_OBJECTIVES)
    by_slug = {o.slug: o for o in loaded}
    for seed in obj.SEEDED_OBJECTIVES:
        got = by_slug[seed.slug]
        assert got.status == seed.status
        assert got.objective == seed.objective
        assert got.subgoals == seed.subgoals
