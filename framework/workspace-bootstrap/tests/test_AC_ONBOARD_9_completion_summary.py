# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.9 — Ritual completion summary.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.9: capabilities-active
list + single-next-action + audit-log location; written to
``<workspace>/.loam/onboarding-summary.md`` + stdout-friendly.
"""

from __future__ import annotations

from pathlib import Path


from loam.workspace_bootstrap.onboarding import run_onboarding


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


def test_summary_contains_all_five_capabilities(tmp_path: Path) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    result = run_onboarding(tmp_path, answerer=_scripted(answers))
    summary_path = result.completion_summary_path
    assert summary_path is not None
    text = summary_path.read_text(encoding="utf-8")
    # All five capability headings or labels present.
    for label in ("Channel:", "Safety profile:", "Extractor:", "Continuous-watch:", "Auto-skill-capture:"):
        assert label in text


def test_summary_contains_next_action(tmp_path: Path) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    result = run_onboarding(tmp_path, answerer=_scripted(answers))
    text = result.completion_summary_path.read_text(encoding="utf-8")
    assert "## Next action" in text
    # One concrete actionable sentence.
    assert "loam odd-extract" in text or "Telegram" in text or "Claude Code" in text


def test_summary_contains_audit_log_path(tmp_path: Path) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    result = run_onboarding(tmp_path, answerer=_scripted(answers))
    text = result.completion_summary_path.read_text(encoding="utf-8")
    assert "## Audit-log" in text
    assert ".loam/audit-log" in text


def test_summary_file_path(tmp_path: Path) -> None:
    bootstrap = tmp_path / "bootstrap.yaml"
    bootstrap.write_text("version: 1\ncontributions: []\n")
    answers = ["y", "3", "2", "2", "2", "2"]
    result = run_onboarding(tmp_path, answerer=_scripted(answers))
    assert result.completion_summary_path == tmp_path / ".loam" / "onboarding-summary.md"
