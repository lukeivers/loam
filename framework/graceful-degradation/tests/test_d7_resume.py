"""D7 — Resume mechanism.

Acceptance (brief):
- Each transient mode auto-resumes after N consecutive probes.
- Auth-broken requires explicit user confirmation via notification.
- Any episode in dwell > 30min gates resume regardless of mode.
- Resume calls orchestrator.resume_activation(); paused scopes resume.
"""

from __future__ import annotations

import pytest

from loam.graceful_degradation import (
    ClaudeClient,
    DegradationComponent,
    DegradationConfig,
    DegradationMode,
    DegradationNotifier,
    FSMState,
)
from loam.graceful_degradation.state import DegradationStore

from .fakes import (
    FakeClock,
    FakeInvoker,
    FakeOrchestrator,
    FakeScope,
    FakeScopeRuntime,
    make_capture_channel,
)


def _build_component(
    *,
    tmp_path,
    script,
    clock=None,
):
    clock = clock or FakeClock()
    cfg = DegradationConfig()
    # Point SQLite at tmp_path to avoid polluting ~/.loam.
    cfg = DegradationConfig.model_validate(
        {**cfg.model_dump(), "state": {"sqlite_path": str(tmp_path / "deg.sqlite")}}
    )
    invoker = FakeInvoker(script, default="OK")
    orch = FakeOrchestrator()
    rt = FakeScopeRuntime()
    ch, sent = make_capture_channel()
    notifier = DegradationNotifier(channels=[ch])
    client = ClaudeClient(invoke=invoker, clock=clock)
    comp = DegradationComponent.build(
        cfg=cfg,
        orchestrator=orch,
        scope_runtime=rt,
        notifier=notifier,
        client=client,
        clock=clock,
    )
    return comp, orch, rt, notifier, client, invoker, clock, sent


async def test_auto_resume_for_down_after_probe_succeeds(tmp_path) -> None:
    # Script: 3 connection errors (trip), then "OK" (probe success).
    comp, orch, rt, notifier, client, invoker, clock, sent = _build_component(
        tmp_path=tmp_path,
        script=[
            ConnectionError("x"),
            ConnectionError("x"),
            ConnectionError("x"),
            "OK",  # probe
        ],
    )
    rt.add_scope(FakeScope("s1"))

    # Drive failures through the client — these feed the detector via on_event.
    from loam.graceful_degradation.errors import ClaudeAPIError

    for _ in range(3):
        try:
            await client.call(prompt_name="memory.extraction", text="x")
        except ClaudeAPIError:
            pass

    # FSM should be open; episode active.
    fsm = comp.detector.fsms[DegradationMode.down]
    assert fsm.state == FSMState.open
    assert DegradationMode.down in comp.active_episodes

    # Advance past dwell (30s), tick.
    clock.advance(31.0)
    await comp.tick()
    # half-open triggers probe via _enter_half_open → probe succeeds →
    # record_success → closed → auto_resume.
    assert DegradationMode.down not in comp.active_episodes
    assert orch.resume_calls >= 1


async def test_auth_broken_no_auto_resume(tmp_path) -> None:
    from loam.graceful_degradation.adapter import AdapterEvent
    from loam.graceful_degradation.errors import DegradationSignal

    comp, orch, rt, notifier, client, invoker, clock, sent = _build_component(
        tmp_path=tmp_path,
        script=[],
    )
    # Synthesize an auth_broken event directly.
    event = AdapterEvent(
        call_id="c1",
        prompt_name="memory.extraction",
        model="claude-haiku-4-5",
        ok=False,
        signal=DegradationSignal.auth_broken,
        retry_after=None,
        latency_seconds=0.01,
        status_code=401,
        timestamp=clock.now(),
    )
    await comp._on_adapter_event(event)

    fsm = comp.detector.fsms[DegradationMode.auth_broken]
    assert fsm.state == FSMState.gated
    # No auto-resume even after much clock advance.
    for _ in range(10):
        clock.advance(3600.0)
        await comp.tick()
    assert fsm.state == FSMState.gated
    assert orch.paused is True


async def test_user_confirm_resume_on_auth_broken(tmp_path) -> None:
    from loam.graceful_degradation.adapter import AdapterEvent
    from loam.graceful_degradation.errors import DegradationSignal

    # Script: after user_resume, probe succeeds.
    comp, orch, rt, notifier, client, invoker, clock, sent = _build_component(
        tmp_path=tmp_path,
        script=["OK"],
    )
    # Trip auth-broken.
    event = AdapterEvent(
        call_id="c1",
        prompt_name="memory.extraction",
        model="claude-haiku-4-5",
        ok=False,
        signal=DegradationSignal.auth_broken,
        retry_after=None,
        latency_seconds=0.01,
        status_code=401,
        timestamp=clock.now(),
    )
    await comp._on_adapter_event(event)
    assert orch.paused is True
    # User confirms resume.
    resumed = await comp.user_confirm_resume(DegradationMode.auth_broken)
    assert resumed is True
    # Probe ran; FSM closed; orchestrator resumed.
    assert orch.resume_calls == 1


async def test_long_dwell_gates_resume(tmp_path) -> None:
    # Trip down; advance > 30 min before probe.
    comp, orch, rt, notifier, client, invoker, clock, sent = _build_component(
        tmp_path=tmp_path,
        script=[
            ConnectionError("x"),
            ConnectionError("x"),
            ConnectionError("x"),
            "OK",  # eventually a probe would succeed
        ],
    )
    rt.add_scope(FakeScope("s1"))
    from loam.graceful_degradation.errors import ClaudeAPIError

    for _ in range(3):
        try:
            await client.call(prompt_name="memory.extraction", text="x")
        except ClaudeAPIError:
            pass
    # Advance > 30min.
    clock.advance(1900.0)
    await comp.tick()
    # FSM should end up gated (long dwell gate), not closed.
    fsm = comp.detector.fsms[DegradationMode.down]
    assert fsm.state == FSMState.gated
    # Episode still active.
    assert DegradationMode.down in comp.active_episodes
    assert orch.paused is True
