# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.6 — User-ratification via PM (Y/N/R gate) named in body.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.6: the SKILL body names the PM ratification surface
(`PMRuntime.enqueue_decision` + `surface_next_questions_batch(n=1)`),
the one-line decision-question shape, the Y/N/R semantics including
the `<workspace>/.claude/skills/<slug>/SKILL.md` write-on-Y target,
and the one-question-at-a-time discipline.
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


def test_body_names_pmruntime_enqueue_decision() -> None:
    """Body names PMRuntime.enqueue_decision as the ratification
    primitive."""
    body = _load_body()
    # Permissive: either the dotted name or a separate mention is fine.
    has_pm_call = (
        "PMRuntime.enqueue_decision" in body
        or "pm.enqueue_decision" in body
        or "enqueue_decision" in body
    )
    assert has_pm_call, (
        "AC.SKILLCAP.6: body must name PMRuntime.enqueue_decision "
        "as the ratification enqueue primitive."
    )


def test_body_names_surface_next_questions_batch_n_1() -> None:
    """Body names `surface_next_questions_batch(n=1)` (one-question-
    at-a-time per Decision Q + AC.QSURF.1)."""
    body = _load_body()
    has_batch = (
        "surface_next_questions_batch" in body
    )
    has_n_1 = ("n=1" in body) or ("(n=1)" in body)
    assert has_batch and has_n_1, (
        "AC.SKILLCAP.6: body must name surface_next_questions_batch "
        "with the n=1 batch size."
    )


def test_body_names_y_n_r_semantics() -> None:
    """Body names Y / N / R(evise) ratification semantics."""
    body = _load_body()
    # Permissive: look for the canonical form "Y / N / R" or close.
    has_yn = (
        "Y / N / R" in body
        or "Y/N/R" in body
        or "Y or N or R" in body
    )
    # Must also explain what each does.
    has_revise = "revis" in body.lower()  # "revise" / "revision"
    has_reject = "reject" in body.lower()
    has_ratify_or_materialize = (
        "ratif" in body.lower()
        or "materializ" in body.lower()
        or "materialise" in body.lower()
    )
    assert has_yn and has_revise and has_reject and has_ratify_or_materialize, (
        "AC.SKILLCAP.6: body must name Y/N/R semantics with "
        "revise/reject/ratify-or-materialize each named."
    )


def test_body_names_claude_skills_write_target() -> None:
    """Body names the write-on-Y target path:
    `<workspace>/.claude/skills/<slug>/SKILL.md`."""
    body = _load_body()
    has_target = (
        "<workspace>/.claude/skills/<slug>/SKILL.md" in body
        or ".claude/skills/<slug>/SKILL.md" in body
        or ".claude/skills/<proposed-slug>/SKILL.md" in body
    )
    assert has_target, (
        "AC.SKILLCAP.6: body must name the write-on-Y target path "
        "<workspace>/.claude/skills/<slug>/SKILL.md."
    )


def test_body_references_one_question_at_a_time_discipline() -> None:
    """Body references the v0.1.7 Cycle 4 one-question-at-a-time
    discipline (Decision Q + AC.QSURF.1)."""
    body = _load_body()
    # Permissive: any of these markers indicates the reference.
    markers = (
        "one-question-at-a-time",
        "one question at a time",
        "Decision Q",
        "AC.QSURF.1",
        "v0.1.7 Cycle 4",
    )
    has_marker = any(m in body for m in markers)
    assert has_marker, (
        f"AC.SKILLCAP.6: body must reference the one-question-at-a-"
        f"time discipline (one of {markers})."
    )


def test_body_names_record_response_for_response_capture() -> None:
    """Body names `record_response` as the response-capture primitive
    (closes the ratification loop)."""
    body = _load_body()
    assert "record_response" in body, (
        "AC.SKILLCAP.6: body must name `record_response` as the "
        "response-capture primitive."
    )
