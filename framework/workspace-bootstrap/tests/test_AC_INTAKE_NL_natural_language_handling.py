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

"""AC.INTAKE-* — the four natural-language-handling bugs the loam 1.0
acceptance smoke caught in the onboarding intake
(`docs/experiments/loam-1.0-acceptance-smoke-run.md`). Each test drives the
REAL raw reply the role-played user gave in the smoke transcript, proving the
natural-language case now passes:

  - AC.INTAKE-ECHO.1   — the proposal DISTILLS the user's reply to a short
                         intent phrase; the multi-sentence reply does NOT appear
                         verbatim in the proposal (Bug 1).
  - AC.INTAKE-AFFIRM.1 — natural affirmations with punctuation are recognized;
                         the deep-research gate fires on "Yeah, that'd help"
                         (Bug 2 — the AC.SMOKE.3 gate failure).
  - AC.INTAKE-VACUUM.1 — the idea-vacuum classifier is robust to natural
                         phrasings ("I don't even know where to start") (Bug 3).
  - AC.INTAKE-ROLE.1   — the role slot resolves to a NOUN, not the raw
                         multi-sentence job description (Bug 4).
"""

from __future__ import annotations

from loam.workspace_bootstrap.deep_role_research import (
    RoleResearchResult,
    StubResearchProvider,
)
from loam.workspace_bootstrap.translate_in_intake import (
    IdeaRichness,
    _classify_richness,
    _is_no,
    _is_yes,
    _looks_empty,
    run_translate_in_intake,
)


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers
        self.asked: list[str] = []

    def __call__(self, slug: str, prompt: str) -> str:
        self.asked.append(slug)
        return self._answers.get(slug, "")


class SpyProvider:
    def __init__(self):
        self.invoked_with: list[str] = []

    def research_role(self, role: str) -> RoleResearchResult:
        self.invoked_with.append(role)
        return StubResearchProvider().research_role(role)


# The verbatim raw replies from the 1.0 acceptance-smoke transcript.
VAR_A_STOP_START = (
    "Oh, that's an easy one — writing listing descriptions is killing me. Every "
    "single evening I'm sitting there trying to come up with new ways to say "
    '"sun-drenched kitchen" and "entertainer\'s dream," and it eats two hours I '
    "could be out doing showings or actually talking to clients. I just want it done."
)
VAR_B_STOP_START = (
    "Honestly? I don't even know where to start with that question — like, I just "
    "kind of do my job, you know? Nobody's ever asked me to think about it that way."
)
VAR_C_DESCRIBE_WORK = (
    "I'm a paralegal at a small litigation firm — so most of my day is things "
    "like cite-checking briefs, drafting discovery requests, managing case files, "
    "keeping track of deadlines for hearings and filings. It's a lot of moving "
    "pieces but I honestly couldn't tell you which one of those I'd want to hand "
    "off, they all kind of just... need to happen."
)
VAR_C_DEEP_OPT_IN = (
    "Yeah, that'd actually help — I have no idea where to start, so if you can "
    "figure out what I *should* be thinking about, that's kind of the whole "
    "problem right there."
)


# ---- AC.INTAKE-ECHO.1 — the proposal distills, it does not echo the raw reply. ----


def test_AC_INTAKE_ECHO_1_proposal_distills_not_echoes_the_raw_reply():
    """Variant A's multi-sentence reply must NOT appear verbatim in the proposal
    (the Bug-1 garble: 'Help the user reliably Oh, that's an easy one — …')."""
    answerer = ScriptedAnswerer(
        {"stop_start": VAR_A_STOP_START, "confirm_proposal": "yes"}
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.proposal is not None
    obj = result.proposal.objective_text
    # The whole reply is NOT pasted into the slot.
    assert VAR_A_STOP_START.strip().rstrip(".") not in obj
    # The distilled item references what the user actually said (the concrete job).
    assert "listing descriptions" in obj
    # The proposal stays bounded — it does not balloon to the raw reply length.
    assert len(obj) < len(VAR_A_STOP_START)
    # The opt-in offer also quotes the distilled item, not the raw blob.
    assert VAR_A_STOP_START.strip().rstrip(".") not in (
        result.proposal.one_level_up_offer or ""
    )


# ---- AC.INTAKE-AFFIRM.1 — natural punctuated affirmations are recognized. ----


def test_AC_INTAKE_AFFIRM_1_punctuated_affirmations_read_as_yes():
    assert _is_yes("Yeah, that'd actually help") is True
    assert _is_yes("yes, basically!") is True
    assert _is_yes("Sure.") is True
    assert _is_yes("Yep — go for it") is True
    # Negatives stay negative regardless of punctuation.
    assert _is_no("No.") is True
    assert _is_no("Nope!") is True
    # A substantive correction (no leading yes/no token) is neither — the caller
    # routes it to the correction branch.
    assert _is_yes("actually I want to automate my invoicing") is False
    assert _is_no("actually I want to automate my invoicing") is False


def test_AC_INTAKE_AFFIRM_1_deep_research_gate_fires_on_natural_yes():
    """Variant C's 'Yeah, that'd actually help — …' must fire the deep-research
    path (the AC.SMOKE.3 gate failure: the path NEVER fired because '_is_yes'
    returned False on the trailing-comma token)."""
    spy = SpyProvider()
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "I really don't know — I just do my job",
                "describe_work": VAR_C_DESCRIBE_WORK,
                "deep_opt_in": VAR_C_DEEP_OPT_IN,
            }
        ),
        research_provider=spy,
    )
    assert result.offered_deep_research is True
    assert result.invoked_deep_research is True
    assert spy.invoked_with != []


# ---- AC.INTAKE-VACUUM.1 — the idea-vacuum classifier survives natural phrasing. ----


def test_AC_INTAKE_VACUUM_1_natural_vacuum_phrasing_classifies_empty():
    # The literal "don't know" substring was broken by the inserted "even".
    assert _looks_empty("I don't even know where to start") is True
    assert _looks_empty(VAR_B_STOP_START) is True
    # A reply that names a concrete thing is NOT empty.
    assert _looks_empty("stop writing the weekly status report by hand") is False


def test_AC_INTAKE_VACUUM_1_variant_b_routes_to_the_fallback_ladder():
    """Variant B's blanked reply must route to EMPTY -> the fallback ladder, not
    be misclassified as a PARTIAL idea (which fired the Bug-1 echo on a
    non-answer)."""
    assert _classify_richness(VAR_B_STOP_START) is IdeaRichness.EMPTY
    answerer = ScriptedAnswerer(
        {
            "stop_start": VAR_B_STOP_START,
            "describe_work": "insurance claims adjuster",
            "deep_opt_in": "no",
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.richness is IdeaRichness.EMPTY
    assert result.reached_describe_work is True


# ---- AC.INTAKE-ROLE.1 — the role slot resolves to a NOUN, not the raw blob. ----


def test_AC_INTAKE_ROLE_1_role_slot_resolves_to_a_noun():
    """Variant C's multi-sentence role description must NOT be pasted into the
    '{role}' slot (the Bug-4 garble: 'Here's what loam can do for a I'm a
    paralegal at a small litigation firm — …')."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": "I really don't know — I just do my job",
            "describe_work": VAR_C_DESCRIBE_WORK,
            "deep_opt_in": "no",
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.has_leverage_idea
    close = result.leverage_ideas[0].text
    # The raw multi-sentence blob is NOT in the leverage close.
    assert VAR_C_DESCRIBE_WORK.strip().rstrip(".") not in close
    # The resolved role noun ("paralegal") is used instead.
    assert "paralegal" in close
    # The seeded objective text likewise carries the noun, not the blob.
    assert VAR_C_DESCRIBE_WORK.strip().rstrip(".") not in (
        result.seeded_objective_text or ""
    )
    assert "paralegal" in (result.seeded_objective_text or "")


# ---- Re-run hardening (same four AC families; cases the live smoke surfaced). ----

# Verbatim replies the SECOND smoke re-run produced.
RERUN_A_CONFIRM_CORRECTION = (
    "Uh, sort of? I'm not sure what that sentence even means, honestly. What I "
    "want is simple: I want to stop writing those listing descriptions myself — "
    "I want you to write them for me so I can get my evenings back."
)
RERUN_A_STOP_START = (
    "Oh, that's easy — every single night I'm sitting at my kitchen table writing "
    "up listing descriptions for my properties. You know, the sun-drenched open "
    "floor plan stuff for MLS and Zillow."
)
RERUN_B_STOP_START_WITH_PAIN = (
    "Honestly? I don't know, I just kind of do my job — nobody's ever really "
    "asked me that before. I mean, I guess the thing that eats my day is the "
    "afternoons, once the inspection calls are done, just sitting there grinding "
    "through the write-ups on all the claims I handled that morning."
)
RERUN_C_STOP_START_VACUUM = (
    "I really don't know, I just do my job — I'm not sure what this thing is even "
    "supposed to do for me. Like, I answer emails, I pull case files, I calendar "
    "deadlines, I draft discovery requests... it's just kind of everything, all "
    "day. I don't really have a thing that's broken, it's more just sort of... "
    "constant."
)


def test_AC_INTAKE_AFFIRM_1_filler_led_affirmation_reads_as_yes():
    """A warm confirm that OPENS with a hedge interjection ('Ha, … but yes,
    basically!') is a confirmation — the parser skips leading filler and reads
    the agreement pivot."""
    assert _is_yes("Ha, that's a mouthful — but yes, basically!") is True
    assert _is_yes("yes, exactly that") is True
    assert _is_yes("sure, if you think it helps") is True
    # A hedge with NO clean affirmation ('not sure', 'sort of') is NOT a yes —
    # it routes to the correction branch (a bare 'sure' in 'not sure' must not
    # read as agreement).
    assert _is_yes(RERUN_A_CONFIRM_CORRECTION) is False
    assert _is_no(RERUN_A_CONFIRM_CORRECTION) is False


def test_AC_INTAKE_ECHO_1_correction_is_distilled_not_echoed():
    """When the user corrects the proposal, the seed + leverage close carry the
    distilled ITEM, not a verbatim paste of the whole correction reply (the
    residual the live re-run surfaced on variant A)."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": RERUN_A_STOP_START,
            "confirm_proposal": RERUN_A_CONFIRM_CORRECTION,
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.confirmed is True
    # The whole raw correction is NOT pasted into the seed or the close.
    assert RERUN_A_CONFIRM_CORRECTION.strip().rstrip(".") not in (
        result.seeded_objective_text or ""
    )
    assert result.has_leverage_idea
    close = result.leverage_ideas[0].text
    assert RERUN_A_CONFIRM_CORRECTION.strip().rstrip(".") not in close
    # The distilled item (listing descriptions) is what the close references.
    assert "listing descriptions" in close


def test_AC_INTAKE_VACUUM_1_single_pain_does_not_reach_research_ladder():
    """A reply that says 'I don't know' but singles out ONE concrete pain ('the
    thing that eats my day is the write-ups') is a day-derived PARTIAL idea — it
    must NOT route to the deep-research ladder (the featherlight invariant; the
    regression the live re-run surfaced on variant B)."""
    assert _classify_richness(RERUN_B_STOP_START_WITH_PAIN) is not IdeaRichness.EMPTY
    spy = SpyProvider()
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": RERUN_B_STOP_START_WITH_PAIN, "confirm_proposal": "yes"}
        ),
        research_provider=spy,
    )
    # The day-derived pain went down the propose/verify path, never the ladder.
    assert result.reached_describe_work is False
    assert result.invoked_deep_research is False
    assert spy.invoked_with == []


def test_AC_INTAKE_VACUUM_1_explicit_nothing_broken_stays_a_vacuum():
    """A reply that lists activities but explicitly says 'nothing's broken / it's
    just constant' IS a genuine idea-vacuum — it routes to the ladder even amid
    the activity list (so the opt-in research path stays reachable)."""
    assert _classify_richness(RERUN_C_STOP_START_VACUUM) is IdeaRichness.EMPTY
