"""AC.PROMOTE.10 — Quarterly-review trigger via on-demand only at MVP.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.10: the SKILL body
specifies two triggers — primary on-demand
(`/skill-promotion-review` invocation OR persona auto-recognition
of trigger phrases) + secondary owner-self-discipline 90-day
cadence. NO auto-fire from `framework/scope-of-work/` at MVP;
auto-fire deferred to v0.2.x.
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


def test_body_mentions_on_demand_trigger() -> None:
    """Body must specify on-demand `/skill-promotion-review`
    invocation as the primary trigger."""
    body = _body()
    assert "/skill-promotion-review" in body, (
        "skill-promotion-review: body must specify the on-demand "
        "`/skill-promotion-review` slash invocation as a trigger."
    )
    body_lower = body.lower()
    assert "on-demand" in body_lower or "on demand" in body_lower, (
        "skill-promotion-review: body must frame the primary "
        "trigger as `on-demand`."
    )


def test_body_mentions_90_day_self_discipline_cadence() -> None:
    """Body must mention the 90-day owner-self-discipline cadence."""
    body = _body()
    body_lower = body.lower()
    assert "90 day" in body_lower or "90-day" in body_lower, (
        "skill-promotion-review: body must mention the 90-day "
        "owner-self-discipline cadence."
    )
    assert (
        "self-discipline" in body_lower or "self discipline" in body_lower
    ), (
        "skill-promotion-review: body must frame the 90-day cadence "
        "as owner-`self-discipline` (NOT auto-fire at MVP)."
    )


def test_body_disclaims_scope_of_work_auto_fire_at_mvp() -> None:
    """Body must explicitly disclaim auto-fire via
    `framework/scope-of-work/` at MVP; deferred to v0.2.x."""
    body = _body()
    body_lower = body.lower()
    # Acceptance: body mentions `scope-of-work` AND defers auto-fire
    # to v0.2.x.
    assert "scope-of-work" in body_lower or "scope_of_work" in body_lower, (
        "skill-promotion-review: body must mention `scope-of-work` "
        "framing the auto-fire deferral target."
    )
    assert "v0.2.x" in body or "auto-fire" in body_lower, (
        "skill-promotion-review: body must defer auto-fire (calendar/"
        "cron trigger) to v0.2.x."
    )


def test_body_mentions_filesystem_mtime_for_90_day_lookup() -> None:
    """Body must specify the 90-day cadence uses filesystem mtime
    on prior review artefacts under `.scratch/claude-output/`
    (avoids scope-of-work read; mitigates §6.5)."""
    body = _body()
    body_lower = body.lower()
    assert "mtime" in body_lower, (
        "skill-promotion-review: body must specify filesystem "
        "`mtime` lookup for the 90-day cadence (not scope-of-work)."
    )
