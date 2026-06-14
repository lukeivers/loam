"""Stage shape + methodology definitions + per-stage gate logic.

Per plan §4 AC.OSS-M6.4 + §11 finding #9: the 5-stage shape is
shared across methodologies; the gate's "objective + AC" detection
varies per methodology.

ODD: structural — frontmatter `objective:` + `acceptance_criteria:`
or `## Objective` + `## Acceptance Criteria` section headings.

TDD/BDD/adhoc: at v0.1.0 the gate checks artefact existence + a
methodology-specific minimal sentinel (per plan §10 D-build.M6.7).
The strict per-methodology parser is deferred to v0.2 (out of scope
per plan §5).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import yaml


STAGES: tuple[str, ...] = ("research", "spec", "plan", "build", "review")
"""The 5-stage workflow per plan §1 + AC.OSS-M6.2."""


METHODOLOGIES: tuple[str, ...] = ("odd", "tdd", "bdd", "adhoc")
"""Supported methodology strings per plan §1 + AC.OSS-M6.3."""


@dataclass(frozen=True)
class GateOutcome:
    """Structured result of a per-stage gate check.

    `passed=True` iff all detection rules satisfy. `reason` is a
    stable code (per `errors.StageGateFailedError`) when False; None
    when True.
    """

    passed: bool
    reason: str | None = None
    detail: str | None = None


def stage_index(stage: str) -> int:
    """Return zero-based index of *stage* in `STAGES`. -1 if unknown."""
    try:
        return STAGES.index(stage)
    except ValueError:
        return -1


def next_stage(stage: str) -> str | None:
    """Return the stage that follows *stage* in `STAGES`, or None when
    *stage* is the last (terminal) stage."""
    idx = stage_index(stage)
    if idx < 0 or idx >= len(STAGES) - 1:
        return None
    return STAGES[idx + 1]


def is_terminal_stage(stage: str) -> bool:
    """Return True iff *stage* is the last stage in `STAGES` (i.e.
    advancing from it raises `TerminalStageError`)."""
    return stage == STAGES[-1]


def artefact_path(project_root: Path, stage: str, slug: str) -> Path:
    """Convention: `<project>/<stage>/<slug>.md` (per plan §1 + §4
    AC.OSS-M6.2)."""
    return project_root / stage / f"{slug}.md"


# ---------------------------------------------------------------------
# ODD-shape gate — frontmatter or section-heading detection.
# ---------------------------------------------------------------------


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_OBJECTIVE_HEADING_RE = re.compile(
    r"^##\s+Objective\s*$", re.MULTILINE | re.IGNORECASE
)
_AC_HEADING_RE = re.compile(
    r"^##\s+Acceptance\s+Criteria\s*$", re.MULTILINE | re.IGNORECASE
)


def _check_odd_artefact(text: str) -> GateOutcome:
    """Return GateOutcome for an ODD-methodology artefact body.

    Detection rules (any one path passes; any one missing fails):

      1. Objective: frontmatter `objective:` field with non-empty
         string OR a `## Objective` section heading whose body
         (next non-blank prose) is non-empty.
      2. ACs: frontmatter `acceptance_criteria:` non-empty list OR
         a `## Acceptance Criteria` section heading followed by at
         least one bullet line (`- ...`).
    """
    has_objective = False
    has_ac = False

    fm_match = _FRONTMATTER_RE.match(text)
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
        except yaml.YAMLError:
            fm = {}
        if isinstance(fm, dict):
            objective_val = fm.get("objective")
            if isinstance(objective_val, str) and objective_val.strip():
                has_objective = True
            acs = fm.get("acceptance_criteria")
            if isinstance(acs, list) and len(acs) >= 1:
                has_ac = True

    # Section-heading fall-through (only checked if frontmatter
    # didn't satisfy the rule — additive detection).
    if not has_objective:
        m = _OBJECTIVE_HEADING_RE.search(text)
        if m:
            after = text[m.end() :]
            # Find next non-blank prose line that isn't itself a
            # heading. Non-empty -> satisfied.
            for line in after.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    break
                has_objective = True
                break

    if not has_ac:
        m = _AC_HEADING_RE.search(text)
        if m:
            after = text[m.end() :]
            for line in after.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    break
                if stripped.startswith("-") or stripped.startswith("*"):
                    has_ac = True
                    break

    if not has_objective:
        return GateOutcome(
            passed=False,
            reason="no_objective",
            detail=(
                "Artefact has no recognisable objective. Add an "
                "`objective:` frontmatter field or a `## Objective` "
                "section heading with prose."
            ),
        )
    if not has_ac:
        return GateOutcome(
            passed=False,
            reason="no_ac",
            detail=(
                "Artefact has no recognisable acceptance criteria. "
                "Add an `acceptance_criteria:` frontmatter list or a "
                "`## Acceptance Criteria` section heading with at "
                "least one bullet."
            ),
        )
    return GateOutcome(passed=True)


# ---------------------------------------------------------------------
# TDD / BDD / adhoc gate — minimal-sentinel checks.
# ---------------------------------------------------------------------


def _check_minimal_artefact(
    text: str, *, methodology: str
) -> GateOutcome:
    """Per-methodology minimal-sentinel check.

    Rules (per plan §10 D-build.M6.7 + §11 finding #9):

      - TDD: artefact mentions tests (substring `test` case-insensitive)
        AND has at least one bullet (`- ...`).
      - BDD: artefact mentions a scenario block (heading or text
        containing `scenario` case-insensitive) AND has at least one
        Given/When/Then keyword.
      - adhoc: artefact is non-empty (any non-whitespace content).
    """
    stripped = text.strip()
    if not stripped:
        return GateOutcome(
            passed=False,
            reason="no_objective",
            detail="Artefact is empty. Author at least one prose line.",
        )

    if methodology == "tdd":
        has_test_word = re.search(r"\btest", text, re.IGNORECASE) is not None
        has_bullet = any(
            ln.strip().startswith(("-", "*"))
            for ln in text.splitlines()
        )
        if not has_test_word:
            return GateOutcome(
                passed=False,
                reason="no_objective",
                detail=(
                    "TDD artefact has no recognisable test reference. "
                    "Mention tests (e.g. `## Tests` or a sentence "
                    "containing 'test')."
                ),
            )
        if not has_bullet:
            return GateOutcome(
                passed=False,
                reason="no_ac",
                detail=(
                    "TDD artefact has no bullet list. Add at least "
                    "one `- ...` test entry."
                ),
            )
        return GateOutcome(passed=True)

    if methodology == "bdd":
        has_scenario = re.search(
            r"\bscenario\b", text, re.IGNORECASE
        ) is not None
        has_gwt = re.search(
            r"\b(given|when|then)\b", text, re.IGNORECASE
        ) is not None
        if not has_scenario:
            return GateOutcome(
                passed=False,
                reason="no_objective",
                detail=(
                    "BDD artefact has no recognisable scenario. Add "
                    "a `## Scenario` heading or scenario reference."
                ),
            )
        if not has_gwt:
            return GateOutcome(
                passed=False,
                reason="no_ac",
                detail=(
                    "BDD artefact has no Given/When/Then keywords. "
                    "Add at least one `Given ...`, `When ...`, or "
                    "`Then ...` line."
                ),
            )
        return GateOutcome(passed=True)

    # adhoc
    return GateOutcome(passed=True)


# ---------------------------------------------------------------------
# Four-research-question gate (AC.PFSE.3 — principle-foundation-
# structural-enforcement). A research-plan that omits any of the four
# required research questions cannot advance; the gate refuses on any
# empty question. The four questions are the lens research questions
# canonicalised in docs/FUTURE_IDEAS.md §"Step 3":
#   1. Claude-leverage — what Claude capabilities does this lean on /
#      extend / replace?
#   2. Primary-persona — does this reduce the user's translation burden?
#   3. Harness — does this add to the primary persona's toolkit?
#   4. ODD — objectives + constraints + acceptance without prescribing
#      method?
# Detection is deterministic (section-heading keyword + non-empty body);
# NO LLM (the section-presence check is a parse, plan §6 / Primitive-
# check).
#
# SCOPE (feedback_odd_cdc_scope): the four lens questions are a
# loam-FEATURE-research artefact — they reference VALUE_PROPOSITION, the
# primary persona, and the harness, which are loam-internal. They are
# NOT universal to every ODD project (a NORMAL-USE user's ODD research
# has nothing to do with loam's lenses). The gate is therefore OPT-IN: a
# research artefact gated by the four questions declares itself a
# lens-research plan via a `lens_research: true` frontmatter flag. A
# research artefact without that flag is a generic ODD research stage
# and is NOT subject to the four-question gate (it still passes the
# objective + AC gate). This keeps AC.OSS-M6.4's generic-ODD contract
# intact while giving AC.PFSE.3 teeth on the plans the questions govern.
# ---------------------------------------------------------------------

# Each tuple: (stable id, the alternation of keyword phrases that mark
# the question's section heading). A heading line matching any phrase
# (case-insensitive) opens the section; the section is satisfied iff a
# non-blank, non-heading prose/bullet line follows before the next
# heading.
_RESEARCH_QUESTION_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("claude_leverage", ("claude-leverage", "claude leverage")),
    ("primary_persona", ("primary-persona", "primary persona")),
    ("harness", ("harness",)),
    ("odd", ("odd",)),
)

_HEADING_LINE_RE = re.compile(r"^(#{2,6})\s+(.*\S)\s*$", re.MULTILINE)


def _is_lens_research_plan(text: str) -> bool:
    """True iff the artefact opts into the four-lens-research gate via a
    `lens_research: true` frontmatter flag. Generic ODD research plans
    omit the flag and are NOT subject to the four-question gate."""
    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return False
    try:
        fm = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError:
        return False
    if not isinstance(fm, dict):
        return False
    val = fm.get("lens_research")
    return val is True or (
        isinstance(val, str) and val.strip().lower() in ("true", "yes")
    )


def _heading_has_nonempty_body(text: str, start: int) -> bool:
    """True iff a non-blank, non-heading line follows ``start`` before
    the next heading."""
    after = text[start:]
    for line in after.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return False
        return True
    return False


def _check_research_questions(text: str) -> GateOutcome:
    """Return GateOutcome for the four-research-question gate.

    Walks the artefact's `##`..`######` headings; for each required
    question, the FIRST heading whose text contains one of the question's
    keyword phrases must carry a non-empty body. Any required question
    with no matching heading, or a matching heading with an empty body,
    fails the gate (reason ``missing_research_question``).
    """
    headings = [
        (m.start(), m.end(), m.group(2).lower())
        for m in _HEADING_LINE_RE.finditer(text)
    ]
    missing: list[str] = []
    for qid, phrases in _RESEARCH_QUESTION_MARKERS:
        satisfied = False
        for _start, end, heading_text in headings:
            if any(p in heading_text for p in phrases):
                if _heading_has_nonempty_body(text, end):
                    satisfied = True
                break
        if not satisfied:
            missing.append(qid)
    if missing:
        return GateOutcome(
            passed=False,
            reason="missing_research_question",
            detail=(
                "Research plan is missing or has an empty section for "
                "the required research question(s): "
                + ", ".join(missing)
                + ". Every research plan must answer all four lens "
                "questions (Claude-leverage / Primary-persona / Harness "
                "/ ODD) with a non-empty section before it can advance "
                "(AC.PFSE.3; docs/FUTURE_IDEAS.md Step 3)."
            ),
        )
    return GateOutcome(passed=True)


def check_gate(
    *,
    project_root: Path,
    slug: str,
    stage: str,
    methodology: str,
) -> GateOutcome:
    """Run the structural gate against the project's current stage
    artefact (per plan §4 AC.OSS-M6.4).

    Detection routes:
      - methodology == "odd" → `_check_odd_artefact`, AND for the
        `research` stage, the four-research-question gate (AC.PFSE.3).
      - methodology in {"tdd","bdd","adhoc"} → `_check_minimal_artefact`.
    """
    path = artefact_path(project_root, stage, slug)
    if not path.exists():
        return GateOutcome(
            passed=False,
            reason="artefact_not_found",
            detail=(
                f"Expected artefact at {path.as_posix()} but it does "
                f"not exist. Author the {stage} artefact before "
                f"advancing."
            ),
        )
    text = path.read_text(encoding="utf-8")
    if methodology == "odd":
        outcome = _check_odd_artefact(text)
        if not outcome.passed:
            return outcome
        # The research stage additionally requires the four lens
        # research questions (AC.PFSE.3) WHEN the artefact opts into the
        # lens-research convention (`lens_research: true`). Generic ODD
        # research is not gated by the four questions
        # (feedback_odd_cdc_scope). Other ODD stages are never gated.
        if stage == "research" and _is_lens_research_plan(text):
            return _check_research_questions(text)
        return outcome
    return _check_minimal_artefact(text, methodology=methodology)


def supported_methodologies() -> Sequence[str]:
    """Public accessor for `METHODOLOGIES` (test-friendly)."""
    return METHODOLOGIES
