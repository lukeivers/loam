# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC35.7 — Observability for the renderer lifecycle.

Each renderer call emits a span/event under
``loam.persona.onboarding.render``. The events carry handle as an
attribute.

Amendment #50 retired the transcript-write-back surface; the
question / answer / writeback events that the prior shape fired
are replaced by AC.O.5's ``grounding_persisted`` +
``grounding_episode_failed`` events (see
``test_AC_O_5_persist_grounding_memory_episode.py``). The
renderer-event tests are preserved here.

Plan: docs/plans/amendment-35-primary-persona-renderer-and-onboarding.md
      docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from loam.primary_persona.agent_md import to_agent_md
from loam.primary_persona.contract import PersonaContract


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
    render_events = _events_named(spans, "loam.persona.onboarding.render")
    assert len(render_events) == 1
    attrs = dict(render_events[0].attributes)
    assert attrs["loam.persona.onboarding.handle"] == contract.handle
    assert attrs["loam.persona.onboarding.render.length"] > 0


def test_AC35_7_render_called_twice_emits_two_events(span_exporter_clean):
    """Each call emits its own event (no caching)."""
    contract = _starter_contract()
    to_agent_md(contract)
    to_agent_md(contract)
    spans = span_exporter_clean.get_finished_spans()
    render_events = _events_named(spans, "loam.persona.onboarding.render")
    assert len(render_events) == 2


def test_AC35_7_event_attributes_under_persona_namespace(span_exporter_clean):
    """All onboarding events live under `loam.persona.onboarding.*`."""
    contract = _starter_contract()
    to_agent_md(contract)
    spans = span_exporter_clean.get_finished_spans()
    onboarding_events = [
        ev
        for span in spans
        for ev in span.events
        if ev.name.startswith("loam.persona.onboarding.")
    ]
    assert len(onboarding_events) >= 1
    for ev in onboarding_events:
        # All attributes should also be namespaced (the renderer-event
        # attributes start with loam.persona.onboarding.).
        for k in ev.attributes.keys():
            assert k.startswith("loam.persona.onboarding."), (
                f"event attribute {k!r} not under loam.persona.onboarding namespace"
            )
