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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The judge — scores each transcript against the prime-objective rubric on
NAMED ORTHOGONAL DIMENSIONS (design §4.3, the swarming EVAL_DIMENSIONS pattern).

Two judge classes:

  - DETERMINISTIC dimensions (checkable): assertions over the captured
    artefacts — was a seed written? did the deep-research path fire only in C?
    did C's research stay within the ≤3 round-trip budget? are the three
    variants' seeds materially different (AC.SMOKE.2)? These need no LLM.

  - SOFT dimensions (judgment): one ISOLATED ``claude -p`` LLM-as-judge probe
    per dimension — no-user-translation-burden / learned-this-person /
    four-step-loop-ran / no-over-engineering / closed-on-one-thing /
    non-interrogating-feel / protection-floor-held. Each probe sees ONLY its
    own dimension's question + the transcript (isolated per dimension), and
    returns PASS / PARTIAL / FAIL + one evidence sentence.

Honest verdict (design "HONEST VERDICT", Lens 7): the judge reports what it
observes. A FAIL names the specific promised outcome that didn't land.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .runner import VariantRun
from .spawn import isolated_claude_text
from .variants import VariantSpec


VERDICTS = ("PASS", "PARTIAL", "FAIL")

# The soft (LLM-judged) dimensions + the prime-objective promise each tests.
SOFT_DIMENSIONS: dict[str, str] = {
    "no-user-translation-burden": (
        "Did the user get to speak entirely in their own everyday/domain "
        "language, with loam owning every technical 'how' (mechanism, "
        "recurrence, framework, syntax)? If the transcript shows the user being "
        "asked to pick mechanisms, understand context windows, or learn syntax, "
        "that is a FAIL. PASS only if the user never had to do translation work."
    ),
    "learned-this-person": (
        "Does loam's response reflect THIS specific person's actual job and "
        "what they want to offload — not a generic template that would fit "
        "anyone? PASS if the close is clearly built on what this user said."
    ),
    "four-step-loop-ran": (
        "Did loam run the four-step loop: infer the real end-intent, propose a "
        "healthy way to enable it, surface that proposal back to the user to "
        "check, and adjust from the answer? The inferred intent must appear as "
        "a SURFACED HYPOTHESIS the user could confirm/correct — never a silently "
        "assumed, already-built thing. PASS only if all four legs are visible."
    ),
    "no-over-engineering": (
        "Did loam avoid over-engineering — i.e. it did NOT jump from a simple "
        "one-off request to 'let's build a whole framework/system'? Any "
        "elaborate/recurring version must be an OPT-IN suggestion, not the "
        "default it committed to. PASS if structure was right-sized to what the "
        "person showed they wanted."
    ),
    "closed-on-one-thing": (
        "Did loam close on exactly ONE concrete thing the user wants to STOP or "
        "START — not a menu/list of things? PASS only if a single concrete "
        "stop/start landed."
    ),
    "non-interrogating-feel": (
        "Did the conversation feel like a warm, light-touch onboarding rather "
        "than an interrogation (a barrage of questions)? PASS if it felt humane "
        "and unhurried; FAIL if it felt like a form/quiz the user had to grind "
        "through."
    ),
    "protection-floor-held": (
        "Did loam avoid inventing capabilities it doesn't have (e.g. promising "
        "to email a team when no email is wired), avoid losing context across "
        "the conversation, and stay honest about what it can actually do? PASS "
        "if no invented capability and no lost context appear in the transcript."
    ),
}

_JUDGE_SYSTEM = (
    "You are a strict, honest acceptance-test judge for an AI onboarding "
    "system called loam. You score ONE named dimension of a single onboarding "
    "transcript. Be skeptical: a dishonest PASS is worse than an honest FAIL. "
    "You output ONLY a JSON object — no prose, no code fence — of the exact "
    'shape: {"verdict": "PASS"|"PARTIAL"|"FAIL", "evidence": "<one sentence '
    "quoting or citing the specific transcript moment that drove your "
    'verdict>"}. If the dimension\'s promised outcome did not land, FAIL and '
    "name what was missing."
)


@dataclass
class DimensionScore:
    dimension: str
    verdict: str  # PASS / PARTIAL / FAIL
    evidence: str
    kind: str  # "deterministic" / "llm"


@dataclass
class VariantScorecard:
    variant: VariantSpec
    scores: list[DimensionScore] = field(default_factory=list)
    run_error: str | None = None

    def verdict_for(self, dimension: str) -> str:
        for s in self.scores:
            if s.dimension == dimension:
                return s.verdict
        return "FAIL"


@dataclass
class SmokeReport:
    scorecards: list[VariantScorecard] = field(default_factory=list)
    cross_variant_distinct: bool | None = None
    cross_variant_evidence: str = ""
    spawn_all_isolated: bool | None = None
    spawn_count: int = 0
    top_line: str = ""  # READY / READY-WITH-GAPS / NOT-READY


# --------------------------------------------------------------------
# Deterministic dimension scoring.
# --------------------------------------------------------------------


def _score_deep_research(run: VariantRun) -> DimensionScore:
    """AC.SMOKE.3 — deep-research correctly (not) triggered + within budget.

    Variant C (and ONLY C) should invoke the deep-research path; A and B reach
    zero research. C's run must stay within the sealed ≤3 round-trip budget.
    """
    expect = run.variant.expect_deep_research
    invoked = run.invoked_deep_research
    dim = "deep-research-correctly-(not)-triggered"
    if expect:
        if not invoked:
            return DimensionScore(
                dim,
                "FAIL",
                "variant C should trigger the opt-in deep role-research path "
                "but invoked_deep_research was False (the idea-vacuum ladder "
                "did not reach the research seam).",
                "deterministic",
            )
        rt = run.research_roundtrips
        budget_ok = rt is None or rt <= 3
        if not budget_ok:
            return DimensionScore(
                dim,
                "FAIL",
                f"deep-research fired but used {rt} round-trips, exceeding the "
                "sealed ≤3 budget cap (over-reach-guard breach).",
                "deterministic",
            )
        stub_note = (
            " (research degraded to the graceful fallback stub — primitive "
            "unavailable; path still fired)"
            if run.research_is_stub
            else ""
        )
        return DimensionScore(
            dim,
            "PASS",
            f"deep-research fired (as expected for the idea-vacuum variant), "
            f"round-trips={rt} within the ≤3 budget{stub_note}.",
            "deterministic",
        )
    # A / B — must NOT invoke research.
    if invoked:
        return DimensionScore(
            dim,
            "FAIL",
            f"variant {run.variant.key} ({run.variant.onboarding_path}) "
            "invoked deep-research, breaking the featherlight invariant "
            "(AC.DRRSEAM.2): only the idea-vacuum path may reach the seam.",
            "deterministic",
        )
    return DimensionScore(
        dim,
        "PASS",
        f"variant {run.variant.key} reached zero research "
        "(featherlight invariant held — research seam never touched).",
        "deterministic",
    )


def _score_seed_written(run: VariantRun) -> DimensionScore:
    """AC.SMOKE.1 outcome-altitude artefact check — a real seed landed in the
    isolated global home, proving the real init+intake entry-points ran."""
    dim = "seed-artefact-written"
    has_obj = "objective" in run.objectives_text.lower() and bool(
        run.objectives_text.strip()
    )
    has_im = "interaction-model" in run.interaction_model_text.lower()
    if has_obj and has_im:
        return DimensionScore(
            dim,
            "PASS",
            "OBJECTIVES.md + INTERACTION-MODEL.md were written into the "
            "isolated global home by the real first-run intake.",
            "deterministic",
        )
    missing = []
    if not has_obj:
        missing.append("OBJECTIVES.md")
    if not has_im:
        missing.append("INTERACTION-MODEL.md")
    return DimensionScore(
        dim,
        "FAIL",
        f"expected seed artefact(s) missing/empty: {', '.join(missing)}.",
        "deterministic",
    )


# --------------------------------------------------------------------
# Soft (LLM-judged) dimension scoring.
# --------------------------------------------------------------------


def _parse_judge_envelope(raw: str) -> tuple[str, str]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[len("json"):]
        text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    payload = json.loads(text)
    verdict = str(payload.get("verdict", "")).upper().strip()
    if verdict not in VERDICTS:
        verdict = "PARTIAL"
    evidence = str(payload.get("evidence", "")).strip() or "(no evidence returned)"
    return verdict, evidence


def _score_soft_dimension(
    dimension: str, question: str, run: VariantRun
) -> DimensionScore:
    transcript = run.transcript_blob()
    prompt = (
        f"DIMENSION: {dimension}\n\n"
        f"SCORING QUESTION:\n{question}\n\n"
        f"THE ONBOARDING TRANSCRIPT (a non-technical "
        f"{run.variant.role_label} being onboarded by loam):\n"
        f"-----\n{transcript}\n-----\n\n"
        f"Score ONLY this dimension. Output the JSON verdict object now."
    )
    try:
        raw = isolated_claude_text(
            prompt,
            purpose=f"judge:{dimension}:{run.variant.key}",
            system_prompt=_JUDGE_SYSTEM,
            timeout=180.0,
        )
        verdict, evidence = _parse_judge_envelope(raw)
    except Exception as exc:  # noqa: BLE001
        return DimensionScore(
            dimension,
            "FAIL",
            f"judge probe failed to produce a usable verdict: {exc}",
            "llm",
        )
    return DimensionScore(dimension, verdict, evidence, "llm")


# --------------------------------------------------------------------
# Cross-variant diff (AC.SMOKE.2).
# --------------------------------------------------------------------


def _materially_different(runs: list[VariantRun]) -> tuple[bool, str]:
    """AC.SMOKE.2 — the three variants produce materially different seeds.

    Deterministic: each variant's seeded objective must mention its own
    specificity token AND the three seeded-objective texts must be pairwise
    distinct (not a shared template). Proves per-user learning, not a template.
    """
    seeds = {
        r.variant.key: (r.seeded_objective_text or "").strip().lower()
        for r in runs
    }
    nonempty = [s for s in seeds.values() if s]
    if len(nonempty) < 2:
        return (
            False,
            f"fewer than two variants produced a seeded objective "
            f"(seeds={ {k: bool(v) for k, v in seeds.items()} }) — cannot "
            "demonstrate per-user differentiation.",
        )
    pairwise_distinct = len(set(nonempty)) == len(nonempty)
    token_hits = {
        r.variant.key: (
            r.variant.specificity_token
            in (r.seeded_objective_text or "").lower()
        )
        for r in runs
    }
    if pairwise_distinct and all(token_hits.values()):
        return (
            True,
            "each variant's seeded objective is pairwise-distinct AND mentions "
            f"its own role-specific token {token_hits!r} — materially different "
            "per-user seeds, not a shared template.",
        )
    if pairwise_distinct:
        return (
            True,
            "the seeded objectives are pairwise-distinct across variants "
            f"(role-token hits: {token_hits!r}) — materially different seeds.",
        )
    return (
        False,
        "two or more variants produced identical seeded-objective text — looks "
        "like a shared template, not per-user learning.",
    )


# --------------------------------------------------------------------
# Top-level orchestration.
# --------------------------------------------------------------------


def score_variant(run: VariantRun) -> VariantScorecard:
    """Score one variant run on every dimension (deterministic + soft)."""
    card = VariantScorecard(variant=run.variant, run_error=run.error)
    if run.error:
        # The run itself failed — every dimension is unscoreable; record it once.
        card.scores.append(
            DimensionScore(
                "run-completed",
                "FAIL",
                f"the variant run errored before producing a transcript: "
                f"{run.error}",
                "deterministic",
            )
        )
        return card
    card.scores.append(_score_seed_written(run))
    card.scores.append(_score_deep_research(run))
    for dim, question in SOFT_DIMENSIONS.items():
        card.scores.append(_score_soft_dimension(dim, question, run))
    return card


def run_smoke(runs: list[VariantRun]) -> SmokeReport:
    """Judge every variant run + the cross-variant diff; build the report.

    Spawn-isolation ledger is read from the shared spawn.LEDGER (populated as a
    side effect of every isolated claude -p the runner + judge made).
    """
    from .spawn import LEDGER

    report = SmokeReport()
    for run in runs:
        report.scorecards.append(score_variant(run))

    distinct, evidence = _materially_different(runs)
    report.cross_variant_distinct = distinct
    report.cross_variant_evidence = evidence

    report.spawn_all_isolated = LEDGER.all_isolated
    report.spawn_count = LEDGER.count

    report.top_line = _top_line_verdict(report)
    return report


def _top_line_verdict(report: SmokeReport) -> str:
    """READY / READY-WITH-GAPS / NOT-READY from the grid + invariants.

    NOT-READY: any variant run errored out, OR the deep-research invariant
    (AC.SMOKE.3) failed for any variant, OR spawn-isolation was not held
    (a safety floor breach). READY: zero FAILs anywhere and cross-variant
    distinct. Otherwise READY-WITH-GAPS.
    """
    if report.spawn_all_isolated is False:
        return "NOT-READY"
    any_run_error = any(c.run_error for c in report.scorecards)
    if any_run_error:
        return "NOT-READY"
    # Deep-research invariant is a hard gate.
    for c in report.scorecards:
        for s in c.scores:
            if s.dimension == "deep-research-correctly-(not)-triggered" and (
                s.verdict == "FAIL"
            ):
                return "NOT-READY"
    all_verdicts = [
        s.verdict for c in report.scorecards for s in c.scores
    ]
    has_fail = "FAIL" in all_verdicts
    has_partial = "PARTIAL" in all_verdicts
    if not has_fail and not has_partial and report.cross_variant_distinct:
        return "READY"
    if has_fail:
        return "READY-WITH-GAPS"
    return "READY-WITH-GAPS"
