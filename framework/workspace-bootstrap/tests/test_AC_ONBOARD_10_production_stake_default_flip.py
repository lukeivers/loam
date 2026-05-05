# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.10 — Production-stake forces auto-skill-capture off.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.10 + Decision P SOC-2 floor:
when Q3=production-stake AND Q6=Y, the ritual forces
enable_auto_skill_capture=False; audit-log records the flip.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.manifest import load_manifest
from loam.workspace_bootstrap.onboarding import run_onboarding
from loam.workspace_bootstrap.onboarding_audit import read_audit_entries


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


def test_production_stake_forces_auto_skill_capture_false(
    tmp_path: Path,
) -> None:
    """Q3=production-stake + Q6=Y → final manifest enable_auto_skill_capture=False."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    # Q3=1 production-stake; Q6=1 yes (will be force-flipped to no).
    answers = ["y", "3", "1", "2", "2", "1"]
    result = run_onboarding(tmp_path, answerer=_scripted(answers))
    manifest = load_manifest(bootstrap)
    assert manifest.safety_profile == "production-stake"
    assert manifest.enable_auto_skill_capture is False
    assert result.production_stake_force_flip is True


def test_force_flip_audit_log_entry(tmp_path: Path) -> None:
    """The audit-log carries an onboarding_default_flip entry."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "1", "2", "2", "1"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    entries = read_audit_entries(tmp_path)
    flip_entries = [e for e in entries if e.get("event_kind") == "onboarding_default_flip"]
    assert len(flip_entries) == 1
    assert "production-stake" in flip_entries[0]["notes"]


def test_dev_profile_does_not_force_flip(tmp_path: Path) -> None:
    """When Q3=dev, Q6=Y is honoured (no force-flip)."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "1"]
    result = run_onboarding(tmp_path, answerer=_scripted(answers))
    manifest = load_manifest(bootstrap)
    assert manifest.safety_profile == "dev"
    assert manifest.enable_auto_skill_capture is True
    assert result.production_stake_force_flip is False
