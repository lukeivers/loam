# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.MRR.1 (outcome-altitude) — with NO registry configured, a review through
the production entry (`review_text`) is byte-identical to pre-amendment.

The only new render code is gated on ``show_legs`` (a non-default leg name in
``legs_used ∪ missing_legs``). The default single-Claude path carries no
non-default name, so it emits ZERO new bytes — proven here by the absence of
any leg-annotation surface plus determinism. The wider byte-identity proof is
the unchanged pre-existing AC.AR.* + AR.S suite.
"""
from __future__ import annotations

from conftest import finding_block, make_stub_critic, make_unavailable_critic

from adversarial_review import DEFAULT_LEG_NAME, render_report, review_text


def test_AC_MRR_1_default_render_has_no_leg_annotation(nontrivial_artifact, objective):
    # A real review through review_text with NO registry — the default path.
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "is never stress-tested, so the model fails its objective.",
    )
    result = review_text(nontrivial_artifact, objective, model_fn=make_stub_critic(diff))
    report = render_report(result, "revenue-model.md")

    # The new model-leg render surface is ABSENT (byte-identity: zero new bytes).
    assert "## Model legs" not in report
    assert "model leg:" not in report
    assert "MISSING LEGS" not in report
    # The pre-existing substance still renders unchanged.
    assert "VERDICT:" in report
    assert "churn rate" in report


def test_AC_MRR_1_default_findings_tagged_claude_but_unrendered(
    nontrivial_artifact, objective
):
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "is never stress-tested.",
    )
    result = review_text(nontrivial_artifact, objective, model_fn=make_stub_critic(diff))
    # Internally every finding names the default leg; the run reports it.
    assert result.legs_used == (DEFAULT_LEG_NAME,)
    assert result.missing_legs == ()
    assert result.verdict.findings
    for f in result.verdict.findings:
        assert f.leg == DEFAULT_LEG_NAME


def test_AC_MRR_1_default_render_is_deterministic(nontrivial_artifact, objective):
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "is never stress-tested.",
    )
    r1 = render_report(
        review_text(nontrivial_artifact, objective, model_fn=make_stub_critic(diff)),
        "a.md",
    )
    r2 = render_report(
        review_text(nontrivial_artifact, objective, model_fn=make_stub_critic(diff)),
        "a.md",
    )
    assert r1 == r2


def test_AC_MRR_1_default_unavailable_path_unchanged(nontrivial_artifact, objective):
    # The default-unavailable path (single "claude" leg returns None) must stay
    # byte-identical: missing_legs == ("claude",) is the DEFAULT name, so no
    # non-default name is present and NO "MISSING LEGS" line is emitted.
    result = review_text(
        nontrivial_artifact, objective, model_fn=make_unavailable_critic()
    )
    report = render_report(result, "a.md")
    assert result.ran is False
    assert result.missing_legs == (DEFAULT_LEG_NAME,)
    assert "REVIEW INCONCLUSIVE" in report
    assert "MISSING LEGS" not in report  # default name suppressed (byte-identity)
