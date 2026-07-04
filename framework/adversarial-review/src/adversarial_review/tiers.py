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

"""Depth tiers — STANDARD floor + DEEP parallel per-axis critics (D10/P7).

AC.AR.11:

  * STANDARD (floor, non-skippable): one two-phase critic + validation +
    verdict. Always runs for anything crossing the boundary.
  * DEEP (high-stakes): N critics, one per named axis from the domain
    methodology, run with NO SHARED CONTEXT (each a fresh isolated
    review), findings merged by a SEPARATE judge that PRESERVES
    disagreement. Symmetric free-form panel debate is never the mechanism
    (AI §1.2/§F6: unguided panels collapse into consensus at >85%
    conformity). The structured opposing-sides-debate escalation for a
    contested call (D5 tail) is a documented seam — staged, not live.

The DEEP tier is a fan-out over the SAME STANDARD critic primitive plus a
merge step; it introduces no new critic machinery (Lens 1). Each axis
review is independent — this is what "no shared context" means concretely:
axis critic k never sees axis critic j's findings.

Per ODD §2.5: :class:`Tier` -> AC.AR.11; :func:`run_deep_review` ->
AC.AR.11 (parallel isolated per-axis + merge, no shared context);
:func:`merge_findings` -> AC.AR.11 (separate merge judge, disagreement
preserved).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .corpus import CorpusStore
from .critic import ModelFn
from .findings import Finding
from .pipeline import ReviewResult, run_standard_review
from .validation import ValidatorFn
from .verdict import decide


class Tier(str, Enum):
    """Review depth tier (AC.AR.11)."""

    STANDARD = "STANDARD"
    DEEP = "DEEP"


@dataclass
class AxisReview:
    """One axis's independent review within a DEEP pass.

    Each carries its OWN findings, produced in isolation — never merged
    into a shared context before the separate merge judge sees them.
    """

    axis: str
    findings: list[Finding]
    ran: bool


def merge_findings(axis_reviews: list[AxisReview]) -> list[Finding]:
    """Merge per-axis findings, PRESERVING disagreement (AC.AR.11 / P7).

    The merge is a SEPARATE step from the axis critics (they never saw
    each other). It concatenates every axis's findings — it does NOT
    negotiate them toward consensus or drop a minority finding because
    other axes disagreed. A finding surfaced by one axis and not another
    survives; that is the disagreement-preservation P7 requires (the
    consensus-collapse failure, AI §F6, is precisely the merge dropping a
    correct minority finding). De-duplication is by (location, scenario)
    exact identity only — near-duplicates from different axes are KEPT
    (they are independent corroboration, not noise to collapse).
    """
    merged: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for review in axis_reviews:
        for f in review.findings:
            key = (f.location.strip(), f.scenario.strip())
            if key in seen:
                continue
            seen.add(key)
            merged.append(f)
    return merged


# Default DEEP axes when the domain methodology names none explicitly.
# The named-axis decomposition is what counters generic critique (AI §F3)
# and is loam's EVAL_DIMENSIONS discipline (Lens 5).
DEFAULT_DEEP_AXES = (
    "objective-fulfillment",
    "evidence-and-claims",
    "failure-modes-and-edge-cases",
    "internal-consistency",
)


def run_deep_review(
    artifact: str,
    objective: str,
    *,
    axes: Optional[tuple[str, ...]] = None,
    domain: Optional[str] = None,
    corpus: Optional[CorpusStore] = None,
    model_fn: ModelFn | None = None,
    validator_fn: ValidatorFn | None = None,
) -> ReviewResult:
    """Run a DEEP-tier review: parallel isolated per-axis + merge (AC.AR.11).

    Each axis gets its OWN independent STANDARD review (fresh isolated
    context, no shared state). The axis findings are then merged by a
    separate step preserving disagreement, and ONE verdict is computed
    from the merged, validated set. If NO axis critic could run, the
    result is SUSPECT (inconclusive). Runs axes sequentially here (each
    spawn is already isolated); a parallel executor is a drop-in
    optimization that does not change the no-shared-context guarantee.
    """
    axis_list = axes or DEFAULT_DEEP_AXES
    axis_reviews: list[AxisReview] = []
    any_ran = False
    for axis in axis_list:
        # Each axis review is a full independent STANDARD pass, its
        # objective narrowed to the axis so the critic derives that
        # axis's correct-artifact spec (named-axis decomposition).
        axis_objective = (
            f"{objective}\n\n[Review axis for THIS pass: {axis}. Attack the "
            f"artifact specifically on the '{axis}' axis.]"
        )
        result = run_standard_review(
            artifact,
            axis_objective,
            domain=domain,
            corpus=corpus,
            model_fn=model_fn,
            validator_fn=validator_fn,
            axis=axis,
        )
        axis_reviews.append(
            AxisReview(axis=axis, findings=result.verdict.findings, ran=result.ran)
        )
        any_ran = any_ran or result.ran

    if not any_ran:
        return ReviewResult(
            verdict=decide([], artifact, ran=False),
            methodology_domain=domain or "domain-agnostic",
            methodology_stale=False,
            ran=False,
        )

    merged = merge_findings(axis_reviews)
    # Findings were already lint+validated within each axis pass; compute
    # the merged verdict. Residual-risk fields derive from the merged set.
    from .pipeline import _strongest_surviving, _uncheckable_summary

    verdict = decide(
        merged,
        artifact,
        ran=True,
        strongest_objection=_strongest_surviving(merged),
        uncheckable=_uncheckable_summary(merged),
    )
    return ReviewResult(
        verdict=verdict,
        methodology_domain=domain or "domain-agnostic",
        methodology_stale=False,
        ran=True,
    )
