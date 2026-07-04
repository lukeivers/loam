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

"""The review pipeline — the shared core both manual + gate call.

Wires the four stages into one STANDARD review pass:

    resolve domain methodology (corpus, P6)
      -> two-phase falsification critic (P2)
      -> generic-finding lint (F3)
      -> ground-truth validation (P3)
      -> verdict (block-by-default + residual + zero-findings suspicion,
         P4/P5).

:func:`run_standard_review` is the STANDARD-tier floor (AC.AR.1). The
DEEP tier (tiers.py) composes multiple of these per axis + a merge judge.
The manual entry (manual.py) and the gate entry (gate.py) both call this;
the ONLY difference is the trigger + the activation switch (gate) vs a
direct on-demand call (manual).

The model leg is injectable end-to-end (``model_fn`` / ``validator_fn``)
so tests exercise the REAL seed/critic-parse/validation/verdict logic
deterministically and stub only the spawn boundary. Default legs are the
isolated real spawns (P9).

Per ODD §2.5: :func:`run_standard_review` -> AC.AR.1 + AC.AR.6;
:func:`build_inputs` -> AC.AR.2/AC.AR.9 (seed assembled from the four
allow-listed inputs, methodology resolved from the corpus).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .corpus import CorpusStore
from .critic import ModelFn, run_critic
from .findings import Finding, apply_generic_lint
from .seed import ReviewInputs
from .validation import ValidatorFn, validate_all
from .verdict import Verdict, decide

# The default review protocol seeded into every critic context (the
# "review protocol" allow-listed seed block, AC.AR.2). Names the stance
# + the finding shape; the domain methodology carries the failure
# taxonomy.
DEFAULT_PROTOCOL = (
    "Premortem stance: assume the artifact already failed its objective; "
    "reconstruct why. Derive the correct-artifact spec first, then diff. "
    "Pin every finding to a location + concrete failure scenario + severity. "
    "Run hot for recall; a separate layer validates. You are an internal QA "
    "lens, never a model of any real audience."
)


@dataclass
class ReviewResult:
    """The full result of a review pass.

    ``verdict`` is the gate-facing decision; ``methodology_domain`` /
    ``methodology_stale`` record which corpus doc seeded the critic (or
    that the domain-agnostic floor was used); ``ran`` is False when the
    critic could not run (REVIEW INCONCLUSIVE).
    """

    verdict: Verdict
    methodology_domain: str
    methodology_stale: bool
    ran: bool


def build_inputs(
    artifact: str,
    objective: str,
    *,
    domain: Optional[str] = None,
    protocol: str = DEFAULT_PROTOCOL,
    corpus: Optional[CorpusStore] = None,
    strip_provenance: bool = True,
) -> tuple[ReviewInputs, str, bool]:
    """Assemble the seed inputs, resolving methodology from the corpus (P6).

    Checks the corpus for a domain-specific methodology doc BEFORE any
    pull (AC.AR.9); falls back to the domain-agnostic floor when the
    domain is uncovered or unnamed. Returns
    ``(inputs, methodology_domain, stale)``.
    """
    store = corpus or CorpusStore()
    methodology_domain = "domain-agnostic"
    stale = False
    # Seed the COMPACT checklist (not the full 28KB docs) — faster + a
    # higher-yield critic input (Fagan). The full docs stay in the corpus
    # for citations/provenance and DEEP-tier reference.
    methodology = store.seed_methodology()
    if domain:
        doc = store.resolve(domain)
        if doc is not None:
            # Seed with the domain doc PLUS the agnostic floor.
            methodology = f"{doc.text}\n\n{methodology}"
            methodology_domain = domain
            stale = doc.stale
    inputs = ReviewInputs(
        artifact=artifact,
        objective=objective,
        methodology=methodology,
        protocol=protocol,
        strip_provenance=strip_provenance,
    )
    return inputs, methodology_domain, stale


def run_standard_review(
    artifact: str,
    objective: str,
    *,
    domain: Optional[str] = None,
    corpus: Optional[CorpusStore] = None,
    model_fn: ModelFn | None = None,
    validator_fn: ValidatorFn | None = None,
    strongest_objection: str = "",
    uncheckable: str = "",
    strip_provenance: bool = True,
    axis: str = "",
) -> ReviewResult:
    """Run one STANDARD-tier adversarial review (AC.AR.1).

    Seed -> two-phase critic -> generic lint -> validation -> verdict.
    ``strongest_objection`` / ``uncheckable`` are the residual-risk
    fields a PASS must carry (P5); the manual/gate callers derive them
    from the critic pass (the strongest quarantined/low finding + the
    validator's uncheckable set) and pass them here. When the critic
    cannot run, the verdict is SUSPECT (inconclusive), never PASS.
    """
    inputs, methodology_domain, stale = build_inputs(
        artifact,
        objective,
        domain=domain,
        corpus=corpus,
        strip_provenance=strip_provenance,
    )

    findings, ran = run_critic(inputs, axis=axis, model_fn=model_fn)
    if not ran:
        return ReviewResult(
            verdict=decide([], artifact, ran=False),
            methodology_domain=methodology_domain,
            methodology_stale=stale,
            ran=False,
        )

    apply_generic_lint(findings)
    findings = validate_all(findings, artifact, validator_fn=validator_fn)

    # Derive residual-risk fields for a would-be PASS from the surviving
    # findings when the caller did not supply them: the strongest
    # surviving (non-blocking) objection + the uncheckable set (P5). This
    # guarantees a PASS is never malformed.
    so = strongest_objection or _strongest_surviving(findings)
    un = uncheckable or _uncheckable_summary(findings)

    verdict = decide(
        findings,
        artifact,
        ran=True,
        strongest_objection=so,
        uncheckable=un,
    )
    return ReviewResult(
        verdict=verdict,
        methodology_domain=methodology_domain,
        methodology_stale=stale,
        ran=True,
    )


def _strongest_surviving(findings: list[Finding]) -> str:
    """The strongest non-blocking surviving objection, for a PASS (P5)."""
    if not findings:
        return (
            "no substantive objection survived validation; the strongest "
            "constructible objection is that the review's own coverage is "
            "the binding limit (see what-could-not-be-checked)"
        )
    ranked = sorted(findings, key=lambda f: f.effective_severity(), reverse=True)
    top = ranked[0]
    return f"[{top.location}] {top.scenario}"


def _uncheckable_summary(findings: list[Finding]) -> str:
    """What the review could not check, for a PASS (P5)."""
    quarantined = [
        f for f in findings if f.state.value == "HYPOTHESIZED"
    ]
    if not quarantined:
        return (
            "no finding required an un-runnable check; residual risk is "
            "limited to failure modes outside the seeded methodology's "
            "taxonomy"
        )
    locs = ", ".join(sorted({f.location for f in quarantined})[:5])
    return (
        f"{len(quarantined)} finding(s) could not be validated against "
        f"ground truth and were quarantined (locations: {locs})"
    )
