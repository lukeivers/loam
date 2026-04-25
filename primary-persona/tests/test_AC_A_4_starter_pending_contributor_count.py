"""AC.A.4 — Starter-pending contributor reflects the dev-intent question.

The contributor returned by ``build_starter_pending_contributor``
includes the dev-intent question in the question count surfaced in
its additionalContext block. The ``STARTER_PENDING_MARKER`` prefix is
unchanged. D-A.3 (sub-plan A): the count is *derived* from
``len(ONBOARDING_QUESTIONS)``, not hard-coded — adding a future fifth
question never silently drifts the body text.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract


def test_AC_A_4_contributor_body_mentions_full_question_count():
    """Body text includes the canonical-tuple count (4 in current
    shape — derived from len(ONBOARDING_QUESTIONS), not hard-coded)."""
    persona = _FakeLoadedPersona(contract=_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    assert STARTER_PENDING_MARKER in out
    expected_count = len(ONBOARDING_QUESTIONS)
    # Body surfaces the count somewhere — match on the integer.
    assert f"{expected_count} questions" in out, (
        f"expected '{expected_count} questions' in contributor body, got: {out!r}"
    )


def test_AC_A_4_contributor_count_is_at_least_four_with_dev_intent():
    """With the sub-plan A extension landed, the canonical tuple has
    at least four entries; the body's count is at least four."""
    expected_count = len(ONBOARDING_QUESTIONS)
    assert expected_count >= 4

    persona = _FakeLoadedPersona(contract=_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    # The body should surface 4 (or whatever the tuple length is now).
    assert f"{expected_count} questions" in out


def test_AC_A_4_contributor_marker_unchanged():
    """STARTER_PENDING_MARKER (the bracketed first-line prefix) is
    NOT changed by this amendment — sub-plan A re-extends the
    question tuple, not the marker."""
    persona = _FakeLoadedPersona(contract=_starter_contract())
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    first_line = out.splitlines()[0]
    assert first_line == STARTER_PENDING_MARKER
