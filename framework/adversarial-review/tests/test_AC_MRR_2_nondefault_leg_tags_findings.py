# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.MRR.2 (outcome-altitude) — a non-default critic leg tags every finding.

With the CRITIC role configured to a single NON-default stub leg, the critic
phases call that leg, every produced Finding carries the leg's name, and
`render_report` surfaces the producing leg per finding. Verified through the
real `review_text` entry at STANDARD and DEEP (DEEP forwards the registry per
axis). Lens 0: the review says which model produced which finding.
"""
from __future__ import annotations

from conftest import finding_block, make_stub_critic

from adversarial_review import (
    ModelLeg,
    ModelRoleRegistry,
    Role,
    render_report,
    review_text,
)

_LEG_NAME = "stub-critic"


def _critic_registry(diff_text: str) -> ModelRoleRegistry:
    return ModelRoleRegistry(
        legs={Role.CRITIC: (ModelLeg(_LEG_NAME, make_stub_critic(diff_text)),)}
    )


def test_AC_MRR_2_standard_tags_every_finding(nontrivial_artifact, objective):
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "is never stress-tested, so the model fails its objective.",
    )
    result = review_text(
        nontrivial_artifact, objective, registry=_critic_registry(diff)
    )
    assert result.ran is True
    assert result.verdict.findings, "the non-default leg produced no findings"
    # Every finding names the producing leg (AC.MRR.2).
    for f in result.verdict.findings:
        assert f.leg == _LEG_NAME
    assert result.legs_used == (_LEG_NAME,)
    assert result.missing_legs == ()
    # The render surfaces the producing leg — per finding and in the summary.
    report = render_report(result, "revenue-model.md")
    assert "## Model legs" in report
    assert _LEG_NAME in report
    assert "model leg: " + _LEG_NAME in report


def test_AC_MRR_2_deep_forwards_registry_and_tags(nontrivial_artifact, objective):
    # DEEP runs multiple isolated axis critics; the registry threads through
    # each, so findings across axes carry the producing leg's name.
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "is never stress-tested across the axes.",
    )
    result = review_text(
        nontrivial_artifact, objective, tier="DEEP", registry=_critic_registry(diff)
    )
    assert result.ran is True
    assert result.verdict.findings
    for f in result.verdict.findings:
        assert f.leg == _LEG_NAME
    assert _LEG_NAME in result.legs_used
    report = render_report(result, "revenue-model.md")
    assert "model leg: " + _LEG_NAME in report
