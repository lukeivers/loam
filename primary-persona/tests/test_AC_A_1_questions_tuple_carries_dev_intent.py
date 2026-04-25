"""AC.A.1 — `ONBOARDING_QUESTIONS` carries a dev-intent question.

Sub-plan A (two-modes-and-multi-workspace) extends amendment #35's
canonical question tuple with a fourth required question whose ``id``
is ``"dev_intent"`` and whose ``contract_field`` names the new
``PersonaContract.dev_intent`` field. The framework-level scaffolding
piece this AC measures is the *shape*: id + required flag + contract-
field mapping. The prompt prose is the persona-template's call (per
locked owner ruling D-MASTER.3); the framework holds the field.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

from src.onboarding import ONBOARDING_QUESTIONS, OnboardingQuestion


def test_AC_A_1_questions_tuple_carries_dev_intent_question():
    """Exactly one entry in ONBOARDING_QUESTIONS has id='dev_intent',
    required=True, and contract_field='dev_intent'."""
    matches = [q for q in ONBOARDING_QUESTIONS if q.id == "dev_intent"]
    assert len(matches) == 1, (
        f"expected exactly one dev_intent entry, got {len(matches)}"
    )
    entry = matches[0]
    assert isinstance(entry, OnboardingQuestion)
    assert entry.required is True
    assert entry.contract_field == "dev_intent"


def test_AC_A_1_dev_intent_entry_has_a_non_empty_prompt():
    """The framework ships a starter prompt; the workspace may
    override via the template-override mechanic. Framework-level
    invariant: the prompt is a non-empty string."""
    entry = next(q for q in ONBOARDING_QUESTIONS if q.id == "dev_intent")
    assert isinstance(entry.prompt, str)
    assert entry.prompt.strip() != ""


def test_AC_A_1_dev_intent_question_extends_existing_tuple():
    """The new entry is in addition to the three amendment-#35 entries
    — the canonical tuple has at least four entries, and the original
    three (user_name, persona_given_name, domain_focus) are preserved
    by id."""
    ids = {q.id for q in ONBOARDING_QUESTIONS}
    # Amendment #35's three ids must still be present.
    assert {"user_name", "persona_given_name", "domain_focus"}.issubset(ids)
    # Plus the new sub-plan A entry.
    assert "dev_intent" in ids
    # At least four entries total (no entries removed).
    assert len(ONBOARDING_QUESTIONS) >= 4
