"""AC.PASH.C.1 — Methodology docs prescribe source-edit-commit-before-apply.

Per amendment #142 Scope C (closes FIDRAFT 334). The dev-sdlc
methodology docs (`commit-ladder.md` + `amendment-cycle.md`) AND
`loam-amend-cycle/SKILL.md` explicitly name "commit source edits
BEFORE `loam amend apply`" as a step, in a form a fresh agent
reading the doc end-to-end could not miss.

Plan: docs/plans/amendment-142-plan-author-skill-hygiene-merged.md §4
AC.PASH.C.1; outcome-altitude: false.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

# The three surfaces named by AC.PASH.C.1 + Scope C fence.
SURFACES = [
    "plugins/dev-sdlc/docs/conventions/commit-ladder.md",
    "plugins/dev-sdlc/docs/conventions/amendment-cycle.md",
    "plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md",
]


def test_AC_PASH_C_1_explicit_before_apply_ordering_in_every_surface() -> None:
    """Each surface explicitly names the ordering."""
    # Regex matches "BEFORE ... loam amend apply" with optional
    # backticks + minor whitespace variation. Case-insensitive on
    # "before" since the prose may capitalise differently per
    # context, but the canonical form is uppercase "BEFORE" for
    # emphasis.
    ordering_pattern = re.compile(
        r"before\s+(?:step\s+\d+\s*[—-]\s*)?[`']?loam\s+amend\s+apply",
        re.IGNORECASE,
    )
    for rel in SURFACES:
        path = REPO_ROOT / rel
        assert path.exists(), f"methodology surface missing: {rel}"
        text = path.read_text(encoding="utf-8")
        assert ordering_pattern.search(text), (
            f"surface {rel} does NOT carry the explicit "
            "`before ... loam amend apply` ordering prescription "
            "(amendment #142 Scope C regression)."
        )


def test_AC_PASH_C_1_committed_HEAD_invariant_named() -> None:
    """Each surface names the `committed HEAD` invariant (the
    technical *reason* the ordering matters)."""
    for rel in SURFACES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "committed HEAD" in text, (
            f"surface {rel} does NOT name the `committed HEAD` "
            "invariant; the ordering prescription must explain WHY "
            "(apply runs against committed HEAD)."
        )


def test_AC_PASH_C_1_apply_py_158_anchor_cited() -> None:
    """The methodology docs cite the source anchor (`apply.py:158`)
    or a path-only reference to the verified location for the
    committed-HEAD invariant — reachability check for the
    Tier-0 evidence."""
    # At least ONE of the surfaces must cite the source anchor.
    # (The SKILLs/convention docs need not all carry the citation;
    # one is sufficient for a curious reader to follow up.)
    anchor_pattern = re.compile(
        r"apply\.py(?::\d+|\b)|loam_amend/commands/apply",
        re.IGNORECASE,
    )
    found_anchor = False
    for rel in SURFACES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        if anchor_pattern.search(text):
            found_anchor = True
            break
    assert found_anchor, (
        "No methodology surface cites the source anchor "
        "(`apply.py:158` or equivalent) for the committed-HEAD "
        "invariant; the prescription should carry a Tier-0 pointer."
    )
