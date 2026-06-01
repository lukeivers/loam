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

"""AC.INTENT.6 — STOP-vs-START disposition is read by the LLM extractor, regex
fail-soft.

The extractor's ``disposition`` read drives the close as the PRIMARY path; on an
extractor failure (or an empty/uncertain read) the deterministic
``_detect_disposition`` regex still classifies the raw reply. This retires the
keyword-regex disposition as the SOLE reader (the bug class bitten twice by
phrasing) while keeping the regex as the safety net — the prior AC.DISPOS.1
intent-frame cases still hold through the fallback.
"""

from __future__ import annotations

from loam.workspace_bootstrap.intent_extract import ExtractedIntent
from loam.workspace_bootstrap.translate_in_intake import (
    Disposition,
    _detect_disposition,
    _disposition_from,
    run_translate_in_intake,
)


class FakeExtractor:
    """Returns a fixed extraction (with a disposition) WITHOUT spawning."""

    def __init__(self, extracted: ExtractedIntent):
        self._extracted = extracted

    def extract(self, raw_reply: str, *, prior_proposal: str = "") -> ExtractedIntent:
        return self._extracted

    def extract_adjustment(self, confirm_reply: str, *, item: str, proposal: str = "") -> str:
        return ""


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


# ---- The extractor's disposition is the PRIMARY reader. ----


def test_AC_INTENT_6_extractor_stop_read_drives_disposition():
    extracted = ExtractedIntent(intent="the weekly report", disposition="stop")
    assert _disposition_from("ambiguous phrasing here", extracted) is Disposition.STOP


def test_AC_INTENT_6_extractor_start_read_drives_disposition():
    extracted = ExtractedIntent(intent="journaling", disposition="start")
    assert _disposition_from("ambiguous phrasing here", extracted) is Disposition.START


def test_AC_INTENT_6_extractor_disposition_wins_over_regex_when_they_disagree():
    # The raw text would regex-classify START ("want to ... more"), but the
    # extractor read STOP — the extractor (intent over keywords) wins.
    raw = "I want to do more of my own thing"
    extracted = ExtractedIntent(intent="the manual data entry", disposition="stop")
    assert _disposition_from(raw, extracted) is Disposition.STOP


# ---- The regex is the FAIL-SOFT fallback. ----


def test_AC_INTENT_6_falls_back_to_regex_when_extractor_absent():
    # No extracted read at all (the extractor failed soft -> None) -> the regex
    # classifies the raw reply.
    raw = "I want to stop doing it by hand"
    assert _disposition_from(raw, None) == _detect_disposition(raw)
    assert _disposition_from(raw, None) is Disposition.STOP


def test_AC_INTENT_6_falls_back_to_regex_when_extractor_disposition_empty():
    # An extraction that produced an intent but COULD NOT tell the disposition
    # ("") -> the regex classifies. AC.DISPOS.1 intent-frame case still holds.
    raw = "I want to stop doing it by hand"
    extracted = ExtractedIntent(intent="it by hand", disposition="")
    assert _disposition_from(raw, extracted) is Disposition.STOP


def test_AC_INTENT_6_end_to_end_extractor_disposition_shapes_the_close():
    # A reply the regex would read one way; the extractor's STOP read shapes the
    # close (the offload framing), proving the extractor drives disposition E2E.
    fake = FakeExtractor(
        ExtractedIntent(intent="writing property descriptions", disposition="stop")
    )
    result = run_translate_in_intake(
        answerer=ScriptedAnswerer(
            {
                "stop_start": "honestly I just want my evenings back from the writeups",
                "confirm_proposal": "yes",
            }
        ),
        intent_extractor=fake,
    )
    assert result.proposal is not None
    assert result.proposal.disposition is Disposition.STOP
    # The STOP framing landed (offload), not the START "get to" framing.
    assert "off" in result.leverage_ideas[0].text.lower()
