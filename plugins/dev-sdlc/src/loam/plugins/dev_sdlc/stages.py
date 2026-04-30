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
      - methodology == "odd" → `_check_odd_artefact`.
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
        return _check_odd_artefact(text)
    return _check_minimal_artefact(text, methodology=methodology)


def supported_methodologies() -> Sequence[str]:
    """Public accessor for `METHODOLOGIES` (test-friendly)."""
    return METHODOLOGIES
