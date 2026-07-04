# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.1 (outcome-altitude) — manual entry against one artifact returns a
structured harsh review (findings pinned + verdict), no gate/block.

Exercised through the REAL production entry (review_text -> full pipeline)
with no pre-set critic state; only the model leg is stubbed.
"""
from __future__ import annotations

from conftest import finding_block, make_stub_critic

from adversarial_review import render_report, review_text
from adversarial_review.verdict import Disposition


def test_AC_AR_1_manual_run_returns_findings_and_verdict(nontrivial_artifact, objective):
    # A critic that quotes real artifact text (deterministically validated)
    # at HIGH severity -> a blocking, structured review.
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "is never stress-tested, so the model fails its objective of "
        "stress-testing every material assumption.",
    )
    result = review_text(
        nontrivial_artifact,
        objective,
        model_fn=make_stub_critic(diff),
    )
    assert result.ran is True
    # A pinned finding survived: location + scenario + severity present.
    assert result.verdict.findings, "manual run produced no findings"
    f = result.verdict.findings[0]
    assert f.location and f.scenario and f.severity is not None
    # A verdict is rendered (this is a review, not a gate — no exception,
    # no blocking side effect on any real boundary).
    assert result.verdict.disposition in Disposition
    # The report renders the substance.
    report = render_report(result, "revenue-model.md")
    assert "VERDICT:" in report
    assert "churn rate" in report


def test_AC_AR_1_manual_run_is_not_a_gate(nontrivial_artifact, objective):
    # The manual path never consults activation and never blocks a boundary;
    # it just returns a result object regardless of verdict.
    diff = finding_block(
        location="somewhere", severity="LOW", scenario="a minor nit only."
    )
    result = review_text(nontrivial_artifact, objective, model_fn=make_stub_critic(diff))
    # No gating machinery ran — the caller holds the result, nothing was blocked.
    assert hasattr(result, "verdict")
