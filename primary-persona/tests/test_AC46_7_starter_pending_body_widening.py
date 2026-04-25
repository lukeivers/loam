"""AC46.7 — Starter-pending body widening.

Outcome (per umbrella plan §4a + builder plan §3):

  - When ``contract.is_starter=True``, ``build_starter_pending_
    contributor`` returns a string whose:
      * first line is ``STARTER_PENDING_MARKER`` (preserves AC35.3)
      * body includes each ``OnboardingQuestion``'s id + prompt in a
        structurally-detectable list
      * body includes write-back instruction lines naming
        ``persist_elicitation_transcript`` + the contract path + a
        one-line invocation pattern
      * total length ≤ 2,000 chars (per-contributor budget)
  - When ``contract.is_starter=False``, the contributor returns ""
    (preserves AC35.3 negative path).

This test does NOT regress AC.A.4's "{count} questions" assertion —
the existing test_AC_A_4 file passes against the widened body
unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.contract import PersonaContract
from src.onboarding import (
    ONBOARDING_QUESTIONS,
    STARTER_PENDING_MARKER,
    build_starter_pending_contributor,
)


def _starter_contract() -> PersonaContract:
    return PersonaContract.model_validate(
        {
            "handle": "iris",
            "given_name": "Iris",
            "contract_version": "1.0.0",
            "responsibilities": {
                "single_point_of_contact": "Coordinator.",
                "context_holder": "Holds context.",
                "escalation_judge": "Decides surfacing.",
            },
            "authority_boundary": {
                "tier_a": "defer",
                "tier_b": "defer",
                "tier_c": "execute",
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["x"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
            "is_starter": True,
        }
    )


def _non_starter_contract() -> PersonaContract:
    return PersonaContract.model_validate(
        {
            "handle": "iris",
            "given_name": "Iris",
            "contract_version": "1.0.0",
            "responsibilities": {
                "single_point_of_contact": "Coordinator.",
                "context_holder": "Holds context.",
                "escalation_judge": "Decides surfacing.",
            },
            "authority_boundary": {
                "tier_a": "defer",
                "tier_b": "defer",
                "tier_c": "execute",
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["x"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
            "is_starter": False,
        }
    )


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract
    directory: Path | None = None


def test_AC46_7_starter_body_first_line_is_marker() -> None:
    """First line of the widened body is STARTER_PENDING_MARKER
    (preserves AC35.3)."""
    persona = _FakeLoadedPersona(contract=_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    first_line = out.splitlines()[0]
    assert first_line == STARTER_PENDING_MARKER


def test_AC46_7_starter_body_contains_question_ids() -> None:
    """Body lists every ``OnboardingQuestion`` id."""
    persona = _FakeLoadedPersona(contract=_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    for q in ONBOARDING_QUESTIONS:
        assert f"id={q.id}" in out, f"question id {q.id!r} missing from body"


def test_AC46_7_starter_body_contains_question_prompts() -> None:
    """Body includes every ``OnboardingQuestion``'s prompt text."""
    persona = _FakeLoadedPersona(contract=_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    for q in ONBOARDING_QUESTIONS:
        # Prompt may be multi-line; use a leading substring as the
        # detection key (full-string compare brittles on whitespace
        # rendering).
        prompt_substr = q.prompt.split("\n")[0][:30]
        assert prompt_substr in out, (
            f"question prompt for {q.id!r} missing from body"
        )


def test_AC46_7_starter_body_contains_writeback_instructions() -> None:
    """Body names ``persist_elicitation_transcript``, names the
    contract path, and shows a one-line invocation pattern."""
    persona = _FakeLoadedPersona(
        contract=_starter_contract(),
        directory=Path("/example/personas/iris"),
    )
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    assert "persist_elicitation_transcript" in out
    assert "contract.yaml" in out
    assert "transcript=" in out


def test_AC46_7_starter_body_within_2000_char_budget() -> None:
    """Total body length ≤ 2,000 chars."""
    persona = _FakeLoadedPersona(
        contract=_starter_contract(),
        directory=Path("/example/personas/iris"),
    )
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    assert len(out) <= 2000, (
        f"starter-pending body exceeded 2,000-char budget: {len(out)} chars"
    )


def test_AC46_7_non_starter_returns_empty() -> None:
    """``is_starter=False`` → contributor returns empty string."""
    persona = _FakeLoadedPersona(contract=_non_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    assert out == ""


def test_AC46_7_body_preserves_AC_A_4_question_count_text() -> None:
    """Body still contains the ``{count} questions`` substring used
    by sub-plan A's AC.A.4 test (regression guard)."""
    persona = _FakeLoadedPersona(contract=_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    expected = len(ONBOARDING_QUESTIONS)
    assert f"{expected} questions" in out
