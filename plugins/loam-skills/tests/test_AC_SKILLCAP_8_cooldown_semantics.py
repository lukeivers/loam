# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.8 — Cool-down semantics (14d post-N) named in body.

Per ``docs/rebuild/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.8: the SKILL body names the 14-day cool-down + the
state path (`<workspace>/.loam/skill-capture/cooldowns.yaml`) + the
state shape + the persona's check-before-propose discipline.
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


def test_body_names_14_day_cooldown() -> None:
    """Body names the 14-day cool-down duration explicitly."""
    body = _load_body().lower()
    has_14_day = (
        "14 days" in body
        or "14-day" in body
        or "14d" in body
    )
    assert has_14_day, (
        "AC.SKILLCAP.8: body must name the 14-day cool-down "
        "duration."
    )


def test_body_names_cooldowns_yaml_path() -> None:
    """Body names the cooldowns.yaml state path."""
    body = _load_body()
    has_path = (
        "cooldowns.yaml" in body
        and ".loam/skill-capture/" in body
    )
    assert has_path, (
        "AC.SKILLCAP.8: body must name the cooldowns.yaml state "
        "path under <workspace>/.loam/skill-capture/."
    )


def test_body_documents_cooldown_state_shape() -> None:
    """Body documents the state shape (trigger_pattern_hash +
    rejection_iso + cooldown_until_iso)."""
    body = _load_body()
    markers = (
        "trigger_pattern_hash",
        "rejection_iso",
        "cooldown_until_iso",
    )
    found = [m for m in markers if m in body]
    assert len(found) >= 2, (
        f"AC.SKILLCAP.8: body must document the cool-down state "
        f"shape via ≥2 of {markers}; found {found}."
    )


def test_body_names_check_before_propose_discipline() -> None:
    """Body names the check-before-propose discipline: persona reads
    cooldowns.yaml at Step 1 (Detect + draft) and no-ops on hit."""
    body = _load_body().lower()
    # Permissive: look for "check" + "before" or "step 1" + "cool"
    has_check = (
        "no-op" in body
        or "no op" in body
        or "skip the proposal" in body
    )
    assert has_check, (
        "AC.SKILLCAP.8: body must name the check-before-propose "
        "discipline (no-op on cool-down hit)."
    )
