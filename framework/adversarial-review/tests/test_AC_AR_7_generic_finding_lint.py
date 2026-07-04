# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.7 (F3) — a finding true-of-any-artifact-of-class is flagged generic
and excluded from the verdict calculus."""
from __future__ import annotations

from adversarial_review.findings import (
    Finding,
    Severity,
    ValidationState,
    apply_generic_lint,
    is_generic,
)
from adversarial_review.verdict import Disposition, decide


def test_AC_AR_7_boilerplate_flagged_generic():
    f = Finding(
        claim="robustness",
        location="the whole thing",
        scenario="error handling could be more robust and it could be improved.",
        severity=Severity.HIGH,
    )
    assert is_generic(f) is True


def test_AC_AR_7_anchored_finding_not_generic():
    # Same soft phrase, but with a concrete artifact-specific anchor -> NOT
    # generic (it names something real).
    f = Finding(
        claim="specific",
        location="line 42",
        scenario='error handling could be more robust at "def parse(x)" '
        "where a None input raises unhandled.",
        severity=Severity.HIGH,
    )
    assert is_generic(f) is False


def test_AC_AR_7_generic_finding_excluded_from_verdict():
    generic = Finding(
        "g",
        "somewhere",
        "could be more comprehensive.",
        Severity.CRITICAL,
        state=ValidationState.VALIDATED,
    )
    apply_generic_lint([generic])
    assert generic.generic is True
    # Even though it is CRITICAL and VALIDATED, a generic finding does not block.
    assert generic.blocks() is False
    v = decide([generic], "z" * 50, strongest_objection="x", uncheckable="y")
    assert v.disposition is not Disposition.BLOCK
