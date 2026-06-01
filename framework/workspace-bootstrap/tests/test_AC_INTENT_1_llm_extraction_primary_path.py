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

"""AC.INTENT.1 — the LLM intent-extraction seam is the PRIMARY distillation path.

When a real intent-extractor is registered, the distillation consults it FIRST on
the raw reply, and a usable extraction is used as the distilled intent — preferred
over what the deterministic regex would have produced. This dissolves the
recurring free-form-phrasing extraction misses the six regex-hardening rounds
chased (the smoke's ``four-step-loop-ran`` PARTIAL).
"""

from __future__ import annotations

from loam.workspace_bootstrap.intent_extract import ExtractedIntent
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


class FakeExtractor:
    """A deterministic stand-in for the real ClaudeIntentExtractor — returns a
    fixed extraction WITHOUT spawning, so the test exercises the seam's PRIMARY
    path without a live model call."""

    def __init__(self, extracted: ExtractedIntent):
        self._extracted = extracted
        self.calls: list[str] = []

    def extract(self, raw_reply: str, *, prior_proposal: str = "") -> ExtractedIntent:
        self.calls.append(raw_reply)
        return self._extracted


# A free-form reply whose REGEX distillation differs from a clean human read — the
# extractor should win, landing the model's intent phrase, not the regex's.
_FREEFORM = (
    "ugh, honestly the thing that's killing me is I spend my whole evening "
    "wrestling these property writeups into something that sounds halfway decent"
)
_MODEL_INTENT = "writing property descriptions"


def test_AC_INTENT_1_extractor_consulted_and_preferred():
    fake = FakeExtractor(ExtractedIntent(intent=_MODEL_INTENT))
    distilled = _distill_intent_via_seam(_FREEFORM, extractor=fake)
    # The extractor was consulted (PRIMARY path) ...
    assert fake.calls == [_FREEFORM]
    # ... and its intent is what the distillation returns.
    assert distilled.phrase == _MODEL_INTENT
    assert distilled.extracted is not None
    # The regex would have produced something different (proves the model won).
    assert _distill_intent(_FREEFORM) != _MODEL_INTENT


def test_AC_INTENT_1_extracted_intent_flows_into_the_close():
    """End-to-end: the registered extractor's intent reaches the proposal + close,
    not the regex distillation."""
    fake = FakeExtractor(
        ExtractedIntent(
            intent=_MODEL_INTENT, deeper_end_intent="get their evenings back"
        )
    )
    answerer = ScriptedAnswerer(
        {"stop_start": _FREEFORM, "confirm_proposal": "yes, exactly that"}
    )
    result = run_translate_in_intake(answerer=answerer, intent_extractor=fake)
    assert result.confirmed
    # The proposal + the landed close reference the MODEL's intent phrase.
    assert result.proposal is not None
    assert _MODEL_INTENT in result.proposal.objective_text
    assert result.has_leverage_idea
    assert any(_MODEL_INTENT in i.text for i in result.leverage_ideas)
