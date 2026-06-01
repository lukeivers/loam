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

"""AC.ONDEEP.* — the deep role-research sub-capability (opt-in, own slice,
behind an interface). N3 baseline (D-5 (a)): the opt-in GATE + the interface
SEAM only; the research PASS is the fast-follow slice.

Covers: ★ AC.ONDEEP.1 — the deepening is OPT-IN and OFF the baseline path (the
featherlight invariant: a baseline run NEVER triggers the research pass); plus
the baseline-side of AC.ONDEEP.2 — the seam is callable + degrades gracefully
when the real pass is absent (the stub)."""

from __future__ import annotations

from loam.workspace_bootstrap.deep_role_research import (
    RoleResearchResult,
    StubResearchProvider,
    default_research_provider,
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
    """Records whether the research pass was invoked at all."""

    def __init__(self):
        self.invoked_with: list[str] = []

    def research_role(self, role: str) -> RoleResearchResult:
        self.invoked_with.append(role)
        return StubResearchProvider().research_role(role)


# ---- ★ AC.ONDEEP.1 — featherlight invariant: baseline NEVER triggers research. ----


def test_AC_ONDEEP_1_user_with_a_stop_start_idea_never_triggers_research():
    spy = SpyProvider()
    run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "stop doing the weekly board deck", "confirm_proposal": "yes"}
        ),
        research_provider=spy,
    )
    # A user who named a stop/start thing directly never reaches the research seam.
    assert spy.invoked_with == []


def test_AC_ONDEEP_1_empty_user_with_no_role_detail_never_triggers_research():
    spy = SpyProvider()
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "I can't think of anything", "describe_work": "not sure"}
        ),
        research_provider=spy,
    )
    # No role detail given -> the research pass is never invoked (no interrogation
    # by weight); a gentle generic starter idea is surfaced instead.
    assert spy.invoked_with == []
    assert result.offered_deep_research is False
    assert result.has_leverage_idea


def test_AC_ONDEEP_1_empty_user_who_declines_the_deepening_never_triggers_research():
    spy = SpyProvider()
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "no idea",
                "describe_work": "product manager",
                "deep_opt_in": "no",
            }
        ),
        research_provider=spy,
    )
    # The deepening was OFFERED (real role detail in hand) but DECLINED -> never run.
    assert result.offered_deep_research is True
    assert result.invoked_deep_research is False
    assert spy.invoked_with == []
    # Role ideas were still mined directly (the ladder landed without research).
    assert result.has_leverage_idea


def test_AC_ONDEEP_1_only_role_detail_plus_opt_in_reaches_the_research_pass():
    spy = SpyProvider()
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "I'm new and overwhelmed",
                "describe_work": "registered nurse",
                "deep_opt_in": "yes",
            }
        ),
        research_provider=spy,
    )
    # ONLY this path (idea-vacuum + real role + explicit opt-in) reaches it.
    assert spy.invoked_with == ["registered nurse"]
    assert result.invoked_deep_research is True


# ---- AC.ONDEEP.2 (baseline side) — the seam is callable + degrades gracefully. ----


def test_AC_ONDEEP_2_stub_provider_returns_the_three_named_axes():
    res = StubResearchProvider().research_role("data analyst")
    # The synthesis addresses all three axes (effectiveness / promotion / tools).
    assert res.effectiveness
    assert res.promotion_criteria
    assert res.existing_ai_tools
    assert res.is_stub is True
    assert res.role == "data analyst"


def test_AC_ONDEEP_2_baseline_degrades_gracefully_without_the_real_pass():
    """The baseline composes the DEFAULT provider (the stub) without the
    fast-follow pass present — it does not raise / hang."""
    provider = default_research_provider()
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "dunno",
                "describe_work": "teacher",
                "deep_opt_in": "yes",
            }
        ),
        research_provider=provider,
    )
    # The opt-in path completed against the stub and folded ideas into the close.
    assert result.invoked_deep_research is True
    assert result.research_result is not None
    assert result.research_result.is_stub is True
    assert result.has_leverage_idea
