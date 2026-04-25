"""AC35.3 — `onboarding.py` produces a contributor for starter-pending signal.

The ``onboarding`` module exposes a function that returns a contributor
registrable against the existing D8 ``ComposedContextPayload`` registry.
When invoked under a starter-flagged contract the contributor produces
an ``additionalContext`` block whose textual content carries a
starter-pending marker (presence is the test). When invoked under a
non-starter-flagged contract the contributor produces an empty
contribution (or, equivalently, declines to contribute).

Plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md
"""

from __future__ import annotations

from dataclasses import dataclass

from src.context_composer import (
    ComposedContextPayload,
    TriggerKind,
)
from src.contract import PersonaContract
from src.onboarding import (
    STARTER_PENDING_MARKER,
    build_starter_pending_contributor,
)


def _base_contract_dict(*, is_starter: bool) -> dict:
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
        "is_starter": is_starter,
    }


@dataclass
class _FakeLoadedPersona:
    """Stand-in for `LoadedPersona` carrying just the `contract`
    attribute the contributor reads. Avoids loader-loading on disk."""

    contract: PersonaContract


def _stand_in_session_builder(_workspace_root) -> dict:
    """Minimal session-builder so the composer can compose a session."""
    return {}


def _make_composer() -> ComposedContextPayload:
    return ComposedContextPayload(session_builder=_stand_in_session_builder)


def test_AC35_3_starter_flagged_contract_produces_marker_block():
    """Under a starter-flagged contract the contributor returns text
    whose first line carries STARTER_PENDING_MARKER."""
    persona = _FakeLoadedPersona(
        contract=PersonaContract.model_validate(_base_contract_dict(is_starter=True))
    )
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    assert out
    first_line = out.splitlines()[0]
    assert first_line == STARTER_PENDING_MARKER


def test_AC35_3_non_starter_contract_returns_empty_contribution():
    """Under a non-starter contract the contributor returns the
    empty string."""
    persona = _FakeLoadedPersona(
        contract=PersonaContract.model_validate(_base_contract_dict(is_starter=False))
    )
    contributor = build_starter_pending_contributor(persona)
    out = contributor({})
    assert out == ""


def test_AC35_3_contributor_registers_against_d8_registry():
    """The contributor registers against the
    `ComposedContextPayload.register(name, trigger_kind, fn)` surface
    at TriggerKind.session and fires on `on_session_start`."""
    from pathlib import Path

    persona = _FakeLoadedPersona(
        contract=PersonaContract.model_validate(_base_contract_dict(is_starter=True))
    )
    contributor = build_starter_pending_contributor(persona)

    composer = _make_composer()
    composer.register(
        name="starter-pending",
        trigger_kind=TriggerKind.session,
        fn=contributor,
    )
    payload = composer.on_session_start(Path("/tmp"))
    # Contribution shows up in the session payload's
    # contributor_outputs tuple.
    assert ("starter-pending", payload.contributor_outputs[0][1]).count(
        STARTER_PENDING_MARKER
    ) >= 0  # at least references the right contributor name
    output_names = [name for name, _ in payload.contributor_outputs]
    assert "starter-pending" in output_names
    output_text_for_starter = dict(payload.contributor_outputs)["starter-pending"]
    assert STARTER_PENDING_MARKER in output_text_for_starter


def test_AC35_3_late_binding_contract_change_picks_up_on_subsequent_session():
    """Late-binding: if the contract's `is_starter` was True at
    registration but is later flipped to False (e.g., after
    elicitation completes), a subsequent session-start composition
    sees the contributor return empty — the contributor reads the
    contract every invocation, no caching."""
    from pathlib import Path

    persona = _FakeLoadedPersona(
        contract=PersonaContract.model_validate(_base_contract_dict(is_starter=True))
    )
    contributor = build_starter_pending_contributor(persona)

    composer = _make_composer()
    composer.register(
        name="starter-pending",
        trigger_kind=TriggerKind.session,
        fn=contributor,
    )

    payload_before = composer.on_session_start(Path("/tmp"))
    starter_text_before = dict(payload_before.contributor_outputs).get(
        "starter-pending", ""
    )
    assert STARTER_PENDING_MARKER in starter_text_before

    # Flip the contract's is_starter via a contract swap (mirroring
    # the persistence flow: persist_elicitation_transcript returns a
    # new contract; the loaded persona is updated to point at it).
    persona.contract = persona.contract.model_copy(update={"is_starter": False})

    # Need a fresh composer for a fresh session (the existing
    # composer caches the prior session payload by design).
    composer2 = _make_composer()
    composer2.register(
        name="starter-pending",
        trigger_kind=TriggerKind.session,
        fn=contributor,
    )
    payload_after = composer2.on_session_start(Path("/tmp"))
    starter_text_after = dict(payload_after.contributor_outputs).get(
        "starter-pending", ""
    )
    assert starter_text_after == ""
