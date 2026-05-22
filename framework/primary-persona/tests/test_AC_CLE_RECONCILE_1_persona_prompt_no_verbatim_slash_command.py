# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.RECONCILE.1 — the canonical persona prompt at
``framework/primary-persona/templates/persona-template/prompt.md`` does
NOT prescribe typing ``/handsoff-loop`` (or any other SKILL's slash
command) verbatim into the persona's response, and DOES prescribe
following the auto-loaded SKILL's procedure on build-with-verification
intent.

Per amendment #144 Scope B (TG 11881 ruling): slash commands are
persona-internal mechanism, NOT user-facing output. The persona prompt
predates the ruling; the hook's structural-enforcement layer encodes
the ruling at ``CANONICAL_FORM_TEMPLATE`` in
``loam.primary_persona.intent_classifier``. This test asserts the
persona prompt has been reconciled to match the hook's prescription.

Content-lint shape (not semantic equivalence): the test reads
``prompt.md`` and asserts the conflicting prescription substring is
absent + the reconciled-prescription substring is present.
"""

from __future__ import annotations

from pathlib import Path


PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "templates"
    / "persona-template"
    / "prompt.md"
)


def _read_prompt_text() -> str:
    assert PROMPT_PATH.exists(), (
        f"persona prompt template not found at {PROMPT_PATH}"
    )
    return PROMPT_PATH.read_text(encoding="utf-8")


def test_persona_prompt_does_not_prescribe_verbatim_slash_command_typing() -> None:
    """The pre-amendment-#144 persona prompt prescribed: 'invoke the
    matching SKILL by typing its slash command verbatim into my
    response — `/handsoff-loop`...'

    Per TG 11881 ruling, this prescription is wrong. The reconciled
    prompt MUST NOT contain the verbatim-typing directive."""
    text = _read_prompt_text()
    text_lower = text.lower()
    # The exact phrase the pre-amendment prompt carried.
    assert "typing its slash command verbatim" not in text_lower, (
        "persona prompt still carries the pre-amendment-#144 "
        "verbatim-slash-command directive; per TG 11881 the prompt "
        "should match the hook's prescription (auto-load is primary; "
        "slash commands are persona-internal mechanism, not user-"
        "facing output)."
    )
    # A second, looser, phrase variant that pre-#144 drafts used.
    assert "slash-command invocation bypasses" not in text_lower, (
        "persona prompt still prescribes slash-command invocation as "
        "the bypass path for auto-load — per TG 11881 auto-load IS "
        "the primary path."
    )


def test_persona_prompt_prescribes_auto_load_as_primary_engagement_path() -> None:
    """The reconciled prompt MUST mention that Claude Code's SKILL
    auto-load is the primary mechanism + that the persona follows the
    auto-loaded SKILL's procedure on build-with-verification intent."""
    text = _read_prompt_text()
    text_lower = text.lower()
    # The reconciled prescription substring (per Scope B D-CLE.RECONCILE-TEST).
    assert "auto-load" in text_lower, (
        "persona prompt missing the auto-load reference — Scope B's "
        "reconciliation must surface auto-load as the canonical "
        "engagement path."
    )
    # The persona must FOLLOW the SKILL's procedure (not type its
    # slash command). Match a substring that asserts the routing
    # discipline.
    assert "follow" in text_lower, (
        "persona prompt missing the 'follow' framing for the auto-"
        "loaded SKILL's procedure."
    )


def test_persona_prompt_keeps_inline_build_lens2_violation_framing() -> None:
    """Scope B keeps the Lens 2 violation framing for inline-build on
    build-with-verification intent — the rewrite tightens the routing
    prescription but preserves the substance (inline build is wrong on
    this intent)."""
    text = _read_prompt_text()
    text_lower = text.lower()
    assert "lens 2" in text_lower, (
        "persona prompt missing the Lens 2 violation framing — the "
        "reconciliation should preserve this rule, not delete it."
    )
    assert "inline" in text_lower, (
        "persona prompt missing the inline-build prohibition — Scope "
        "B preserves the substance while tightening the routing path."
    )
