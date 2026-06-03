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

"""AC.WS.REG.2 — a stream may bind zero, one, or many projects AND may
nest under another stream; a span-multiple stream and a nest-both stream
resolve correctly when read (Luke-13511 span-AND-nest intent)."""

from __future__ import annotations

from loam.primary_persona.keep_pace import work_streams as ws


def _streams():
    return [
        ws.WorkStream(slug="loam", attention="active", objective="o",
                      detail_path="d", projects=["loam"]),
        # spans TWO projects
        ws.WorkStream(slug="platform", attention="active", objective="o",
                      detail_path="d", projects=["loam", "cairn"]),
        # binds ZERO projects
        ws.WorkStream(slug="money", attention="active", objective="o",
                      detail_path="d", projects=[]),
        # nests under loam AND spans a project (span-AND-nest)
        ws.WorkStream(slug="fbm-quality", attention="active", objective="o",
                      detail_path="d", projects=["loam"], nest_under="loam"),
    ]


def test_AC_WS_REG_2_zero_one_many_projects() -> None:
    streams = {s.slug: s for s in _streams()}
    assert streams["money"].projects == []          # zero
    assert streams["loam"].projects == ["loam"]      # one
    assert streams["platform"].projects == ["loam", "cairn"]  # many


def test_AC_WS_REG_2_ground_truth_bound_derived_from_projects() -> None:
    streams = {s.slug: s for s in _streams()}
    assert streams["loam"].ground_truth_bound is True
    assert streams["platform"].ground_truth_bound is True
    assert streams["money"].ground_truth_bound is False  # AC.WS.DERIVE.2 path


def test_AC_WS_REG_2_nest_resolves() -> None:
    children = ws.resolve_nest(_streams())
    assert children.get("loam") == ["fbm-quality"], (
        "fbm-quality must resolve under the loam parent"
    )


def test_AC_WS_REG_2_span_and_nest_together() -> None:
    # The span-AND-nest stream: binds a project AND nests under a parent.
    streams = {s.slug: s for s in _streams()}
    sub = streams["fbm-quality"]
    assert sub.projects == ["loam"], "the sub-stream still binds its project"
    assert sub.nest_under == "loam", "and nests under its parent"


def test_AC_WS_REG_2_round_trips_through_register() -> None:
    text = ws.render_register(_streams())
    loaded = {s.slug: s for s in ws.load_streams(text)}
    assert loaded["platform"].projects == ["loam", "cairn"]
    assert loaded["fbm-quality"].nest_under == "loam"
    assert loaded["fbm-quality"].projects == ["loam"]
    assert loaded["money"].projects == []
