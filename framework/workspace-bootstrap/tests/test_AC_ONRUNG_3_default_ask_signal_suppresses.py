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

"""AC.ONRUNG.3 — DEFAULT IS TO ASK; a clear one-off signal SUPPRESSES.

Owner correction (Luke 13403, precise): the one-rung-up question is asked BY
DEFAULT. The user's signal is a SUPPRESSOR ONLY — it turns the ask OFF when the
user clearly signals one-off / "no thanks" / overwhelmed-just-this-once / explicit
decline. With NO clear suppressing signal -> ASK. This is NOT "ask only when a
recurrence signal is present" (that would invert the default).

The landed deliverable (the ONE thing) is present in BOTH cases — suppression
removes only the rung+1 rider, never the literal landed ask.
"""

from __future__ import annotations

import pytest

from loam.workspace_bootstrap.translate_in_intake import (
    _one_off_signal_present,
    run_translate_in_intake,
)


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


def _close(stop_start: str, confirm: str = "yes") -> str:
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": stop_start, "confirm_proposal": confirm}
        )
    )
    assert len(result.leverage_ideas) == 1  # always ONE landed thing
    return result.leverage_ideas[0].text.lower()


# ---- DEFAULT: a neutral request (no suppressing signal) -> the ask IS present. ---


def test_AC_ONRUNG_3_neutral_request_asks_by_default():
    close = _close("stop writing listing descriptions for properties by hand")
    assert "optional" in close  # the one-rung ask is present BY DEFAULT


def test_AC_ONRUNG_3_default_ask_present_when_confirmation_adds_nothing():
    close = _close("stop drafting policyholder letters", confirm="yes")
    assert "optional" in close


# ---- SUPPRESSORS: a clear one-off signal turns the ask OFF. ---


@pytest.mark.parametrize(
    "one_off_reply",
    [
        "yes — but honestly just this once, no thanks to anything more",
        "yeah, just this one thing for now",
        "sure, but I'm so overwhelmed I just want this one done",
        "yes, keep it simple — nothing fancy",
        "ok but a one-off is fine, I don't want anything more",
    ],
)
def test_AC_ONRUNG_3_clear_one_off_signal_suppresses_the_ask(one_off_reply):
    close = _close(
        "stop writing listing descriptions for properties", confirm=one_off_reply
    )
    assert "optional" not in close  # the one-rung ask is SUPPRESSED...
    # ...but the landed deliverable is STILL present (suppression removes only
    # the rider, never the literal landed ask).
    assert "loam" in close


def test_AC_ONRUNG_3_one_off_signal_in_the_stop_start_reply_also_suppresses():
    # The suppressor can appear in the FIRST turn too, not just the confirmation.
    close = _close(
        "stop writing listing descriptions — just this one thing, I'm overwhelmed"
    )
    assert "optional" not in close
    assert "loam" in close


def test_AC_ONRUNG_3_suppressor_detector_is_direction_correct():
    # The detector fires ONLY on a suppressing signal — a neutral reply is NOT
    # suppressed (so the default-ask stands). This pins the default direction.
    assert _one_off_signal_present("just this once, no thanks") is True
    assert _one_off_signal_present("yes, that's exactly right") is False
    assert _one_off_signal_present("") is False
