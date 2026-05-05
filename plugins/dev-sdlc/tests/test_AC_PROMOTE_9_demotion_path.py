"""AC.PROMOTE.9 — Demotion path per layered-skills §4.4.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.9: the SKILL body
includes a `Demotion path` sub-section in §"How the persona
applies it". The persona surfaces "skill X has fired N times
since promotion at <commit-SHA>; demote or retire?". On demote:
corrective amendment cycle moves the SKILL.md back to
workspace-local. On retire: deletes entirely. Both rare; treated
as explicit visible amendment.
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


def test_body_mentions_demote_action() -> None:
    """Body must mention `demote` as a named action."""
    body = _body()
    body_lower = body.lower()
    assert "demote" in body_lower, (
        "skill-promotion-review: body must mention `demote` as a "
        "named demotion-path action."
    )


def test_body_mentions_retire_action() -> None:
    """Body must mention `retire` as a named action."""
    body = _body()
    body_lower = body.lower()
    assert "retire" in body_lower, (
        "skill-promotion-review: body must mention `retire` as a "
        "named demotion-path action."
    )


def test_body_mentions_corrective_amendment() -> None:
    """Demotion runs as a corrective amendment cycle (not silent
    deletion)."""
    body = _body()
    body_lower = body.lower()
    assert "corrective" in body_lower, (
        "skill-promotion-review: body must frame demotion as a "
        "`corrective` amendment cycle."
    )


def test_body_frames_demotion_as_rare_explicit() -> None:
    """Demotion must be framed as rare + explicit visible
    amendment, not routine."""
    body = _body()
    body_lower = body.lower()
    assert "rare" in body_lower, (
        "skill-promotion-review: body must frame demotion as `rare`."
    )
    # Acceptance: body uses one of explicit / visible / not-routine
    # framing. The plan-doc §3 AC.PROMOTE.9 names "explicit visible
    # amendment" verbatim.
    assert "explicit" in body_lower, (
        "skill-promotion-review: body must frame demotion as "
        "`explicit` visible amendment."
    )


def test_body_mentions_n_times_since_promotion_framing() -> None:
    """Body must mention the firing-count framing per layered-skills
    §4.4: 'skill X has fired N times since promotion'."""
    body = _body()
    body_lower = body.lower()
    # Acceptance: body mentions "fired" (verb) AND the count
    # framing ("N times" or equivalent).
    assert "fired" in body_lower, (
        "skill-promotion-review: body must use the `fired` verb "
        "framing the firing-count signal."
    )
    assert (
        "N times" in body
        or "n times" in body_lower
        or "since promotion" in body_lower
    ), (
        "skill-promotion-review: body must reference the "
        "firing-count or `since promotion` framing per layered-skills "
        "§4.4."
    )
