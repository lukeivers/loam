"""AC.E.4 — `classify_workspace` does NOT inspect VALUE_PROPOSITION.md.

Sub-plan E (two-modes-and-multi-workspace, amendment #42). The
classification source-of-truth moves from
``docs/rebuild/VALUE_PROPOSITION.md`` presence (amendment #39's
heuristic) to the workspace-local dev-intent answer. The function's
behaviour MUST NOT depend on whether ``VALUE_PROPOSITION.md`` exists
at the workspace root.

The test surfaces the decoupling empirically: a workspace where
``VALUE_PROPOSITION.md`` IS present AND ``dev_intent`` is ``"no"``
classifies as ``"user"``. (Under the old heuristic this would have
returned ``"pos-v2-dev"``.) The presence of the canonical file is
content, not a marker.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/E-classify-workspace-replacement.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.onboarding import dev_intent_storage_path

from loam.workspace_bootstrap.adapters.tracker_seed import (
    CLASSIFICATION_LOAM_DEV,
    CLASSIFICATION_USER,
    FRAMEWORK_VALUE_PROP_RELPATH,
    classify_workspace,
)


def _contract_dict(dev_intent: str) -> dict:
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


def _seed_contract(workspace: Path, dev_intent: str) -> None:
    personas_dir = dev_intent_storage_path(workspace)
    persona_dir = personas_dir / "iris"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(_contract_dict(dev_intent))
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())


def _drop_framework_value_prop(workspace: Path) -> None:
    """Place a dummy ``docs/rebuild/VALUE_PROPOSITION.md`` at the
    framework path. Content is irrelevant — the marker check is what
    we're isolating."""
    target = workspace / FRAMEWORK_VALUE_PROP_RELPATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Workspace Value Proposition\n\n(content)\n")


def test_AC_E_4_classify_user_with_value_prop_present_and_dev_intent_no(
    tmp_path: Path,
) -> None:
    """A workspace where VALUE_PROPOSITION.md IS present AND dev_intent
    is ``"no"`` classifies as ``"user"``. Under amendment #39's
    heuristic this would have returned ``"pos-v2-dev"`` — that
    behaviour is gone."""
    workspace = tmp_path / "ws-vp-present-user"
    workspace.mkdir()
    _drop_framework_value_prop(workspace)
    _seed_contract(workspace, dev_intent="no")

    assert (workspace / FRAMEWORK_VALUE_PROP_RELPATH).is_file()
    assert classify_workspace(workspace) == CLASSIFICATION_USER


def test_AC_E_4_classify_dev_with_no_value_prop_and_dev_intent_yes(
    tmp_path: Path,
) -> None:
    """The mirror: a workspace where VALUE_PROPOSITION.md is ABSENT
    and dev_intent is ``"yes"`` classifies as ``"pos-v2-dev"``. Under
    the old heuristic this would have returned ``"user"``."""
    workspace = tmp_path / "ws-no-vp-dev"
    workspace.mkdir()
    _seed_contract(workspace, dev_intent="yes")

    assert not (workspace / FRAMEWORK_VALUE_PROP_RELPATH).exists()
    assert classify_workspace(workspace) == CLASSIFICATION_LOAM_DEV


def test_AC_E_4_value_prop_presence_irrelevant_to_classification(
    tmp_path: Path,
) -> None:
    """For each (dev_intent, VALUE_PROPOSITION.md presence) pair the
    classification is determined solely by dev_intent. The test
    enumerates the four combinations and asserts."""
    cases = [
        ("yes", True, CLASSIFICATION_LOAM_DEV),
        ("yes", False, CLASSIFICATION_LOAM_DEV),
        ("no", True, CLASSIFICATION_USER),
        ("no", False, CLASSIFICATION_USER),
    ]
    for i, (dev_intent, vp_present, expected) in enumerate(cases):
        workspace = tmp_path / f"ws-{i}"
        workspace.mkdir()
        if vp_present:
            _drop_framework_value_prop(workspace)
        _seed_contract(workspace, dev_intent=dev_intent)
        actual = classify_workspace(workspace)
        assert actual == expected, (
            f"case {i} (dev_intent={dev_intent}, vp_present={vp_present}): "
            f"expected {expected}, got {actual}"
        )
