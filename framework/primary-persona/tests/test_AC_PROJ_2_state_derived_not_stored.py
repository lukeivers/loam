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

"""AC.PROJ.2 — a registered-FBM-bound project's STATE is composed from a
FRESH derive_project_state call, never a stored/stale status string;
changing ground truth and re-reading reflects the change.

Plan §6 AC.PROJ.2 (mirrors the streams lens AC.WS.DERIVE.1). Outcome:
derived-not-stored, verifiable by changing the derivation result and
re-rendering with NO register edit.
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


def test_AC_PROJ_2_state_composed_from_fresh_derive() -> None:
    items = [FakeItem("o1", "work", belongs_to_project="loam")]
    block = P.render_projects_block(
        items=items, derive=lambda n: _record(("core", "merged"))
    )
    # The STATE phrase comes from the derive record, not from any stored
    # string on the item.
    assert "built (merged)" in block


def test_AC_PROJ_2_changing_ground_truth_reflects_without_register_edit() -> None:
    items = [FakeItem("o1", "work", belongs_to_project="loam")]
    state = {"liveness": "unbuilt"}

    def derive(_name: str):
        return _record(("core", state["liveness"]))

    first = P.render_projects_block(items=items, derive=derive)
    assert "not built" in first

    # Change the ground truth the derivation reads — the SAME items, no
    # register/item edit. A fresh render reflects the change (derived,
    # not stored).
    state["liveness"] = "merged"
    second = P.render_projects_block(items=items, derive=derive)
    assert "built (merged)" in second
    assert "not built" not in second


def test_AC_PROJ_2_no_stored_status_on_item_is_load_bearing() -> None:
    """The item carries no status string; the STATE is fully derived."""
    items = [FakeItem("o1", "work", belongs_to_project="cairn")]
    assert not hasattr(items[0], "stored_state")
    block = P.render_projects_block(
        items=items, derive=lambda n: _record(("vetting", "sealed"))
    )
    assert "built (sealed, not yet merged)" in block
