"""AC.A.6 — Reading the answer when absent yields the documented default.

Sub-plan A (two-modes-and-multi-workspace) exposes a pure function
``read_dev_intent(workspace_root) -> Literal["yes", "no", "absent"]``
returning ``"absent"`` when the contract has not yet had the question
answered (e.g. before onboarding completes; on a workspace whose
contract is mid-starter; on a workspace with no contract at all).

Per locked owner ruling 4, ``"absent"`` is treated as ``"no"`` by
sub-plan E. Sub-plan A's responsibility is the read surface; the
consumer mapping lives in E.

Amendment #50 (conversational-onboarding rewrite) replaced the
write-back surface with ``persist_grounding`` taking a structured
``GroundingCapture``; the read surface (``read_dev_intent`` /
``dev_intent_storage_path`` / ``_primary_contract_path``) is
unchanged. This test file is re-targeted at the new write-back
to seed the read fixture without re-exporting any removed symbol.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
      docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.onboarding import (
    GroundingCapture,
    dev_intent_storage_path,
    persist_grounding,
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


def _grounding_with(dev_intent: str) -> GroundingCapture:
    return GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="Iris",
        single_point_of_contact="Coordinator for daily operations.",
        context_holder="Carries cross-session context.",
        escalation_judge="Routes irreversible moves to the user.",
        dev_intent=dev_intent,  # type: ignore[arg-type]
        captured_summary=("Listened to a day-walkthrough.",),
    )


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract
    directory: Path | None = None


def _seed_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """Set up a workspace with a starter contract on disk + a
    .claude/ subdir so persist_grounding can write the agent file.

    Returns ``(workspace_root, contract_path)``.
    """
    personas_dir = dev_intent_storage_path(tmp_path)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(_starter_contract_dict())
    contract_path = persona_dir / "contract.yaml"
    contract_path.write_text(contract.to_yaml())
    # The grounding write-back also writes a prompt.md from the
    # framework template; the rendered file lands at persona_dir/
    # prompt.md per AC.O.4. We create the .claude/ root so the
    # agent-file write can land too.
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    return tmp_path, contract_path


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
    """After persist_grounding writes dev_intent='yes', the reader
    returns 'yes'."""
    workspace_root, contract_path = _seed_workspace(tmp_path)
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(
        contract=contract, directory=contract_path.parent
    )

    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding_with("yes"),
        contract_path=contract_path,
    )

    out = read_dev_intent(workspace_root)
    assert out == "yes"


def test_AC_A_6_after_no_persist_returns_no(tmp_path: Path):
    """After persist_grounding writes dev_intent='no', the reader
    returns 'no'."""
    workspace_root, contract_path = _seed_workspace(tmp_path)
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona = _FakeLoadedPersona(
        contract=contract, directory=contract_path.parent
    )

    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding_with("no"),
        contract_path=contract_path,
    )

    out = read_dev_intent(workspace_root)
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
