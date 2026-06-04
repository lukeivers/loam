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

"""AC.PROJ.3 — a project bound to NO registered FBM project surfaces a
staleness/cadence next-action AND is explicitly marked "no ground-truth
project bound"; it never fabricates a derived build-STATE.

Plan §6 AC.PROJ.3 (the architecture §5 honest gap as an AC).
"""

from __future__ import annotations

from dataclasses import dataclass

from loam.primary_persona.keep_pace import projects as P


@dataclass
class FakeItem:
    objective_id: str
    goal: str
    belongs_to_project: str | None = None
    tagged_streams: tuple = ()
    priority: str | None = None


def test_AC_PROJ_3_unbound_project_marked_honestly() -> None:
    items = [
        FakeItem("o1", "house repairs plan", belongs_to_project="personal-home"),
        FakeItem("o2", "heloc path", belongs_to_project="personal-home"),
    ]
    # The derivation returns None for an unregistered project (the real
    # registry returns None for an unregistered name).
    block = P.render_projects_block(items=items, derive=lambda n: None)
    assert "personal-home" in block
    assert "no ground-truth project bound" in block


def test_AC_PROJ_3_unbound_never_fabricates_build_state() -> None:
    items = [FakeItem("o1", "money push", belongs_to_project="money")]
    block = P.render_projects_block(items=items, derive=lambda n: None)
    # No build-liveness phrase appears for an unbound project.
    for phrase in ("built (merged)", "built (sealed", "not built", "wired"):
        assert phrase not in block


def test_AC_PROJ_3_mixed_bound_and_unbound_in_one_block() -> None:
    from dataclasses import dataclass as _dc, field as _f

    @_dc
    class FakeComponent:
        name: str
        liveness: object

    @_dc
    class FakeLiveness:
        value: str

    @_dc
    class FakeRecord:
        head_sha: str = "abc123def"
        components: tuple = _f(default_factory=tuple)

    items = [
        FakeItem("o1", "loam work", belongs_to_project="loam"),
        FakeItem("o2", "money work", belongs_to_project="money"),
    ]

    def derive(name: str):
        if name == "loam":
            return FakeRecord(
                components=(FakeComponent("core", FakeLiveness("merged")),)
            )
        return None  # money is unregistered

    block = P.render_projects_block(items=items, derive=derive)
    assert "built (merged)" in block  # loam, derived
    assert "no ground-truth project bound" in block  # money, honest mark
