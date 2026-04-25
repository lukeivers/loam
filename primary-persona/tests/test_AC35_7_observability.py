"""AC35.7 — Observability for the renderer + onboarding lifecycle.

Each renderer call, each onboarding question dispatched, each answer
recorded, each contract write-back, and each ``is_starter`` transition
emits a span/event under ``pos.persona.onboarding.*``. The events
carry workspace slug + handle as attributes (when applicable).

Plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.agent_md import to_agent_md
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
    """Collect events with the given name across the recorded spans."""
    out = []
    for span in spans:
        for ev in span.events:
            if ev.name == name:
                out.append(ev)
    return out


def test_AC35_7_render_emits_onboarding_render_event(span_exporter_clean):
    """Each `to_agent_md()` invocation emits a render event."""
    contract = _starter_contract()
    to_agent_md(contract)
    spans = span_exporter_clean.get_finished_spans()
    render_events = _events_named(spans, "pos.persona.onboarding.render")
    assert len(render_events) == 1
    attrs = dict(render_events[0].attributes)
    assert attrs["pos.persona.onboarding.handle"] == contract.handle
    assert attrs["pos.persona.onboarding.render.length"] > 0


def test_AC35_7_render_called_twice_emits_two_events(span_exporter_clean):
    """Each call emits its own event (no caching)."""
    contract = _starter_contract()
    to_agent_md(contract)
    to_agent_md(contract)
    spans = span_exporter_clean.get_finished_spans()
    render_events = _events_named(spans, "pos.persona.onboarding.render")
    assert len(render_events) == 2


def test_AC35_7_complete_transcript_emits_full_event_set(
    span_exporter_clean, tmp_path: Path
):
    """A complete transcript fires:
       - one question event per known question
       - one answer event per answered required question
       - one writeback event with completed=True
       - one starter-flag-transition event (True→False)
    """
    contract = _starter_contract()
    persona = _FakeLoadedPersona(contract=contract)
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {
        "user_name": "Luke",
        "persona_given_name": "Aurelia",
        "domain_focus": "Helper for technical research.",
    }
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
        workspace_slug="my-workspace",
    )
    spans = span_exporter_clean.get_finished_spans()

    # Question events: one per ONBOARDING_QUESTIONS entry.
    question_events = _events_named(spans, "pos.persona.onboarding.question")
    assert len(question_events) >= 3
    for ev in question_events:
        attrs = dict(ev.attributes)
        assert attrs["pos.persona.onboarding.handle"] == contract.handle
        assert attrs["pos.persona.onboarding.workspace_slug"] == "my-workspace"

    # Answer events: one per non-empty answered required question.
    answer_events = _events_named(spans, "pos.persona.onboarding.answer")
    assert len(answer_events) == 3  # all three answers non-empty

    # Writeback event: exactly one, completed=True.
    writeback_events = _events_named(spans, "pos.persona.onboarding.writeback")
    assert len(writeback_events) == 1
    wb_attrs = dict(writeback_events[0].attributes)
    assert wb_attrs["pos.persona.onboarding.writeback.completed"] is True
    assert wb_attrs["pos.persona.onboarding.handle"] == contract.handle

    # Starter-flag-transition: True→False.
    flag_events = _events_named(
        spans, "pos.persona.onboarding.starter_flag_transition"
    )
    assert len(flag_events) == 1
    flag_attrs = dict(flag_events[0].attributes)
    assert flag_attrs["pos.persona.onboarding.starter_flag.from"] is True
    assert flag_attrs["pos.persona.onboarding.starter_flag.to"] is False


def test_AC35_7_incomplete_transcript_emits_writeback_with_completed_false(
    span_exporter_clean, tmp_path: Path
):
    """Incomplete transcript: writeback event fires with
    completed=False; no starter-flag-transition event (no transition)."""
    contract = _starter_contract()
    persona = _FakeLoadedPersona(contract=contract)
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(contract.to_yaml())

    transcript = {"user_name": "Luke"}  # missing required questions
    persist_elicitation_transcript(
        loaded_persona=persona,
        transcript=transcript,
        contract_path=contract_path,
    )
    spans = span_exporter_clean.get_finished_spans()

    writeback_events = _events_named(spans, "pos.persona.onboarding.writeback")
    assert len(writeback_events) == 1
    assert (
        dict(writeback_events[0].attributes)[
            "pos.persona.onboarding.writeback.completed"
        ]
        is False
    )

    flag_events = _events_named(
        spans, "pos.persona.onboarding.starter_flag_transition"
    )
    assert len(flag_events) == 0  # no transition (still True)


def test_AC35_7_event_attributes_under_persona_namespace(span_exporter_clean):
    """All onboarding events live under `pos.persona.onboarding.*`."""
    contract = _starter_contract()
    to_agent_md(contract)
    spans = span_exporter_clean.get_finished_spans()
    onboarding_events = [
        ev
        for span in spans
        for ev in span.events
        if ev.name.startswith("pos.persona.onboarding.")
    ]
    assert len(onboarding_events) >= 1
    for ev in onboarding_events:
        # All attributes should also be namespaced (the renderer-event
        # attributes start with pos.persona.onboarding.).
        for k in ev.attributes.keys():
            assert k.startswith("pos.persona.onboarding."), (
                f"event attribute {k!r} not under pos.persona.onboarding namespace"
            )
