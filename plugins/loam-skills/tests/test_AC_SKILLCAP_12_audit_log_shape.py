# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLCAP.12 — Audit-log shape named in body.

Per ``docs/rebuild/plans/v0-2-0-cycle-2-auto-skill-creation.md`` §4
AC.SKILLCAP.12: the SKILL body names the audit-log directory
(`<workspace>/.loam/skill-capture/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`),
the 6 event-kinds, and the SOC-2 audit-trail floor (Decision P)
discipline source.
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


# Six event-kinds named at master plan + plan-doc §4 AC.SKILLCAP.12.
REQUIRED_EVENT_KINDS = (
    "skill_capture_trigger_fired",
    "skill_capture_proposal_drafted",
    "skill_capture_ratified",
    "skill_capture_rejected",
    "skill_capture_revised",
    "skill_capture_cooldown_active",
)


def test_body_names_audit_log_directory_path() -> None:
    """Body names the audit-log directory under
    <workspace>/.loam/skill-capture/audit-log/."""
    body = _load_body()
    has_dir = (
        ".loam/skill-capture/audit-log/" in body
    )
    assert has_dir, (
        "AC.SKILLCAP.12: body must name the audit-log directory "
        "<workspace>/.loam/skill-capture/audit-log/."
    )


def test_body_names_audit_log_filename_convention() -> None:
    """Body names the audit-log filename convention
    `<YYYY-MM-DD>-<NNNN>.yaml`."""
    body = _load_body()
    has_filename = (
        "<YYYY-MM-DD>-<NNNN>.yaml" in body
    )
    assert has_filename, (
        "AC.SKILLCAP.12: body must name the audit-log filename "
        "convention <YYYY-MM-DD>-<NNNN>.yaml."
    )


def test_body_names_all_six_event_kinds() -> None:
    """Body names all 6 event-kinds explicitly."""
    body = _load_body()
    missing = [k for k in REQUIRED_EVENT_KINDS if k not in body]
    assert not missing, (
        f"AC.SKILLCAP.12: body missing event-kinds {missing}. "
        f"Required: {REQUIRED_EVENT_KINDS}."
    )


def test_body_references_soc_2_audit_trail_floor() -> None:
    """Body references the SOC-2 audit-trail floor (Decision P) as
    the discipline source."""
    body = _load_body()
    has_soc = "SOC-2" in body or "SOC 2" in body
    has_decision = "Decision P" in body
    assert has_soc and has_decision, (
        "AC.SKILLCAP.12: body must reference the SOC-2 audit-trail "
        "floor AND Decision P as the discipline source."
    )


def test_body_references_pm_audit_log_cross_reference() -> None:
    """Body documents that ratification audit entries are ALSO
    recorded in PM's audit-log (cross-reference, not duplication)."""
    body = _load_body()
    has_pm_audit = (
        "PM's audit-log" in body
        or "per-project-pm" in body  # the runtime that owns the audit-log
        or "PM audit-log" in body
    )
    has_cross_reference = (
        "surface_question" in body
        and "record_response" in body
    )
    assert has_pm_audit or has_cross_reference, (
        "AC.SKILLCAP.12: body must document the cross-reference to "
        "per-project-pm's audit-log (via 'surface_question' + "
        "'record_response' or PM audit-log naming)."
    )
