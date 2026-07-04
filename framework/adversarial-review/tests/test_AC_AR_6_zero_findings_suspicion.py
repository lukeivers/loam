# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.6 (P5) — zero substantive validated findings on a NONTRIVIAL artifact
=> SUSPICION on the review, never a clean pass."""
from __future__ import annotations

from adversarial_review.findings import Finding, Severity, ValidationState
from adversarial_review.verdict import Disposition, decide

_NONTRIVIAL = "y" * 500


def test_AC_AR_6_nontrivial_zero_findings_is_suspect():
    v = decide([], _NONTRIVIAL, strongest_objection="x", uncheckable="y")
    assert v.disposition is Disposition.SUSPECT
    assert "suspect" in v.suspicion_reason.lower()


def test_AC_AR_6_only_quarantined_findings_still_suspect():
    # A nontrivial artifact whose only findings are quarantined (non
    # -substantive) is still suspect — a review that found nothing it could
    # stand behind is the anomaly.
    quarantined = Finding(
        "q", "loc", "scenario", Severity.HIGH, state=ValidationState.HYPOTHESIZED
    )
    v = decide([quarantined], _NONTRIVIAL, strongest_objection="x", uncheckable="y")
    assert v.disposition is Disposition.SUSPECT


def test_AC_AR_6_substantive_validated_finding_is_not_suspect():
    substantive = Finding(
        "s", "loc", "scenario", Severity.MEDIUM, state=ValidationState.VALIDATED
    )
    v = decide([substantive], _NONTRIVIAL, strongest_objection="x", uncheckable="y")
    # MEDIUM validated is substantive but below the HIGH blocking bar -> PASS.
    assert v.disposition is Disposition.PASS


def test_AC_AR_6_review_that_did_not_run_is_suspect_not_pass():
    v = decide([], _NONTRIVIAL, ran=False)
    assert v.disposition is Disposition.SUSPECT
    assert "inconclusive" in v.suspicion_reason.lower()
