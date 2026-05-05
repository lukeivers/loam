"""AC.PROMOTE.2 — 3-signal MVP body specifies primary gates.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.2: the SKILL body
enumerates the 3 primary signals per Decision L (Categorization
+ Quality + Conflict primary; Reusability + Tests + Usage
secondary non-blocking). Each primary signal must name its
vocabulary; secondary signals must be framed as non-blocking.
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


def test_body_names_all_three_primary_signals() -> None:
    """Categorization + Quality + Conflict are named explicitly."""
    body = _body()
    for signal in ("Categorization", "Quality", "Conflict"):
        assert signal in body, (
            f"skill-promotion-review: body must name primary signal "
            f"`{signal}` (3-signal MVP per Decision L)."
        )


def test_body_names_categorization_vocabulary() -> None:
    """Categorization vocabulary: HARNESS-GENERAL / DEV-SPECIFIC /
    PROJECT-SPECIFIC."""
    body = _body()
    for value in ("HARNESS-GENERAL", "DEV-SPECIFIC", "PROJECT-SPECIFIC"):
        assert value in body, (
            f"skill-promotion-review: body must name Categorization "
            f"value `{value}`."
        )


def test_body_names_quality_vocabulary() -> None:
    """Quality vocabulary: PASS / FAIL / NEEDS-REVISION."""
    body = _body()
    for value in ("PASS", "FAIL", "NEEDS-REVISION"):
        assert value in body, (
            f"skill-promotion-review: body must name Quality value "
            f"`{value}`."
        )


def test_body_names_conflict_vocabulary() -> None:
    """Conflict vocabulary: NO-CONFLICT / DUPLICATE / WIDER /
    NARROWER / ADJACENT."""
    body = _body()
    for value in (
        "NO-CONFLICT",
        "DUPLICATE",
        "WIDER",
        "NARROWER",
        "ADJACENT",
    ):
        assert value in body, (
            f"skill-promotion-review: body must name Conflict value "
            f"`{value}`."
        )


def test_body_names_secondary_signals() -> None:
    """Secondary signals: Reusability + Tests + Usage."""
    body = _body()
    for signal in ("Reusability", "Tests", "Usage"):
        assert signal in body, (
            f"skill-promotion-review: body must mention secondary "
            f"signal `{signal}`."
        )


def test_body_frames_secondary_as_non_blocking() -> None:
    """Decision L: secondary signals are non-blocking. Body must
    explicitly state secondary signals do NOT block a promotion
    recommendation that the primary signals pass."""
    body = _body()
    body_lower = body.lower()
    # Acceptance: body mentions both "secondary" and "non-blocking"
    # (or equivalent "do not block" / "don't block" phrasing).
    assert "secondary" in body_lower, (
        "skill-promotion-review: body must frame Reusability + "
        "Tests + Usage explicitly as `secondary` signals."
    )
    assert (
        "non-blocking" in body_lower
        or "do not block" in body_lower
        or "don't block" in body_lower
        or "do NOT block" in body
    ), (
        "skill-promotion-review: body must frame secondary signals "
        "as non-blocking (per Decision L)."
    )
