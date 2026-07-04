# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.5 (P4/P5) — gate verdict BLOCKs by default on validated top-severity
findings; owner override is explicit; a PASS missing the strongest-surviving
-objection + what-couldn't-be-checked is malformed and rejected."""
from __future__ import annotations

import pytest

from adversarial_review.findings import Finding, Severity, ValidationState
from adversarial_review.verdict import Disposition, MalformedVerdict, decide

_SHORT = "x" * 50  # trivial artifact so zero-findings != suspicion here


def _validated(sev: Severity) -> Finding:
    f = Finding("c", "loc", "scenario", sev, state=ValidationState.VALIDATED)
    return f


def test_AC_AR_5_validated_high_finding_blocks_by_default():
    v = decide([_validated(Severity.HIGH)], _SHORT)
    assert v.disposition is Disposition.BLOCK
    assert v.blocking is True


def test_AC_AR_5_override_is_explicit_and_recorded():
    v = decide([_validated(Severity.CRITICAL)], _SHORT)
    assert v.blocking is True
    v.override("owner accepts the risk for the FY27 board deadline")
    assert v.overridden is True
    assert v.blocking is False
    assert "board deadline" in v.override_reason


def test_AC_AR_5_override_requires_a_reason():
    v = decide([_validated(Severity.HIGH)], _SHORT)
    with pytest.raises(ValueError):
        v.override("   ")


def test_AC_AR_5_pass_requires_named_residual_risk():
    # No blocking findings, trivial artifact -> PASS is possible, but a PASS
    # with no residual naming is malformed and rejected (P5).
    with pytest.raises(MalformedVerdict):
        decide([], _SHORT, strongest_objection="", uncheckable="")


def test_AC_AR_5_wellformed_pass_carries_residual():
    v = decide(
        [],
        _SHORT,
        strongest_objection="the sample size is small",
        uncheckable="could not re-run the upstream data pull",
    )
    assert v.disposition is Disposition.PASS
    assert v.strongest_objection
    assert v.uncheckable


def test_AC_AR_5_only_block_is_overridable():
    v = decide(
        [],
        _SHORT,
        strongest_objection="minor",
        uncheckable="nothing material",
    )
    assert v.disposition is Disposition.PASS
    with pytest.raises(ValueError):
        v.override("cannot override a pass")
