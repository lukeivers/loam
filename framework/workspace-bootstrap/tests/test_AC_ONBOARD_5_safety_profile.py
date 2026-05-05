# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.5 — Q3 safety profile + production-stake highlight on Rails.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.5: three branches; rails →
production-stake highlighted; non-Rails → no highlight; manifest
safety_profile written via the existing v0.1.6 mechanism.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.manifest import load_manifest
from loam.workspace_bootstrap.onboarding import _compose_prompt, run_onboarding
from loam.workspace_bootstrap.language_detection import LanguageDetection


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


@pytest.mark.parametrize(
    "answer,expected_profile",
    [
        ("1", "production-stake"),
        ("2", "dev"),
        ("3", "research"),
    ],
)
def test_safety_profile_branches_persisted(
    tmp_path: Path, answer: str, expected_profile: str
) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", answer, "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    manifest = load_manifest(bootstrap)
    assert manifest.safety_profile == expected_profile


def test_rails_detection_highlights_production_stake() -> None:
    """When language=rails the prompt includes the [recommended] tag."""
    detection = LanguageDetection(primary="rails", signals=("Gemfile",))
    prompt = _compose_prompt("safety_profile", detection, None, {"language": "rails"})
    assert "production-stake" in prompt
    assert "[recommended" in prompt


def test_non_rails_detection_no_highlight() -> None:
    """Non-Rails language → prompt has no [recommended] highlight."""
    detection = LanguageDetection(primary="ts", signals=("package.json",))
    prompt = _compose_prompt("safety_profile", detection, None, {"language": "ts"})
    assert "[recommended" not in prompt
    # All three options still listed (user can pick any).
    assert "production-stake" in prompt
    assert "dev" in prompt
    assert "research" in prompt
