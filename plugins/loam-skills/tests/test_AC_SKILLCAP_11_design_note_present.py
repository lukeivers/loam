# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.11 — Design note present + structured.

Per ``docs/rebuild/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.11: the design note exists at
`docs/design/auto-skill-capture-shape.md` with required sections,
universal-tier framing, user-ratifies-not-persona-decides framing,
v0.2.x deferred-trigger naming, and Eric grounding.

The design note is co-shipping with the SKILL per Lens 5 stopping-
criterion (separate cycle would be coordination overhead).
"""

from __future__ import annotations

from pathlib import Path


# Repo root: tests/ → plugins/loam-skills/ → plugins/ → repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DESIGN_NOTE_PATH = REPO_ROOT / "docs" / "design" / "auto-skill-capture-shape.md"


REQUIRED_SECTIONS = (
    "## §1 — architecture",
    "## §2 — triggers",
    "## §3 — workflow",
    "## §4 — cool-down",
    "## §5 — failure modes",
    "## §6 — composition",
    "## §7 — forward path",
)


def test_design_note_file_exists() -> None:
    """Design note file is present at the canonical path."""
    assert DESIGN_NOTE_PATH.is_file(), (
        f"AC.SKILLCAP.11: design note must exist at "
        f"{DESIGN_NOTE_PATH}."
    )


def test_design_note_has_required_sections() -> None:
    """Design note has the 7 required sections."""
    text = DESIGN_NOTE_PATH.read_text(encoding="utf-8").lower()
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    assert not missing, (
        f"AC.SKILLCAP.11: design note missing sections {missing}. "
        f"Required: {REQUIRED_SECTIONS}."
    )


def test_design_note_names_universal_tier() -> None:
    """Design note names the universal-tier framing."""
    text = DESIGN_NOTE_PATH.read_text(encoding="utf-8").lower()
    has_universal = (
        "universal-tier" in text
        or "universal tier" in text
        or "universal across" in text
    )
    assert has_universal, (
        "AC.SKILLCAP.11: design note must name the universal-tier "
        "framing."
    )


def test_design_note_names_ratification_gate_framing() -> None:
    """Design note names the user-ratifies-not-persona-decides
    framing — the structural defence against silent skill-write."""
    text = DESIGN_NOTE_PATH.read_text(encoding="utf-8").lower()
    has_ratify = "user-ratif" in text or "ratification gate" in text
    has_silent = "silent" in text  # "silent skill-write" / "silent"
    assert has_ratify and has_silent, (
        "AC.SKILLCAP.11: design note must name the user-ratification "
        "gate AND the silent-skill-write anti-pattern."
    )


def test_design_note_names_deferred_three_triggers() -> None:
    """Design note names the v0.2.x deferred 3 triggers (CLAUDE.md
    drift / memory-recall / hook-trigger)."""
    text = DESIGN_NOTE_PATH.read_text(encoding="utf-8")
    has_claude_drift = (
        "CLAUDE.md drift" in text
        or "CLAUDE.md-drift" in text
    )
    has_memory_recall = (
        "memory-recall" in text
        or "Memory-recall" in text
    )
    has_hook_trigger = (
        "hook-trigger" in text
        or "Hook-trigger" in text
    )
    assert has_claude_drift, (
        "AC.SKILLCAP.11: design note must name CLAUDE.md drift "
        "deferred trigger."
    )
    assert has_memory_recall, (
        "AC.SKILLCAP.11: design note must name memory-recall "
        "deferred trigger."
    )
    assert has_hook_trigger, (
        "AC.SKILLCAP.11: design note must name hook-trigger "
        "deferred trigger."
    )


def test_design_note_names_eric_grounding() -> None:
    """Design note names Eric — concrete grounding for universal-tier
    framing."""
    text = DESIGN_NOTE_PATH.read_text(encoding="utf-8")
    assert "Eric" in text, (
        "AC.SKILLCAP.11: design note must name Eric (concrete "
        "grounding for the universal-tier framing)."
    )
