# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.HOOK.2 — the additionalContext template body references
``handsoff-loop`` SKILL + auto-load mechanism and does NOT prescribe
verbatim slash-command typing.

Per amendment #144 Scope A + Scope B (TG 11881 ruling):

  - the template MUST mention ``handsoff-loop`` (so Claude Code's
    SKILL matcher fires on the injected text);
  - the template MUST mention auto-load (the canonical engagement
    path);
  - the template MUST NOT instruct the persona to type
    ``/handsoff-loop`` verbatim as a routine routing path (slash
    commands are persona-internal mechanism, NOT user-facing
    output);
  - the template MAY reference the slash command as a manual backup
    invocation — the "never as routine" prohibition is the
    structural assertion, not "the literal string is forbidden."

This test asserts the template body invariants. The CLI integration
(stdin/stdout round-trip) is exercised by AC.CLE.HOOK.3.
"""

from __future__ import annotations

from loam.primary_persona.intent_classifier import (
    CANONICAL_FORM_TEMPLATE,
    INTENT_BUILD_WITH_VERIFICATION,
    build_hook_output,
)


def test_template_mentions_handsoff_loop_skill_by_name() -> None:
    assert "handsoff-loop" in CANONICAL_FORM_TEMPLATE


def test_template_mentions_auto_load_mechanism() -> None:
    # Match the canonical phrasing: "auto-load" or "auto-load[ed]"
    # appears in the body. Lowercased compare so the test stays robust
    # if the template wording is later case-shifted.
    assert "auto-load" in CANONICAL_FORM_TEMPLATE.lower()


def test_template_forbids_inline_build_on_build_with_verification() -> None:
    """The template must encode the hard structural forcing — inline
    build is a Lens 2 violation on this classification."""
    body_lower = CANONICAL_FORM_TEMPLATE.lower()
    assert "do not build inline" in body_lower
    assert "lens 2" in body_lower


def test_template_does_not_prescribe_typing_slash_command_verbatim() -> None:
    """Per TG 11881 ruling, slash commands are NOT user-facing — the
    template MUST NOT instruct the persona to type ``/handsoff-loop``
    verbatim into a response.

    Allowed: mentioning the slash command exists as a manual backup
    invocation. Forbidden: prescribing it as the routine routing
    path. We assert via the strict negative substring that the
    pos3-pre-promotion drafts of the persona prompt carried."""
    body_lower = CANONICAL_FORM_TEMPLATE.lower()
    # The pre-amendment-#144 persona prompt used phrasing like
    # "by typing its slash command verbatim" — that exact framing
    # MUST NOT appear in the hook's additionalContext body.
    assert "typing its slash command verbatim" not in body_lower
    assert "type /handsoff-loop verbatim" not in body_lower
    # The template MUST state that no slash-command typing is required.
    assert "no slash command typing is required" in body_lower


def test_build_hook_output_emits_envelope_on_build_with_verification() -> None:
    """``build_hook_output`` returns a non-empty Claude Code envelope
    when the intent is build-with-verification."""
    output = build_hook_output(INTENT_BUILD_WITH_VERIFICATION)
    assert output is not None
    assert output["hookEventName"] == "UserPromptSubmit"
    assert "hookSpecificOutput" in output
    inner = output["hookSpecificOutput"]
    assert "additionalContext" in inner
    body = inner["additionalContext"]
    assert "handsoff-loop" in body
    assert "auto-load" in body.lower()


def test_build_hook_output_returns_none_on_non_build_intent() -> None:
    """No injection for pure-question / tiny-tweak / ambiguous."""
    assert build_hook_output("pure-question") is None
    assert build_hook_output("tiny-tweak") is None
    assert build_hook_output("ambiguous") is None
