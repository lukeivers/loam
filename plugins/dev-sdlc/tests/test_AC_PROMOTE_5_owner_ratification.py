"""AC.PROMOTE.5 — Owner-ratification via PM batch API one-at-a-time.

Per v0.2.1 Cycle 2 plan-doc §3 AC.PROMOTE.5: the SKILL body
instructs the persona to call `enqueue_decision` +
`surface_next_questions_batch(n=1)` + `record_response` per
candidate, with default-to-no framing per Decision G; bundled
questions are forbidden per Decision Q.
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


def test_body_names_pm_batch_api_methods() -> None:
    """Body must explicitly name the three PM batch API methods:
    enqueue_decision + surface_next_questions_batch + record_response.
    Verified at framework/per-project-pm/src/loam/per_project_pm/
    runtime.py: lines 240 / 313 / 405."""
    body = _body()
    for method in (
        "enqueue_decision",
        "surface_next_questions_batch",
        "record_response",
    ):
        assert method in body, (
            f"skill-promotion-review: body must name PM batch API "
            f"method `{method}`."
        )


def test_body_specifies_n_equals_one_per_candidate() -> None:
    """Body must specify `n=1` for surface_next_questions_batch
    (one-at-a-time per Decision Q)."""
    body = _body()
    assert "n=1" in body, (
        "skill-promotion-review: body must specify `n=1` on "
        "surface_next_questions_batch (one-at-a-time per Decision Q)."
    )


def test_body_frames_default_to_no() -> None:
    """Body must frame promotion default as `No` per Decision G."""
    body = _body()
    body_lower = body.lower()
    assert "default-to-no" in body_lower or "default to no" in body_lower, (
        "skill-promotion-review: body must explicitly frame the "
        "ratification default as `No` (Decision G)."
    )
    # The question template literal must contain "(default)" attached
    # to the No option per the question framing in §7.
    assert "No (default)" in body or "no (default)" in _body().lower(), (
        "skill-promotion-review: body must show the question template "
        "with `No (default)` as the first option."
    )


def test_body_disclaims_bundled_question_shape() -> None:
    """Body must explicitly disclaim bundled-question shape (asking
    about multiple candidates in one prompt) per Decision Q."""
    body = _body()
    body_lower = body.lower()
    # Acceptance: body mentions either "bundled" / "bundle" or
    # "one-at-a-time" or "per-candidate" framing for the PM block.
    assert (
        "bundled" in body_lower
        or "bundle" in body_lower
        or "one-at-a-time" in body_lower
        or "per-candidate" in body_lower
        or "per candidate" in body_lower
    ), (
        "skill-promotion-review: body must disclaim bundled-question "
        "shape OR explicitly frame the PM block as one-at-a-time / "
        "per-candidate (per Decision Q)."
    )


def test_body_carries_question_template() -> None:
    """Body must carry the question template covering the three
    options: No (default) / Yes — author tests + run amendment cycle
    / Defer to next review."""
    body = _body()
    assert "Promote" in body, (
        "skill-promotion-review: body must include the literal "
        "`Promote` verb in the question template."
    )
    assert "author tests" in body or "Author tests" in body, (
        "skill-promotion-review: body must mention `author tests` "
        "as the Yes-path action in the question template."
    )
    assert "Defer" in body or "defer" in body, (
        "skill-promotion-review: body must mention `Defer` as the "
        "third option in the question template."
    )
