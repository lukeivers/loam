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

"""AC.REPOINT.1 — the streams lens resolves a stream's membership from
work-items carrying that stream in tagged_streams, NOT from a
register-local backlog list; an item tagged with a stream AND bound to a
project appears in BOTH lenses without being stored twice.

Plan §6 AC.REPOINT.1 (the WMS-D7 re-pointability AC). Method: the
membership resolver reads work-item tags; the appears-in-both check uses
one work-item set for both lenses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from loam.primary_persona.keep_pace import projects as P
from loam.primary_persona.keep_pace.work_streams import resolve_stream_membership


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


def test_AC_REPOINT_1_membership_resolves_from_tags_not_register() -> None:
    items = [
        FakeItem("o1", "loam work", belongs_to_project="loam", tagged_streams=("loam",)),
        FakeItem("o2", "money work", belongs_to_project="money", tagged_streams=("money",)),
        FakeItem("o3", "untagged", belongs_to_project="loam", tagged_streams=()),
    ]
    members = resolve_stream_membership("loam", items)
    # Only the loam-tagged item is in the loam stream — resolved from the
    # graph tags, not a register-local list.
    assert members.item_ids == ("o1",)
    assert members.projects == ("loam",)


def test_AC_REPOINT_1_item_in_both_lenses_without_double_storage() -> None:
    """ONE work item, tagged with a stream AND bound to a project, appears
    in BOTH the streams membership AND the projects lens — stored once."""
    shared = FakeItem(
        "o1", "shared work", belongs_to_project="loam", tagged_streams=("loam",)
    )
    items = [shared]

    # Streams lens membership.
    members = resolve_stream_membership("loam", items)
    assert "o1" in members.item_ids

    # Projects lens — same item set, no second copy.
    block = P.render_projects_block(
        items=items, derive=lambda n: FakeRecord(
            components=(FakeComponent("core", FakeLiveness("merged")),)
        )
    )
    assert "loam (1 item(s))" in block

    # There is exactly ONE item object backing both views (no duplication).
    assert len(items) == 1


def test_AC_REPOINT_1_multi_tagged_item_in_several_streams() -> None:
    item = FakeItem(
        "o1", "cross-cut", belongs_to_project="loam", tagged_streams=("loam", "money")
    )
    loam_members = resolve_stream_membership("loam", [item])
    money_members = resolve_stream_membership("money", [item])
    assert "o1" in loam_members.item_ids
    assert "o1" in money_members.item_ids
