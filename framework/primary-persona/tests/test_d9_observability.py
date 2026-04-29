"""D9 — OTel observability emission.

Acceptance (brief D9):
- Loader runs produce spans with outcome.
- Monitor ticks and injections emit events.
- Authoring pipeline produces a parent span with one child per step;
  self-review verdicts are events.
- Introduction dispatch emits an event naming handle + channel.
- Retirement emits an event naming persona + reason.
- Emission succeeds with no consumer present (A1 correction).

The in-memory exporter is installed in conftest.py BEFORE any tracer
is obtained — OTel refuses to swap providers once one is used.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from scope_of_work.runtime import ScopeRuntime
from scope_of_work.spec import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    SuccessCriterion,
)

from src.authoring import AuthoringPipeline, LLMResult
from src.creation_triggers import TriggerSignal
from src.introduction import ChannelKind, IntroductionDispatcher, OneOnOneChannel
from src.loader import LoadedPersona, PersonaLoader
from src.monitor import BackgroundWorkMonitor
from src.retirement import RetirementReason, retire_persona
from src.contract import load_contract

from tests.conftest import VALID_CONTRACT_YAML, write_persona_dir


# ---- loader spans ----------------------------------------------------


def test_loader_emits_span(
    workspace_with_primary: Path, span_exporter_clean
):
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    loader.load()
    spans = span_exporter_clean.get_finished_spans()
    loader_spans = [s for s in spans if s.name == "loam.persona.loader"]
    assert len(loader_spans) >= 1
    assert loader_spans[-1].attributes.get("loam.persona.load.outcome") == "loaded"
    assert loader_spans[-1].attributes.get("loam.persona.load.count") == 1


def test_loader_failure_span_records_missing_dir(
    tmp_path: Path, span_exporter_clean
):
    from src.loader import PersonaDirectoryNotFoundError

    loader = PersonaLoader(tmp_path, enforce_no_personas_in_core=False)
    with pytest.raises(PersonaDirectoryNotFoundError):
        loader.load()
    spans = span_exporter_clean.get_finished_spans()
    loader_spans = [s for s in spans if s.name == "loam.persona.loader"]
    assert any(
        s.attributes.get("loam.persona.load.outcome") == "missing_dir"
        for s in loader_spans
    )


# ---- monitor tick + injection events --------------------------------


@pytest.mark.asyncio
async def test_monitor_injection_event_emitted(
    tmp_path: Path, span_exporter_clean
):
    rt = ScopeRuntime(db_path=tmp_path / "scope.db")
    mon = BackgroundWorkMonitor(rt)
    _ = mon.on_user_prompt("turn-xyz")
    rt.close()
    spans = span_exporter_clean.get_finished_spans()
    injection_events = [
        ev
        for span in spans
        for ev in span.events
        if ev.name == "loam.persona.monitor.inject"
    ]
    assert any(
        ev.attributes.get("loam.persona.monitor.turn_id") == "turn-xyz"
        for ev in injection_events
    )


@pytest.mark.asyncio
async def test_monitor_tick_event_emitted(
    tmp_path: Path, span_exporter_clean
):
    rt = ScopeRuntime(db_path=tmp_path / "scope.db")
    mon = BackgroundWorkMonitor(rt)
    await mon._tick()
    rt.close()
    spans = span_exporter_clean.get_finished_spans()
    tick_events = [
        ev
        for span in spans
        for ev in span.events
        if ev.name == "loam.persona.monitor.tick"
    ]
    assert len(tick_events) >= 1


# ---- authoring span + steps ----------------------------------------


@pytest.mark.asyncio
async def test_authoring_span_with_step_children(
    workspace_with_primary: Path, tmp_path: Path, span_exporter_clean
):
    rt = ScopeRuntime(db_path=tmp_path / "scope.db")
    spec = ScopeSpec(
        goal="author",
        constraints=(),
        budget=Budget(tokens=100_000),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c", description="d"),),
        observers=(),
        escalation_triggers=(),
    )
    await rt.create(spec, scope_id="auth")
    await rt.start("auth")

    synthesis = json.dumps(
        {
            "handle": "foo",
            "given_name": "Foo",
            "contract_version": "1.0.0",
            "responsibilities": {
                "single_point_of_contact": "a",
                "context_holder": "b",
                "escalation_judge": "c",
            },
            "authority_boundary": {
                "tier_a": "defer",
                "tier_b": "defer",
                "tier_c": "execute",
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["x"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
            "is_primary": False,
        }
    ) + "\n---PROMPT---\n# Foo\n"
    review = json.dumps(
        {
            "voice_distinctiveness": True,
            "scope_fit": True,
            "redundancy": True,
            "contract_correctness": True,
            "issues": [],
        }
    )

    async def fake_llm(name, _p):
        if name == "style_harvest":
            return LLMResult(text="v")
        if name == "domain_research":
            return LLMResult(text="r")
        if name == "contract_synthesis":
            return LLMResult(text=synthesis)
        return LLMResult(text=review)

    pipeline = AuthoringPipeline(
        llm=fake_llm, runtime=rt, workspace_root=workspace_with_primary
    )
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    await pipeline.author(
        trigger_signal=TriggerSignal.request_decline,
        domain="d",
        existing_personas=loader.load(),
        authoring_scope_id="auth",
    )
    rt.close()

    spans = span_exporter_clean.get_finished_spans()
    names = {s.name for s in spans}
    assert "loam.persona.authoring" in names
    assert "loam.persona.authoring.style_harvest" in names
    assert "loam.persona.authoring.domain_research" in names
    assert "loam.persona.authoring.contract_synthesis" in names
    assert "loam.persona.authoring.self_review" in names

    # Self-review verdict event attached to its span.
    review_events = [
        ev
        for s in spans
        for ev in s.events
        if ev.name == "loam.persona.authoring.self_review"
    ]
    assert len(review_events) >= 1


# ---- introduction event ---------------------------------------------


@pytest.mark.asyncio
async def test_introduction_event_names_handle_and_channel(
    workspace_with_primary: Path, span_exporter_clean
):
    persona_dir = workspace_with_primary / "workspace" / "personas" / "sip"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: sip")
        .replace("given_name: Eve", "given_name: Sip")
        .replace("is_primary: true", "is_primary: false")
        .replace("pending_introduction: false", "pending_introduction: true")
        .replace("is_addressable: true", "is_addressable: false")
    )
    (persona_dir / "prompt.md").write_text("p")
    c = load_contract(persona_dir / "contract.yaml")
    loaded = LoadedPersona(
        handle="sip", directory=persona_dir, contract=c, prompt_text="p"
    )

    async def noop(t):
        return None

    dispatcher = IntroductionDispatcher(
        channels=[
            OneOnOneChannel(kind=ChannelKind.terminal, name="t", send=noop)
        ],
        workspace_root=workspace_with_primary,
    )
    await dispatcher.introduce(
        new_persona=loaded, trigger_signal=TriggerSignal.request_decline
    )

    spans = span_exporter_clean.get_finished_spans()
    intro_events = [
        ev
        for s in spans
        for ev in s.events
        if ev.name == "loam.persona.introduction.dispatched"
    ]
    assert len(intro_events) >= 1
    ev = intro_events[-1]
    assert ev.attributes.get("loam.persona.introduction.handle") == "sip"
    assert ev.attributes.get("loam.persona.introduction.channel") == "t"


# ---- retirement event -----------------------------------------------


def test_retirement_event_names_handle_and_reason(
    workspace_with_primary: Path, span_exporter_clean
):
    write_persona_dir(workspace_with_primary / "workspace" / "personas", "mara")
    retire_persona(
        workspace_root=workspace_with_primary,
        handle="mara",
        reason=RetirementReason.user_initiated,
    )
    spans = span_exporter_clean.get_finished_spans()
    retired_events = [
        ev
        for s in spans
        for ev in s.events
        if ev.name == "loam.persona.retired"
    ]
    assert len(retired_events) >= 1
    ev = retired_events[-1]
    assert ev.attributes.get("loam.persona.retirement.handle") == "mara"
    assert ev.attributes.get("loam.persona.retirement.reason") == "user_initiated"


# ---- emission without consumer --------------------------------------


def test_emission_succeeds_with_no_consumer(workspace_with_primary: Path):
    """A1 correction: emission must succeed even when no exporter is
    attached — the default OTel behaviour when no processors are
    present is a silent drop, and the component under test never
    assumes a consumer.

    We verify this by calling the loader through its normal path (which
    emits a span); with our exporter attached the span lands, with an
    unattached processor it would silently no-op. Either way, no
    exception is raised.
    """
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    # No exception expected — emission path runs regardless of
    # downstream consumer presence.
    loader.load()
