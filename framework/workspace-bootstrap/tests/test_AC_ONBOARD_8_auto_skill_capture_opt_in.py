# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.8 — Q6 auto-skill-capture opt-in (Y / N-default).

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.8 + layered-skills §3.6
Decision E: N is the default; manifest writes via the existing
v0.2.0 Cycle 2 enable_auto_skill_capture field.
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
    "answer,expected_flag",
    [
        ("1", True),
        ("2", False),
    ],
)
def test_auto_skill_capture_branches(
    tmp_path: Path, answer: str, expected_flag: bool
) -> None:
    """Q6 branches set the enable_auto_skill_capture manifest field."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", answer]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    manifest = load_manifest(bootstrap)
    assert manifest.enable_auto_skill_capture is expected_flag


def test_n_is_default_in_prompt() -> None:
    """The Q6 prompt highlights N as the default."""
    detection = LanguageDetection(primary="ts", signals=("package.json",))
    prompt = _compose_prompt("auto_skill_capture", detection, None, {})
    assert "[default]" in prompt
    assert "(2) No" in prompt
