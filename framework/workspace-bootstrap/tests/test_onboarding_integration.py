# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Integration test — full onboarding ritual end-to-end on synthetic-rails.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.14: asserts every AC's
exit-state simultaneously (manifest fields + audit-log + summary
file + activation side-effects).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from loam.workspace_bootstrap.manifest import load_manifest
from loam.workspace_bootstrap.onboarding import QUESTION_SLUGS, run_onboarding
from loam.workspace_bootstrap.onboarding_audit import (
    audit_log_path,
    read_audit_entries,
)


FIXTURES = Path(__file__).parent / "fixtures" / "fresh-user-onboarding"


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


def test_full_ritual_end_to_end_rails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Synthetic-rails fixture + production-stake selection + extractor
    yes (mocked) + watch yes + skill-capture yes (force-flipped to no
    by production-stake) → all expected side-effects."""
    # Fake home so Telegram marker writes don't pollute test runner.
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))

    workspace = tmp_path / "ws"
    shutil.copytree(FIXTURES / "synthetic-rails", workspace)
    bootstrap = workspace / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")

    # Q1=Y (rails); Q2=1 telegram; Q3=1 production-stake;
    # Q4=1 extractor-yes; Q5=1 watch-yes; Q6=1 capture-yes (force-flip).
    answers = ["y", "1", "1", "1", "1", "1"]

    result = run_onboarding(
        workspace,
        answerer=_scripted(answers),
        extractor_cmd=["/usr/bin/true"],
    )

    # Manifest fields all populated.
    manifest = load_manifest(bootstrap)
    assert manifest.language_primary == "rails"
    assert manifest.channel_preference == "telegram"
    assert manifest.safety_profile == "production-stake"
    assert manifest.extractor_opt_in == "yes"
    assert manifest.watch_opt_in == "yes"
    # AC.ONBOARD.10: production-stake forces auto-skill-capture off.
    assert manifest.enable_auto_skill_capture is False
    assert manifest.onboarding_completed_at is not None

    # Audit-log: every event_kind emitted.
    entries = read_audit_entries(workspace)
    kinds = {e["event_kind"] for e in entries}
    assert "onboarding_started" in kinds
    assert "onboarding_question_asked" in kinds
    assert "onboarding_response_recorded" in kinds
    assert "onboarding_capability_activated" in kinds
    assert "onboarding_default_flip" in kinds
    assert "onboarding_completed" in kinds

    # Six question_asked entries (one per slug).
    asked = [e for e in entries if e["event_kind"] == "onboarding_question_asked"]
    assert len(asked) == len(QUESTION_SLUGS) == 6

    # Three activations fired (telegram + extractor + watch).
    assert len(result.activations) == 3
    activation_kinds = {a.kind for a in result.activations}
    assert {"channel-telegram", "extractor", "watch-pointer"} == activation_kinds

    # Completion summary written.
    summary = result.completion_summary_path
    assert summary.exists()
    summary_text = summary.read_text(encoding="utf-8")
    assert "production-stake" in summary_text
    # Force-flip note surfaced per AC.ONBOARD.10.
    assert "auto-skill-capture" in summary_text.lower()

    # Watch-pointer file written.
    pointer = workspace / ".loam" / "continuous-watch-pointer.md"
    assert pointer.exists()

    # Telegram marker written under fake home.
    telegram_marker = fake_home / ".loam" / "telegram-setup-offered"
    assert telegram_marker.exists()


def test_full_ritual_idempotent_rerun(tmp_path: Path) -> None:
    """D2 steady-state: re-run on an already-onboarded workspace
    completes successfully (re-reads manifest + re-asks questions +
    no exception)."""
    workspace = tmp_path
    bootstrap = workspace / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers_1 = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(workspace, answerer=_scripted(answers_1))
    # Re-run — no exception.
    answers_2 = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(workspace, answerer=_scripted(answers_2))
    # Manifest still readable; onboarding_completed_at present.
    manifest = load_manifest(bootstrap)
    assert manifest.onboarding_completed_at is not None
