"""AC.E.1 — `classify_workspace` returns "pos-v2-dev" iff dev_intent
is "yes".

Sub-plan E (two-modes-and-multi-workspace, amendment #42) replaces
amendment #39's ``VALUE_PROPOSITION.md``-presence heuristic with a
read of the workspace-local dev-intent answer (sub-plan A's
``read_dev_intent`` reader). When the persona contract carries
``dev_intent: yes``, the workspace classifies as ``"pos-v2-dev"``.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/E-classify-workspace-replacement.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.onboarding import dev_intent_storage_path

from loam.workspace_bootstrap.adapters.tracker_seed import (
    CLASSIFICATION_LOAM_DEV,
    classify_workspace,
)


def _starter_contract_dict(dev_intent: str) -> dict:
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
        "dev_intent": dev_intent,
    }


def _seed_contract(workspace_root: Path, dev_intent: str) -> None:
    """Write a persona contract carrying the given dev_intent value at
    the workspace's persona-storage location."""
    personas_dir = dev_intent_storage_path(workspace_root)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(_starter_contract_dict(dev_intent))
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())


def test_AC_E_1_classify_dev_when_dev_intent_yes(tmp_path: Path) -> None:
    """A workspace whose persona contract carries ``dev_intent: yes``
    classifies as ``"pos-v2-dev"``."""
    workspace = tmp_path / "ws-dev"
    workspace.mkdir()
    _seed_contract(workspace, dev_intent="yes")

    assert classify_workspace(workspace) == CLASSIFICATION_LOAM_DEV


def test_AC_E_1_classify_dev_when_dev_intent_yes_returns_string(
    tmp_path: Path,
) -> None:
    """The classification return is the string sentinel
    ``"pos-v2-dev"`` (the constant value), not a different shape."""
    workspace = tmp_path / "ws-dev-string"
    workspace.mkdir()
    _seed_contract(workspace, dev_intent="yes")

    out = classify_workspace(workspace)
    assert out == "pos-v2-dev"
    assert isinstance(out, str)
