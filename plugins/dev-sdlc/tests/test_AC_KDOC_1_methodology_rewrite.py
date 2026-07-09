"""AC.KDOC.1 — methodology spec rewritten with every
plan-§5-scope-item-3 element present (KEEL adoption program Phase 1).

Leanness guard (converted, amendment #197 / AC.BVG.1, 2026-07-09): the
old `assert n <= 380` absolute line ceiling (raised 360→380 in v1.11.0)
was a brittle exact-value pin — it fired on any legitimate prose growth
and trained the "rebaseline the number to match reality" reflex (Class E
of the 2026-07-08 release-seal near-miss audit). The guard's STATED
intent, Tier-0 across three sources (this doc §10.2, the line-budget-raise
plan, docs/experiments/v1-11-0-hard-smoke.md), was never a line count: it
is *leanness / no return of the dropped 8-lens sprawl*. That intent is now
asserted directly — the seven design lenses (CLAUDE.md Lens 1–7) must not
return as re-absorbed sections — plus the required-element presence below.
The doc may grow freely as long as the lens sprawl does not return
(D-EG.ANTISPRAWL).

Checkable per-element list per the plan's AC table:
spine-as-system; §2.5 forward/reverse leading; altitude tests +
drift-mode catalogue promoted in; banding as evidence grades under
check-kinds with criteria binary; VERIFIED = ran-green-at-SHA +
ASSERTED + extractor mapping note; halt-and-surface; per-criterion
altitude declaration; change-management unbundled; honest ancestry;
KEEL primitive frame + unification table; lean plan-doc standard with
8-lens sections dropped. Plan: docs/plans/keel-adoption-program.md §5.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC = REPO_ROOT / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"


def _text() -> str:
    return SPEC.read_text(encoding="utf-8")


def _flat() -> str:
    """Whitespace-collapsed text so anchors survive line-wrap changes."""
    return re.sub(r"\s+", " ", _text())


# The seven design lenses (CLAUDE.md Lens 1-7). The dropped "mandatory
# per-plan 8-lens sections" (odd-methodology §10.2) are these expositions;
# if the sprawl returned to this spec it would re-introduce their distinctive
# labels — currently zero of them appear here (the spec references the lenses
# only as a pointer: "the design lenses stay at feature-proposal altitude").
_DESIGN_LENS_NAMES = (
    "Claude-leverage-first",
    "Harness + primary-persona",
    "ODD authoring",
    "scope ↔ confidence",
    "Swarming",
    "Principle-conflict",
    "Ruthless Feedback",
)
# 4-of-7 present, or ANY as a markdown header, is the sprawl signature. A lone
# incidental prose mention (< 4, non-header) is not the dropped sprawl.
_SPRAWL_NAME_THRESHOLD = 4


def _design_lens_sprawl_present(text: str) -> bool:
    """True iff the dropped 8-lens design-lens sprawl has returned to *text*.

    Two independent signals (either fires): (1) any design-lens label appears
    as a markdown header — a returned lens SECTION; (2) at least
    ``_SPRAWL_NAME_THRESHOLD`` of the seven labels appear anywhere — a
    re-absorbed exposition. This replaces the brittle absolute line ceiling
    with the leanness property the guard exists to protect (AC.BVG.1).
    """
    flat = re.sub(r"\s+", " ", text)
    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line):
            for name in _DESIGN_LENS_NAMES:
                if name in line:
                    return True
    present = sum(1 for name in _DESIGN_LENS_NAMES if name in flat)
    return present >= _SPRAWL_NAME_THRESHOLD


def test_no_8lens_design_lens_sprawl_returned() -> None:
    """AC.BVG.1 — the leanness property: the dropped 8-lens sprawl has not
    returned to the shipped spec (replaces the old `n <= 380` ceiling)."""
    assert not _design_lens_sprawl_present(_text()), (
        "the dropped 8-lens design-lens sprawl has returned to the "
        "methodology spec (design-lens labels re-absorbed as sections)"
    )


REQUIRED_ELEMENTS = [
    # (element name, distinctive anchor string)
    ("spine documented as the system", "## 0. The spine"),
    ("spine: plan-before-code", "plan-before-code is a hard rule"),
    ("spine: seal-time executed suites + fence", "blast-radius fence"),
    ("§2.5 forward/reverse leading",
     "§2.5 forward/reverse coverage — the leading rule"),
    ("forward direction", "**forward (authoring):**"),
    ("reverse direction", "**reverse (review):**"),
    ("altitude tests promoted in", "§9.1 The four altitudes"),
    ("drift-mode catalogue promoted in", "§9.2 The seven drift modes"),
    ("self-checks promoted in", "§9.3 The five self-checks"),
    ("criteria binary", "true / not-yet-true"),
    ("check-kind mechanical", "**mechanical**"),
    ("check-kind judged", "**judged**"),
    ("check-kind attested", "**attested**"),
    ("VERIFIED = ran green at a known SHA", "ran green at a known SHA"),
    ("assumed-green = ASSERTED", "**ASSERTED** — assumed-green"),
    ("extractor mapping note", "ASSERTED evidence grade"),
    ("halt-and-surface", "halt-and-surface"),
    ("per-criterion altitude declaration",
     "§3.6 Per-criterion altitude declaration"),
    ("mechanism-pinning legitimate when mechanism is the deliverable",
     "legitimate when the mechanism is the deliverable"),
    ("change-management unbundled",
     "ODD is how criteria are written; KEEL is how they are enforced"),
    ("amendment cycle is change-management not methodology",
     "change-management, not part of the authoring methodology"),
    ("ancestry: KAOS", "KAOS"),
    ("ancestry: Ulwick", "Ulwick"),
    ("ancestry: Adzic", "Adzic"),
    ("ancestry: Meyer", "Meyer"),
    ("KEEL lifecycle frame",
     "Capture → Translate → Ratify → Bind → Build → Verify → Deliver"),
    ("Amend user-only", "the AI proposes, never enacts"),
    ("unification table", "| Consumer | Charter (verbatim intent) |"),
    ("plan-doc standard promoted", "§10.2 The plan-doc standard"),
    ("8-lens sections dropped", "8-lens sections are dropped"),
    ("one .S smoke", "`.S` smoke"),
]


@pytest.mark.parametrize(
    "name,anchor", REQUIRED_ELEMENTS, ids=[e[0] for e in REQUIRED_ELEMENTS]
)
def test_required_element_present(name: str, anchor: str) -> None:
    assert anchor in _flat(), f"element missing from rewritten spec: {name}"


# --- AC.BVG.S — outcome-altitude for the leanness conversion ---------------
# outcome-altitude: true. Exercises the converted leanness check on real-shaped
# inputs with no pre-set state — one legitimate-growth input that must PASS and
# one sprawl-return input that must RED. This is the proof the guard now tracks
# its intent rather than a magic line number.

# A legitimately-required feature checklist — the exact shape (a ~13-line §7.x
# resource-check block) that grew the spec 360->373 and tripped the old ceiling.
# It carries no design-lens labels, so leanness is intact.
_LEGIT_GROWTH_BLOCK = """
**§7.7 The example new required check (a legitimate feature checklist).**
Every plan naming a retry budget declares the failure mode it bounds; a
retry cap with no named failure mode is a defect (analogous to the §7.6
cap-bias catch). Retirement criterion: the check retires when the budget
primitive lands. Reviewers flag a retry cap with no named failure mode.
This is required content, not sprawl.
"""

# The dropped 8-lens sprawl returning: the seven design-lens labels re-absorbed
# as full sections (both sprawl signals fire — headers AND >= 4 names present).
_RETURNED_8LENS_SPRAWL = """
## Appendix: the design lenses (every plan answers all seven)

### Lens 1 — Claude-leverage-first
What Claude capability does this lean on or extend?

### Lens 2 — Harness + primary-persona value
Does this reduce the translation burden and add to the toolkit?

### Lens 3 — ODD authoring
Objective + constraints + acceptance criteria; method is the builder's call.

### Lens 4 — Prompt scope ↔ confidence
Tighten scope when confidence in one outcome is high.

### Lens 5 — Swarming
Decompose into subtasks each with a tighter acceptance criterion.

### Lens 6 — Principle-conflict resolution
Name the conflict, name the signals, make the call, surface if non-obvious.

### Lens 7 — Ruthless Feedback
Name the disagreement, the evidence, the alternative.
"""


def test_AC_BVG_S_leanness_passes_legitimate_growth() -> None:
    """A legitimately-grown spec (real doc + a new required feature checklist)
    PASSES the converted leanness check — the old line ceiling would have
    false-RED'd here (this is the 360->380 treadmill removed)."""
    grown = _text() + _LEGIT_GROWTH_BLOCK
    assert not _design_lens_sprawl_present(grown)


def test_AC_BVG_S_leanness_reds_on_returned_sprawl() -> None:
    """The dropped 8-lens sprawl returning (real doc + re-absorbed design-lens
    sections) REDs the converted leanness check — the property the guard
    actually protects, caught structurally rather than by line count."""
    bloated = _text() + _RETURNED_8LENS_SPRAWL
    assert _design_lens_sprawl_present(bloated)
