# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.2 — Trigger 1 (explicit-request) named in SKILL body.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.2: the SKILL body explicitly names the explicit-request
trigger, lists ≥3 phrase examples (including "remember this", a
"make this a {thing,skill}" variant, and "let's codify this" or
"capture this as a skill"), and states the on-match semantic
(immediate proposal-draft mode).
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "skill-capture-proposal"
    / "SKILL.md"
)


def _load_body() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n.*?\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match
    return match.group(1)


def test_body_names_explicit_request_trigger() -> None:
    """Body names the explicit-request trigger explicitly."""
    body = _load_body().lower()
    assert ("explicit request" in body) or ("explicit-request" in body), (
        "AC.SKILLCAP.2: body must name the explicit-request trigger."
    )


def test_body_includes_remember_this_phrase() -> None:
    """Phrase-list includes "remember this" (highest-precision
    canonical phrase)."""
    body = _load_body().lower()
    assert "remember this" in body, (
        "AC.SKILLCAP.2: body must include the canonical "
        "'remember this' phrase as an explicit-request example."
    )


def test_body_includes_make_this_phrase_variant() -> None:
    """Phrase-list includes a "make this a {thing,skill,reusable}"
    variant — the second canonical explicit-request phrase."""
    body = _load_body().lower()
    has_variant = (
        "make this a thing" in body
        or "make this a skill" in body
        or "make this reusable" in body
    )
    assert has_variant, (
        "AC.SKILLCAP.2: body must include a 'make this a {thing/"
        "skill/reusable}' phrase variant."
    )


def test_body_includes_codify_or_capture_phrase() -> None:
    """Phrase-list includes a "let's codify this" or "capture this
    as a skill" variant — the third canonical explicit-request
    phrase."""
    body = _load_body().lower()
    has_variant = (
        "let's codify this" in body
        or "let's capture this" in body
        or "capture this as a skill" in body
        or "save this as a skill" in body
    )
    assert has_variant, (
        "AC.SKILLCAP.2: body must include a 'codify' or 'capture as "
        "skill' phrase variant."
    )


def test_body_states_immediate_draft_semantic() -> None:
    """On match → proposal-draft mode immediately. Body names the
    immediate semantic."""
    body = _load_body().lower()
    # Look for "immediately" within proximity of explicit-request
    # discussion. Permissive match: "immediately" anywhere in body
    # is enough — the explicit-request section is the only place
    # the SKILL discusses immediate-draft mode (no other trigger
    # is immediate; Trigger 2 + 3 require thresholds).
    assert "immediately" in body, (
        "AC.SKILLCAP.2: body must state the immediate-draft "
        "semantic (the 'immediately' keyword) for the explicit-"
        "request trigger."
    )


def test_body_lists_three_or_more_explicit_phrases() -> None:
    """Phrase-list has ≥3 examples — the AC requirement."""
    body = _load_body().lower()
    candidate_phrases = (
        "remember this",
        "make this a thing",
        "make this a skill",
        "make this reusable",
        "let's codify this",
        "let's capture this",
        "capture this as a skill",
        "save this as a skill",
        "remember this pattern",
        "add this to my skills",
    )
    found = [p for p in candidate_phrases if p in body]
    assert len(found) >= 3, (
        f"AC.SKILLCAP.2: body must include ≥3 phrase examples; "
        f"found {len(found)}: {found}"
    )
