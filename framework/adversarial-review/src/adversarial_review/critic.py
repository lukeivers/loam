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

"""The adversarial critic — two-phase falsification (P2 / D5 / AC.AR.3).

The critic generalizes the sealed ``loam-external-reviewer`` core (its
non-deferential stance, VERIFIED/INFERRED/HYPOTHESIZED evidence tiers,
GOOD/DRIFT voice, banded severity) from milestone-codebase review to
"any artifact against its stated objective" (D3). The tasking is
FALSIFICATION phrased as accomplished failure — "this artifact shipped
and was torn apart; reconstruct why" (premortem, GEN §2) — never
"evaluate/assess", which invokes the agreement prior (F1).

Two phases, ORDERED (P2 / J2):

  1. DERIVE — from objective + methodology alone, with the artifact
     ABSENT, construct the spec a correct artifact must satisfy.
  2. DIFF   — reveal the artifact; diff it against the derivation and
     emit findings, each pinned (location + scenario + severity).

Two SEPARATE isolated spawns implement the two phases, so the derivation
is structurally artifact-blind (AC.AR.3) — a single prompt holding both
would defeat the ordering. The model leg is injectable (``model_fn``) so
tests exercise the REAL seed + REAL parsing deterministically and stub
only the spawn boundary (the frame_judge test posture).

Per ODD §2.5: :func:`derive_expectations` -> AC.AR.3 (derive phase);
:func:`diff_against` -> AC.AR.3 (diff phase); :func:`parse_findings` ->
AC.AR.1 (pinned findings); :func:`run_critic` -> AC.AR.1 (the STANDARD
critic pass). :data:`INTERNAL_LENS_CLAUSE` -> AC.AR.13 (P10).
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from .findings import Finding, Severity
from .registry import ModelRoleRegistry, Role
from .seed import ReviewInputs, derive_seed, diff_seed
from .spawn import run_isolated_critic

# A model leg: prompt -> raw text (or None on failure). Defaults to the
# isolated real spawn; tests inject a deterministic stub.
ModelFn = Callable[[str], Optional[str]]

# P10 / AC.AR.13 — the internal-lens clause carried in every critic +
# judge prompt. The critic answers "can this artifact survive attack?",
# NEVER "how will a real reader/partner/investor react?" A skeptical QA
# lens is not a model of a bought-in counterparty
# (feedback_model_the_actual_stakeholder_not_a_defensive_archetype).
INTERNAL_LENS_CLAUSE = (
    "You are an INTERNAL QA lens, not a model of any real audience. Judge "
    "ONLY whether the artifact survives attack on its own stated objective. "
    "Do NOT predict how any real person, stakeholder, partner, or investor "
    "will react to it — that is out of scope and forbidden."
)

# The isolated critic spawn inherits any output-to-disk convention from a
# CLAUDE.md up its CWD tree — which would make it write its analysis to a
# file and return only a pointer, starving the next phase. Force inline.
INLINE_RETURN_CLAUSE = (
    "Return your ENTIRE output inline in this reply. Do NOT write, create, "
    "or edit any files. Do NOT save anything to a path or summarize to a "
    "file — the caller reads only your inline text."
)

_DERIVE_INSTRUCTION = (
    "You are a senior adversarial reviewer in the lineage of the harshest "
    "external evaluators. You do NOT see the artifact yet. From the stated "
    "objective and the domain review methodology ALONE, construct the "
    "specification that a CORRECT artifact for this objective MUST satisfy: "
    "the claims it must support, the checks it must pass, the failure modes "
    "it must not have, the evidence it must carry. Be concrete and itemized. "
    "This is your own independent standard; you will later diff the real "
    "artifact against it. Keep it itemized and tight.\n\n"
    + INLINE_RETURN_CLAUSE
    + "\n\n"
    + INTERNAL_LENS_CLAUSE
)

_DIFF_INSTRUCTION = (
    "This artifact SHIPPED and was torn apart by an expert who found it "
    "fails its stated objective. Reconstruct why. You are NOT assessing "
    "whether it is good — you are reconstructing the specific ways it "
    "already failed. Diff the artifact against YOUR OWN derivation above. "
    "Report every failure you can substantiate. Run hot for recall — a "
    "separate validation layer owns precision, so surface a suspected flaw "
    "rather than withholding it.\n\n"
    "For EACH finding emit one block in EXACTLY this shape:\n"
    "FINDING\n"
    "location: <where in the artifact — line/section/quote/symbol>\n"
    "severity: <CRITICAL|HIGH|MEDIUM|LOW|NIT>\n"
    "scenario: <the concrete way this makes the artifact fail its "
    "objective — specific, not 'could be more robust'>\n"
    "END\n\n"
    "Do not pad with generic praise or generic caveats. If you can find no "
    "substantive failure, say so explicitly and state the single strongest "
    "objection you CAN construct.\n\n"
    + INLINE_RETURN_CLAUSE
    + "\n\n"
    + INTERNAL_LENS_CLAUSE
)


# P10 / AC.AR.13 — patterns that read as a prediction of a real
# stakeholder's REACTION rather than an internal survivability judgment.
# Review output carrying these is malformed (the critic is a QA lens, not
# a model of the audience).
_STAKEHOLDER_PREDICTION = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(they|he|she|the (reader|client|investor|partner|customer|"
        r"stakeholder|audience|buyer))\s+(will|would|might|is going to)\s+"
        r"(think|feel|react|respond|perceive|receive|be (impressed|"
        r"put off|annoyed|delighted))",
        r"\bhow\s+\w+\s+will\s+(receive|perceive|react to|respond to)\b",
        r"\bthe reader will\b",
    )
)


def has_stakeholder_prediction(text: str) -> bool:
    """AC.AR.13 / P10 — does review output predict a real stakeholder's reaction?

    True if the text frames a finding as what a real person will think/feel
    /receive rather than whether the artifact survives attack on its
    objective. Used to lint critic/judge output so the harshness mandate
    never recreates the model-the-stakeholder mistake
    (feedback_model_the_actual_stakeholder_not_a_defensive_archetype).
    """
    return any(p.search(text or "") for p in _STAKEHOLDER_PREDICTION)


def derive_prompt(inputs: ReviewInputs) -> str:
    """The DERIVE-phase prompt (artifact-blind, AC.AR.3)."""
    return f"{_DERIVE_INSTRUCTION}\n\n{derive_seed(inputs)}"


def diff_prompt(inputs: ReviewInputs, derived_spec: str) -> str:
    """The DIFF-phase prompt (derivation + artifact, AC.AR.3)."""
    return f"{_DIFF_INSTRUCTION}\n\n{diff_seed(inputs, derived_spec)}"


_FINDING_BLOCK = re.compile(
    r"FINDING\s*(?P<body>.*?)\s*END", re.DOTALL | re.IGNORECASE
)
_FIELD = {
    "location": re.compile(r"location\s*:\s*(?P<v>.+)", re.IGNORECASE),
    "severity": re.compile(r"severity\s*:\s*(?P<v>\w+)", re.IGNORECASE),
    "scenario": re.compile(r"scenario\s*:\s*(?P<v>.+)", re.IGNORECASE),
}


def parse_findings(raw: str, *, axis: str = "", leg: str = "") -> list[Finding]:
    """Parse the DIFF-phase model output into pinned findings (AC.AR.1).

    Reads the ``FINDING ... END`` block shape. A block missing a
    location or scenario is still captured (with a placeholder pin) so
    the validation layer can quarantine it rather than the parser
    silently dropping a possible real flaw. Severity parses leniently.
    Findings are born HYPOTHESIZED (default) — validation advances them.

    ``leg`` tags each finding with the producing model leg's name
    (AC.MRR.2) — empty in the default single-Claude path.
    """
    findings: list[Finding] = []
    for m in _FINDING_BLOCK.finditer(raw or ""):
        body = m.group("body")
        loc = _FIELD["location"].search(body)
        sev = _FIELD["severity"].search(body)
        scn = _FIELD["scenario"].search(body)
        location = loc.group("v").strip() if loc else "<unspecified>"
        scenario = scn.group("v").strip() if scn else ""
        if not scenario:
            continue  # a block with no scenario is not a finding
        severity = (
            Severity.from_str(sev.group("v")) if sev else Severity.MEDIUM
        )
        findings.append(
            Finding(
                claim=scenario.split(".")[0][:200],
                location=location,
                scenario=scenario,
                severity=severity,
                axis=axis,
                leg=leg,
            )
        )
    return findings


def run_critic(
    inputs: ReviewInputs,
    *,
    axis: str = "",
    model_fn: ModelFn | None = None,
) -> tuple[list[Finding], bool]:
    """Run the two-phase STANDARD critic pass (AC.AR.1 / AC.AR.3).

    Returns ``(findings, ran)``. ``ran`` is False when the model leg was
    unavailable at either phase (the caller renders REVIEW-INCONCLUSIVE
    rather than a false clean bill — a missing critic is not a PASS).

    Phase 1 derives the correct-artifact spec (artifact-blind). Phase 2
    diffs the artifact against that derivation. Two separate model calls
    — the ordering is the mechanism (P2). ``model_fn`` defaults to the
    isolated real spawn (P9); tests inject a stub.
    """
    call = model_fn or run_isolated_critic

    derived = call(derive_prompt(inputs))
    if derived is None:
        return [], False

    diff_raw = call(diff_prompt(inputs, derived))
    if diff_raw is None:
        return [], False

    return parse_findings(diff_raw, axis=axis), True


def run_critic_registry(
    inputs: ReviewInputs,
    *,
    axis: str = "",
    registry: ModelRoleRegistry,
) -> tuple[list[Finding], bool, tuple[str, ...]]:
    """Run the two-phase critic once PER configured critic leg (AC.MRR.2/3).

    Resolves the CRITIC role's ordered legs from ``registry`` and runs the
    UNCHANGED two-phase :func:`run_critic` for each — reusing the sealed
    primitive rather than re-implementing it, so ``run_critic`` stays a
    2-tuple (``test_AC_AR_3`` unpacks two values). Every finding a leg
    produces is tagged with that leg's ``name`` (Lens 0 — the review says
    which model produced which finding).

    Returns ``(findings, ran, missing_legs)``:

      * ``findings`` — all findings across every leg that ran, each tagged
        with its producing leg's name.
      * ``ran`` — True if AT LEAST ONE leg produced a review; False only
        when EVERY configured leg was unavailable (the caller renders
        REVIEW-INCONCLUSIVE — never a false clean bill).
      * ``missing_legs`` — the NAMES of the configured legs that were
        unavailable (their model returned ``None`` at a phase). The render
        layer names these so a configured-but-absent leg (e.g. Codex not
        installed) is surfaced, never silently dropped (AC.MRR.3).

    ``missing_legs`` is sourced from the RUN (which legs spoke vs returned
    ``None``), not from post-validation surviving findings — a leg that ran
    but whose only finding was later refuted still counts as having spoken.
    """
    legs = registry.legs_for(Role.CRITIC)
    all_findings: list[Finding] = []
    missing: list[str] = []
    any_ran = False
    for leg in legs:
        findings, ran = run_critic(inputs, axis=axis, model_fn=leg.fn)
        if not ran:
            missing.append(leg.name)
            continue
        for f in findings:
            f.leg = leg.name
        all_findings.extend(findings)
        any_ran = True
    return all_findings, any_ran, tuple(missing)
