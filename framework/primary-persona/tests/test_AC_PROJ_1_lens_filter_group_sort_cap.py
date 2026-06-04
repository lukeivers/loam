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

"""AC.PROJ.1 — the projects lens: filter belongs-to-project, group, sort
by priority, render one capped block via Slice-D discipline.

Plan §6 AC.PROJ.1. Outcome: a projects view exists, filtered+grouped+
sorted+capped — not a second wall of text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from loam.primary_persona.keep_pace import projects as P


@dataclass
class FakeItem:
    objective_id: str
    goal: str
    belongs_to_project: str | None = None
    tagged_streams: tuple = ()
    priority: str | None = None


@dataclass
class FakeComponent:
    name: str
    liveness: object


@dataclass
class FakeLiveness:
    value: str


@dataclass
class FakeRecord:
    head_sha: str = "abc123def"
    components: tuple = field(default_factory=tuple)


def _record(*pairs) -> FakeRecord:
    return FakeRecord(
        components=tuple(
            FakeComponent(name=n, liveness=FakeLiveness(value=v)) for n, v in pairs
        )
    )


def test_AC_PROJ_1_filters_to_bound_items_only() -> None:
    items = [
        FakeItem("o1", "bound work", belongs_to_project="loam"),
        FakeItem("o2", "unbound work", belongs_to_project=None),
    ]
    block = P.render_projects_block(
        items=items, derive=lambda n: _record(("core", "merged"))
    )
    assert "loam" in block
    # The unbound item's goal text must NOT appear (it is not a bounded
    # effort; the projects lens is bounded-effort only).
    assert "unbound work" not in block


def test_AC_PROJ_1_groups_by_project_and_counts() -> None:
    items = [
        FakeItem("o1", "a", belongs_to_project="loam"),
        FakeItem("o2", "b", belongs_to_project="loam"),
        FakeItem("o3", "c", belongs_to_project="cairn"),
    ]
    block = P.render_projects_block(
        items=items, derive=lambda n: _record(("x", "merged"))
    )
    assert "loam (2 item(s))" in block
    assert "cairn (1 item(s))" in block


def test_AC_PROJ_1_sorts_within_project_by_priority() -> None:
    items = [
        FakeItem("o1", "low", belongs_to_project="loam", priority="proposed"),
        FakeItem("o2", "high", belongs_to_project="loam", priority="owner_pending"),
        FakeItem("o3", "mid", belongs_to_project="loam", priority="active"),
    ]
    groups = P._items_by_project(items)
    ordered_goals = [it.goal for it in groups["loam"]]
    # owner_pending (rank 0) < active (1) < proposed (2).
    assert ordered_goals == ["high", "mid", "low"]


def test_AC_PROJ_1_block_within_hard_cap() -> None:
    # Many projects with long names — the block must never exceed the cap.
    items = [
        FakeItem(f"o{i}", f"goal {i}", belongs_to_project=f"project-{i:03d}-with-a-long-name")
        for i in range(50)
    ]
    block = P.render_projects_block(
        items=items, derive=lambda n: _record(("c", "merged"))
    )
    assert len(block) <= P._PROJECTS_BLOCK_CHAR_CAP


def test_AC_PROJ_1_no_bound_items_yields_empty() -> None:
    items = [FakeItem("o1", "unbound", belongs_to_project=None)]
    assert P.render_projects_block(items=items, derive=lambda n: None) == ""
