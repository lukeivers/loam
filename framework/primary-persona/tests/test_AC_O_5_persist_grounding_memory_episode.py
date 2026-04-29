"""AC.O.5 — ``persist_grounding`` writes a tagged-learning memory
episode.

When ``persist_grounding`` is invoked with a memory client
available (the live MCP client per the in-flight Stop-hook
plan's ``_default_memory_client_factory``), it writes one
episode through ``add_episode`` with ``source_description`` set
to the deterministic onboarding-grounding tag
(``"onboarding-grounding"``) and a body containing the captured
summary bullets + the inferred fields.

When no memory client is available (factory returns None — the
pre-Stop-hook-landing state), the function does not raise; the
disk write-back succeeds; no episode is attempted.

When the memory client is available but ``add_episode`` raises,
the function does not raise; the disk write-back succeeds; the
episode-write failure is observable via an event but not via an
exception to the caller.

Plan: docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.contract import PersonaContract
from src.onboarding import GroundingCapture, persist_grounding


def _starter_contract_dict() -> dict:
    return {
        "handle": "iris",
        "given_name": "Iris",
        "contract_version": "1.0.0",
        "responsibilities": {
            "single_point_of_contact": "Coordinator.",
            "context_holder": "Carries context.",
            "escalation_judge": "Routes escalations.",
        },
        "authority_boundary": {
            "tier_a": "defer",
            "tier_b": "defer",
            "tier_c": "execute",
            "tier_d": "defer",
        },
        "escalation_taxonomy": {"categories": ["x"]},
        "severity_vocabulary": {"labels": ["a", "b"]},
        "is_starter": True,
    }


def _grounding() -> GroundingCapture:
    return GroundingCapture(
        user_preferred_name="Luke",
        persona_given_name="Aurelia",
        single_point_of_contact="Coordinator for ops.",
        context_holder="Holds cross-session context.",
        escalation_judge="Routes irreversible moves.",
        dev_intent="no",
        captured_summary=(
            "Mornings are when the real work gets done.",
            "Afternoons are getting eaten by Slack.",
        ),
    )


@dataclass
class _FakeLoadedPersona:
    contract: PersonaContract
    directory: Path | None = None


def _seed(tmp_path: Path) -> tuple[_FakeLoadedPersona, Path]:
    contract = PersonaContract.model_validate(_starter_contract_dict())
    persona_dir = tmp_path / "personas" / "iris"
    persona_dir.mkdir(parents=True)
    contract_path = persona_dir / "contract.yaml"
    contract_path.write_text(contract.to_yaml())
    (tmp_path / ".claude" / "agents").mkdir(parents=True)
    return _FakeLoadedPersona(contract=contract, directory=persona_dir), contract_path


# ---- fakes -----------------------------------------------------------


class _SyncFakeMemoryClient:
    """Sync fake — captures add_episode calls; returns a dict.
    Mirrors the MemoryClient Protocol surface but synchronously
    so the test can inspect calls without asyncio.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def add_episode(
        self,
        *,
        name: str,
        body: str,
        source_description: str,
        reference_time: datetime,
        source: str,
        group_id: str,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "name": name,
                "body": body,
                "source_description": source_description,
                "reference_time": reference_time,
                "source": source,
                "group_id": group_id,
            }
        )
        return {"episode_uuid": "fake-uuid", "nodes_extracted": 0, "edges_extracted": 0}


class _RaisingFakeMemoryClient:
    def add_episode(self, **kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("memory-down")


# ---- tests -----------------------------------------------------------


def test_AC_O_5_factory_returns_client_writes_one_episode(tmp_path: Path):
    """A factory that returns a non-None client: persist_grounding
    drives one add_episode call with the onboarding-grounding tag."""
    persona, contract_path = _seed(tmp_path)
    client = _SyncFakeMemoryClient()
    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
        memory_client_factory=lambda: client,
    )
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["source_description"] == "onboarding-grounding"


def test_AC_O_5_episode_body_contains_captured_summary(tmp_path: Path):
    """The episode body carries the captured-summary bullets."""
    persona, contract_path = _seed(tmp_path)
    client = _SyncFakeMemoryClient()
    grounding = _grounding()
    persist_grounding(
        loaded_persona=persona,
        grounding=grounding,
        contract_path=contract_path,
        memory_client_factory=lambda: client,
    )
    body = client.calls[0]["body"]
    for bullet in grounding.captured_summary:
        assert bullet in body


def test_AC_O_5_factory_returns_none_no_episode_attempted(tmp_path: Path):
    """A factory that returns None: no add_episode call attempted;
    disk write-back still succeeds."""
    persona, contract_path = _seed(tmp_path)
    new_contract = persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
        memory_client_factory=lambda: None,
    )
    # Disk write-back observable: contract reload reflects new state.
    assert new_contract.is_starter is False
    assert new_contract.given_name == "Aurelia"


def test_AC_O_5_no_factory_no_episode_attempted(tmp_path: Path):
    """When memory_client_factory is omitted entirely, no episode
    is attempted; disk write-back still succeeds."""
    persona, contract_path = _seed(tmp_path)
    new_contract = persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
    )
    assert new_contract.is_starter is False


def test_AC_O_5_raising_client_does_not_propagate(
    tmp_path: Path, span_exporter_clean
):
    """A raising client: persist_grounding does not raise; disk
    write-back succeeds; an episode-failure event is emitted."""
    persona, contract_path = _seed(tmp_path)
    client = _RaisingFakeMemoryClient()

    new_contract = persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
        memory_client_factory=lambda: client,
    )
    # Disk write-back succeeded.
    assert new_contract.is_starter is False
    # Episode-failure event emitted.
    spans = span_exporter_clean.get_finished_spans()
    failure_events = [
        ev
        for sp in spans
        for ev in sp.events
        if ev.name == "loam.persona.onboarding.grounding_episode_failed"
    ]
    assert len(failure_events) == 1
    attrs = dict(failure_events[0].attributes)
    assert "RuntimeError" in attrs["loam.persona.onboarding.grounding_episode.error"]


def test_AC_O_5_raising_factory_does_not_propagate(
    tmp_path: Path, span_exporter_clean
):
    """A factory itself that raises: persist_grounding swallows;
    disk write-back succeeds; failure event emitted."""
    persona, contract_path = _seed(tmp_path)

    def _bad_factory() -> Any:
        raise RuntimeError("factory-down")

    new_contract = persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
        memory_client_factory=_bad_factory,
    )
    assert new_contract.is_starter is False
    spans = span_exporter_clean.get_finished_spans()
    failure_events = [
        ev
        for sp in spans
        for ev in sp.events
        if ev.name == "loam.persona.onboarding.grounding_episode_failed"
    ]
    assert len(failure_events) == 1


def test_AC_O_5_episode_uses_workspace_slug_when_provided(tmp_path: Path):
    """The episode's group_id is the workspace_slug when supplied."""
    persona, contract_path = _seed(tmp_path)
    client = _SyncFakeMemoryClient()
    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
        workspace_slug="my-workspace",
        memory_client_factory=lambda: client,
    )
    assert client.calls[0]["group_id"] == "my-workspace"


def test_AC_O_5_episode_falls_back_to_handle_when_slug_absent(tmp_path: Path):
    """The episode's group_id falls back to the persona handle when
    no workspace_slug is provided."""
    persona, contract_path = _seed(tmp_path)
    client = _SyncFakeMemoryClient()
    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
        memory_client_factory=lambda: client,
    )
    assert client.calls[0]["group_id"] == "iris"


def test_AC_O_5_grounding_persisted_event_emitted(
    tmp_path: Path, span_exporter_clean
):
    """A successful persist_grounding emits the grounding-persisted
    event."""
    persona, contract_path = _seed(tmp_path)
    persist_grounding(
        loaded_persona=persona,
        grounding=_grounding(),
        contract_path=contract_path,
    )
    spans = span_exporter_clean.get_finished_spans()
    events = [
        ev
        for sp in spans
        for ev in sp.events
        if ev.name == "loam.persona.onboarding.grounding_persisted"
    ]
    assert len(events) == 1
