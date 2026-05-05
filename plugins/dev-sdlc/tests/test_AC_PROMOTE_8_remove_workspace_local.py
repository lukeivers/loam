"""AC.PROMOTE.8 — Remove workspace-local copy post-promotion.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.8: after graduation
seals, the SKILL body instructs the persona to delete the
workspace-local SKILL.md and replace it with a single-line
pointer.md. The original SKILL.md MUST be removed; leaving both
copies in place would cause Anthropic's filesystem-discovery to
auto-load both.
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


def test_body_mentions_delete_workspace_local_skill_md() -> None:
    """Body must instruct the persona to delete the workspace-local
    SKILL.md after promotion."""
    body = _body()
    body_lower = body.lower()
    assert "delete" in body_lower, (
        "skill-promotion-review: body must instruct the persona to "
        "`delete` the workspace-local SKILL.md post-promotion."
    )


def test_body_mentions_pointer_md_replacement() -> None:
    """Body must specify pointer.md as the replacement file."""
    body = _body()
    assert "pointer.md" in body, (
        "skill-promotion-review: body must name `pointer.md` as the "
        "replacement marker for the deleted workspace-local SKILL.md."
    )


def test_body_describes_pointer_md_content() -> None:
    """Body must describe the pointer.md single-line content
    (target path + commit SHA reference)."""
    body = _body()
    body_lower = body.lower()
    assert "graduated" in body_lower, (
        "skill-promotion-review: body must describe pointer.md "
        "content using the verb `graduated`."
    )
    # Acceptance: the pointer.md content references either the
    # target plugin path or the commit SHA.
    assert "commit" in body_lower or "sha" in body_lower, (
        "skill-promotion-review: pointer.md content must reference "
        "the graduation commit SHA."
    )


def test_body_disclaims_duplicate_auto_load_risk() -> None:
    """Body must explicitly warn about Anthropic filesystem-
    discovery auto-loading both copies if the workspace-local SKILL.md
    is left in place."""
    body = _body()
    body_lower = body.lower()
    assert "auto-load" in body_lower or "auto load" in body_lower, (
        "skill-promotion-review: body must mention `auto-load` "
        "framing the duplicate-discovery risk."
    )
    # Acceptance: body mentions either "duplicate" / "ambiguous" /
    # "both copies" framing the risk.
    assert (
        "both copies" in body_lower
        or "duplicate" in body_lower
        or "ambiguous" in body_lower
    ), (
        "skill-promotion-review: body must explicitly disclaim the "
        "duplicate auto-load risk (Anthropic filesystem discovery)."
    )
