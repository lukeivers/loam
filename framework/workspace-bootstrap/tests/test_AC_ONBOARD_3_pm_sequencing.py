# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.3 — Question sequencing via PM batch API n=1.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.3 + Decision Q + AC.QSURF.1
(v0.1.7 Cycle 4 verified). The onboarding ritual calls
``enqueue_decision`` once per question and ``surface_next_questions_batch(n=1)``
to render exactly one at a time. PM-side edits are NOT required.
"""

from __future__ import annotations

from pathlib import Path


from loam.workspace_bootstrap.onboarding import QUESTION_SLUGS, run_onboarding


class _PMRecorder:
    """Minimal PM mock that records enqueue + surface calls."""

    def __init__(self) -> None:
        self.enqueue_calls: list[dict] = []
        self.surface_calls: list[int | None] = []

    def enqueue_decision(self, question_text: str, *, provenance: str | None = None) -> int:
        self.enqueue_calls.append(
            {"text": question_text, "provenance": provenance}
        )
        return len(self.enqueue_calls)

    def surface_next_questions_batch(self, n: int | None = None):
        self.surface_calls.append(n)
        return ()


def _scripted(answers: list[str]):
    it = iter(answers)
    return lambda slug, prompt: next(it)


def test_enqueue_called_once_per_question(tmp_path: Path) -> None:
    """One enqueue_decision call per onboarding question (six total)."""
    (tmp_path / "bootstrap.yaml").write_text("version: 1\ncontributions: []\n")
    pm = _PMRecorder()
    answers = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers), pm_runtime=pm)
    assert len(pm.enqueue_calls) == len(QUESTION_SLUGS) == 6


def test_surface_batch_called_with_n_eq_1(tmp_path: Path) -> None:
    """Each surface call uses n=1 per Decision Q one-at-a-time."""
    (tmp_path / "bootstrap.yaml").write_text("version: 1\ncontributions: []\n")
    pm = _PMRecorder()
    answers = ["y", "3", "2", "2", "2", "2"]
    run_onboarding(tmp_path, answerer=_scripted(answers), pm_runtime=pm)
    assert len(pm.surface_calls) == 6
    assert all(n == 1 for n in pm.surface_calls)


def test_provenance_carries_question_slug(tmp_path: Path) -> None:
    """Each enqueue carries provenance=onboarding:Q<slug> per the plan-doc."""
    (tmp_path / "bootstrap.yaml").write_text("version: 1\ncontributions: []\n")
    pm = _PMRecorder()
    run_onboarding(
        tmp_path,
        answerer=_scripted(["y", "3", "2", "2", "2", "2"]),
        pm_runtime=pm,
    )
    provenances = [call["provenance"] for call in pm.enqueue_calls]
    assert all(p and p.startswith("onboarding:Q") for p in provenances)
    slugs = [p.removeprefix("onboarding:Q") for p in provenances]
    assert slugs == list(QUESTION_SLUGS)
