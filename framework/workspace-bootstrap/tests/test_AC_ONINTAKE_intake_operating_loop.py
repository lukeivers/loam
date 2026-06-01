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

"""AC.ONINTAKE.* — the translate-in intake runs the operating loop on a new
user (N3). Covers: the single stop/start close (.1), propose-not-echo (.2),
the verify gate (.3 — reject vs confirm yield DIFFERENT seed), the over-reach
guard (.4), the fallback ladder (.5), the leverage-idea close (.6)."""

from __future__ import annotations

from loam.workspace_bootstrap.translate_in_intake import (
    Disposition,
    IdeaRichness,
    run_translate_in_intake,
)


class ScriptedAnswerer:
    """Answer questions from a dict keyed by slug (a list -> answer per ask)."""

    def __init__(self, answers: dict[str, str]):
        self._answers = answers
        self.asked: list[str] = []

    def __call__(self, slug: str, prompt: str) -> str:
        self.asked.append(slug)
        return self._answers.get(slug, "")


# ---- AC.ONINTAKE.1 — leads toward ONE stop/start thing; never a list. ----


def test_AC_ONINTAKE_1_closes_on_one_stop_start_thing():
    answerer = ScriptedAnswerer(
        {
            "stop_start": "stop writing the weekly status report by hand",
            "confirm_proposal": "yes",
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    # It asked the single stop/start question and did NOT spray a multi-field
    # list — only the bounded close + verify were asked.
    assert "stop_start" in answerer.asked
    # No interrogation: the bounded set is small (stop/start + confirm), never a
    # form. The transcript holds at most a handful of turns.
    assert len(result.transcript) <= 3
    assert result.confirmed is True


def test_AC_ONINTAKE_1_detects_start_disposition():
    answerer = ScriptedAnswerer(
        {"stop_start": "start doing weekly investor updates", "confirm_proposal": "yes"}
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.proposal is not None
    assert result.proposal.disposition == Disposition.START


# ---- AC.ONINTAKE.2 — an end-intent is PROPOSED, not a verbatim echo. ----


def test_AC_ONINTAKE_2_proposal_is_not_a_verbatim_echo():
    raw = "stop manually formatting the chapter exports"
    answerer = ScriptedAnswerer({"stop_start": raw, "confirm_proposal": "yes"})
    result = run_translate_in_intake(answerer=answerer)
    assert result.proposal is not None
    # The proposal is a healthy-enablement SHAPE over the raw answer, distinct
    # from the verbatim echo (it adds the why/enablement framing).
    assert result.proposal.objective_text != raw
    assert "stops getting in the way" in result.proposal.objective_text


# ---- ★ AC.ONINTAKE.3 — the load-bearing verify gate. ----


def test_AC_ONINTAKE_3_reject_vs_confirm_yield_different_seed():
    """The seed is gated on VERIFICATION, not on the silent inference: a run
    that REJECTS the proposal seeds DIFFERENT state than one that CONFIRMS."""
    confirm = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "stop doing manual data entry", "confirm_proposal": "yes"}
        )
    )
    reject = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "stop doing manual data entry", "confirm_proposal": "no"}
        )
    )
    # Confirm seeds an objective; reject seeds nothing (different outcomes).
    assert confirm.confirmed is True
    assert confirm.seeded_objective_text is not None
    assert reject.confirmed is False
    assert reject.seeded_objective_text is None


def test_AC_ONINTAKE_3_correction_replaces_the_seed():
    """A correction ('no, it's actually X') changes WHAT gets seeded — proving
    the seed follows the user's verified answer, not the raw inference."""
    corrected = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop doing manual data entry",
                "confirm_proposal": "actually I want to automate my invoicing",
            }
        )
    )
    assert corrected.confirmed is True
    assert "invoicing" in (corrected.seeded_objective_text or "")
    # The leverage idea references the CORRECTED item, not the original.
    assert any("invoicing" in idea.text for idea in corrected.leverage_ideas)


# ---- AC.ONINTAKE.4 — over-reach guarded: at most one level up, opt-in. ----


def test_AC_ONINTAKE_4_one_time_ask_does_not_silently_seed_a_framework():
    answerer = ScriptedAnswerer(
        {"stop_start": "stop doing this one report", "confirm_proposal": "yes"}
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.proposal is not None
    # The recurring option is OFFERED (opt-in), never the proposal that seeds.
    assert result.proposal.one_level_up_offer is not None
    assert "optional" in result.proposal.one_level_up_offer.lower()
    # The seeded objective is the literal ask, not a silently-upgraded framework.
    assert "recurring deterministic framework" not in (
        result.seeded_objective_text or ""
    )


# ---- AC.ONINTAKE.5 — the fallback ladder is reachable + graceful. ----


def test_AC_ONINTAKE_5_empty_user_reaches_describe_work_and_gets_role_ideas():
    answerer = ScriptedAnswerer(
        {
            "stop_start": "I can't think of anything",
            "describe_work": "civil engineer",
            "deep_opt_in": "no",
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.richness is IdeaRichness.EMPTY
    assert result.reached_describe_work is True
    assert result.described_role == "civil engineer"
    # Ideas were mined DIRECTLY from the role (before any deep research).
    assert result.has_leverage_idea
    assert any("civil engineer" in idea.text for idea in result.leverage_ideas)
    # It did NOT jump straight to / get forced into the deep research pass.
    assert result.invoked_deep_research is False


def test_AC_ONINTAKE_5_ladder_does_not_run_for_a_user_with_an_idea():
    answerer = ScriptedAnswerer(
        {"stop_start": "stop doing the weekly board deck", "confirm_proposal": "yes"}
    )
    result = run_translate_in_intake(answerer=answerer)
    # A user with an idea never reaches the describe-work rung.
    assert result.reached_describe_work is False
    assert "describe_work" not in answerer.asked


# ---- ★ AC.ONINTAKE.6 — ends with >=1 person-specific leverage idea. ----


def test_AC_ONINTAKE_6_close_surfaces_a_person_specific_leverage_idea():
    answerer = ScriptedAnswerer(
        {
            "stop_start": "stop reconciling spreadsheets every Monday",
            "confirm_proposal": "yes",
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.has_leverage_idea
    idea = result.leverage_ideas[0]
    # Specific to the user's stated item — not generic boilerplate.
    assert idea.is_specific_to("reconciling spreadsheets")


def test_AC_ONINTAKE_6_two_different_answers_yield_two_different_leverage_ideas():
    """The specificity probe: different stated items -> different ideas (a
    generic-boilerplate implementation would emit the same idea both times)."""
    a = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "stop chasing late invoices", "confirm_proposal": "yes"}
        )
    )
    b = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": "stop formatting podcast show notes", "confirm_proposal": "yes"}
        )
    )
    assert a.leverage_ideas[0].text != b.leverage_ideas[0].text
    assert "invoices" in a.leverage_ideas[0].text
    assert "show notes" in b.leverage_ideas[0].text
