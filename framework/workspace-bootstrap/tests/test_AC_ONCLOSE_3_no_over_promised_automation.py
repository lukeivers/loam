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

"""AC.ONCLOSE.3 — the close does NOT over-promise unattended automation.

The close proposes right-sized help (loam does the work when you bring it the
basics); it does NOT claim the thing "happens reliably without you having to
push it forward each time." The recurring/elaborate version stays the OPT-IN
``one_level_up_offer``, never the default the close commits to. This is the
rerun2 ``no-over-engineering`` + ``protection-floor-held`` FAIL on variant A.
"""

from __future__ import annotations

from loam.workspace_bootstrap.translate_in_intake import run_translate_in_intake


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


# The over-promise phrases the rerun2 close emitted (the START-disposition pitch).
_OVER_PROMISE = (
    "happens reliably without you",
    "without you having to push it forward",
    "without you having to push it",
)


def test_AC_ONCLOSE_3_start_disposition_close_has_no_over_promise():
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "start doing weekly investor updates",
                "confirm_proposal": "yes",
            }
        )
    )
    close = result.leverage_ideas[0].text.lower()
    for phrase in _OVER_PROMISE:
        assert phrase not in close, f"over-promise phrase leaked into close: {phrase!r}"


def test_AC_ONCLOSE_3_stop_disposition_close_has_no_over_promise():
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop writing listing descriptions by hand every night",
                "confirm_proposal": "yes",
            }
        )
    )
    close = result.leverage_ideas[0].text.lower()
    for phrase in _OVER_PROMISE:
        assert phrase not in close


def test_AC_ONCLOSE_3_recurring_stays_an_opt_in_offer():
    """The elaborate/recurring version is OFFERED as the opt-in one-level-up,
    marked optional — it is NOT the default the close commits to."""
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "stop doing the one weekly report",
                "confirm_proposal": "yes",
            }
        )
    )
    assert result.proposal is not None
    offer = result.proposal.one_level_up_offer or ""
    assert offer  # the recurring version is present as an OFFER
    assert "optional" in offer.lower()
    # The landed close itself does not commit to recurrence-by-default.
    assert "recurring" not in result.leverage_ideas[0].text.lower()
