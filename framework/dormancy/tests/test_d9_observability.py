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

"""D9 — OTel observability emission.

Acceptance (brief):
- Detection events, FSM transitions, policy dispatches, notification-
  threshold crossings, resume events all produce OTel spans/events.
- Narrative Claude calls produce spans with `loam.prompt.type =
  degradation-narrative`.
- Emission succeeds with no consumer present.
"""

from __future__ import annotations

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from loam.dormancy import (
    ClaudeClient,
    DegradationComponent,
    DegradationConfig,
    DegradationMode,
    DegradationNotifier,
)
from loam.dormancy import observability as gd_obs

from .fakes import (
    FakeClock,
    FakeInvoker,
    FakeOrchestrator,
    FakeScope,
    FakeScopeRuntime,
    make_capture_channel,
)


@pytest.fixture(autouse=True)
def setup_otel_exporter(monkeypatch):
    """Install an in-memory exporter for testing."""

    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Swap the module-level tracer.
    monkeypatch.setattr(gd_obs, "_TRACER", provider.get_tracer("loam.dormancy", "0.10.0"))
    yield exporter
    exporter.clear()


def _build_component(tmp_path, *, script=None):
    clock = FakeClock()
    cfg = DegradationConfig.model_validate(
        {
            **DegradationConfig().model_dump(),
            "state": {"sqlite_path": str(tmp_path / "deg.sqlite")},
        }
    )
    invoker = FakeInvoker(script or [], default="OK")
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
    return comp, orch, rt, client, clock


async def test_adapter_emits_claude_call_span(tmp_path, setup_otel_exporter) -> None:
    comp, orch, rt, client, clock = _build_component(tmp_path)
    await client.call(prompt_name="memory.extraction", text="x")
    spans = setup_otel_exporter.get_finished_spans()
    call_spans = [s for s in spans if s.name == "loam.dormancy.claude_call"]
    assert len(call_spans) == 1
    attrs = dict(call_spans[0].attributes or {})
    assert attrs.get("loam.prompt.type") == "memory.extraction"
    assert attrs.get("loam.model") == "claude-haiku-4-5"


async def test_narrative_claude_call_uses_degradation_narrative_type(
    tmp_path, setup_otel_exporter
) -> None:
    """v1.1 R12 — narrative spans carry `loam.prompt.type =
    degradation-narrative`."""
    comp, orch, rt, client, clock = _build_component(
        tmp_path, script=["A 2-sentence summary."]
    )
    text = await comp.narrative.render_alert(
        episode_id="ep",
        mode=DegradationMode.rate_limited,
        signal="rate_limited",
        policy="pause_llm_only",
        paused_scope_count=1,
    )
    spans = setup_otel_exporter.get_finished_spans()
    call_spans = [s for s in spans if s.name == "loam.dormancy.claude_call"]
    assert any(
        dict(s.attributes or {}).get("loam.prompt.type") == "degradation-narrative"
        for s in call_spans
    )


async def test_fsm_transition_emits_span(tmp_path, setup_otel_exporter) -> None:
    comp, orch, rt, client, clock = _build_component(
        tmp_path,
        script=[
            ConnectionError("x"),
            ConnectionError("x"),
            ConnectionError("x"),
        ],
    )
    from loam.dormancy.errors import ClaudeAPIError

    for _ in range(3):
        try:
            await client.call(prompt_name="memory.extraction", text="x")
        except ClaudeAPIError:
            pass

    spans = setup_otel_exporter.get_finished_spans()
    transition_spans = [
        s for s in spans if s.name == "loam.dormancy.fsm_transition"
    ]
    assert len(transition_spans) >= 1
    attrs = dict(transition_spans[0].attributes or {})
    assert "loam.dormancy.mode" in attrs
    assert "loam.dormancy.from_state" in attrs
    assert "loam.dormancy.to_state" in attrs


async def test_episode_started_span_emitted(tmp_path, setup_otel_exporter) -> None:
    comp, orch, rt, client, clock = _build_component(
        tmp_path,
        script=[
            ConnectionError("x"),
            ConnectionError("x"),
            ConnectionError("x"),
        ],
    )
    rt.add_scope(FakeScope("s1"))
    from loam.dormancy.errors import ClaudeAPIError

    for _ in range(3):
        try:
            await client.call(prompt_name="memory.extraction", text="x")
        except ClaudeAPIError:
            pass

    spans = setup_otel_exporter.get_finished_spans()
    episode_spans = [
        s for s in spans if s.name == "loam.dormancy.episode_started"
    ]
    assert len(episode_spans) == 1


async def test_notification_span_emitted(tmp_path, setup_otel_exporter) -> None:
    from loam.dormancy.adapter import AdapterEvent
    from loam.dormancy.errors import DegradationSignal

    comp, orch, rt, client, clock = _build_component(tmp_path)
    # auth_broken forces notification immediately.
    event = AdapterEvent(
        call_id="c",
        prompt_name="p",
        model="m",
        ok=False,
        signal=DegradationSignal.auth_broken,
        retry_after=None,
        latency_seconds=0.01,
        status_code=401,
        timestamp=clock.now(),
    )
    await comp._on_adapter_event(event)
    spans = setup_otel_exporter.get_finished_spans()
    notif_spans = [
        s for s in spans if s.name == "loam.dormancy.notification_dispatched"
    ]
    assert len(notif_spans) >= 1


async def test_emission_succeeds_with_no_consumer_a1_safe() -> None:
    """The default SDK tracer (no provider set) is a noop; calling
    every emission helper must succeed."""
    # No consumer fixture — use the default global tracer which is
    # noop by default if no TracerProvider is installed.

    # These calls must not raise even with the noop tracer.
    gd_obs.fsm_transition("down", "closed", "open", "trip:connection_error")
    gd_obs.episode_started(
        episode_id="ep",
        signal="connection_error",
        policy="pause_all",
        paused_scope_ids=["s1"],
        mode="down",
    )
    gd_obs.episode_resolved(
        episode_id="ep",
        duration_seconds=10.0,
        resolution_kind="auto",
        resumed_scope_count=1,
    )
    gd_obs.policy_decision(policy="pause_all", episode_id="ep", mode="down")
    gd_obs.probe_call(
        mode="down", result="ok", attempt_n=1, latency_seconds=0.1
    )
    gd_obs.notification_dispatched(
        episode_id="ep",
        channel="terminal",
        outcome="delivered",
        threshold_triggered="time",
        tier=2,
    )


async def test_probe_span_emitted_on_half_open(tmp_path, setup_otel_exporter) -> None:
    comp, orch, rt, client, clock = _build_component(
        tmp_path,
        script=[
            ConnectionError("x"),
            ConnectionError("x"),
            ConnectionError("x"),
            "OK",  # probe
        ],
    )
    from loam.dormancy.errors import ClaudeAPIError

    for _ in range(3):
        try:
            await client.call(prompt_name="memory.extraction", text="x")
        except ClaudeAPIError:
            pass
    clock.advance(31.0)
    await comp.tick()

    spans = setup_otel_exporter.get_finished_spans()
    probe_spans = [s for s in spans if s.name == "loam.dormancy.probe_call"]
    assert len(probe_spans) >= 1
