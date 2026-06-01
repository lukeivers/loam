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

"""AC.INTENT.2 — FAIL-SOFT: the seam degrades to the deterministic regex.

The load-bearing invariant: on extractor unavailable / timeout / error / empty /
unparseable, distillation FALLS BACK to the existing regex ``_distill_intent`` and
``run_translate_in_intake`` never raises and never hangs. With NO extractor
registered (the baseline default), the path is PURE REGEX — no spawn — and the
distillation output is byte-identical to pre-seam. The extractor is consulted at
most ONCE per distillation (bounded).
"""

from __future__ import annotations

from loam.workspace_bootstrap.intent_extract import (
    DisabledIntentExtractor,
    ExtractedIntent,
    IntentExtractUnavailableError,
    default_intent_extractor,
)
from loam.workspace_bootstrap.translate_in_intake import (
    _distill_intent,
    _distill_intent_via_seam,
    run_translate_in_intake,
)


class ScriptedAnswerer:
    def __init__(self, answers: dict[str, str]):
        self._answers = answers

    def __call__(self, slug: str, prompt: str) -> str:
        return self._answers.get(slug, "")


class RaisingExtractor:
    def __init__(self, exc: Exception):
        self._exc = exc
        self.calls = 0

    def extract(self, raw_reply: str, *, prior_proposal: str = "") -> ExtractedIntent:
        self.calls += 1
        raise self._exc


class EmptyExtractor:
    """Returns a non-usable (empty-intent) extraction — must fall back to regex."""

    def extract(self, raw_reply: str, *, prior_proposal: str = "") -> ExtractedIntent:
        return ExtractedIntent(intent="   ")


_REPLY = "Oh, easy — writing listing descriptions, it eats my whole evening."


def test_AC_INTENT_2_unavailable_falls_back_to_regex():
    raising = RaisingExtractor(IntentExtractUnavailableError("no claude binary"))
    distilled = _distill_intent_via_seam(_REPLY, extractor=raising)
    assert distilled.extracted is None
    assert distilled.phrase == _distill_intent(_REPLY)
    # Consulted at most ONCE (bounded).
    assert raising.calls == 1


def test_AC_INTENT_2_unexpected_exception_also_fails_soft():
    """A misbehaving extractor that raises something OTHER than the sentinel must
    STILL fail soft — onboarding can never break on a model-call bug."""
    raising = RaisingExtractor(RuntimeError("boom"))
    distilled = _distill_intent_via_seam(_REPLY, extractor=raising)
    assert distilled.extracted is None
    assert distilled.phrase == _distill_intent(_REPLY)


def test_AC_INTENT_2_empty_extraction_falls_back_to_regex():
    distilled = _distill_intent_via_seam(_REPLY, extractor=EmptyExtractor())
    assert distilled.extracted is None
    assert distilled.phrase == _distill_intent(_REPLY)


def test_AC_INTENT_2_default_is_disabled_pure_regex():
    """The baseline default extractor DECLINES (no spawn) and the distillation is
    byte-identical to the deterministic regex."""
    assert isinstance(default_intent_extractor(), DisabledIntentExtractor)
    distilled = _distill_intent_via_seam(
        _REPLY, extractor=default_intent_extractor()
    )
    assert distilled.extracted is None
    assert distilled.phrase == _distill_intent(_REPLY)


def test_AC_INTENT_2_run_completes_when_extractor_raises():
    """The whole intake completes (never raises/hangs) when the extractor fails —
    the close still lands on the regex distillation."""
    answerer = ScriptedAnswerer(
        {"stop_start": _REPLY, "confirm_proposal": "yes exactly"}
    )
    raising = RaisingExtractor(IntentExtractUnavailableError("timeout"))
    result = run_translate_in_intake(answerer=answerer, intent_extractor=raising)
    assert result.confirmed
    assert result.has_leverage_idea
    # The close references the REGEX-distilled item (the fallback path ran).
    assert any("listing descriptions" in i.text for i in result.leverage_ideas)
