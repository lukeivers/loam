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

"""AC.ONCLOSE.5 — a NEGATED correction distills the ASSERTED intent.

When the user corrects loam's misread with a negation ('it's not that I have
trouble starting it — I want you to write them for me'), the close + seed
reference the ASSERTED work (the writing/draft-for-me intent), NOT the negated
clause ('trouble starting it'). This is the exact rerun2 variant-A failure: the
close quoted 'it's not that I have trouble starting it' back at the user.
"""

from __future__ import annotations

from loam.workspace_bootstrap.translate_in_intake import (
    _distill_intent,
    run_translate_in_intake,
)


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


# The exact rerun2 variant-A correction reply (transcript line 114).
RERUN2_A_CORRECTION = (
    "Well, it's not that I have trouble starting it — I do it every night, "
    "that's the problem! What I want is to just not have to write them myself "
    "anymore, or at least not spend two hours on it. Can it just do the writing "
    "for me if I give it the basics on the property?"
)
RERUN2_A_STOP_START = (
    "Honestly? Writing listing descriptions. Every single night I'm sitting "
    "there trying to come up with fresh ways to say sun-drenched kitchen for "
    "eight different properties, and it eats two hours."
)


def test_AC_ONCLOSE_5_negated_correction_distills_asserted_not_negated():
    distilled = _distill_intent(RERUN2_A_CORRECTION)
    low = distilled.lower()
    # The asserted work (the writing/offload) — NOT the negated clause.
    assert "writing" in low or "write" in low
    assert "trouble starting" not in low
    assert "trouble" not in low


def test_AC_ONCLOSE_5_close_lands_asserted_intent_after_negated_correction():
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": RERUN2_A_STOP_START,
                "confirm_proposal": RERUN2_A_CORRECTION,
            }
        )
    )
    assert result.confirmed is True
    close = result.leverage_ideas[0].text.lower()
    seed = (result.seeded_objective_text or "").lower()
    # The close + seed reference the asserted writing intent, not 'trouble starting'.
    assert "trouble starting" not in close
    assert "trouble starting" not in seed
    assert "writing" in close or "write" in close


def test_AC_ONCLOSE_5_short_negated_correction_distills_asserted_noun():
    """A short negated correction that names the item ('not that I have trouble
    starting it — I want to stop writing those listing descriptions') distills
    the named asserted item."""
    distilled = _distill_intent(
        "it's not that I have trouble starting it — I want to stop writing "
        "those listing descriptions myself"
    ).lower()
    assert "listing descriptions" in distilled
    assert "trouble" not in distilled
