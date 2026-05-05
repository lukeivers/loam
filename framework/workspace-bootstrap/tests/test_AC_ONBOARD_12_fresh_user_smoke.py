# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.12 — Fresh-user smoke fixture.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.12: four synthetic-tree
shapes; ritual completes; audit-log + summary + manifest fields
present.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from loam.workspace_bootstrap.manifest import load_manifest
from loam.workspace_bootstrap.onboarding import run_onboarding
from loam.workspace_bootstrap.onboarding_audit import audit_log_path


FIXTURES = Path(__file__).parent / "fixtures" / "fresh-user-onboarding"


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


@pytest.mark.parametrize(
    "fixture_name,expected_language",
    [
        ("synthetic-rails", "rails"),
        ("synthetic-jsts", "ts"),
        ("synthetic-mixed", "mixed"),
        ("synthetic-unknown", "unknown"),
    ],
)
def test_full_ritual_against_fixture(
    tmp_path: Path,
    fixture_name: str,
    expected_language: str,
) -> None:
    """Each fixture exercises full ritual end-to-end."""
    workspace = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, workspace)
    (workspace / "bootstrap.yaml").write_text(
        "version: 1\ncontributions: []\n"
    )

    if expected_language == "unknown":
        answers = ["python", "3", "2", "2", "2", "2"]
    elif expected_language == "mixed":
        answers = ["1", "3", "2", "2", "2", "2"]
    else:
        answers = ["y", "3", "2", "2", "2", "2"]

    result = run_onboarding(
        workspace,
        answerer=_scripted(answers),
    )

    assert result.skipped is False
    assert result.language_detection.primary == expected_language
    assert audit_log_path(workspace).exists()
    assert result.completion_summary_path.exists()

    manifest = load_manifest(workspace / "bootstrap.yaml")
    assert manifest.onboarding_completed_at is not None
    assert manifest.language_primary is not None
