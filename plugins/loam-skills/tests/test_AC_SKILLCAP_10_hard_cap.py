# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.10 — Hard-cap (20 workspace-local SKILLs) named in body.

Per ``docs/rebuild/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.10: the SKILL body names the 20-skill hard-cap on
workspace-local SKILLs at `<workspace>/.claude/skills/`, the no-op
+ promotion-rubric-pointer behavior on cap-reached, and the
filesystem-walk count source.
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


def test_body_names_20_skill_hard_cap() -> None:
    """Body names the 20-skill hard-cap explicitly."""
    body = _load_body()
    has_cap = (
        "hard-cap (20)" in body
        or "hard-cap of 20" in body
        or "hard-cap at 20" in body
        or "20 SKILLs" in body
        or "20 workspace-local" in body
        or "20 skills" in body.lower()
        or "20-skill hard-cap" in body
        or "≥ 20" in body
        or "≥20" in body
        or "count ≥ 20" in body
    )
    assert has_cap, (
        "AC.SKILLCAP.10: body must name the 20-skill hard-cap."
    )


def test_body_names_workspace_local_path() -> None:
    """Body names the workspace-local skills path
    `<workspace>/.claude/skills/`."""
    body = _load_body()
    has_path = (
        "<workspace>/.claude/skills/" in body
        or ".claude/skills/<*>/SKILL.md" in body
        or ".claude/skills/<slug>/" in body
    )
    assert has_path, (
        "AC.SKILLCAP.10: body must name the workspace-local skills "
        "path <workspace>/.claude/skills/."
    )


def test_body_names_promotion_rubric_pointer() -> None:
    """Body names the promotion-rubric forward pointer (skill-
    promotion-review at v0.2.1)."""
    body = _load_body()
    has_promotion = "skill-promotion-review" in body
    has_v021 = "v0.2.1" in body
    assert has_promotion and has_v021, (
        "AC.SKILLCAP.10: body must name skill-promotion-review and "
        "v0.2.1 as the promotion forward path."
    )


def test_body_names_filesystem_walk_count_source() -> None:
    """Body names the filesystem-walk as the SKILL count source
    (matches Anthropic's discovery primitive)."""
    body = _load_body().lower()
    has_walk = (
        "filesystem-walk" in body
        or "filesystem walk" in body
        or "walk" in body
    )
    assert has_walk, (
        "AC.SKILLCAP.10: body must name filesystem-walk as the count "
        "source."
    )


def test_body_states_no_op_on_cap_reached() -> None:
    """Body states the no-op behavior on cap-reached + persona-
    surfaces-note semantic."""
    body = _load_body().lower()
    has_no_op = "no-op" in body or "no op" in body
    has_surface = "surface" in body
    assert has_no_op and has_surface, (
        "AC.SKILLCAP.10: body must state the no-op + surface-a-note "
        "behavior on cap-reached."
    )
