"""D7 — introduction protocol.

Acceptance (brief D7):
- New persona directory persisted with pending_introduction=True and
  is_addressable=False.
- Structured introduction dispatched only to one-on-one channels —
  never to group channels (hard guard).
- If zero one-on-one channels reachable, introduction is queued and
  fires when next channel activates.
- is_addressable flips True only on next non-retire message; retire
  moves to _retired/ without ever flipping it.
- No message identifying new persona as sender can be delivered before
  is_addressable=True.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from src.authoring import AuthoringOutcome, AuthoringPipeline, LLMResult
from src.contract import PersonaContract, load_contract
from src.creation_triggers import TriggerSignal
from src.introduction import (
    ChannelKind,
    IntroductionDispatcher,
    IntroductionOutcome,
    OneOnOneChannel,
)
from src.loader import LoadedPersona, PersonaLoader

from tests.conftest import VALID_CONTRACT_YAML, write_persona_dir


# ---- one-on-one channel invariant -----------------------------------


def test_one_on_one_channel_rejects_is_group_true():
    async def noop_send(_t):
        return None

    with pytest.raises(ValueError):
        OneOnOneChannel(
            kind=ChannelKind.personal_telegram,
            name="scotch-lovers-chat",
            send=noop_send,
            is_group=True,
        )


def test_dispatcher_rejects_group_channel(tmp_path: Path):
    async def noop(_t):
        return None

    ch = OneOnOneChannel(
        kind=ChannelKind.terminal, name="t", send=noop, is_group=False
    )
    # Cannot construct a group channel directly — but if a caller
    # bypasses the dataclass invariant the dispatcher still guards.
    object.__setattr__(ch, "is_group", True)

    with pytest.raises(ValueError):
        IntroductionDispatcher(channels=[ch], workspace_root=tmp_path)


# ---- delivery -------------------------------------------------------


@pytest.mark.asyncio
async def test_introduction_delivered_to_active_channel(
    workspace_with_primary: Path,
):
    captured: list[str] = []

    async def fake_send(text: str) -> None:
        captured.append(text)

    terminal = OneOnOneChannel(
        kind=ChannelKind.terminal, name="terminal-1", send=fake_send
    )
    dispatcher = IntroductionDispatcher(
        channels=[terminal], workspace_root=workspace_with_primary
    )

    # Persist a pending persona (as authoring would).
    persona_dir = workspace_with_primary / "workspace" / "personas" / "sip"
    persona_dir.mkdir(parents=True)
    contract_yaml = (
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: sip")
        .replace("given_name: Eve", "given_name: Sip")
        .replace("pending_introduction: false", "pending_introduction: true")
        .replace("is_addressable: true", "is_addressable: false")
        .replace("is_primary: true", "is_primary: false")
    )
    (persona_dir / "contract.yaml").write_text(contract_yaml)
    (persona_dir / "prompt.md").write_text("# Sip\n")

    contract = load_contract(persona_dir / "contract.yaml")
    loaded = LoadedPersona(
        handle="sip",
        directory=persona_dir,
        contract=contract,
        prompt_text="# Sip\n",
    )

    record = await dispatcher.introduce(
        new_persona=loaded,
        trigger_signal=TriggerSignal.explicit_user_mention,
    )
    assert record.outcome == IntroductionOutcome.delivered
    assert record.channel_used == "terminal-1"
    assert len(captured) == 1
    assert "Sip" in captured[0] and "sip" in captured[0]


@pytest.mark.asyncio
async def test_introduction_queued_when_no_active_channel(
    workspace_with_primary: Path,
):
    async def noop(_t):
        return None

    inactive = OneOnOneChannel(
        kind=ChannelKind.terminal,
        name="dormant",
        send=noop,
        is_active=False,
    )
    dispatcher = IntroductionDispatcher(
        channels=[inactive], workspace_root=workspace_with_primary
    )

    persona_dir = workspace_with_primary / "workspace" / "personas" / "sip"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: sip")
        .replace("pending_introduction: false", "pending_introduction: true")
        .replace("is_addressable: true", "is_addressable: false")
        .replace("is_primary: true", "is_primary: false")
    )
    (persona_dir / "prompt.md").write_text("# Sip\n")

    contract = load_contract(persona_dir / "contract.yaml")
    loaded = LoadedPersona(
        handle="sip",
        directory=persona_dir,
        contract=contract,
        prompt_text="# Sip\n",
    )

    record = await dispatcher.introduce(
        new_persona=loaded, trigger_signal=TriggerSignal.request_decline
    )
    assert record.outcome == IntroductionOutcome.queued_no_channel
    assert record.channel_used is None


@pytest.mark.asyncio
async def test_flush_queue_delivers_when_channel_activates(
    workspace_with_primary: Path,
):
    captured: list[str] = []

    async def record(text: str) -> None:
        captured.append(text)

    channel = OneOnOneChannel(
        kind=ChannelKind.terminal,
        name="terminal-1",
        send=record,
        is_active=False,
    )
    dispatcher = IntroductionDispatcher(
        channels=[channel], workspace_root=workspace_with_primary
    )

    persona_dir = workspace_with_primary / "workspace" / "personas" / "sip"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: sip")
        .replace("pending_introduction: false", "pending_introduction: true")
        .replace("is_addressable: true", "is_addressable: false")
        .replace("is_primary: true", "is_primary: false")
    )
    (persona_dir / "prompt.md").write_text("# Sip\n")

    contract = load_contract(persona_dir / "contract.yaml")
    loaded = LoadedPersona(
        handle="sip",
        directory=persona_dir,
        contract=contract,
        prompt_text="# Sip\n",
    )

    # Queue first.
    queued = await dispatcher.introduce(
        new_persona=loaded, trigger_signal=TriggerSignal.request_decline
    )
    assert queued.outcome == IntroductionOutcome.queued_no_channel

    # Activate channel; flush.
    object.__setattr__(channel, "is_active", True)
    delivered = await dispatcher.flush_queue()
    assert len(delivered) == 1
    assert delivered[0].outcome == IntroductionOutcome.delivered
    assert len(captured) == 1


# ---- addressability transitions --------------------------------------


def test_make_addressable_flips_flags(workspace_with_primary: Path):
    persona_dir = workspace_with_primary / "workspace" / "personas" / "sip"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: sip")
        .replace("pending_introduction: false", "pending_introduction: true")
        .replace("is_addressable: true", "is_addressable: false")
        .replace("is_primary: true", "is_primary: false")
    )
    (persona_dir / "prompt.md").write_text("p")

    dispatcher = IntroductionDispatcher(
        channels=[],
        workspace_root=workspace_with_primary,
    )
    dispatcher.make_addressable("sip")

    reread = load_contract(persona_dir / "contract.yaml")
    assert reread.pending_introduction is False
    assert reread.is_addressable is True


# ---- guard: message cannot be sent before addressable ---------------


def test_guard_raises_for_pending_persona(workspace_with_primary: Path):
    persona_dir = workspace_with_primary / "workspace" / "personas" / "sip"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        VALID_CONTRACT_YAML.replace("handle: eve", "handle: sip")
        .replace("pending_introduction: false", "pending_introduction: true")
        .replace("is_addressable: true", "is_addressable: false")
        .replace("is_primary: true", "is_primary: false")
    )
    (persona_dir / "prompt.md").write_text("p")
    contract = load_contract(persona_dir / "contract.yaml")
    pending = LoadedPersona(
        handle="sip",
        directory=persona_dir,
        contract=contract,
        prompt_text="p",
    )
    with pytest.raises(RuntimeError) as exc:
        IntroductionDispatcher.assert_not_sent_before_addressable(
            pending, sender_handle="sip"
        )
    assert "not addressable" in str(exc.value)


def test_guard_allows_addressable_persona(workspace_with_primary: Path):
    persona_dir = workspace_with_primary / "workspace" / "personas" / "eve"
    contract = load_contract(persona_dir / "contract.yaml")
    loaded = LoadedPersona(
        handle="eve", directory=persona_dir, contract=contract, prompt_text="x"
    )
    # No exception expected.
    IntroductionDispatcher.assert_not_sent_before_addressable(
        loaded, sender_handle="eve"
    )


def test_guard_ignores_mismatched_handle(workspace_with_primary: Path):
    # Guard is only checking the persona identified as sender; if the
    # persona given is a different handle, guard is a no-op.
    persona_dir = workspace_with_primary / "workspace" / "personas" / "eve"
    contract = load_contract(persona_dir / "contract.yaml")
    loaded = LoadedPersona(
        handle="eve", directory=persona_dir, contract=contract, prompt_text="x"
    )
    IntroductionDispatcher.assert_not_sent_before_addressable(
        loaded, sender_handle="someone-else"
    )


# ---- end-to-end: authoring -> intro -> acknowledgement -------------


@pytest.mark.asyncio
async def test_authored_persona_is_not_addressable_until_acknowledged(
    workspace_with_primary: Path, tmp_path: Path
):
    """Integration: authoring pipeline persists a pending persona;
    the introduction protocol guards it until acknowledged."""
    from scope_of_work.runtime import ScopeRuntime
    from scope_of_work.spec import Budget, ScopeSpec, SuccessCriterion, ReversibilityClass
    import json as _json

    rt = ScopeRuntime(db_path=tmp_path / "scope.db")

    spec = ScopeSpec(
        goal="author",
        constraints=(),
        budget=Budget(tokens=100_000),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(SuccessCriterion(criterion_id="c1", description="d"),),
        observers=(),
        escalation_triggers=(),
    )
    await rt.create(spec, scope_id="s-auth")
    await rt.start("s-auth")

    synthesis_output = _json.dumps(
        {
            "handle": "nellie",
            "given_name": "Nellie",
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
    ) + "\n---PROMPT---\n# Nellie\n"
    review_output = _json.dumps(
        {
            "voice_distinctiveness": True,
            "scope_fit": True,
            "redundancy": True,
            "contract_correctness": True,
            "issues": [],
        }
    )

    async def fake_llm(name, _prompt):
        if name == "style_harvest":
            return LLMResult(text="v")
        if name == "domain_research":
            return LLMResult(text="r")
        if name == "contract_synthesis":
            return LLMResult(text=synthesis_output)
        if name.startswith("self_review"):
            return LLMResult(text=review_output)
        raise AssertionError(f"unexpected prompt {name!r}")

    pipeline = AuthoringPipeline(
        llm=fake_llm, runtime=rt, workspace_root=workspace_with_primary
    )
    loader = PersonaLoader(
        workspace_with_primary, enforce_no_personas_in_core=False
    )
    result = await pipeline.author(
        trigger_signal=TriggerSignal.explicit_user_mention,
        domain="shopping",
        existing_personas=loader.load(),
        authoring_scope_id="s-auth",
    )
    assert result.outcome == AuthoringOutcome.persisted

    # Load persona; must be pending + not addressable.
    new_contract = load_contract(result.persona_dir / "contract.yaml")
    assert new_contract.pending_introduction is True
    assert new_contract.is_addressable is False

    new_loaded = LoadedPersona(
        handle="nellie",
        directory=result.persona_dir,
        contract=new_contract,
        prompt_text="# Nellie\n",
    )

    # Guard rejects sending as this persona before acknowledgement.
    with pytest.raises(RuntimeError):
        IntroductionDispatcher.assert_not_sent_before_addressable(
            new_loaded, sender_handle="nellie"
        )

    # Now introduce + acknowledge:
    captured: list[str] = []

    async def sendit(t):
        captured.append(t)

    dispatcher = IntroductionDispatcher(
        channels=[
            OneOnOneChannel(
                kind=ChannelKind.terminal, name="t", send=sendit
            )
        ],
        workspace_root=workspace_with_primary,
    )
    record = await dispatcher.introduce(
        new_persona=new_loaded,
        trigger_signal=TriggerSignal.explicit_user_mention,
    )
    assert record.outcome == IntroductionOutcome.delivered

    # User acknowledges; flag flips.
    dispatcher.make_addressable("nellie")
    reread = load_contract(result.persona_dir / "contract.yaml")
    reread_loaded = LoadedPersona(
        handle="nellie",
        directory=result.persona_dir,
        contract=reread,
        prompt_text="# Nellie\n",
    )
    # Guard now allows — no exception.
    IntroductionDispatcher.assert_not_sent_before_addressable(
        reread_loaded, sender_handle="nellie"
    )
    rt.close()
