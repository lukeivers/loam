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

"""AC.ONCLOSE.2 — the close lands on EXACTLY ONE thing, never a menu.

A completed intake produces exactly ONE primary leverage idea (the landed
stop/start). Research findings + role context fold INTO the seed (and the one
idea), they are NOT emitted as additional co-equal close ideas. This is the
rerun2 ``closed-on-one-thing`` FAIL: every path emitted a 2-3 item menu (the CLI
prints every ``leverage_ideas`` entry as a co-equal ``>> `` close line).
"""

from __future__ import annotations

from loam.workspace_bootstrap.deep_role_research import (
    RoleResearchResult,
    StubResearchProvider,
)
from loam.workspace_bootstrap.translate_in_intake import run_translate_in_intake


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers
        self.asked: list[str] = []

    def __call__(self, slug: str, prompt: str) -> str:
        self.asked.append(slug)
        return self._answers.get(slug, "")


class SpyProvider:
    def research_role(self, role: str) -> RoleResearchResult:
        return StubResearchProvider().research_role(role)


def test_AC_ONCLOSE_2_idea_rich_path_lands_one_idea():
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop reconciling spreadsheets every Monday",
                "confirm_proposal": "yes",
            }
        )
    )
    assert len(result.leverage_ideas) == 1


def test_AC_ONCLOSE_2_day_derived_path_lands_one_idea():
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": (
                    "honestly I don't know, but the thing that eats my day is "
                    "grinding through the claim write-ups every afternoon."
                ),
                "confirm_proposal": "yes",
            }
        )
    )
    assert len(result.leverage_ideas) == 1


def test_AC_ONCLOSE_2_idea_vacuum_with_research_lands_one_idea():
    """The idea-vacuum path that fires research must STILL land exactly one close
    idea — the research synthesis folds into the seed, not into extra close
    lines (the rerun2 3-item menu)."""
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "I really don't know, I just do my job",
                "describe_work": (
                    "I'm a paralegal — cite-checking briefs, drafting discovery "
                    "requests, managing case files, calendaring deadlines."
                ),
                "deep_opt_in": "yes",
                "ladder_check": "yes",
            }
        ),
        research_provider=SpyProvider(),
    )
    assert result.invoked_deep_research is True
    assert len(result.leverage_ideas) == 1
    # The research synthesis is retained on the result (folded into the seed),
    # NOT discarded — it just isn't a co-equal close idea.
    assert result.research_result is not None
    assert "paralegal" in (result.seeded_objective_text or "").lower()
