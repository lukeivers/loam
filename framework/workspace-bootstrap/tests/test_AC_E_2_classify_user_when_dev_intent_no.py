"""AC.E.2 — `classify_workspace` returns "user" when dev_intent is
"no".

Sub-plan E (two-modes-and-multi-workspace, amendment #42). When the
persona contract carries ``dev_intent: no``, the workspace classifies
as ``"user"`` regardless of any other heuristic that pre-dated the
amendment (e.g. ``VALUE_PROPOSITION.md`` presence — see AC.E.4 for
the explicit isolation test).

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/E-classify-workspace-replacement.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.onboarding import dev_intent_storage_path

from loam.workspace_bootstrap.adapters.tracker_seed import (
    CLASSIFICATION_USER,
    classify_workspace,
)


def _user_contract_dict() -> dict:
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
        "is_starter": False,
        "is_primary": True,
        "dev_intent": "no",
    }


def _seed_user_contract(workspace_root: Path) -> None:
    personas_dir = dev_intent_storage_path(workspace_root)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(_user_contract_dict())
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())


def test_AC_E_2_classify_user_when_dev_intent_no(tmp_path: Path) -> None:
    """A workspace whose persona contract carries ``dev_intent: no``
    classifies as ``"user"``."""
    workspace = tmp_path / "ws-user"
    workspace.mkdir()
    _seed_user_contract(workspace)

    assert classify_workspace(workspace) == CLASSIFICATION_USER


def test_AC_E_2_classify_user_when_dev_intent_no_returns_string(
    tmp_path: Path,
) -> None:
    """The classification return is the string sentinel ``"user"``."""
    workspace = tmp_path / "ws-user-string"
    workspace.mkdir()
    _seed_user_contract(workspace)

    out = classify_workspace(workspace)
    assert out == "user"
    assert isinstance(out, str)
