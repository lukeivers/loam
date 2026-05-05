# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.15 — Survey-as-default-source.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.15 (NEW per Luke 2026-05-05
ruling): tolerant H2 parser; never block on parse failure; env-var
override; conventional default path.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from loam.workspace_bootstrap.survey_parser import (
    SurveyDefaults,
    SURVEY_ENV_VAR,
    parse_survey_file,
    resolve_survey_path,
)
from loam.workspace_bootstrap.onboarding import run_onboarding


FIXTURES = Path(__file__).parent / "fixtures" / "fresh-user-onboarding" / "survey-files"


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


def test_well_formed_survey_prefills_all_six(tmp_path: Path) -> None:
    """A fully-populated survey file pre-fills all six question slots."""
    defaults = parse_survey_file(FIXTURES / "well-formed.md")
    assert defaults is not None
    assert defaults.language is not None
    assert defaults.channel is not None
    assert defaults.safety_profile is not None
    assert defaults.extractor is not None
    assert defaults.watch is not None
    assert defaults.auto_skill_capture is not None


def test_partial_survey_leaves_unmatched_none(tmp_path: Path) -> None:
    """A survey with only 3 sections returns None for the other slots."""
    defaults = parse_survey_file(FIXTURES / "partial.md")
    assert defaults is not None
    # The three present in partial.md.
    assert defaults.language is not None
    assert defaults.channel is not None
    assert defaults.safety_profile is not None
    # The three absent.
    assert defaults.extractor is None
    assert defaults.watch is None
    assert defaults.auto_skill_capture is None


def test_malformed_survey_does_not_crash(tmp_path: Path) -> None:
    """Per AC.ONBOARD.15: never block on parse failure."""
    # Should return None or an empty SurveyDefaults; must NOT raise.
    defaults = parse_survey_file(FIXTURES / "malformed.md")
    if defaults is not None:
        assert defaults.language is None
        assert defaults.channel is None


def test_env_var_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """LOAM_ONBOARDING_SURVEY env-var honours an absolute path."""
    custom = tmp_path / "custom-survey.md"
    custom.write_text("## 1. Language\n\nrails\n")
    monkeypatch.setenv(SURVEY_ENV_VAR, str(custom))
    resolved = resolve_survey_path()
    assert resolved == custom


def test_no_survey_returns_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When no survey file exists, resolve returns None (fall-through)."""
    monkeypatch.delenv(SURVEY_ENV_VAR, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    resolved = resolve_survey_path()
    assert resolved is None


def test_survey_pre_fill_path_through_ritual(tmp_path: Path) -> None:
    """End-to-end: ritual reads survey + records survey_defaults."""
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["1", "1", "1", "1", "1", "1"]
    result = run_onboarding(
        tmp_path,
        answerer=_scripted(answers),
        survey_path=FIXTURES / "well-formed.md",
    )
    assert result.survey_defaults is not None
    assert result.survey_defaults.language is not None


def test_keyword_overlap_match() -> None:
    """Heading without numeric prefix still matches via keyword overlap.

    partial.md uses "## Language" (no "1.") and "## Communication channel".
    """
    defaults = parse_survey_file(FIXTURES / "partial.md")
    assert defaults is not None
    assert defaults.language == "ts"
    assert defaults.channel == "cli"
