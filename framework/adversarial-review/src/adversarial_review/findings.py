# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Finding model + severity taxonomy + generic-finding lint.

The unit of adversarial-review output. Every finding pins the three
things D6 / AI-§F3 require: an artifact LOCATION, a concrete FAILURE
SCENARIO, and a SEVERITY drawn from a taxonomy fixed BEFORE the review
(GEN §6 adversarial-collaboration pre-commitment — so harshness cannot
be negotiated down artifact-by-artifact).

Per ODD §2.5 every construct here traces to a named AC:

  * :class:`Severity` + the pre-committed order  -> AC.AR.5 (verdict
    from validated top-severity only; taxonomy fixed in advance).
  * :class:`ValidationState`                     -> AC.AR.4 (validated
    vs quarantined-HYPOTHESIZED).
  * :class:`Finding` field requirements          -> AC.AR.1/AC.AR.4
    (location + scenario + severity pins).
  * :func:`is_generic`                           -> AC.AR.7 (generic
    -finding lint; F3 — the failure that most resembles success).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, IntEnum


class Severity(IntEnum):
    """Pre-committed severity taxonomy (AC.AR.5).

    Ordered so a plain ``>=`` comparison expresses "at or above the
    blocking bar". The taxonomy is fixed here, in code, ONCE — not
    re-negotiated per review (GEN §6). ``CRITICAL`` and ``HIGH`` are the
    blocking band by default; ``NIT`` never blocks (AC.AR.4/AC.AR.5).
    """

    NIT = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    @classmethod
    def from_str(cls, token: str) -> "Severity":
        """Parse a severity token leniently; unknown -> ``MEDIUM``.

        Lenient because the token is model-authored; an unrecognizable
        severity is treated as MEDIUM (present, not blocking-by-default,
        surfaced) rather than dropped.
        """
        key = (token or "").strip().upper()
        return cls.__members__.get(key, cls.MEDIUM)


# The default blocking bar: a validated finding at or above HIGH blocks
# the boundary (AC.AR.5). Held as a module constant so gate + manual +
# tests reference ONE source of truth.
BLOCKING_BAR = Severity.HIGH


class ValidationState(str, Enum):
    """A finding's validation status (AC.AR.4).

    ``VALIDATED``   — re-checked against ground truth; eligible to block.
    ``HYPOTHESIZED`` — could not be validated (unverifiable / failed the
                       re-check); quarantined: visible, severity-capped,
                       NEVER blocking. This is the precision valve — the
                       critic runs hot for recall (AI §1.1), the
                       validation layer owns precision, and an
                       un-validated finding is surfaced but defanged
                       rather than making the critic timid (the forbidden
                       fix, P3).
    ``REFUTED``     — the re-check positively DISPROVED the finding; it is
                       dropped from the surfaced set entirely.
    """

    VALIDATED = "VALIDATED"
    HYPOTHESIZED = "HYPOTHESIZED"
    REFUTED = "REFUTED"


# The severity cap applied to a quarantined (HYPOTHESIZED) finding
# (AC.AR.4): no matter what the critic claimed, an un-validated finding
# cannot count above MEDIUM, so it can never reach the blocking bar.
HYPOTHESIZED_SEVERITY_CAP = Severity.MEDIUM


@dataclass
class Finding:
    """One adversarial-review finding.

    ``location`` + ``scenario`` + ``severity`` are the mandatory pins
    (AC.AR.1/AC.AR.4). ``claim`` is the one-line assertion. ``state``
    starts HYPOTHESIZED and is advanced only by the validation layer
    (AC.AR.4) — a finding is NOT born validated. ``evidence`` records
    what the validator checked (the re-read passage, the re-derived
    number, the run result). ``axis`` names which review axis produced it
    (DEEP tier / merge-judge provenance, AC.AR.11). ``generic`` is set by
    :func:`is_generic` (AC.AR.7).
    """

    claim: str
    location: str
    scenario: str
    severity: Severity
    state: "ValidationState" = ValidationState.HYPOTHESIZED
    evidence: str = ""
    axis: str = ""
    generic: bool = False

    def effective_severity(self) -> Severity:
        """Severity after the quarantine cap (AC.AR.4).

        A VALIDATED finding keeps its claimed severity; anything else is
        capped at :data:`HYPOTHESIZED_SEVERITY_CAP` so it can never reach
        the blocking bar. A generic finding (AC.AR.7) is likewise capped —
        it is excluded from the verdict calculus regardless of claimed
        severity.
        """
        if self.generic:
            return min(self.severity, HYPOTHESIZED_SEVERITY_CAP)
        if self.state is ValidationState.VALIDATED:
            return self.severity
        return min(self.severity, HYPOTHESIZED_SEVERITY_CAP)

    def blocks(self) -> bool:
        """Does this finding block the boundary (AC.AR.4/AC.AR.5)?

        Only a VALIDATED, non-generic finding at or above the blocking
        bar blocks. Quarantined + generic + refuted findings never block.
        """
        if self.state is not ValidationState.VALIDATED or self.generic:
            return False
        return self.effective_severity() >= BLOCKING_BAR

    def is_substantive(self) -> bool:
        """A VALIDATED, non-generic finding at MEDIUM or above.

        The zero-findings-suspicion check (AC.AR.6) counts substantive
        findings; a review that surfaces only NITs and quarantined guesses
        on a nontrivial artifact is itself suspicious.
        """
        return (
            self.state is ValidationState.VALIDATED
            and not self.generic
            and self.effective_severity() >= Severity.MEDIUM
        )


# ---------------------------------------------------------------------
# Generic-finding lint (AC.AR.7 / AI §F3)
# ---------------------------------------------------------------------

# Phrases that read as true of ANY artifact of the class — the "generic
# critique is the failure that most resembles success" tell (Liang, AI
# §F3). A finding whose scenario/claim is ONLY one of these, with no
# artifact-specific pin, is flagged generic and excluded from the verdict
# calculus. The list is the build-time knob; the GATE behavior (generic
# excluded) is what the AC asserts.
_GENERIC_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bcould be more robust\b",
        r"\bcould be improved\b",
        r"\bcould be better\b",
        r"\bmore comprehensive\b",
        r"\berror[- ]handling could\b",
        r"\bconsider adding (more )?(tests|documentation|comments)\b",
        r"\blacks sufficient (tests|documentation|comments)\b",
        r"\bcould benefit from\b",
        r"\bmay want to consider\b",
        r"\bnot production[- ]ready\b(?!.{0,80}\bbecause\b)",
        r"\bedge cases (may|might) (not )?be\b",
    )
)

# A finding earns an exemption from the generic lint if it carries a
# concrete artifact-specific anchor: a line/section/quote/number pin.
_SPECIFIC_ANCHOR = re.compile(
    r"(line\s+\d+|:\d+\b|section\s+\S+|§\s*\S+|\"[^\"]{6,}\"|'[^']{6,}'"
    r"|\bfunction\s+\w+|\bclass\s+\w+|\b\d+(\.\d+)?%|\$\s?\d)",
    re.IGNORECASE,
)


def is_generic(finding: Finding) -> bool:
    """AC.AR.7 — would this finding read as true of ANY artifact of the class?

    A finding is generic when its text matches a generic pattern AND it
    carries no concrete artifact-specific anchor (a line/section/quote/
    number/symbol pin) in its location or scenario. A finding that names
    a specific location or quotes the artifact is, by construction, not
    the boilerplate F3 warns about — even if it also contains a soft
    phrase.
    """
    haystack = f"{finding.claim}\n{finding.scenario}"
    matches_generic = any(p.search(haystack) for p in _GENERIC_PATTERNS)
    if not matches_generic:
        return False
    anchored = bool(
        _SPECIFIC_ANCHOR.search(finding.location)
        or _SPECIFIC_ANCHOR.search(finding.scenario)
    )
    return not anchored


def apply_generic_lint(findings: list[Finding]) -> list[Finding]:
    """Set ``generic`` on every finding that trips the lint (AC.AR.7).

    Mutates in place and returns the list for chaining. Generic findings
    stay VISIBLE (they are not dropped) but are excluded from the verdict
    calculus via :meth:`Finding.effective_severity` / :meth:`blocks`.
    """
    for f in findings:
        f.generic = is_generic(f)
    return findings
