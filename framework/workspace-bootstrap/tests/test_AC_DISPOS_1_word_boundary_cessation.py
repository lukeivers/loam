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

"""AC.DISPOS.1 — disposition detection is word-boundary-aware (no STOP→START
inversion via a substring match).

The rerun8 acceptance smoke (variant A) inverted the user's intent: "I'd love to
just... not do that anymore" was classified START because the START token "more"
matched the TAIL of "any-more". The fix matches tokens on word boundaries and
treats cessation phrasings ("not ... anymore", "no longer", "off my plate",
"sick of") as STOP. A genuine START ("I want to start journaling", "I should do
more reviews") still reads START.
"""

from __future__ import annotations

import pytest

from loam.workspace_bootstrap.translate_in_intake import (
    Disposition,
    _detect_disposition,
    run_translate_in_intake,
)


@pytest.mark.parametrize(
    "reply,expected",
    [
        # The rerun8 variant-A inversion case — the regression this fixes.
        (
            "I spend two hours every night writing up the listing descriptions. "
            "I'd love to just... not do that anymore.",
            Disposition.STOP,
        ),
        # Cessation tells with no literal "stop".
        ("no longer want to chase the invoices", Disposition.STOP),
        ("take cite-checking briefs off my plate", Disposition.STOP),
        ("I'm sick of writing the claim summaries", Disposition.STOP),
        ("I'm so tired of formatting the reports", Disposition.STOP),
        # An intent-frame governing a stop-verb is a STOP, not a START — the
        # rerun11 variant-A inversion ("I want to stop ..." read START because
        # "want to" preceded "stop").
        ("Writing descriptions is killing me. I want to stop doing it by hand", Disposition.STOP),
        ("I want to stop writing them myself", Disposition.STOP),
        ("I need to quit chasing invoices", Disposition.STOP),
        ("I'd love to offload the nightly write-ups", Disposition.STOP),
        ("I want to get rid of the manual export", Disposition.STOP),
        # Genuine STARTs still read START (no over-correction).
        ("I want to start journaling every morning", Disposition.START),
        ("I should begin reviewing more of the contracts", Disposition.START),
        ("I need to do more of the planning myself", Disposition.START),
    ],
)
def test_AC_DISPOS_1_word_boundary_disposition(reply, expected):
    assert _detect_disposition(reply) == expected


def test_AC_DISPOS_1_anymore_does_not_trip_more_token():
    """The specific substring bug: 'anymore' must NOT match the START token
    'more'."""
    assert _detect_disposition("I just don't want to do this anymore") == (
        Disposition.STOP
    )


def test_AC_DISPOS_1_stop_intent_yields_offload_close():
    """End-to-end: a STOP phrasing flows to the OFFLOAD framing + close, not the
    inverted 'reliably get to' START framing (the variant-A failure)."""

    class ScriptedAnswerer:
        def __init__(self, answers):
            self._answers = answers

        def __call__(self, slug, prompt):
            return self._answers.get(slug, "")

    answerer = ScriptedAnswerer(
        {
            "stop_start": (
                "I spend two hours every night writing listing descriptions. "
                "I'd love to just... not do that anymore."
            ),
            "confirm_proposal": "yes exactly",
        }
    )
    result = run_translate_in_intake(answerer=answerer)
    assert result.confirmed
    # The proposal is the OFFLOAD framing, never the inverted "reliably get to".
    assert result.proposal is not None
    assert "reliably get to" not in result.proposal.objective_text
    assert "offload" in result.proposal.objective_text.lower()
