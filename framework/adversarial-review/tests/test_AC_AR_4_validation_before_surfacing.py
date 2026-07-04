# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.4 (P3/J3) — a finding blocks only after ground-truth validation;
unvalidated findings quarantine as HYPOTHESIZED (visible, severity-capped,
non-blocking); a refuted finding is dropped."""
from __future__ import annotations

from adversarial_review.findings import Finding, Severity, ValidationState
from adversarial_review.validation import validate_all, validate_finding

_ARTIFACT = (
    "line one of the artifact\n"
    'the model uses "a 12% growth assumption" without a source\n'
    "final line\n"
)


def test_AC_AR_4_quoted_anchor_present_validates_and_can_block():
    f = Finding(
        claim="unsourced growth",
        location='"a 12% growth assumption"',
        scenario='the "a 12% growth assumption" is unsourced.',
        severity=Severity.HIGH,
    )
    validate_finding(f, _ARTIFACT)
    assert f.state is ValidationState.VALIDATED
    assert f.blocks() is True


def test_AC_AR_4_absent_quoted_anchor_is_refuted():
    f = Finding(
        claim="fabricated",
        location='"a 99% growth assumption that is not in the text"',
        scenario='the "a 99% growth assumption that is not in the text" is bad.',
        severity=Severity.CRITICAL,
    )
    validate_finding(f, _ARTIFACT)
    assert f.state is ValidationState.REFUTED
    assert f.blocks() is False


def test_AC_AR_4_unanchored_finding_is_quarantined_nonblocking():
    f = Finding(
        claim="vibe",
        location="the general tone",
        scenario="the overall approach feels weak but I cannot pin it.",
        severity=Severity.CRITICAL,
    )
    validate_finding(f, _ARTIFACT)  # no anchor, no validator
    assert f.state is ValidationState.HYPOTHESIZED
    assert f.blocks() is False
    # Severity is capped so a quarantined finding can never reach the bar.
    assert f.effective_severity() <= Severity.MEDIUM


def test_AC_AR_4_refuted_findings_dropped_from_surfaced_set():
    good = Finding("g", '"final line"', 'the "final line" is wrong.', Severity.HIGH)
    bad = Finding("b", '"nonexistent quoted span here"', 'x "nonexistent quoted span here" y.', Severity.HIGH)
    survivors = validate_all([good, bad], _ARTIFACT)
    assert good in survivors
    assert bad not in survivors  # refuted -> dropped


def test_AC_AR_4_isolated_validator_used_only_without_anchor():
    # A finding with no executable anchor delegates to the isolated validator.
    f = Finding("v", "no quote here", "a claim with no anchor.", Severity.HIGH)

    def validator(prompt: str):
        return "checked it against the text\nVALID"

    validate_finding(f, _ARTIFACT, validator_fn=validator)
    assert f.state is ValidationState.VALIDATED
    assert f.blocks() is True
