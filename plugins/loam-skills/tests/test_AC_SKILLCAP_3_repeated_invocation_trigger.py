# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.3 — Trigger 2 (repeated-invocation) named in SKILL body.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.3: the SKILL body explicitly names the repeated-
invocation trigger, names the ≥3 threshold, names the structural-
overlap heuristic, and explicitly frames detection as session-
scoped (NOT M-FBM episode-store reads — defers M-FBM dependency to
v0.2.x per master plan §7.3).
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


def test_body_names_repeated_invocation_trigger() -> None:
    """Body names the repeated-invocation trigger."""
    body = _load_body().lower()
    assert (
        "repeated invocation" in body
        or "repeated-invocation" in body
    ), (
        "AC.SKILLCAP.3: body must name the repeated-invocation "
        "trigger."
    )


def test_body_states_three_or_more_threshold() -> None:
    """Body names the ≥3 threshold for repeated-invocation."""
    body = _load_body()
    # Look for "3 or more" or "3+" or "≥3" near the trigger discussion.
    # Permissive: any of these markers anywhere indicates the
    # threshold semantic.
    has_threshold = (
        "3 or more" in body
        or "3+" in body
        or "≥3" in body
        or "≥ 3" in body
        or "three or more" in body
    )
    assert has_threshold, (
        "AC.SKILLCAP.3: body must state the ≥3 threshold (one of: "
        "'3 or more', '3+', '≥3', '≥ 3', 'three or more')."
    )


def test_body_names_structural_overlap_heuristic() -> None:
    """Body names the structural-overlap heuristic for matching
    repeated invocations."""
    body = _load_body().lower()
    assert "structural overlap" in body, (
        "AC.SKILLCAP.3: body must name 'structural overlap' as the "
        "matching heuristic."
    )


def test_body_names_70_percent_overlap_threshold() -> None:
    """Body names the ≥70% structural-overlap threshold."""
    body = _load_body().lower()
    has_70 = "70%" in body or "70 percent" in body
    assert has_70, (
        "AC.SKILLCAP.3: body must name the ≥70% structural-overlap "
        "threshold."
    )


def test_body_states_session_scoped() -> None:
    """Body explicitly states detection is session-scoped — within
    a single session's conversation memory; NOT M-FBM episode-store
    reads."""
    body = _load_body().lower()
    has_scope = (
        "session-scoped" in body
        or "within a session" in body
        or "within a single session" in body
        or "in the current session" in body
    )
    assert has_scope, (
        "AC.SKILLCAP.3: body must state detection is session-scoped."
    )


def test_body_explicitly_defers_mfbm_to_v_0_2_x() -> None:
    """Body names M-FBM (the deferred dependency) and the v0.2.x
    forward path so the deferral is observable."""
    body = _load_body()
    has_mfbm = "M-FBM" in body
    has_deferral = (
        "v0.2.x" in body
        or "deferred" in body.lower()
    )
    assert has_mfbm and has_deferral, (
        "AC.SKILLCAP.3: body must name M-FBM as the deferred "
        "dependency AND name the v0.2.x deferral forward path."
    )
