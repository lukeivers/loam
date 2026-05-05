# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.7 — Q5 continuous-watch opt-in (Y / Defer-default / N).

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.7: Defer is the default for
fresh-user low-context per master plan §7.1.
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
    "answer,expected",
    [
        ("1", "yes"),
        ("2", "deferred"),
        ("3", "no"),
    ],
)
def test_watch_branches_persist_field(
    tmp_path: Path, answer: str, expected: str
) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", answer, "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    manifest = load_manifest(bootstrap)
    assert manifest.watch_opt_in == expected


def test_defer_is_default_in_prompt() -> None:
    """The Q5 prompt highlights Defer as the default per §7.1."""
    detection = LanguageDetection(primary="rails", signals=("Gemfile",))
    prompt = _compose_prompt("watch", detection, None, {})
    assert "Defer" in prompt
    assert "[default]" in prompt


def test_y_branch_writes_pointer_file(tmp_path: Path) -> None:
    """Q5=Y writes the continuous-watch-pointer.md per plan-doc §7."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "1", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers))
    pointer = tmp_path / ".loam" / "continuous-watch-pointer.md"
    assert pointer.exists()
