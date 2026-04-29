"""AC.O.2 — Starter-pending contributor body points at the playbook,
not at a question list.

``build_starter_pending_contributor(loaded_persona)`` returns a
contributor whose body, when invoked under a starter-flagged
contract:

  - has ``STARTER_PENDING_MARKER`` as the first line (preserved
    structural marker);
  - references the playbook in ``prompt.md``;
  - names the ``persist_grounding`` write-back surface;
  - names the resolved contract path;
  - does NOT carry a numbered question list (no ``id=user_name``,
    ``id=persona_given_name``, ``id=domain_focus``,
    ``id=dev_intent`` markers — the AC35.3 / AC.A.4 question-list
    shape is replaced);
  - is ≤ 2,000 chars.

Under a non-starter contract the contributor returns the empty
string.

Plan: docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loam.primary_persona.contract import PersonaContract
from loam.primary_persona.onboarding import (
    STARTER_PENDING_MARKER,
    build_starter_pending_contributor,
)


def _starter_contract() -> PersonaContract:
    return PersonaContract.model_validate(
        {
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
        }
    )


def _non_starter_contract() -> PersonaContract:
    return PersonaContract.model_validate(
        {
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
        }
    )


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract
    directory: Path | None = None


def test_AC_O_2_marker_is_first_line():
    persona = _FakeLoadedPersona(contract=_starter_contract())
    body = build_starter_pending_contributor(persona)({})
    assert body.splitlines()[0] == STARTER_PENDING_MARKER


def test_AC_O_2_body_references_playbook_and_prompt_md():
    persona = _FakeLoadedPersona(contract=_starter_contract())
    body = build_starter_pending_contributor(persona)({})
    assert "playbook" in body
    assert "prompt.md" in body


def test_AC_O_2_body_names_persist_grounding():
    persona = _FakeLoadedPersona(contract=_starter_contract())
    body = build_starter_pending_contributor(persona)({})
    assert "persist_grounding" in body


def test_AC_O_2_body_names_contract_path_when_directory_known():
    persona = _FakeLoadedPersona(
        contract=_starter_contract(),
        directory=Path("/example/personas/iris"),
    )
    body = build_starter_pending_contributor(persona)({})
    # The body should include the path the loaded persona's
    # directory resolves to.
    assert "contract.yaml" in body
    assert "/example/personas/iris" in body


def test_AC_O_2_body_names_placeholder_path_when_directory_unknown():
    persona = _FakeLoadedPersona(contract=_starter_contract())
    body = build_starter_pending_contributor(persona)({})
    # When directory is None, the body falls back to the
    # placeholder shape so the persona has a stable surface to
    # report.
    assert "<workspace>" in body or "workspace" in body
    assert "contract.yaml" in body


def test_AC_O_2_body_omits_old_question_id_list_markers():
    """The new body must not contain the prior elicitation's
    ``id=<question_id>`` markers — the question-list shape is the
    structural pattern this rewrite replaces."""
    persona = _FakeLoadedPersona(
        contract=_starter_contract(),
        directory=Path("/example/personas/iris"),
    )
    body = build_starter_pending_contributor(persona)({})
    for q_id in ("user_name", "persona_given_name", "domain_focus"):
        assert f"id={q_id}" not in body, (
            f"body still carries question-list marker id={q_id!r}"
        )


def test_AC_O_2_body_within_2000_char_budget():
    persona = _FakeLoadedPersona(
        contract=_starter_contract(),
        directory=Path("/example/personas/iris"),
    )
    body = build_starter_pending_contributor(persona)({})
    assert len(body) <= 2000, (
        f"starter-pending body exceeded 2,000-char budget: "
        f"{len(body)} chars"
    )


def test_AC_O_2_non_starter_contract_returns_empty():
    persona = _FakeLoadedPersona(contract=_non_starter_contract())
    body = build_starter_pending_contributor(persona)({})
    assert body == ""
