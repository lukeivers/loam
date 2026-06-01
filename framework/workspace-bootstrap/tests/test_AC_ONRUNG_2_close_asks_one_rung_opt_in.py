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

"""AC.ONRUNG.2 — the close ASKS at most rung+1, opt-in, never rung+2+.

The close still LANDS the literal request as the ONE landed deliverable
(AC.ONCLOSE.2 intact). The one-rung-up is a SINGLE OPTIONAL rider QUESTION the
user can decline — NOT a second landed deliverable, NOT an assertion of structure.
A doc request's rider asks about a TEMPLATE, never a workflow/system (rung+2+).
"""

from __future__ import annotations

from loam.workspace_bootstrap.translate_in_intake import run_translate_in_intake


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


def _run(stop_start: str, confirm: str = "yes"):
    return run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {"stop_start": stop_start, "confirm_proposal": confirm}
        )
    )


def test_AC_ONRUNG_2_close_lands_exactly_one_idea_with_the_rider():
    # The rider is folded into the SAME single landed idea — still ONE thing.
    result = _run("stop writing listing descriptions for properties by hand")
    assert len(result.leverage_ideas) == 1


def test_AC_ONRUNG_2_rider_is_an_opt_in_ask_not_an_assertion():
    result = _run("stop writing listing descriptions for properties by hand")
    close = result.leverage_ideas[0].text.lower()
    # Phrased as an opt-in the user can decline.
    assert "optional" in close
    assert "could" in close or "if it'd help" in close
    # An opt-in offer, not a committed-structure assertion.
    assert "i've built" not in close
    assert "i've set up" not in close
    assert "i set up" not in close


def test_AC_ONRUNG_2_doc_request_asks_about_template_never_workflow_or_system():
    result = _run("stop drafting policyholder letters every afternoon")
    close = result.leverage_ideas[0].text.lower()
    assert "template" in close  # EXACTLY rung+1 for a doc
    assert "workflow" not in close  # rung+2 forbidden
    assert "system" not in close  # rung+3 forbidden


def test_AC_ONRUNG_2_the_landed_deliverable_is_still_present_alongside_the_rider():
    result = _run("stop writing the weekly client report")
    close = result.leverage_ideas[0].text.lower()
    # The literal ask landed as the ONE thing...
    assert "off your plate" in close or "loam" in close
    # ...AND the opt-in rung+1 ask is appended (default-ask).
    assert "optional" in close
