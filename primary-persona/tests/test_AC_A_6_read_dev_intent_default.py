"""AC.A.6 — Reading the answer when absent yields the documented default.

Sub-plan A (two-modes-and-multi-workspace) exposes a pure function
``read_dev_intent(workspace_root) -> Literal["yes", "no", "absent"]``
returning ``"absent"`` when the contract has not yet had the question
answered (e.g. before onboarding completes; on a workspace whose
contract is mid-starter; on a workspace with no contract at all).

Per locked owner ruling 4, ``"absent"`` is treated as ``"no"`` by
sub-plan E. Sub-plan A's responsibility is the read surface; the
consumer mapping lives in E.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.contract import PersonaContract
from src.onboarding import (
    dev_intent_storage_path,
    persist_elicitation_transcript,
    read_dev_intent,
)


def _starter_contract_dict() -> dict:
    return {
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
        "is_primary": True,
    }


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract


def test_AC_A_6_no_contract_returns_absent(tmp_path: Path):
    """A workspace with no personas/ directory at all returns 'absent'."""
    out = read_dev_intent(tmp_path)
    assert out == "absent"


def test_AC_A_6_starter_contract_with_unanswered_returns_absent(tmp_path: Path):
    """A starter-flagged contract whose dev_intent is the unanswered
    sentinel returns 'absent'."""
    personas_dir = dev_intent_storage_path(tmp_path)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(_starter_contract_dict())
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())

    out = read_dev_intent(tmp_path)
    assert out == "absent"


def test_AC_A_6_after_yes_persist_returns_yes(tmp_path: Path):
    """After persist_elicitation_transcript writes dev_intent='yes',
    the reader returns 'yes'."""
    personas_dir = dev_intent_storage_path(tmp_path)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(_starter_contract_dict())
    contract_path = persona_dir / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    persona = _FakeLoadedPersona(contract=contract)
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript={
            "user_name": "Luke",
            "persona_given_name": "Iris",
            "domain_focus": "Helper.",
            "dev_intent": "yes",
        },
        contract_path=contract_path,
    )

    out = read_dev_intent(tmp_path)
    assert out == "yes"


def test_AC_A_6_after_no_persist_returns_no(tmp_path: Path):
    """After persist_elicitation_transcript writes dev_intent='no',
    the reader returns 'no'."""
    personas_dir = dev_intent_storage_path(tmp_path)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(_starter_contract_dict())
    contract_path = persona_dir / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    persona = _FakeLoadedPersona(contract=contract)
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript={
            "user_name": "Luke",
            "persona_given_name": "Iris",
            "domain_focus": "Helper.",
            "dev_intent": "no",
        },
        contract_path=contract_path,
    )

    out = read_dev_intent(tmp_path)
    assert out == "no"


def test_AC_A_6_malformed_contract_returns_absent(tmp_path: Path):
    """A persona directory whose contract fails to load returns
    'absent' — fail-safe (the reader never raises)."""
    personas_dir = dev_intent_storage_path(tmp_path)
    persona_dir = personas_dir / "broken"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text("not: { valid yaml")

    out = read_dev_intent(tmp_path)
    assert out == "absent"
