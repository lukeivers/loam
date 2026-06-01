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

"""AC.ONCLOSE.1 — the four-step loop's SURFACE-AND-CHECK leg runs on EVERY path.

Before the leverage close, loam surfaces the inferred end-intent as a checkable
hypothesis the user can confirm/correct — on the CLEAR/PARTIAL path
(``confirm_proposal``), the day-derived path (also CLEAR/PARTIAL after the
derivable-pain demotion), AND the idea-vacuum-after-research path
(``ladder_check``). This is the rerun2 ``four-step-loop-ran`` FAIL: the ladder
paths jumped straight from describe_work/research to a close with no surfaced
hypothesis.
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


def _check_turn(result, *, fragment: str) -> bool:
    """True when SOME transcript turn surfaced the inferred intent as a check
    (a confirm/check slug whose prompt the user could confirm/correct)."""
    return any(slug in ("confirm_proposal", "ladder_check") for slug, _ in result.transcript)


def test_AC_ONCLOSE_1_clear_path_surfaces_a_hypothesis():
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop writing the weekly status report by hand",
                "confirm_proposal": "yes",
            }
        )
    )
    assert "confirm_proposal" in [s for s, _ in result.transcript]
    assert _check_turn(result, fragment="status report")


def test_AC_ONCLOSE_1_day_derived_path_surfaces_a_hypothesis():
    """A day-derived reply that names a single pain ('the thing that eats my day
    is the write-ups') routes through the PARTIAL propose/verify path — it gets
    the surfaced confirm_proposal hypothesis, not a silent close."""
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": (
                    "I don't really know, I just do my job — but the thing that "
                    "eats my day is grinding through the claim write-ups every "
                    "afternoon."
                ),
                "confirm_proposal": "yes",
            }
        )
    )
    assert "confirm_proposal" in [s for s, _ in result.transcript]
    # The ladder (describe_work) was NOT reached — it went down the verify path.
    assert result.reached_describe_work is False


def test_AC_ONCLOSE_1_idea_vacuum_after_research_surfaces_a_hypothesis():
    """The idea-vacuum ladder (vacuum -> describe_work -> opt-in research) now
    SURFACES a single inferred starting point (ladder_check) for the user to
    confirm/correct BEFORE landing the close — the missing legs 3-4."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": "I really don't know, I just do my job",
            "describe_work": (
                "I'm a paralegal — my days are cite-checking briefs, drafting "
                "discovery requests, managing case files, calendaring deadlines."
            ),
            "deep_opt_in": "yes",
            "ladder_check": "yes",
        }
    )
    result = run_translate_in_intake(answerer=answerer, research_provider=SpyProvider())
    assert result.invoked_deep_research is True
    # The surfaced-hypothesis turn ran AFTER research and BEFORE the close.
    assert "ladder_check" in answerer.asked
    assert answerer.asked.index("ladder_check") > answerer.asked.index("deep_opt_in")
