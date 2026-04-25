"""AC.A.7 — OTel event surface for the dev-intent answer.

Sub-plan A (two-modes-and-multi-workspace) emits two new event types:

- ``pos.persona.onboarding.dev_intent_question`` — once per starter
  session at question time.
- ``pos.persona.onboarding.dev_intent_answer`` — once when the answer
  is recorded.

Both carry the persona handle + workspace_slug attributes (consistent
with amendment #35's existing event shape). Observability is a
toolkit primitive (AC.PO.2).

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.contract import PersonaContract
from src.onboarding import persist_elicitation_transcript


def _starter_contract() -> PersonaContract:
    return PersonaContract.model_validate(
        {
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
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["x"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
            "is_starter": True,
        }
    )


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract


def _events_named(spans, name: str) -> list:
    out = []
    for span in spans:
        for ev in span.events:
            if ev.name == name:
                out.append(ev)
    return out


def test_AC_A_7_dev_intent_question_event_emitted_with_handle_and_slug(
    span_exporter_clean, tmp_path: Path
):
    """Persisting a transcript that includes dev_intent emits exactly
    one ``pos.persona.onboarding.dev_intent_question`` event carrying
    handle + workspace_slug."""
    contract = _starter_contract()
    persona = _FakeLoadedPersona(contract=contract)
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper.",
        "dev_intent": "yes",
    }
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
        workspace_slug="ws-slug",
    )

    spans = span_exporter_clean.get_finished_spans()
    qevents = _events_named(spans, "pos.persona.onboarding.dev_intent_question")
    assert len(qevents) == 1
    attrs = dict(qevents[0].attributes)
    assert attrs["pos.persona.onboarding.handle"] == contract.handle
    assert attrs["pos.persona.onboarding.workspace_slug"] == "ws-slug"


def test_AC_A_7_dev_intent_answer_event_emitted_with_normalised_value(
    span_exporter_clean, tmp_path: Path
):
    """Persisting a transcript with dev_intent='yes' emits exactly one
    ``pos.persona.onboarding.dev_intent_answer`` event whose answer
    attribute is the normalised contract literal."""
    contract = _starter_contract()
    persona = _FakeLoadedPersona(contract=contract)
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper.",
        "dev_intent": "yes",
    }
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
        workspace_slug="ws-slug",
    )

    spans = span_exporter_clean.get_finished_spans()
    aevents = _events_named(spans, "pos.persona.onboarding.dev_intent_answer")
    assert len(aevents) == 1
    attrs = dict(aevents[0].attributes)
    assert attrs["pos.persona.onboarding.handle"] == contract.handle
    assert attrs["pos.persona.onboarding.dev_intent.answer"] == "yes"
    assert attrs["pos.persona.onboarding.workspace_slug"] == "ws-slug"


def test_AC_A_7_dev_intent_answer_event_normalises_synonym(
    span_exporter_clean, tmp_path: Path
):
    """A free-text synonym ('develop') for yes surfaces in the
    answer event as the normalised literal 'yes' — observability
    captures the contract value, not the user's free-text input."""
    contract = _starter_contract()
    persona = _FakeLoadedPersona(contract=contract)
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper.",
        "dev_intent": "develop",
    }
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )

    spans = span_exporter_clean.get_finished_spans()
    aevents = _events_named(spans, "pos.persona.onboarding.dev_intent_answer")
    assert len(aevents) == 1
    assert (
        dict(aevents[0].attributes)["pos.persona.onboarding.dev_intent.answer"]
        == "yes"
    )


def test_AC_A_7_no_answer_event_when_dev_intent_omitted(
    span_exporter_clean, tmp_path: Path
):
    """If the transcript omits dev_intent, the answer event does NOT
    fire (incomplete transcript). The question event still fires
    (every known question's lifecycle is observed)."""
    contract = _starter_contract()
    persona = _FakeLoadedPersona(contract=contract)
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Iris",
        "domain_focus": "Helper.",
        # dev_intent omitted
    }
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )

    spans = span_exporter_clean.get_finished_spans()
    qevents = _events_named(spans, "pos.persona.onboarding.dev_intent_question")
    aevents = _events_named(spans, "pos.persona.onboarding.dev_intent_answer")
    assert len(qevents) == 1  # question still asked
    assert len(aevents) == 0  # no answer recorded
