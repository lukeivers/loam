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

"""AC.INTENT.4 — leg 4 (adjust-from-the-answer) is visible on every confirmed path.

After the verify gate, the close ADJUSTS from what the confirmation revealed — a
concrete DETAIL the user added, or a capability DOUBT they raised — so the loop's
fourth leg is visible and the close is NOT a verbatim restatement of the
pre-confirmation proposal (the smoke's ``four-step-loop-ran`` PARTIAL). A
capability doubt is answered HONESTLY: loam acknowledges the question and frames
what it actually does WITHOUT inventing an unverified capability (the variant-C
``protection-floor-held`` FAIL).
"""

from __future__ import annotations

from loam.workspace_bootstrap.translate_in_intake import run_translate_in_intake


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


def _close_text(result) -> str:
    return " ".join(i.text for i in result.leverage_ideas)


def test_AC_INTENT_4_confirmation_detail_is_reflected_in_close():
    """A confirmation that adds a concrete detail → the close reflects it (the
    close is not a verbatim restatement of the proposal)."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": "writing listing descriptions, it eats my evenings",
            "confirm_proposal": (
                "yes exactly — especially the split-levels, I always stall on "
                "those blank-page openers"
            ),
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.confirmed
    close = _close_text(result)
    # Leg 4 fired: the close reflects the added detail, so it differs from the
    # plain proposal-restate close.
    plain = (
        result.proposal.objective_text if result.proposal else ""
    )
    assert close  # a close landed
    # The adjustment sentence is appended (the close carries more than the bare
    # leverage idea — leg 4 is visible).
    assert "Heard you" in close or "split" in close.lower() or "blank" in close.lower()
    assert close != plain


def test_AC_INTENT_4_capability_doubt_answered_honestly():
    """A follow-up doubt about capability → the close ADDRESSES it and makes no
    unqualified capability claim (protection-floor)."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": "cite-checking briefs, it's the tedious part",
            "confirm_proposal": (
                "yeah but I don't really understand how this would work — does it "
                "actually know how to read a Bluebook citation?"
            ),
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.confirmed
    close = _close_text(result).lower()
    # The doubt is acknowledged (leg 4 ADDRESSED it, did not ignore it).
    assert "your question" in close or "you review" in close or "judgment" in close
    # Honest framing — no invented unqualified capability claim like "loam can do
    # the grunt of it" with NO qualification (the variant-C FAIL).
    assert "you review" in close or "the call stays yours" in close


def test_AC_INTENT_4_downstream_goal_from_confirmation_is_reflected():
    """The confirmation's NEW downstream goal ('…so I'd have time to return calls
    and close files') is what leg 4 reflects — NOT a re-read of the first reply
    (the rerun8 variant-B PARTIAL: leg 4 ignored exactly this clause)."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": (
                "my whole afternoon disappears into writing up the claim-summary "
                "narratives, six or eight of them piling up by five-thirty"
            ),
            "confirm_proposal": (
                "yeah that's exactly it — if I could get some help there, I'd "
                "actually have time to return calls and close files out before "
                "the end of the day"
            ),
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.confirmed
    close = _close_text(result).lower()
    # Leg 4 reflects the DOWNSTREAM GOAL the confirmation added, not turn 1.
    assert "return calls" in close or "close files" in close
    assert "real goal" in close or "aiming you" in close


def test_AC_INTENT_4_leg4_never_over_promises_automation():
    """The leg-4 adjustment must NEVER over-promise automation (AC.ONCLOSE.3) —
    even when the LLM seam's adjustment read drifts into 'fully automated' (the
    rerun9 variant-A no-over-engineering FAIL). The over-promise is rejected and
    leg 4 falls through to a right-sized reflection."""
    from loam.workspace_bootstrap.intent_extract import ExtractedIntent
    from loam.workspace_bootstrap.translate_in_intake import (
        Disposition,
        ProposedEndIntent,
        _is_over_promise,
        _leg4_adjustment_text,
    )

    assert _is_over_promise("this could be fully automated, not just assisted")
    intent = ProposedEndIntent(
        slug="x",
        disposition=Disposition.STOP,
        objective_text="",
        raw_answer="writing property descriptions",
        clean_item="writing property descriptions",
        extracted=ExtractedIntent(
            intent="writing property descriptions",
            adjustment=(
                "the volume and routine cadence suggest this could be fully "
                "automated, not just assisted"
            ),
        ),
    )
    out = _leg4_adjustment_text(
        "yes exactly, I just want to describe the house and have it come out ready",
        intent,
    )
    assert "fully automat" not in out.lower()
    assert "automated, not just" not in out.lower()


def test_AC_INTENT_4_no_added_detail_yields_clean_close():
    """A bare 'yes' that adds nothing leaves the close clean (no forced, empty
    adjustment turn) — leg 4 reflects ONLY what the confirmation actually added."""
    answerer = ScriptedAnswerer(
        {
            "stop_start": "writing listing descriptions",
            "confirm_proposal": "yes",
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.confirmed
    close = _close_text(result)
    # No doubt, no detail → no appended adjustment clause.
    assert "your question" not in close.lower()
    assert "Heard you" not in close
