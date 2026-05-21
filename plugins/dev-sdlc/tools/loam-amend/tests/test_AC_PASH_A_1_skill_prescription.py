"""AC.PASH.A.1 — Plan-author SKILLs prescribe canonical `narrative.target` form.

Per amendment #142 Scope A (closes FIDRAFT 330). A fresh persona/agent
following the plan-author SKILLs to author a new manifest MUST emit
`narrative.target: docs/plans/sealed/<slug>.md` by default — NOT a
component name (the #138 bug shape) NOR the pre-T1.4 legacy form
`framework/<comp>/seals/SEAL_COMMIT.<slug>`.

This is a SKILL-prose verification: greps the four plan-author SKILL
files for the canonical-form prescription string + asserts the legacy
form is no longer the prescribed default (still allowed as
back-compat, but not the default for new amendments).

Plan: docs/plans/amendment-142-plan-author-skill-hygiene-merged.md §4
AC.PASH.A.1; outcome-altitude: false.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

# The four plan-author SKILLs that authoring agents read at manifest-
# authoring time (per plan-doc §5 fence + Scope A surface list).
SKILL_FILES = [
    "plugins/dev-sdlc/skills/plan-docs-author/SKILL.md",
    "plugins/dev-sdlc/skills/plan-before-code-author/SKILL.md",
    "plugins/dev-sdlc/skills/loam-amend-cycle/SKILL.md",
    "plugins/dev-sdlc/skills/seal-narrative-writer/SKILL.md",
]

# The canonical-form prescription string. Each SKILL must contain
# `docs/plans/sealed/<slug>.md` literally (the canonical post-T1.4
# archive-on-seal target).
CANONICAL_FORM = "docs/plans/sealed/<slug>.md"


def test_AC_PASH_A_1_canonical_form_in_every_plan_author_skill() -> None:
    """Every plan-author SKILL prescribes the canonical
    `narrative.target` form."""
    for rel in SKILL_FILES:
        path = REPO_ROOT / rel
        assert path.exists(), f"SKILL file missing: {rel}"
        text = path.read_text(encoding="utf-8")
        assert CANONICAL_FORM in text, (
            f"SKILL {rel} does NOT prescribe the canonical "
            f"`narrative.target` form `{CANONICAL_FORM}` "
            "(amendment #142 Scope A regression)."
        )


def test_AC_PASH_A_1_legacy_form_not_prescribed_as_default() -> None:
    """Legacy form `<component>/seals/SEAL_COMMIT.<slug>` is allowed
    as back-compat but NOT prescribed as the default.

    Detection: the SKILL prose must NOT contain the legacy form WITHOUT
    also containing an explicit "back-compat" / "legacy" qualifier
    nearby (within the same paragraph or within ~500 chars). The
    canonical-form prescription wins.
    """
    legacy_form = "plugins/<plugin>/seals/SEAL_COMMIT.<slug>"
    for rel in SKILL_FILES:
        path = REPO_ROOT / rel
        text = path.read_text(encoding="utf-8")
        # If the legacy form appears at all, it must appear alongside
        # a "back-compat" / "legacy" / "pre-T1.4" qualifier within the
        # same paragraph or sentence (the qualifier disambiguates
        # legacy-as-back-compat from legacy-as-default).
        if legacy_form not in text:
            continue
        # Walk every occurrence; each must be near a back-compat tell.
        cursor = 0
        while True:
            idx = text.find(legacy_form, cursor)
            if idx == -1:
                break
            # Look in a window of ~500 chars around the occurrence for
            # the back-compat qualifier.
            window = text[max(0, idx - 500):idx + 500]
            assert any(
                tell in window.lower()
                for tell in ("back-compat", "back compat", "legacy", "pre-t1.4")
            ), (
                f"SKILL {rel} contains the legacy form "
                f"`{legacy_form}` without a back-compat / legacy "
                "qualifier nearby; amendment #142 Scope A regression "
                "— the canonical form must be the default."
            )
            cursor = idx + len(legacy_form)
