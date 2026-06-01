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

"""AC.INTENT.4 (ladder) — leg 4 is visible on the idea-vacuum FALLBACK LADDER too.

The rerun8 acceptance smoke (variant C, paralegal idea-vacuum) reached the close
via the fallback ladder, where leg 4 was absent: the paralegal confirmed at
``ladder_check`` but added a GUIDANCE hedge ("I honestly don't even know what
'taking it off my plate' would look like, so you'd have to walk me through it")
and the ladder close ignored it. Leg 4 is now wired into the ladder close too —
a guidance hedge is answered by OFFERING to walk them through it (no invented
capability, no interrogation).
"""

from __future__ import annotations

from loam.workspace_bootstrap.deep_role_research import (
    RoleResearchResult,
    StubResearchProvider,
)
from loam.workspace_bootstrap.translate_in_intake import (
    _confirmation_wants_guidance,
    run_translate_in_intake,
)


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


class StubProvider:
    def research_role(self, role: str) -> RoleResearchResult:
        return StubResearchProvider().research_role(role)


def test_AC_INTENT_4_ladder_guidance_hedge_detected():
    assert _confirmation_wants_guidance(
        "Yeah sure, though I don't even know what taking it off my plate would "
        "look like, so you'd have to walk me through it"
    )
    # A clean yes is NOT a guidance hedge.
    assert not _confirmation_wants_guidance("yes, exactly that")


def test_AC_INTENT_4_ladder_close_addresses_guidance_hedge():
    """The variant-C path: idea-vacuum -> describe-work -> ladder_check confirmed
    WITH a guidance hedge -> the ladder close offers to walk them through it."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": "I really don't know, I just do my job",
            "describe_work": (
                "I'm a paralegal at a litigation firm — cite-checking briefs, "
                "drafting discovery requests, managing case files, tracking "
                "deadlines"
            ),
            "deep_opt_in": "no, let's just start somewhere",
            "ladder_check": (
                "Yeah, sure — that one takes forever. Though I honestly don't "
                "even know what 'taking it off my plate' would look like, so "
                "you'd have to walk me through it."
            ),
        }
    )
    result = run_translate_in_intake(
        answerer=answerer, research_provider=StubProvider()
    )
    assert result.reached_describe_work
    assert result.has_leverage_idea
    close = " ".join(i.text for i in result.leverage_ideas).lower()
    # Leg 4 fired on the ladder: the close OFFERS to walk them through it.
    assert "walk you through" in close or "step by step" in close
    # No interrogation — leg 4 is a statement, not a new question appended.
    assert "no prep needed" in close


def test_AC_INTENT_4_ladder_clean_yes_no_forced_adjustment():
    """A clean ladder_check 'yes' with nothing added leaves the ladder close clean
    (no forced empty adjustment)."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": "I really don't know, I just do my job",
            "describe_work": (
                "I'm a paralegal — cite-checking briefs, drafting discovery "
                "requests, managing case files"
            ),
            "deep_opt_in": "no",
            "ladder_check": "yes",
        }
    )
    result = run_translate_in_intake(
        answerer=answerer, research_provider=StubProvider()
    )
    close = " ".join(i.text for i in result.leverage_ideas).lower()
    assert "walk you through" not in close
    assert "no prep needed" not in close
