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

"""The verdict — teeth by default, and a PASS that names its own residual.

D8 / P4 / P5 / AC.AR.5 / AC.AR.6:

  * BLOCK by default when any VALIDATED finding is at or above the
    blocking bar; owner override is an explicit act, recorded.
  * A PASS is MALFORMED unless it names (a) the strongest surviving
    objection and (b) what the review could not check. A clean bill with
    no named residual risk is structurally rejected (P5) — the ritual
    inoculation Nemeth warns about (GEN §3) is exactly the thing with no
    named residual.
  * Zero substantive VALIDATED findings on a NONTRIVIAL artifact is an
    ANOMALY (suspicion on the review), not a clean bill (P5 / F7).

The verdict does NOT model any real stakeholder (P10 / AC.AR.13) — it
answers "did the artifact survive attack?", full stop.

Per ODD §2.5: :class:`Disposition` -> AC.AR.5; :func:`decide` ->
AC.AR.5 + AC.AR.6; :func:`_wellformed_pass` -> AC.AR.5 (P5 malformed
-PASS rejection); the suspicion path -> AC.AR.6.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .findings import Finding

# Below this artifact size (chars) a review that finds nothing is not
# automatically suspicious — a two-line artifact can legitimately be
# clean. Above it, zero substantive findings is an anomaly (AC.AR.6).
NONTRIVIAL_ARTIFACT_CHARS = 400


class Disposition(str, Enum):
    """The three verdict dispositions (AC.AR.5 / AC.AR.6).

    ``BLOCK``      — validated top-severity findings exist; the boundary
                     is held until they are resolved or the owner
                     explicitly overrides.
    ``PASS``       — survived attack; MUST carry a named strongest
                     objection + what-couldn't-be-checked (P5).
    ``SUSPECT``    — zero substantive validated findings on a nontrivial
                     artifact, OR the review could not run (inconclusive):
                     suspicion on the REVIEW, never a clean bill (P5/F7).
    """

    BLOCK = "BLOCK"
    PASS = "PASS"
    SUSPECT = "SUSPECT"


@dataclass
class Verdict:
    """A rendered adversarial-review verdict.

    ``disposition`` drives the gate (AC.AR.5). ``blocking`` is the
    computed gate signal (True only for BLOCK, and only until an explicit
    override). ``strongest_objection`` + ``uncheckable`` are the MANDATORY
    residual-risk fields on any non-BLOCK verdict (P5). ``overridden``
    records an explicit owner override (AC.AR.5). ``findings`` is the full
    surfaced set (validated + quarantined). ``suspicion_reason`` explains
    a SUSPECT disposition (AC.AR.6).
    """

    disposition: Disposition
    findings: list[Finding]
    strongest_objection: str = ""
    uncheckable: str = ""
    suspicion_reason: str = ""
    overridden: bool = False
    override_reason: str = ""

    @property
    def blocking(self) -> bool:
        """Gate signal: does this verdict hold the boundary (AC.AR.5)?

        BLOCK blocks unless explicitly overridden. SUSPECT does NOT hard
        -block the manual path but is surfaced loudly; at a live gate the
        dispatcher policy decides whether SUSPECT holds (default: treat
        SUSPECT as non-clean, re-run deeper). PASS never blocks.
        """
        return self.disposition is Disposition.BLOCK and not self.overridden

    def override(self, reason: str) -> "Verdict":
        """Record an EXPLICIT owner override of a BLOCK (AC.AR.5).

        Override is an act, not a default — it requires a reason and is
        recorded on the verdict so "it passed review" can never quietly
        mean "someone waved it through". Only a BLOCK is overridable.
        """
        if self.disposition is not Disposition.BLOCK:
            raise ValueError("only a BLOCK verdict can be overridden")
        if not reason.strip():
            raise ValueError("override requires an explicit reason (AC.AR.5)")
        self.overridden = True
        self.override_reason = reason.strip()
        return self


class MalformedVerdict(ValueError):
    """Raised when a PASS is constructed without its mandatory residual (P5)."""


def _wellformed_pass(strongest_objection: str, uncheckable: str) -> None:
    """Reject a PASS missing its residual-risk naming (P5 / AC.AR.5).

    A PASS with no strongest-surviving-objection or no what-couldn't-be
    -checked is malformed output — the rubber stamp P5 structurally
    forbids. Raising here makes the malformed PASS impossible to
    construct, rather than merely discouraged.
    """
    if not strongest_objection.strip():
        raise MalformedVerdict(
            "PASS missing the strongest surviving objection (P5 / AC.AR.5): "
            "a clean bill with no named residual risk is malformed output."
        )
    if not uncheckable.strip():
        raise MalformedVerdict(
            "PASS missing 'what the review could not check' (P5 / AC.AR.5)."
        )


def decide(
    findings: list[Finding],
    artifact: str,
    *,
    ran: bool = True,
    strongest_objection: str = "",
    uncheckable: str = "",
) -> Verdict:
    """Compute the verdict from validated findings (AC.AR.5 / AC.AR.6).

    Rules, in order:

      1. If the critic never ran (``ran`` False) -> SUSPECT (inconclusive):
         a missing review is never a PASS.
      2. If any VALIDATED, non-generic finding blocks -> BLOCK.
      3. Else, if the artifact is nontrivial and there are zero
         SUBSTANTIVE validated findings -> SUSPECT (zero-findings anomaly,
         AC.AR.6). A nontrivial artifact that "passes clean" is suspicious
         of the review, not proof of the artifact.
      4. Else -> PASS, which MUST carry a named strongest objection +
         what-couldn't-be-checked (P5); a PASS without them raises
         MalformedVerdict.
    """
    if not ran:
        return Verdict(
            disposition=Disposition.SUSPECT,
            findings=findings,
            suspicion_reason=(
                "the adversarial critic could not run (model/spawn "
                "unavailable) — REVIEW INCONCLUSIVE; not a clean bill"
            ),
        )

    if any(f.blocks() for f in findings):
        return Verdict(disposition=Disposition.BLOCK, findings=findings)

    substantive = [f for f in findings if f.is_substantive()]
    nontrivial = len(artifact) >= NONTRIVIAL_ARTIFACT_CHARS
    if nontrivial and not substantive:
        return Verdict(
            disposition=Disposition.SUSPECT,
            findings=findings,
            suspicion_reason=(
                "zero substantive validated findings on a nontrivial "
                f"artifact ({len(artifact)} chars): treat the REVIEW as "
                "suspect and re-run deeper — do NOT read this as a clean "
                "bill (P5 / AC.AR.6)"
            ),
        )

    _wellformed_pass(strongest_objection, uncheckable)
    return Verdict(
        disposition=Disposition.PASS,
        findings=findings,
        strongest_objection=strongest_objection.strip(),
        uncheckable=uncheckable.strip(),
    )
