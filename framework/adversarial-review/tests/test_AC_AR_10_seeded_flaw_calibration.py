# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.10 (outcome-altitude, P8) — feeding a seeded-flaw artifact reads back a
computed catch rate; the harness matches critic findings to seeded flaws.

Unit variant here (deterministic, offline): the SCORING logic + an
end-to-end calibrate() with an injected critic. The REAL isolated-critic
variant is the opt-in smoke (test_AC_AR_S_real_calibration_smoke.py) and is
run once at build time for the proof."""
from __future__ import annotations

from conftest import finding_block, make_stub_critic, make_unavailable_critic

from adversarial_review.calibration import SeededFlaw, calibrate, score
from adversarial_review.findings import Finding, Severity

# An artifact carrying two planted, distinctively-anchored flaws.
_SEEDED_ARTIFACT = (
    "# Bridge load spec\n\n"
    "The main span is rated for FLAW_UNSOURCED_LOAD of 40 tons with no "
    "citation for the figure.\n"
    "The safety factor section reads FLAW_MISSING_SAFETY_FACTOR and omits "
    "any safety factor entirely.\n"
    "The remaining sections are complete and internally consistent and "
    "correctly derive the deflection under the rated load using standard "
    "beam theory across the full span.\n"
)

_FLAWS = [
    SeededFlaw("F1", "FLAW_UNSOURCED_LOAD", "load rating is unsourced", "HIGH"),
    SeededFlaw("F2", "FLAW_MISSING_SAFETY_FACTOR", "no safety factor", "CRITICAL"),
]

_OBJECTIVE = "a correct, fully-sourced, code-compliant bridge load spec"


def test_AC_AR_10_score_computes_catch_rate():
    # Critic caught F1 (anchor in scenario) but missed F2.
    caught = Finding(
        "c", "the load section", "the FLAW_UNSOURCED_LOAD rating is unsourced.",
        Severity.HIGH,
    )
    result = score(_FLAWS, [caught])
    assert result.total == 2
    assert result.catch_rate == 0.5
    assert "F1" in result.caught
    assert "F2" in result.missed


def test_AC_AR_10_perfect_catch_rate():
    findings = [
        Finding("a", "x", "FLAW_UNSOURCED_LOAD here.", Severity.HIGH),
        Finding("b", "y", "FLAW_MISSING_SAFETY_FACTOR here.", Severity.CRITICAL),
    ]
    result = score(_FLAWS, findings)
    assert result.catch_rate == 1.0
    assert result.missed == []


def test_AC_AR_10_calibrate_end_to_end_with_injected_critic():
    # An end-to-end calibrate() over the seeded artifact with an injected
    # critic that reports both planted flaws -> catch rate 1.0.
    diff = "\n".join(
        (
            finding_block(
                'the load line "FLAW_UNSOURCED_LOAD"',
                "HIGH",
                'the rated load "FLAW_UNSOURCED_LOAD" is unsourced.',
            ),
            finding_block(
                'the safety section "FLAW_MISSING_SAFETY_FACTOR"',
                "CRITICAL",
                'no safety factor: "FLAW_MISSING_SAFETY_FACTOR".',
            ),
        )
    )
    result = calibrate(
        _SEEDED_ARTIFACT, _OBJECTIVE, _FLAWS, model_fn=make_stub_critic(diff)
    )
    assert result.ran is True
    assert result.catch_rate == 1.0


def test_AC_AR_10_unrun_review_is_inconclusive_not_zero():
    result = calibrate(
        _SEEDED_ARTIFACT, _OBJECTIVE, _FLAWS, model_fn=make_unavailable_critic()
    )
    assert result.ran is False
    # Inconclusive is distinct from a real 0% catch rate.
    assert result.missed == ["F1", "F2"]
