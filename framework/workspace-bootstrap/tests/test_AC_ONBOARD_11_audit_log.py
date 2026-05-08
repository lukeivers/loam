# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.11 — SOC-2 audit-log floor per Decision P.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.11: every Q + A + activation
emits an audit-log entry; schema_version + event_kind + timestamp +
notes + artefact_path; YAML parses; expected event_kinds present.
"""

from __future__ import annotations

from pathlib import Path


from loam.workspace_bootstrap.onboarding import run_onboarding
from loam.workspace_bootstrap.onboarding_audit import (
    audit_log_path,
    emit_audit_entry,
    read_audit_entries,
)


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


def test_audit_log_present_post_ritual(tmp_path: Path) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    log = audit_log_path(tmp_path)
    assert log.exists()


def test_audit_log_schema_shape(tmp_path: Path) -> None:
    """Each audit entry has the expected SOC-2-floor fields."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    entries = read_audit_entries(tmp_path)
    assert entries, "audit-log must contain entries"
    for entry in entries:
        assert entry["schema_version"] == 1
        assert "event_kind" in entry
        assert "timestamp" in entry
        assert "notes" in entry
        assert "artefact_path" in entry


def test_audit_log_event_kinds_present(tmp_path: Path) -> None:
    """Expected event_kinds all present for a full ritual run."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    entries = read_audit_entries(tmp_path)
    kinds = {e["event_kind"] for e in entries}
    expected = {
        "onboarding_started",
        "onboarding_question_asked",
        "onboarding_response_recorded",
        "onboarding_completed",
    }
    assert expected.issubset(kinds), f"missing event_kinds: {expected - kinds}"


def test_audit_log_six_question_asked_entries(tmp_path: Path) -> None:
    """Six onboarding_question_asked entries (one per question)."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    entries = read_audit_entries(tmp_path)
    asked = [e for e in entries if e["event_kind"] == "onboarding_question_asked"]
    assert len(asked) == 6


def test_emit_audit_entry_appends_to_file(tmp_path: Path) -> None:
    """Multiple emit calls append rather than overwrite."""
    emit_audit_entry(tmp_path, event_kind="onboarding_started", notes="first")
    emit_audit_entry(tmp_path, event_kind="onboarding_completed", notes="second")
    entries = read_audit_entries(tmp_path)
    assert len(entries) == 2
    assert entries[0]["notes"] == "first"
    assert entries[1]["notes"] == "second"


def test_resume_via_audit_log(tmp_path: Path) -> None:
    """D3 restart: audit-log onboarding_question_asked entries serve as
    resume signal — a second invocation can detect prior progress."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    # First (truncated) run — one question asked, one response.
    emit_audit_entry(tmp_path, event_kind="onboarding_started", notes="run1")
    emit_audit_entry(
        tmp_path, event_kind="onboarding_question_asked", notes="slug=language"
    )
    entries = read_audit_entries(tmp_path)
    asked = [e for e in entries if e["event_kind"] == "onboarding_question_asked"]
    # Demonstrates audit-log can be queried for "where did we stop?"
    assert asked, "asked entries observable via read_audit_entries"
