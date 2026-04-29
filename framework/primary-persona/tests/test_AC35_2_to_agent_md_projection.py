"""AC35.2 — `to_agent_md()` projects a contract onto a Claude-Code subagent-file shape.

A pure function ``to_agent_md(contract)`` returns a string whose
parsed YAML frontmatter contains:

  - ``name == contract.handle``
  - ``description`` derived from ``contract.responsibilities.single_point_of_contact``
  - ``model: inherit``

The body contains an identity-anchor block (compaction-resilience
marker) followed by a persona-prompt block. Calling the function
twice with the same contract returns identical strings (idempotence).

A malformed contract (built via ``model_construct`` to bypass
validation) raises ``AgentMdProjectionError`` — never silent garbage.

Plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md
"""

from __future__ import annotations

import yaml
import pytest

from loam.primary_persona.agent_md import AgentMdProjectionError, to_agent_md
from loam.primary_persona.contract import PersonaContract


def _base_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": (
                "Coordinator for personal logistics and life-admin work. "
                "Sub-clauses appear after the first sentence."
            ),
            "context_holder": "Carries ongoing context across sessions.",
            "escalation_judge": "Decides when to surface to the user.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "execute",
        },
        "escalation_taxonomy": {"categories": ["irreversible-action"]},
        "severity_vocabulary": {
            "labels": ["crisis", "urgent", "material", "advisory"]
        },
    }


def _parse_frontmatter(rendered: str) -> dict:
    """Extract the YAML frontmatter dict from a `to_agent_md` output."""
    assert rendered.startswith("---\n"), "frontmatter must open with ---"
    body_split = rendered.split("---\n", 2)
    # body_split[0] == "" (before first ---)
    # body_split[1] == frontmatter YAML
    # body_split[2] == body
    fm = yaml.safe_load(body_split[1])
    assert isinstance(fm, dict), "frontmatter must parse as a YAML mapping"
    return fm


# ---- positive: frontmatter shape ------------------------------------


def test_AC35_2_frontmatter_name_matches_handle():
    contract = PersonaContract.model_validate(_base_contract_dict())
    rendered = to_agent_md(contract)
    fm = _parse_frontmatter(rendered)
    assert fm["name"] == contract.handle


def test_AC35_2_frontmatter_description_derived_from_responsibilities():
    """`description` is one line, derived from
    `responsibilities.single_point_of_contact`."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    rendered = to_agent_md(contract)
    fm = _parse_frontmatter(rendered)
    desc = fm["description"]
    # One sentence, no newline, derived from the source prose.
    assert "\n" not in desc
    # Sentinel keyword from the source prose appears.
    assert "Coordinator" in desc
    assert "personal logistics" in desc


def test_AC35_2_frontmatter_model_inherit():
    contract = PersonaContract.model_validate(_base_contract_dict())
    rendered = to_agent_md(contract)
    fm = _parse_frontmatter(rendered)
    assert fm["model"] == "inherit"


# ---- positive: body shape -------------------------------------------


def test_AC35_2_body_contains_identity_anchor_block():
    """The body opens with a structural identity-anchor block
    addressed by the contract's handle and given_name."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    rendered = to_agent_md(contract)
    # Strip frontmatter; remainder is the body.
    body = rendered.split("---\n", 2)[2]
    assert "Identity anchor" in body
    assert contract.given_name in body
    assert contract.handle in body


def test_AC35_2_body_contains_persona_prompt_section_with_supplied_text():
    """When prompt_text is supplied, its content appears in the body."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    prompt_text = "## Voice\n\nHeadline-first; numbered lists for multi-part."
    rendered = to_agent_md(contract, prompt_text=prompt_text)
    body = rendered.split("---\n", 2)[2]
    assert "# Persona prompt" in body
    assert "Headline-first" in body
    assert "numbered lists for multi-part" in body


def test_AC35_2_body_contains_persona_prompt_section_without_supplied_text():
    """When prompt_text is absent, the body still has the section
    with a pointer to the workspace prompt.md."""
    contract = PersonaContract.model_validate(_base_contract_dict())
    rendered = to_agent_md(contract)
    body = rendered.split("---\n", 2)[2]
    assert "# Persona prompt" in body
    assert f"personas/{contract.handle}/prompt.md" in body


# ---- positive: idempotence (same contract → same string) -----------


def test_AC35_2_idempotence_same_contract_produces_same_string():
    contract = PersonaContract.model_validate(_base_contract_dict())
    a = to_agent_md(contract)
    b = to_agent_md(contract)
    assert a == b


def test_AC35_2_idempotence_with_prompt_text():
    contract = PersonaContract.model_validate(_base_contract_dict())
    text = "Voice prose here."
    a = to_agent_md(contract, prompt_text=text)
    b = to_agent_md(contract, prompt_text=text)
    assert a == b


# ---- negative: malformed contract → structural exception -----------


def test_AC35_2_empty_handle_raises_projection_error():
    """A contract with an empty handle (built via model_construct
    bypass) raises AgentMdProjectionError, not silent garbage."""
    base = PersonaContract.model_validate(_base_contract_dict())
    # model_construct bypasses Pydantic validation.
    bad = base.model_copy(update={"handle": ""})
    # Pydantic's strict validators on the field still run; force-set
    # via model_construct.
    bad = PersonaContract.model_construct(
        **{**base.model_dump(), "handle": ""}
    )
    with pytest.raises(AgentMdProjectionError):
        to_agent_md(bad)


def test_AC35_2_empty_given_name_raises_projection_error():
    base = PersonaContract.model_validate(_base_contract_dict())
    bad = PersonaContract.model_construct(
        **{**base.model_dump(), "given_name": ""}
    )
    with pytest.raises(AgentMdProjectionError):
        to_agent_md(bad)


def test_AC35_2_whitespace_responsibilities_raises_projection_error():
    """Whitespace-only single_point_of_contact (built via
    model_construct bypass) raises AgentMdProjectionError when the
    description-deriver tries to render."""
    from loam.primary_persona.contract import Responsibilities

    base = PersonaContract.model_validate(_base_contract_dict())
    bad_responsibilities = Responsibilities.model_construct(
        single_point_of_contact="   ",
        context_holder=base.responsibilities.context_holder,
        escalation_judge=base.responsibilities.escalation_judge,
    )
    bad = PersonaContract.model_construct(
        **{**base.model_dump(), "responsibilities": bad_responsibilities}
    )
    with pytest.raises(AgentMdProjectionError):
        to_agent_md(bad)
