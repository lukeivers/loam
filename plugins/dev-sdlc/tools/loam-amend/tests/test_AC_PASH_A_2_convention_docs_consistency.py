"""AC.PASH.A.2 — Convention docs prescribe the same canonical `narrative.target` form.

Per amendment #142 Scope A (closes FIDRAFT 330). The `plan-docs.md`
+ `commit-ladder.md` convention docs prescribe the canonical
`docs/plans/sealed/<slug>.md` form, consistent with the four
plan-author SKILLs.

Plan: docs/plans/amendment-142-plan-author-skill-hygiene-merged.md §4
AC.PASH.A.2; outcome-altitude: false.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

CONVENTION_FILES = [
    "plugins/dev-sdlc/docs/conventions/plan-docs.md",
    "plugins/dev-sdlc/docs/conventions/commit-ladder.md",
]

CANONICAL_FORM = "docs/plans/sealed/<slug>.md"


def test_AC_PASH_A_2_canonical_form_in_every_convention_doc() -> None:
    """Both convention docs prescribe the canonical form."""
    for rel in CONVENTION_FILES:
        path = REPO_ROOT / rel
        assert path.exists(), f"convention doc missing: {rel}"
        text = path.read_text(encoding="utf-8")
        assert CANONICAL_FORM in text, (
            f"convention doc {rel} does NOT prescribe the canonical "
            f"`narrative.target` form `{CANONICAL_FORM}` "
            "(amendment #142 Scope A regression)."
        )


def test_AC_PASH_A_2_consistency_across_all_six_surfaces() -> None:
    """All six surfaces (4 SKILLs + 2 convention docs) name the
    canonical form; no surface prescribes a *different* form as
    the default."""
    all_surfaces = [
        "plugins/dev-sdlc/skills/plan-docs-author/SKILL.md",
        "plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md",
        "plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md",
        "plugins/dev-sdlc/skills/seal-narrative-writer/SKILL.md",
        "plugins/dev-sdlc/docs/conventions/plan-docs.md",
        "plugins/dev-sdlc/docs/conventions/commit-ladder.md",
    ]
    missing = []
    for rel in all_surfaces:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        if CANONICAL_FORM not in text:
            missing.append(rel)
    assert not missing, (
        "Surfaces missing canonical `narrative.target` prescription: "
        f"{missing}. Amendment #142 Scope A requires all six surfaces "
        "to converge on the same form."
    )
