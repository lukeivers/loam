"""AC.O.3 — ``persist_grounding`` accepts a structured
``GroundingCapture`` and writes contract.yaml.

On a well-formed payload the function writes the contract YAML to
``contract_path`` with the captured fields applied
(given_name, responsibilities.* fields, dev_intent, is_starter=False);
the new file round-trips through ``load_contract`` to an
equivalent contract. On a malformed payload (any required field
empty, dev-intent not in {yes, no}) raises
``OnboardingGroundingError`` without writing any file.

Plan: docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from src.contract import PersonaContract, load_contract
from src.onboarding import (
    GroundingCapture,
    OnboardingGroundingError,
    persist_grounding,
)


def _starter_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Default starter SPOC.",
            "context_holder": "Carries ongoing context.",
            "escalation_judge": "Decides surfacing.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "defer",
        },
        "escalation_taxonomy": {"categories": ["x"]},
        "severity_vocabulary": {"labels": ["a", "b"]},
        "is_starter": True,
    }


def _well_formed_grounding() -> GroundingCapture:
    return GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="Aurelia",
        single_point_of_contact=(
            "Coordinator for personal-life operations and workspace "
            "continuity."
        ),
        context_holder=(
            "Tracks what's in flight, what's stalled, and what's "
            "deferred across sessions."
        ),
        escalation_judge=(
            "Routes irreversible and high-leverage moves to Luke; "
            "handles routine moves directly."
        ),
        dev_intent="no",
        captured_summary=(
            "Mornings are when the real work gets done; afternoons "
            "are getting eaten by Slack.",
            "Wants help with daily synthesis and triage.",
        ),
    )


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract
    directory: Path | None = None


def _seed(tmp_path: Path) -> tuple[_FakeLoadedPersona, Path]:
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona_dir = tmp_path / "personas" / "iris"
    persona_dir.mkdir(parents=True)
    contract_path = persona_dir / "contract.yaml"
    contract_path.write_text(contract.to_yaml())
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    persona = _FakeLoadedPersona(contract=contract, directory=persona_dir)
    return persona, contract_path


def test_AC_O_3_well_formed_grounding_writes_contract(tmp_path: Path):
    """A well-formed GroundingCapture writes a valid contract that
    round-trips through load_contract."""
    persona, contract_path = _seed(tmp_path)
    grounding = _well_formed_grounding()

    new_contract = persist_grounding(
        loaded_persona=persona,
        grounding=grounding,
        contract_path=contract_path,
    )

    assert new_contract.given_name == grounding.persona_given_name
    assert (
        new_contract.responsibilities.single_point_of_contact
        == grounding.single_point_of_contact
    )
    assert (
        new_contract.responsibilities.context_holder
        == grounding.context_holder
    )
    assert (
        new_contract.responsibilities.escalation_judge
        == grounding.escalation_judge
    )
    assert new_contract.dev_intent == "no"
    assert new_contract.is_starter is False

    reloaded = load_contract(contract_path)
    assert reloaded.given_name == grounding.persona_given_name
    assert (
        reloaded.responsibilities.single_point_of_contact
        == grounding.single_point_of_contact
    )
    assert reloaded.dev_intent == "no"
    assert reloaded.is_starter is False


def test_AC_O_3_dev_intent_yes_persists(tmp_path: Path):
    persona, contract_path = _seed(tmp_path)
    grounding = GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="Aurelia",
        single_point_of_contact="Helper for technical work.",
        context_holder="Holds context.",
        escalation_judge="Routes escalations.",
        dev_intent="yes",
        captured_summary=("Working on pos-v2 itself.",),
    )
    new_contract = persist_grounding(
        loaded_persona=persona,
        grounding=grounding,
        contract_path=contract_path,
    )
    assert new_contract.dev_intent == "yes"


def test_AC_O_3_empty_user_preferred_name_raises_no_write(tmp_path: Path):
    persona, contract_path = _seed(tmp_path)
    contract_path.write_text("PLACEHOLDER")
    bad = GroundingCapture(
        user_preferred_name="",
        persona_given_name="Aurelia",
        single_point_of_contact="x",
        context_holder="x",
        escalation_judge="x",
        dev_intent="no",
        captured_summary=("y",),
    )
    with pytest.raises(OnboardingGroundingError):
        persist_grounding(
            loaded_persona=persona,
            grounding=bad,
            contract_path=contract_path,
        )
    assert contract_path.read_text() == "PLACEHOLDER"


def test_AC_O_3_whitespace_persona_given_name_raises(tmp_path: Path):
    persona, contract_path = _seed(tmp_path)
    contract_path.write_text("PLACEHOLDER")
    bad = GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="   ",
        single_point_of_contact="x",
        context_holder="x",
        escalation_judge="x",
        dev_intent="no",
        captured_summary=("y",),
    )
    with pytest.raises(OnboardingGroundingError):
        persist_grounding(
            loaded_persona=persona,
            grounding=bad,
            contract_path=contract_path,
        )
    assert contract_path.read_text() == "PLACEHOLDER"


def test_AC_O_3_unknown_dev_intent_raises_no_write(tmp_path: Path):
    persona, contract_path = _seed(tmp_path)
    contract_path.write_text("PLACEHOLDER")
    bad = GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="Aurelia",
        single_point_of_contact="x",
        context_holder="x",
        escalation_judge="x",
        dev_intent="maybe",  # type: ignore[arg-type]
        captured_summary=("y",),
    )
    with pytest.raises(OnboardingGroundingError):
        persist_grounding(
            loaded_persona=persona,
            grounding=bad,
            contract_path=contract_path,
        )
    assert contract_path.read_text() == "PLACEHOLDER"


def test_AC_O_3_empty_captured_summary_raises_no_write(tmp_path: Path):
    persona, contract_path = _seed(tmp_path)
    contract_path.write_text("PLACEHOLDER")
    bad = GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="Aurelia",
        single_point_of_contact="x",
        context_holder="x",
        escalation_judge="x",
        dev_intent="no",
        captured_summary=(),
    )
    with pytest.raises(OnboardingGroundingError):
        persist_grounding(
            loaded_persona=persona,
            grounding=bad,
            contract_path=contract_path,
        )
    assert contract_path.read_text() == "PLACEHOLDER"


def test_AC_O_3_whitespace_captured_summary_bullet_raises(tmp_path: Path):
    persona, contract_path = _seed(tmp_path)
    contract_path.write_text("PLACEHOLDER")
    bad = GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="Aurelia",
        single_point_of_contact="x",
        context_holder="x",
        escalation_judge="x",
        dev_intent="no",
        captured_summary=("valid", "   "),
    )
    with pytest.raises(OnboardingGroundingError):
        persist_grounding(
            loaded_persona=persona,
            grounding=bad,
            contract_path=contract_path,
        )
    assert contract_path.read_text() == "PLACEHOLDER"
