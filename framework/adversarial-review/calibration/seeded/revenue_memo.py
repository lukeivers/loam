# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""A seeded-flaw calibration fixture (P8 / AC.AR.10).

A short revenue memo with three GLARING, unambiguous planted flaws, each
carrying a natural numeric/textual anchor a competent adversarial critic
will almost certainly cite when reporting it. This is the calibration
input for the reviewer-measures-itself proof.
"""
from __future__ import annotations

from adversarial_review.calibration import SeededFlaw

OBJECTIVE = (
    "A defensible seed-round revenue memo an investor could rely on: every "
    "number internally consistent, every market claim sourced, no arithmetic "
    "errors, no internal contradictions."
)

ARTIFACT = """# Acme Corp — seed round revenue memo

## Company stage
Acme is pre-revenue and pre-launch; the product ships next quarter.

## Market
The total addressable market is $50B (source: internal estimate).

## Revenue projection
We will onboard 12 enterprise customers in year one at $350K each.
Total year-one revenue: 12 customers x $350K = $3.6M.

## Traction
Our current $2M ARR comes from three design partners who signed last year.

## Ask
We are raising a $6M seed round against this $3.6M year-one plan, which
fully funds operations through FY29.
"""

# Each flaw's anchor is a phrase actually present at the flaw site that a
# critic locating the flaw will reference.
FLAWS = [
    SeededFlaw(
        "ARITHMETIC",
        anchor="$3.6M",
        description="12 x $350K = $4.2M, not the stated $3.6M — arithmetic error",
        severity_floor="HIGH",
    ),
    SeededFlaw(
        "CONTRADICTION",
        anchor="$2M ARR",
        description="claims 'pre-revenue' in stage but '$2M ARR' in traction "
        "— internal contradiction",
        severity_floor="CRITICAL",
    ),
    SeededFlaw(
        "UNSOURCED",
        anchor="$50B",
        description="the $50B TAM is 'sourced' only to an internal estimate "
        "— unsupported market claim",
        severity_floor="MEDIUM",
    ),
]
