"""AC35.4 — Elicitation transcript produces a contract write-back via `to_yaml()`.

Given a starter-flagged contract and a synthetic transcript carrying
answers to each elicitation question, the ``onboarding`` module
writes the answers back to the contract via the existing ``to_yaml()``
write-back surface. Reloading the persisted YAML produces a contract
whose prose fields contain the answers and whose ``is_starter`` is
``False``. A transcript missing answers to required questions leaves
the contract starter-flagged (the AC bounds the outcome: incomplete
elicitation does not flip ``is_starter``).

Plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from src.contract import PersonaContract
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
            "context_holder": "Carries ongoing context across sessions.",
            "escalation_judge": "Decides when to surface to the user.",
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


def test_AC35_4_complete_transcript_persists_answers_and_flips_is_starter(
    tmp_path: Path,
):
    """Complete transcript → answers reach the contract on disk and
    is_starter flips to False."""
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)

    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris-Refined",
        "domain_focus": (
            "Coordinator for personal finance and life-admin work. "
            "Sub-clauses follow."
        ),
        # Sub-plan A (two-modes-and-multi-workspace) extends the
        # canonical question tuple with a fourth required entry
        # (``dev_intent``). The AC35.4 outcome shape — complete
        # transcript flips ``is_starter`` to False — is unchanged;
        # the fixture data advances to match the extended definition
        # of "complete transcript" per owner ruling 2026-04-25 (a).
        "dev_intent": "no",
    }

    new_contract = persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )

    # Returned contract reflects the transcript answers.
    assert new_contract.given_name == "Iris-Refined"
    assert (
        "personal finance and life-admin"
        in new_contract.responsibilities.single_point_of_contact
    )
    assert new_contract.is_starter is False

    # On-disk YAML round-trips.
    from src.contract import load_contract

    reloaded = load_contract(contract_path)
    assert reloaded.given_name == "Iris-Refined"
    assert (
        "personal finance and life-admin"
        in reloaded.responsibilities.single_point_of_contact
    )
    assert reloaded.is_starter is False


def test_AC35_4_incomplete_transcript_leaves_is_starter_true(tmp_path: Path):
    """Incomplete transcript → is_starter stays True. Next session
    re-opens elicitation."""
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)

    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    # Missing `domain_focus` (required).
    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris-Refined",
    }

    new_contract = persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )
    # Best-effort partial application: given_name reaches the contract...
    assert new_contract.given_name == "Iris-Refined"
    # ...but is_starter stays True (incomplete elicitation).
    assert new_contract.is_starter is True

    # The on-disk YAML reflects the same.
    from src.contract import load_contract

    reloaded = load_contract(contract_path)
    assert reloaded.is_starter is True


def test_AC35_4_empty_string_answer_treated_as_missing(tmp_path: Path):
    """A transcript value that is the empty string (or whitespace)
    counts as missing — the persona honoured `(skippable)` and the
    user skipped that question."""
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)

    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris-Refined",
        "domain_focus": "   ",  # whitespace — treated as missing
    }

    new_contract = persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )
    # given_name persists.
    assert new_contract.given_name == "Iris-Refined"
    # SPOC unchanged.
    assert (
        new_contract.responsibilities.single_point_of_contact
        == "Default starter SPOC line."
    )
    assert new_contract.is_starter is True


def test_AC35_4_transcript_with_unknown_question_id_rejected(tmp_path: Path):
    """Structurally-malformed transcript (unknown question id) raises
    OnboardingTranscriptError. Distinct from incomplete (which is a
    normal state)."""
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)

    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {"unknown_question_id": "something"}

    with pytest.raises(OnboardingTranscriptError):
        persist_elicitation_transcript(
            loaded_persona=persona,
            transcript=transcript,
            contract_path=contract_path,
        )


def test_AC35_4_transcript_with_non_str_value_rejected(tmp_path: Path):
    """Structurally-malformed transcript (non-str value) raises
    OnboardingTranscriptError."""
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)

    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript: dict = {"user_name": 42}  # int, not str
    with pytest.raises(OnboardingTranscriptError):
        persist_elicitation_transcript(
            loaded_persona=persona,
            transcript=transcript,
            contract_path=contract_path,
        )


def test_AC35_4_complete_transcript_round_trips_through_to_yaml(tmp_path: Path):
    """The write-back uses the contract's existing `to_yaml()` surface;
    reloading the YAML produces the same logical contract."""
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(contract=contract)

    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Aurelia",
        "domain_focus": "Helper for technical research and writing.",
        # Sub-plan A extension — fourth required answer (see
        # complete-transcript test above for rationale).
        "dev_intent": "yes",
    }

    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )

    yaml_text = contract_path.read_text()
    # YAML carries the new given_name + flipped is_starter.
    assert "given_name: Aurelia" in yaml_text
    assert "is_starter: false" in yaml_text
