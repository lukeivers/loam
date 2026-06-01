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

"""AC.ONCLOSE.4 — the close references the user's NAMED item, not a generic triad.

The close lands on the person's own words (the distilled stop/start item, or the
day-derived named task like 'cite-checking briefs') — NOT a generic-assistant
"status updates / formatting / the chasing" headline. This is the rerun2
``learned-this-person`` FAIL across variants B and C (the close genericised the
named pain into 'status updates, formatting, chasing').
"""

from __future__ import annotations

from loam.workspace_bootstrap.deep_role_research import (
    RoleResearchResult,
    StubResearchProvider,
)
from loam.workspace_bootstrap.translate_in_intake import (
    _named_task_from_description,
    run_translate_in_intake,
)


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


class SpyProvider:
    def research_role(self, role: str) -> RoleResearchResult:
        return StubResearchProvider().research_role(role)


# The generic triad the rerun2 close led with (the genericisation to avoid).
_GENERIC_TRIAD = "the status updates, the formatting, the chasing"


def test_AC_ONCLOSE_4_named_task_extracted_from_description():
    desc = (
        "I'm a paralegal — my days are cite-checking briefs, drafting discovery "
        "requests, managing case files, calendaring deadlines."
    )
    task = _named_task_from_description(desc)
    assert task is not None
    assert "cite" in task.lower()


def test_AC_ONCLOSE_4_idea_rich_close_references_the_named_item():
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop reconciling spreadsheets every Monday",
                "confirm_proposal": "yes",
            }
        )
    )
    close = result.leverage_ideas[0].text.lower()
    assert "reconciling spreadsheets" in close
    assert _GENERIC_TRIAD not in close


def test_AC_ONCLOSE_4_day_derived_close_lands_the_named_task_not_the_triad():
    """The ladder close references the user's NAMED task ('cite-checking briefs'),
    and does NOT lead with the generic 'status updates / formatting / chasing'
    triad."""
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
    close = result.leverage_ideas[0].text.lower()
    assert "cite" in close  # the person's own named task
    assert _GENERIC_TRIAD not in close
