"""AC35.5 — Renderer regenerates on contract change.

Given a freshly-loaded contract, calling ``to_agent_md()`` and then
mutating the contract (e.g., ``given_name`` change) and calling
``to_agent_md()`` again produces a string whose frontmatter or body
field reflecting the changed prose differs between the two calls.
The renderer reads from the contract argument every call; it has no
caching that would shadow a subsequent contract change.

Plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md
"""

from __future__ import annotations

from src.agent_md import to_agent_md
from src.contract import PersonaContract


def _base_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Coordinator for the user's domain.",
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
    }


def test_AC35_5_render_twice_with_same_contract_yields_equality():
    contract = PersonaContract.model_validate(_base_contract_dict())
    a = to_agent_md(contract)
    b = to_agent_md(contract)
    assert a == b


def test_AC35_5_render_then_mutate_then_render_yields_inequality_on_changed_field():
    """Mutating `given_name` changes the identity-anchor block."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    a = to_agent_md(contract)
    mutated = contract.model_copy(update={"given_name": "Eris"})
    b = to_agent_md(mutated)
    assert a != b
    # The given_name change reaches the body's identity-anchor block.
    assert "Iris" in a
    assert "Eris" in b


def test_AC35_5_render_then_mutate_responsibilities_changes_description():
    """Mutating `responsibilities.single_point_of_contact` changes the
    frontmatter description."""
    from src.contract import Responsibilities

    contract = PersonaContract.model_validate(_base_contract_dict())
    a = to_agent_md(contract)
    new_resp = Responsibilities(
        single_point_of_contact="Helper for technical research and writing.",
        context_holder=contract.responsibilities.context_holder,
        escalation_judge=contract.responsibilities.escalation_judge,
    )
    mutated = contract.model_copy(update={"responsibilities": new_resp})
    b = to_agent_md(mutated)
    assert a != b
    assert "Coordinator" in a
    assert "Helper for technical research" in b


def test_AC35_5_no_caching_shadows_contract_change():
    """Repeated mutate-and-render cycles produce strings reflecting
    the latest contract — no internal cache shadows a change."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    rendered_each = []
    for name in ("Alpha", "Beta", "Gamma"):
        mutated = contract.model_copy(update={"given_name": name})
        rendered_each.append(to_agent_md(mutated))
    for name, rendered in zip(("Alpha", "Beta", "Gamma"), rendered_each):
        assert name in rendered
    # Each rendered string carries its own given_name; no shadowing.
    assert rendered_each[0] != rendered_each[1] != rendered_each[2]
