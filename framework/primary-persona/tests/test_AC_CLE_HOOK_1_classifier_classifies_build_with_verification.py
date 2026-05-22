# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.HOOK.1 — the intent-classifier module classifies a soft
``"I want a tool that does X. show me it works"`` prompt as
``build-with-verification``.

Per amendment #144 Scope A: the classifier MUST recognise the eight
reference soft phrasings from the persona prompt's translate-inbound
stanza AND the anti-trigger cases (pure-question / tiny-tweak). Unit
test exercises the classifier directly (no stdin/stdout); the CLI
integration is exercised by AC.CLE.HOOK.3.
"""

from __future__ import annotations

import pytest

from loam.primary_persona.intent_classifier import (
    INTENT_AMBIGUOUS,
    INTENT_BUILD_WITH_VERIFICATION,
    INTENT_PURE_QUESTION,
    classify_intent,
)


# Eight reference soft phrasings — full build-with-verification join.
# Each carries both a buildable-artifact trigger AND a verification-
# expectation trigger.
_BUILD_WITH_VERIFICATION_CASES = [
    "I want a tool that does X. show me it works",
    "build me a thing that converts X to Y, and check it works",
    "make me a small CLI that fetches feeds. prove it works",
    "I need a script that renames files, and run an example",
    "can you build a converter and verify it works",
    "I want to build a Python package that does X. don't come back until it works",
    "give me a utility that does X, includes tests please",
    "create a small program. make sure it works",
]


# Pure-question cases — anti-trigger fires, no build trigger.
_PURE_QUESTION_CASES = [
    "what does this function do",
    "how does the binary search work in this file",
    "explain the difference between X and Y",
    "why did you choose Z here",
]


# Build-only cases (no verification expectation) — classifier marks
# these ambiguous so the persona uses its own judgment. Mirrors the
# pos3-local pre-promotion behaviour.
_AMBIGUOUS_BUILD_ONLY_CASES = [
    "build me a tool that does X",
    "I want a script that fetches feeds",
]


@pytest.mark.parametrize("prompt", _BUILD_WITH_VERIFICATION_CASES)
def test_classifier_fires_build_with_verification_on_soft_phrasings(
    prompt: str,
) -> None:
    """Each of the eight reference soft phrasings classifies as
    build-with-verification."""
    assert (
        classify_intent(prompt) == INTENT_BUILD_WITH_VERIFICATION
    ), f"prompt did not classify as build-with-verification: {prompt!r}"


@pytest.mark.parametrize("prompt", _PURE_QUESTION_CASES)
def test_classifier_returns_pure_question_on_anti_triggers(
    prompt: str,
) -> None:
    """Anti-trigger cases classify as pure-question (NOT build-with-
    verification)."""
    assert classify_intent(prompt) == INTENT_PURE_QUESTION, (
        f"anti-trigger prompt classified as a build: {prompt!r}"
    )


@pytest.mark.parametrize("prompt", _AMBIGUOUS_BUILD_ONLY_CASES)
def test_classifier_returns_ambiguous_on_build_without_verification(
    prompt: str,
) -> None:
    """Build trigger without verification trigger → ambiguous (the
    persona retains judgment)."""
    assert classify_intent(prompt) == INTENT_AMBIGUOUS, (
        f"build-only prompt did not classify ambiguous: {prompt!r}"
    )


def test_classifier_empty_prompt_returns_ambiguous() -> None:
    assert classify_intent("") == INTENT_AMBIGUOUS
    assert classify_intent("   \n  ") == INTENT_AMBIGUOUS


def test_classifier_tiny_tweak_phrasing_is_pure_question() -> None:
    """Tiny-tweak phrasings (rename, fix the typo, update the
    comment) carry no build trigger; the anti-trigger sends them to
    pure-question."""
    assert classify_intent("rename this variable to X") == INTENT_PURE_QUESTION
    assert classify_intent("fix the typo in line 12") == INTENT_PURE_QUESTION
