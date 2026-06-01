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

"""AC.UM.AREA.1/.2/.3 — the work-anchor -> area classification (D-N4.1).

AC.UM.AREA.1: the anchor resolves to exactly one slug from AIM_AREAS.
AC.UM.AREA.2: an unknown / low-confidence anchor resolves to ``default``.
AC.UM.AREA.3: the classifier reads the EXISTING anchor, doesn't recompute.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace import interaction_model as im
from loam.primary_persona.keep_pace.work_anchor import WorkAnchor
from loam.workspace_bootstrap.seed_writer import AIM_AREAS as SEED_AREAS


def test_AC_UM_AREA_1_taxonomy_binds_to_seed_writer() -> None:
    """The classifier's taxonomy is exactly the N3 seed-writer's AIM_AREAS
    (the read contract) — a drift in the seed-writer is caught here, not
    silently tolerated."""
    assert set(im.AIM_AREAS) == set(SEED_AREAS)
    assert im.AIM_AREAS == SEED_AREAS  # same order too


def test_AC_UM_AREA_1_resolves_to_one_known_slug() -> None:
    """Every classification result is a single slug drawn from AIM_AREAS."""
    prompts = [
        "write the next litrpg chapter",
        "handle the invoice payment",
        "fix the python build and run the tests",
        "decide the roadmap strategy and weigh the tradeoffs",
        "add a keep-pace hook contributor to the harness",
        "what's the weather like",
    ]
    for p in prompts:
        area = im.classify_area(WorkAnchor(prompt=p))
        assert area in im.AIM_AREAS, f"{p!r} -> {area!r} not a known slug"


def test_AC_UM_AREA_1_routes_each_area() -> None:
    """A keyword-bearing prompt routes to the matching area."""
    cases = {
        "write the next chapter of the litrpg novel": "their-domain-work",
        "handle the invoice and revenue payment": "ops-and-money",
        "fix the python module bug and run the tests": "code-and-builds",
        "decide the strategy and weigh the tradeoffs": "decisions-and-tradeoffs",
        "wire a new keep-pace hook contributor": "harness-mechanics",
    }
    for prompt, expected in cases.items():
        assert im.classify_area(WorkAnchor(prompt=prompt)) == expected, (
            f"{prompt!r} did not route to {expected!r}"
        )


def test_AC_UM_AREA_2_unknown_routes_to_default() -> None:
    """A no-keyword anchor resolves to ``default`` (the openness prior)."""
    assert im.classify_area(WorkAnchor(prompt="hmm interesting")) == "default"
    assert im.classify_area(WorkAnchor(prompt="")) == "default"


def test_AC_UM_AREA_2_consequence_areas_win_ties() -> None:
    """A prompt that touches both a money keyword and a build keyword
    routes to the consequence-bearing area (ops-and-money), never
    under-routing a money turn to the bolder default."""
    # "deploy" + "publish" are money/ops keywords; "build" is code. The
    # consequence-bearing area must win.
    area = im.classify_area(
        WorkAnchor(prompt="deploy and publish the build to production")
    )
    assert area == "ops-and-money"


def test_AC_UM_AREA_3_reads_anchor_does_not_recompute() -> None:
    """The classifier consumes the anchor's tokens (its objective + subgoal
    + last-topic), not just the prompt — composing on the existing anchor.
    A vague prompt with a litrpg objective routes to their-domain-work via
    the OBJECTIVE anchor (the term the bare prompt cannot supply)."""
    anchor = WorkAnchor(
        prompt="continue",  # carries no area keyword
        objective_texts=[
            "Produce the LitRPG series 'Patch Notes for Reality' novels"
        ],
        subgoals=["canon-consistency-across-the-series"],
    )
    # The objective anchor (litrpg/novels/canon) routes it — proving the
    # classifier reads the whole anchor, not just the prompt.
    assert im.classify_area(anchor) == "their-domain-work"
