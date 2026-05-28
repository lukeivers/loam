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

"""AC.KP5.2 — the two real objectives (fiction pipeline + revenue push)
are seeded, both ``active``, each with a completion criterion + >=1
subgoal."""

from __future__ import annotations

from loam.primary_persona.keep_pace import objectives as obj


def test_AC_KP5_2_exactly_two_seeded_both_active() -> None:
    assert len(obj.SEEDED_OBJECTIVES) == 2
    for o in obj.SEEDED_OBJECTIVES:
        assert o.status == "active"
        assert o.completion.strip()
        assert len(o.subgoals) >= 1


def test_AC_KP5_2_fiction_pipeline_present() -> None:
    fiction = [o for o in obj.SEEDED_OBJECTIVES if "litrpg" in o.slug.lower()]
    assert len(fiction) == 1
    f = fiction[0]
    text = (f.objective + " " + " ".join(f.subgoals)).lower()
    assert "litrpg" in text
    assert "patch notes for reality" in f.objective.lower()


def test_AC_KP5_2_revenue_push_present() -> None:
    revenue = [
        o
        for o in obj.SEEDED_OBJECTIVES
        if "revenue" in o.slug.lower() or "independence" in o.slug.lower()
    ]
    assert len(revenue) == 1
    r = revenue[0]
    assert "passive" in r.objective.lower() or "independence" in r.objective.lower()
