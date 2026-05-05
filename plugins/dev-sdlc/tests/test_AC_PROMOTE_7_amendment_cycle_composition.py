"""AC.PROMOTE.7 — Land-in-target via amendment cycle composition.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.7: graduation composes
wholesale on the `loam-amend-cycle` SKILL — the SKILL body must
delegate to `loam-amend-cycle` for the amendment ladder (move
SKILL.md → feat commit → loam amend apply → loam amend seal),
NOT re-implement.
"""

from __future__ import annotations

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "skill-promotion-review"
    / "SKILL.md"
)


def _body() -> str:
    text = SKILL_PATH.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"{SKILL_PATH}: frontmatter parse failed."
    return match.group(2)


def test_body_references_loam_amend_cycle_skill() -> None:
    """Body must reference the `loam-amend-cycle` SKILL as the
    composition target for graduation."""
    body = _body()
    assert "loam-amend-cycle" in body, (
        "skill-promotion-review: body must reference the "
        "`loam-amend-cycle` SKILL as the graduation amendment-cycle "
        "delegate."
    )


def test_body_describes_skill_md_move() -> None:
    """Body must describe moving SKILL.md from workspace-local to
    target plugin path."""
    body = _body()
    body_lower = body.lower()
    assert "move" in body_lower, (
        "skill-promotion-review: body must describe `move` of the "
        "SKILL.md from workspace-local to target plugin."
    )
    assert "plugins/loam-skills/" in body, (
        "skill-promotion-review: body must name "
        "`plugins/loam-skills/` as the HARNESS-GENERAL graduation "
        "target."
    )
    assert "plugins/dev-sdlc/skills/" in body, (
        "skill-promotion-review: body must name "
        "`plugins/dev-sdlc/skills/` as the DEV-SPECIFIC graduation "
        "target."
    )


def test_body_names_feat_commit_subject_form() -> None:
    """Body must specify the feat-commit subject form for
    graduation."""
    body = _body()
    assert "feat(" in body, (
        "skill-promotion-review: body must specify the conventional-"
        "commit `feat(<plugin>):` subject form."
    )
    assert "promote" in body.lower(), (
        "skill-promotion-review: body must use the verb `promote` "
        "in the graduation feat-commit subject form."
    )


def test_body_names_apply_and_seal_steps() -> None:
    """Body must name the `loam amend apply` + `loam amend seal`
    steps as the bookkeeping mechanism."""
    body = _body()
    assert "loam amend apply" in body, (
        "skill-promotion-review: body must name `loam amend apply` "
        "as the apply step."
    )
    assert "loam amend seal" in body, (
        "skill-promotion-review: body must name `loam amend seal` "
        "as the seal step."
    )


def test_body_disclaims_reimplementation_of_amendment_ladder() -> None:
    """Body must explicitly delegate the amendment ladder; not
    re-implement step-by-step."""
    body = _body()
    body_lower = body.lower()
    # Acceptance: body uses `delegate` framing, OR explicitly says
    # "do not re-implement" / "compose on" / "do NOT re-implement".
    assert (
        "delegate" in body_lower
        or "compose" in body_lower
        or "re-implement" in body_lower
        or "reimplement" in body_lower
    ), (
        "skill-promotion-review: body must use composition-framing "
        "(`delegate` / `compose` / disclaim `re-implement`) for the "
        "amendment ladder."
    )
