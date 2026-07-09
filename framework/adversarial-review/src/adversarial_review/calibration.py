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

"""Seeded-flaw calibration — the reviewer measures ITSELF (P8 / D9 / AC.AR.10).

This is the anti-sham instrument the brief calls non-negotiable for v1.
The headline risk (F7) is the stage silently going soft while still
looking harsh; a reviewer whose detection rate is never measured is
faith, not protection. Calibration hands the stage an artifact with KNOWN
seeded flaws and reads back a CATCH RATE — Fagan inspection-yield
measurement (GEN §4) / mutation testing, applied to the reviewer itself.

A seeded flaw is matched to a finding when the finding's location OR
scenario contains the flaw's ``anchor`` (a distinctive string the flaw
plants in the artifact). This makes matching deterministic and auditable
— no LLM-judged "did it basically catch it".

Two run modes:

  * :func:`score` — deterministic: given a seeded artifact + the findings
    a critic produced, compute the catch rate. Pure, offline, exercises
    the SCORING logic (AC.AR.10 unit variant).
  * :func:`calibrate` — end-to-end: run the REAL (or injected) review
    over the seeded artifact and score it (AC.AR.10 real variant). Used
    for the build-time proof + the periodic cadence.

Per ODD §2.5: :class:`SeededFlaw` + :func:`build_seeded_artifact` ->
AC.AR.10 (known flaws); :func:`score` -> AC.AR.10 (catch rate);
:func:`calibrate` -> AC.AR.10 (real run reads back a rate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .critic import ModelFn
from .findings import Finding
from .manual import review_text
from .registry import ModelRoleRegistry
from .validation import ValidatorFn


@dataclass
class SeededFlaw:
    """A known flaw planted in a calibration artifact (AC.AR.10).

    ``anchor`` is a distinctive string the flaw plants in the artifact;
    a critic finding is credited with catching this flaw iff the anchor
    appears in the finding's location or scenario. ``description`` is for
    the human reading the calibration report; ``severity_floor`` is the
    minimum severity a real catch should assign (a HIGH flaw caught only
    as a NIT is a partial catch — recorded but flagged).
    """

    id: str
    anchor: str
    description: str
    severity_floor: str = "MEDIUM"


@dataclass
class CalibrationResult:
    """A calibration run's outcome (AC.AR.10).

    ``catch_rate`` is caught/total. ``caught`` / ``missed`` name which
    seeded flaws were found. ``ran`` is False when the review could not
    run (the calibration is inconclusive, not a 0.0 — a 0% catch rate and
    an un-run review are different failures).
    """

    catch_rate: float
    caught: list[str]
    missed: list[str]
    total: int
    ran: bool
    extra_findings: int = 0
    detail: list[str] = field(default_factory=list)


def _flaw_caught(flaw: SeededFlaw, findings: list[Finding]) -> Optional[Finding]:
    """Return the finding that caught ``flaw`` (anchor match), else None."""
    for f in findings:
        if flaw.anchor in f.location or flaw.anchor in f.scenario:
            return f
    return None


def score(
    flaws: list[SeededFlaw],
    findings: list[Finding],
    *,
    ran: bool = True,
) -> CalibrationResult:
    """Compute the catch rate from seeded flaws + critic findings (AC.AR.10).

    Deterministic + offline: a flaw is caught iff a finding's location or
    scenario contains its anchor. Findings not matching any seeded flaw
    are counted as ``extra_findings`` (the critic may legitimately find
    real flaws beyond the seeded set — recorded, not penalized).
    """
    if not ran:
        return CalibrationResult(
            catch_rate=0.0,
            caught=[],
            missed=[f.id for f in flaws],
            total=len(flaws),
            ran=False,
            detail=["review did not run — calibration INCONCLUSIVE"],
        )
    caught: list[str] = []
    missed: list[str] = []
    matched_findings: set[int] = set()
    detail: list[str] = []
    for flaw in flaws:
        hit = _flaw_caught(flaw, findings)
        if hit is not None:
            caught.append(flaw.id)
            matched_findings.add(id(hit))
            detail.append(f"CAUGHT {flaw.id}: {flaw.description}")
        else:
            missed.append(flaw.id)
            detail.append(f"MISSED {flaw.id}: {flaw.description}")
    extra = sum(1 for f in findings if id(f) not in matched_findings)
    total = len(flaws)
    rate = (len(caught) / total) if total else 0.0
    return CalibrationResult(
        catch_rate=rate,
        caught=caught,
        missed=missed,
        total=total,
        ran=True,
        extra_findings=extra,
        detail=detail,
    )


def calibrate(
    artifact: str,
    objective: str,
    flaws: list[SeededFlaw],
    *,
    tier: str = "STANDARD",
    domain: Optional[str] = None,
    model_fn: ModelFn | None = None,
    validator_fn: ValidatorFn | None = None,
    registry: ModelRoleRegistry | None = None,
) -> CalibrationResult:
    """Run the review over a seeded artifact + read back the catch rate.

    End-to-end (AC.AR.10 real variant): runs the actual review pipeline
    (real isolated critic by default, or an injected ``model_fn`` for a
    deterministic test) over the seeded artifact, then scores every
    finding surfaced by the review against the seeded flaws. This is the
    proof that the reviewer actually catches planted flaws — the
    build-time proof and the periodic-cadence measurement both call this.

    ``registry`` (AC.CDX.1) routes the critic role at named model legs — e.g.
    the Codex leg (``codex.codex_critic_registry``) — so calibration can prove
    a non-default leg (WS-D2) catches a planted defect through the production
    pipeline. ``None`` reproduces the default single-Claude pass; a passed
    ``registry`` takes precedence over ``model_fn`` (the multi-leg path).
    """
    result = review_text(
        artifact,
        objective,
        tier=tier,
        domain=domain,
        model_fn=model_fn,
        validator_fn=validator_fn,
        registry=registry,
    )
    return score(flaws, result.verdict.findings, ran=result.ran)
