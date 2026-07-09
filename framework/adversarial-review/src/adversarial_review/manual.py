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

"""Manual on-demand review — the first-class, no-gate entry point (AC.AR.1).

Owner requirement: point the review at ONE named artifact + a stated
objective and get the full harsh review back — NO automation, NO gate,
NO blocking. This is the PRIMARY usable surface while the gate ships
inactive. It calls the exact same pipeline the gate would; the only
difference is there is no boundary trigger and no activation switch — a
manual run always runs and always just returns the review.

Usage (library):

    from adversarial_review.manual import review_file
    result = review_file("path/to/artifact.md", objective="...", tier="DEEP")
    print(render_report(result, "path/to/artifact.md"))

Usage (CLI):

    python -m adversarial_review.manual ARTIFACT --objective "..." [--deep]
      [--domain NAME] [--objective-file PATH]

Per ODD §2.5: :func:`review_file` -> AC.AR.1 (manual entry, no gate);
:func:`render_report` -> AC.AR.1/AC.AR.13 (harsh review out; internal
-lens framing, no stakeholder prediction).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .critic import ModelFn
from .findings import ValidationState
from .pipeline import ReviewResult, run_standard_review
from .registry import DEFAULT_LEG_NAME, ModelRoleRegistry
from .tiers import Tier, run_deep_review
from .validation import ValidatorFn
from .verdict import Disposition


def review_file(
    artifact_path: str,
    objective: str,
    *,
    tier: str = "STANDARD",
    domain: Optional[str] = None,
    model_fn: ModelFn | None = None,
    validator_fn: ValidatorFn | None = None,
    registry: ModelRoleRegistry | None = None,
) -> ReviewResult:
    """Run a manual review of one artifact file (AC.AR.1) — no gate.

    Reads the artifact from disk, runs the STANDARD (default) or DEEP
    pipeline, and returns the review result. Never consults the
    activation switch and never blocks anything — a manual run is pure
    on-demand review. ``registry`` (AC.MRR.*) routes the critic role at
    named model legs; None reproduces the default single-Claude pass.
    """
    text = Path(artifact_path).read_text(encoding="utf-8")
    return review_text(
        text,
        objective,
        tier=tier,
        domain=domain,
        model_fn=model_fn,
        validator_fn=validator_fn,
        registry=registry,
    )


def review_text(
    artifact: str,
    objective: str,
    *,
    tier: str = "STANDARD",
    domain: Optional[str] = None,
    model_fn: ModelFn | None = None,
    validator_fn: ValidatorFn | None = None,
    registry: ModelRoleRegistry | None = None,
) -> ReviewResult:
    """Manual review of an in-memory artifact string (AC.AR.1).

    ``registry`` (AC.MRR.*) resolves the critic role to named model legs;
    None reproduces the pre-amendment single-Claude pass byte-identically.
    """
    t = Tier(tier.upper()) if isinstance(tier, str) else tier
    if t is Tier.DEEP:
        return run_deep_review(
            artifact,
            objective,
            domain=domain,
            model_fn=model_fn,
            validator_fn=validator_fn,
            registry=registry,
        )
    return run_standard_review(
        artifact,
        objective,
        domain=domain,
        model_fn=model_fn,
        validator_fn=validator_fn,
        registry=registry,
    )


def render_report(result: ReviewResult, artifact_label: str) -> str:
    """Render the full harsh review as a text report (AC.AR.1).

    Leads with the verdict, then the validated blocking findings, then
    the quarantined (unvalidated) findings clearly marked non-blocking,
    then the mandatory residual-risk block (P5). Internal-lens only — no
    stakeholder-reaction framing (P10).
    """
    v = result.verdict
    # AC.MRR.1/2/3 — annotate model legs ONLY when a NON-default leg name
    # appears (in legs_used ∪ missing_legs). The default single-Claude path
    # — whether it ran or was unavailable (missing_legs == ("claude",)) —
    # carries no non-default name, so ZERO new bytes are emitted and the
    # rendered report is byte-identical to pre-amendment (AC.MRR.1). Gating
    # on the NAME (not on bool(missing_legs)) is what preserves the
    # default-unavailable path.
    show_legs = any(
        name != DEFAULT_LEG_NAME
        for name in (*result.legs_used, *result.missing_legs)
    )
    lines: list[str] = []
    lines.append(f"# Adversarial review — {artifact_label}")
    lines.append("")
    lines.append(f"VERDICT: {v.disposition.value}")
    if v.disposition is Disposition.SUSPECT:
        lines.append(f"  SUSPICION: {v.suspicion_reason}")
    lines.append(
        f"  methodology: {result.methodology_domain}"
        + ("  [STALE — refresh due]" if result.methodology_stale else "")
    )
    if not result.ran:
        lines.append(
            "  REVIEW INCONCLUSIVE — the critic could not run; this is NOT a "
            "clean bill."
        )
        if show_legs and result.missing_legs:
            lines.append(
                "  MISSING LEGS: "
                + ", ".join(result.missing_legs)
                + " — configured model leg(s) unavailable; not a clean bill."
            )
        lines.append(
            "  USABLE FALLBACK: if you are invoking this from INSIDE a running "
            "Claude session, the nested `claude -p` critic spawn can hang on "
            "interactive-slot contention. Do NOT retry the subprocess path — "
            "run the in-session backend instead (no nested subprocess): "
            "`python -m adversarial_review insession derive|diff|finalize`, "
            "supplying each critic phase from a FRESH Task subagent. See the "
            "adversarial-review SKILL for the handshake."
        )
        return "\n".join(lines)

    validated = [
        f for f in v.findings if f.state is ValidationState.VALIDATED and not f.generic
    ]
    quarantined = [
        f for f in v.findings if f.state is ValidationState.HYPOTHESIZED
    ]
    generic = [f for f in v.findings if f.generic]

    blocking = [f for f in validated if f.blocks()]

    # AC.MRR.2/3 — model-leg provenance block (only when a non-default leg
    # is present; the default single-Claude review adds nothing here).
    if show_legs:
        lines.append("")
        lines.append("## Model legs")
        lines.append(
            "  produced findings: "
            + (", ".join(result.legs_used) if result.legs_used else "(none)")
        )
        if result.missing_legs:
            lines.append(
                "  MISSING (configured but unavailable, not a clean bill): "
                + ", ".join(result.missing_legs)
            )

    lines.append("")
    lines.append(f"## Validated findings ({len(validated)}) — "
                 f"{len(blocking)} blocking")
    for f in sorted(validated, key=lambda x: x.effective_severity(), reverse=True):
        mark = "BLOCK" if f.blocks() else "     "
        lines.append(
            f"  [{mark}] {f.effective_severity().name:8} {f.location}"
        )
        lines.append(f"          {f.scenario}")
        if show_legs and f.leg:
            lines.append(f"          model leg: {f.leg}")
        if f.evidence:
            lines.append(f"          evidence: {f.evidence}")

    if quarantined:
        lines.append("")
        lines.append(
            f"## Quarantined findings ({len(quarantined)}) — NON-BLOCKING, "
            "could not be validated against ground truth"
        )
        for f in quarantined:
            lines.append(f"  [HYPOTH] {f.severity.name:8} {f.location}")
            lines.append(f"          {f.scenario}")
            if show_legs and f.leg:
                lines.append(f"          model leg: {f.leg}")

    if generic:
        lines.append("")
        lines.append(
            f"## Generic findings ({len(generic)}) — excluded from the verdict "
            "(true of any artifact of the class)"
        )

    lines.append("")
    lines.append("## Residual risk (mandatory on any non-BLOCK verdict, P5)")
    if v.disposition is Disposition.PASS:
        lines.append(f"  strongest surviving objection: {v.strongest_objection}")
        lines.append(f"  what the review could NOT check: {v.uncheckable}")
    elif v.disposition is Disposition.BLOCK:
        lines.append(
            "  BLOCK — resolve the blocking findings above or record an "
            "explicit owner override (verdict.override(reason))."
        )
    return "\n".join(lines)


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="adversarial-review",
        description="Manual on-demand adversarial review of one artifact "
        "(no gate, no blocking).",
    )
    p.add_argument("artifact", help="path to the artifact file to review")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--objective", help="the artifact's stated objective")
    g.add_argument(
        "--objective-file", help="path to a file holding the objective"
    )
    p.add_argument("--domain", help="domain for methodology lookup", default=None)
    p.add_argument(
        "--deep", action="store_true", help="DEEP tier (parallel per-axis)"
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry (AC.AR.1). Prints the report; exit 0 always (no gate)."""
    args = _build_argparser().parse_args(argv)
    objective = (
        Path(args.objective_file).read_text(encoding="utf-8")
        if args.objective_file
        else args.objective
    )
    result = review_file(
        args.artifact,
        objective,
        tier="DEEP" if args.deep else "STANDARD",
        domain=args.domain,
    )
    print(render_report(result, args.artifact))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
