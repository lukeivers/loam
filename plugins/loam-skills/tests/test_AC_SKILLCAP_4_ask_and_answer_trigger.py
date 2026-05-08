# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.4 — Trigger 3 (ask-and-answer) named in SKILL body.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.4: the SKILL body explicitly names the ask-and-answer
trigger, names the 3+ exchanges + answer-stabilization threshold,
names the non-dev-emphasis (especially valuable for non-dev users),
and explicitly frames detection as session-scoped.
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


def test_body_names_ask_and_answer_trigger() -> None:
    """Body names the ask-and-answer trigger."""
    body = _load_body().lower()
    assert (
        "ask and answer" in body
        or "ask-and-answer" in body
    ), (
        "AC.SKILLCAP.4: body must name the ask-and-answer trigger."
    )


def test_body_states_three_exchange_threshold() -> None:
    """Body names the 3+ exchanges threshold."""
    body = _load_body()
    has_threshold = (
        "3 or more" in body
        or "3+" in body
        or "≥3" in body
        or "≥ 3" in body
        or "three or more" in body
    )
    assert has_threshold, (
        "AC.SKILLCAP.4: body must name the 3+ exchanges threshold."
    )


def test_body_names_answer_stabilization() -> None:
    """Body names answer-text stabilization across exchanges."""
    body = _load_body().lower()
    assert "stabilizes" in body or "stabilized" in body or "stable" in body, (
        "AC.SKILLCAP.4: body must name answer-text stabilization "
        "(via 'stabilizes', 'stabilized', or 'stable')."
    )


def test_body_emphasizes_non_dev_users() -> None:
    """Body names the non-dev-user value-add explicitly."""
    body = _load_body().lower()
    has_non_dev = (
        "non-dev" in body
        or "non dev" in body
        or "non-developer" in body
    )
    assert has_non_dev, (
        "AC.SKILLCAP.4: body must name the especial value for "
        "non-dev users."
    )


def test_body_states_session_scoped() -> None:
    """Body explicitly states detection is session-scoped — within
    a single session's conversation memory."""
    body = _load_body().lower()
    has_scope = (
        "session-scoped" in body
        or "within a session" in body
        or "within a single session" in body
        or "in the current session" in body
    )
    assert has_scope, (
        "AC.SKILLCAP.4: body must state detection is session-scoped."
    )


def test_body_names_question_text_similarity() -> None:
    """Body names the question-text similarity heuristic."""
    body = _load_body().lower()
    # Permissive: any of "question-text", "question shape", "similarity"
    # mentioned in the ask-and-answer context.
    has_qt = (
        "question-text" in body
        or "question text" in body
        or "shape of question" in body
        or "question shape" in body
    )
    has_similarity = (
        "similarity" in body
        or "overlap" in body
    )
    assert has_qt and has_similarity, (
        "AC.SKILLCAP.4: body must name the question-text similarity "
        "heuristic (question-text/shape + similarity/overlap)."
    )
