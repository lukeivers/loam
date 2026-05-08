# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.9 — Per-week budget (≤3 proposals/week) named in body.

Per ``docs/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.9: the SKILL body names the ≤3 proposals/week cap, the
rolling 7-day window, the state path
(`<workspace>/.loam/skill-capture/budget.yaml`), and the reset
semantic (oldest event ages out → cap reopens).
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


def test_body_names_three_proposals_per_week_cap() -> None:
    """Body names the ≤3 proposals/week cap explicitly."""
    body = _load_body()
    has_cap = (
        "≤3" in body
        or "≤ 3" in body
        or "weekly_cap: 3" in body
        or "3 proposals" in body
        or "3/week" in body
    )
    assert has_cap, (
        "AC.SKILLCAP.9: body must name the ≤3 proposals cap."
    )


def test_body_names_rolling_7_day_window() -> None:
    """Body names the rolling 7-day window."""
    body = _load_body().lower()
    has_window = (
        "rolling 7-day" in body
        or "7-day window" in body
        or "rolling-7-day" in body
        or "7d" in body
        or "rolling 7 day" in body
    )
    assert has_window, (
        "AC.SKILLCAP.9: body must name the rolling 7-day window."
    )


def test_body_names_budget_yaml_path() -> None:
    """Body names the budget.yaml state path under
    <workspace>/.loam/skill-capture/."""
    body = _load_body()
    has_path = (
        "budget.yaml" in body
        and ".loam/skill-capture/" in body
    )
    assert has_path, (
        "AC.SKILLCAP.9: body must name the budget.yaml state path "
        "under <workspace>/.loam/skill-capture/."
    )


def test_body_documents_budget_reset_semantic() -> None:
    """Body documents the budget reset semantic: oldest event ages
    out → cap reopens."""
    body = _load_body().lower()
    has_reset = (
        "ages out" in body
        or "rolling-window reset" in body
        or "rolling window reset" in body
        or "oldest event" in body
    )
    assert has_reset, (
        "AC.SKILLCAP.9: body must document the budget reset semantic "
        "(rolling-window age-out → cap reopens)."
    )


def test_body_documents_budget_state_shape() -> None:
    """Body documents the budget state shape — weekly_cap +
    proposed_at_iso + outcome fields."""
    body = _load_body()
    markers = (
        "weekly_cap",
        "proposed_at_iso",
        "outcome",
    )
    found = [m for m in markers if m in body]
    assert len(found) >= 2, (
        f"AC.SKILLCAP.9: body must document budget state shape via "
        f"≥2 of {markers}; found {found}."
    )
