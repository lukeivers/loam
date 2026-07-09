"""AC.KDOC.1 — methodology spec rewritten ≤380 lines with every
plan-§5-scope-item-3 element present (KEEL adoption program Phase 1).

Line budget raised 360 → 380 in v1.11.0 (amendment
dev-sdlc-kdoc-methodology-line-budget-raise, AC.MSLB.1) to admit the
recall-volume AC.RVL.8 cap-bias checklist (§7.6 + reviewer item 15).

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


# Budget raised 360 -> 380 (v1.11.0, amendment dev-sdlc-kdoc-methodology-line-budget-raise,
# AC.MSLB.1): the recall-volume reshape's AC.RVL.8 cap-bias checklist (§7.6 +
# reviewer item 15 in odd-methodology.md) is required content that grew the spec
# 360 -> 373. The guard's intent is leanness / no return of the dropped 8-lens
# sprawl; a ~13-line legitimately-required feature checklist is not that bloat, so
# the bound admits it with a little headroom while still catching real bloat.
def test_spec_at_most_380_lines() -> None:
    n = len(_text().splitlines())
    assert n <= 380, f"rewritten spec is {n} lines (> 380)"


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
