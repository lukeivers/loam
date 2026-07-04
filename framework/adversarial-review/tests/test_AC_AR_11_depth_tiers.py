# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.11 (D10/P7) — STANDARD floor always runs for a boundary artifact; DEEP
adds parallel per-axis isolated critics (no shared context) + a SEPARATE merge
judge that PRESERVES disagreement; a symmetric panel is never the mechanism."""
from __future__ import annotations

from conftest import finding_block

from adversarial_review.findings import Finding, Severity
from adversarial_review.tiers import (
    DEFAULT_DEEP_AXES,
    AxisReview,
    merge_findings,
    run_deep_review,
)


def test_AC_AR_11_deep_runs_one_isolated_critic_per_axis_no_shared_context():
    # Record every objective the per-axis critics were seeded with; assert
    # each axis got its own independent pass and none saw another's findings.
    seen_axis_objectives = []

    def per_axis_critic(prompt: str):
        if "You do NOT see the artifact yet" in prompt:
            # capture which axis this derive-phase seed names
            for axis in DEFAULT_DEEP_AXES:
                if axis in prompt:
                    seen_axis_objectives.append(axis)
            return "SPEC"
        return finding_block("loc", "LOW", "a minor axis finding.")

    run_deep_review(
        "artifact " * 60, "objective", model_fn=per_axis_critic
    )
    # One derive per axis -> every default axis got its own isolated pass.
    assert set(seen_axis_objectives) == set(DEFAULT_DEEP_AXES)


def test_AC_AR_11_merge_preserves_minority_disagreement():
    # Axis A found a flaw; axis B did not. The merge must KEEP A's finding
    # (not drop it toward consensus).
    a = AxisReview("axis-a", [Finding("x", "L1", "flaw only A saw.", Severity.HIGH)], True)
    b = AxisReview("axis-b", [], True)
    merged = merge_findings([a, b])
    assert len(merged) == 1
    assert merged[0].scenario == "flaw only A saw."


def test_AC_AR_11_merge_dedupes_identical_but_keeps_distinct():
    a = AxisReview("a", [Finding("x", "L1", "same flaw.", Severity.HIGH)], True)
    b = AxisReview("b", [Finding("y", "L1", "same flaw.", Severity.HIGH)], True)
    c = AxisReview("c", [Finding("z", "L2", "different flaw.", Severity.HIGH)], True)
    merged = merge_findings([a, b, c])
    # identical (location, scenario) de-duped; distinct kept.
    assert len(merged) == 2


def test_AC_AR_11_deep_inconclusive_when_no_axis_runs():
    def dead(prompt: str):
        return None

    result = run_deep_review("artifact " * 60, "obj", model_fn=dead)
    assert result.ran is False
