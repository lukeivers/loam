"""AC.A.3 — `persist_elicitation_transcript` writes `dev_intent` back.

When the elicitation transcript carries a ``"yes"`` or ``"no"`` value
at key ``"dev_intent"``, the contract on disk has the corresponding
field set; when the transcript omits the question, the field stays at
the unanswered sentinel and ``is_starter`` stays True (incomplete
transcript). The starter-flag transition path is extended to consider
``dev_intent`` as a required answer for completion.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from src.contract import PersonaContract, load_contract
from src.onboarding import (
    OnboardingTranscriptError,
    persist_elicitation_transcript,
)


def _starter_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Default starter SPOC line.",
            "context_holder": "Carries ongoing context.",
            "escalation_judge": "Decides when to surface.",
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


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract


def _persist(transcript: dict, contract_path: Path) -> PersonaContract:
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)
    contract_path.write_text(contract.to_yaml())
    return persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )


def test_AC_A_3_complete_transcript_with_dev_intent_yes_writes_yes(tmp_path: Path):
    """A complete four-answer transcript with dev_intent='yes' writes
    that value to the contract on disk."""
    contract_path = tmp_path / "contract.yaml"
    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper for technical work.",
        "dev_intent": "yes",
    }
    new_contract = _persist(transcript, contract_path)

    assert new_contract.dev_intent == "yes"
    assert new_contract.is_starter is False

    reloaded = load_contract(contract_path)
    assert reloaded.dev_intent == "yes"
    assert reloaded.is_starter is False


def test_AC_A_3_complete_transcript_with_dev_intent_no_writes_no(tmp_path: Path):
    """A complete four-answer transcript with dev_intent='no' writes
    that value to the contract on disk."""
    contract_path = tmp_path / "contract.yaml"
    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper for personal admin.",
        "dev_intent": "no",
    }
    new_contract = _persist(transcript, contract_path)

    assert new_contract.dev_intent == "no"
    assert new_contract.is_starter is False


def test_AC_A_3_omitted_dev_intent_keeps_unanswered_and_starter_true(
    tmp_path: Path,
):
    """A transcript that omits dev_intent leaves the contract field at
    its unanswered sentinel and ``is_starter`` stays True (incomplete
    transcript). Next session re-opens elicitation."""
    contract_path = tmp_path / "contract.yaml"
    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper for technical work.",
        # dev_intent omitted — required question, transcript incomplete
    }
    new_contract = _persist(transcript, contract_path)

    assert new_contract.dev_intent == "unanswered"
    assert new_contract.is_starter is True

    reloaded = load_contract(contract_path)
    assert reloaded.dev_intent == "unanswered"
    assert reloaded.is_starter is True


def test_AC_A_3_unrecognised_dev_intent_answer_raises(tmp_path: Path):
    """A transcript value at dev_intent that is neither yes/no nor a
    recognised synonym raises OnboardingTranscriptError. Distinct from
    incomplete (which is a normal state) — this is structural."""
    contract_path = tmp_path / "contract.yaml"
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper.",
        "dev_intent": "perhaps",
    }
    with pytest.raises(OnboardingTranscriptError):
        persist_elicitation_transcript(
            loaded_persona=persona,
            transcript=transcript,
            contract_path=contract_path,
        )


def test_AC_A_3_dev_intent_synonyms_normalise(tmp_path: Path):
    """Free-text yes/no synonyms (e.g. 'develop') normalise to the
    contract's Literal admissible values before validation."""
    contract_path = tmp_path / "contract.yaml"
    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper.",
        "dev_intent": "develop",  # synonym for "yes"
    }
    new_contract = _persist(transcript, contract_path)
    assert new_contract.dev_intent == "yes"
