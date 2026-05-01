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

"""Amendment #20 — S2 silent-except bundle new-behaviour tests (sites 1-5).

Research doc: docs/rebuild/plans/research/amendment-20-s2-silent-excepts-research.md.

Five new tests covering the five self-correction silent-except sites:
  Site 1 — build_trigger_from_span attribute-lookup failure emits span.
  Site 2 — OTelAnomalyPoller.run_forever timeout iteration emits poll_tick span.
  Site 3 — audit_subscription drops one-on-one notify observably when no loop.
  Site 4 — episode_refused status-set fallback captured as span event.
  Site 5 — cost_refusal_caught status-set fallback captured as span event.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from loam.self_correction import observability as sc_obs
from loam.self_correction.triggers import (
    OTelAnomalyPoller,
    build_trigger_from_span,
)
from loam.self_correction.completion_check import CompletionPrecheck


@pytest.fixture
def setup_sc_exporter(monkeypatch):
    """Install an in-memory OTel exporter and swap the module tracer."""
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(
        sc_obs,
        "_TRACER",
        provider.get_tracer("loam.self_correction", "0.1.0"),
    )
    yield exporter
    exporter.clear()


class _RaisingAttrs:
    """Mimic SpanRecord.attributes whose .get raises."""

    def get(self, key: str) -> Any:  # noqa: D401
        raise RuntimeError("attribute lookup boom")


class _SpanWithRaisingAttrs:
    """Minimal span stub whose .attributes.get raises on lookup."""

    def __init__(self) -> None:
        self.attributes = _RaisingAttrs()
        self.name = "loam.test.failure"
        self.status = "ERROR"
        self.status_message = "boom"
        self.span_id = "sp-1"
        self.trace_id = "tr-1"


def test_S2_site1_build_trigger_from_span_attribute_failure_emits_span(
    setup_sc_exporter,
) -> None:
    """Site 1 — scope-id lookup failure surfaces via emitter; scope_id
    falls back to None (existing default)."""
    span_stub = _SpanWithRaisingAttrs()
    tr = build_trigger_from_span(span=span_stub)

    assert tr.scope_id is None
    finished = setup_sc_exporter.get_finished_spans()
    failure_spans = [
        s
        for s in finished
        if s.name == "loam.correction.span_attribute_lookup_failed"
    ]
    assert len(failure_spans) == 1
    attrs = dict(failure_spans[0].attributes or {})
    assert attrs.get("loam.correction.attribute_name") == "loam.scope.id"
    assert attrs.get("loam.correction.exception_class") == "RuntimeError"


class _FakeQueryAPI:
    """Query API that returns no spans — we just need run_once to execute."""

    def find_spans(self, flt, limit: int) -> list:
        return []


async def test_S2_site2_poll_tick_emits_span_on_timeout_iteration(
    setup_sc_exporter,
) -> None:
    """Site 2 — the sleep-with-early-wake pattern now emits a liveness
    span per timeout-driven iteration."""

    async def handler(trigger) -> None:
        return None

    # Tiny interval so a single timeout fires quickly. The poller runs
    # until we set `_stopped` from outside; we give it just enough time
    # to tick once.
    poller = OTelAnomalyPoller(
        query_api=_FakeQueryAPI(),
        handler=handler,
        poll_interval_seconds=0.01,  # sub-second interval
    )

    async def stop_after(delay: float) -> None:
        await asyncio.sleep(delay)
        poller.stop()

    # Let at least one timeout-iteration happen.
    await asyncio.gather(poller.run_forever(), stop_after(0.05))

    tick_spans = [
        s
        for s in setup_sc_exporter.get_finished_spans()
        if s.name == "loam.correction.poll_tick"
    ]
    assert tick_spans, "expected at least one poll_tick span"
    attrs = dict(tick_spans[0].attributes or {})
    assert attrs.get("loam.correction.poller_name") == "otel_anomaly"


class _FakeStore:
    """Minimal store fake for CompletionPrecheck site-3 test."""

    def __init__(self, episode_id: str, scope_id: str, present: set) -> None:
        self._ep = type(
            "EP",
            (),
            {"episode_id": episode_id, "correction_scope_id": scope_id},
        )()
        self._scope_id = scope_id
        self._present = present

    def get_episode_by_scope(self, scope_id: str):
        return self._ep if scope_id == self._scope_id else None

    def record_types_for(self, episode_id: str):
        return self._present


def test_S2_site3_audit_subscription_drops_notify_with_no_loop_observably(
    setup_sc_exporter,
) -> None:
    """Site 3 — audit handler invoked from sync context (no running loop)
    emits audit_notify_no_loop instead of silently passing."""
    from loam.scope_of_work import ScopeState

    store = _FakeStore(
        episode_id="ep-123",
        scope_id="scope-abc",
        present=set(),  # missing all four record types -> triggers audit
    )
    check = CompletionPrecheck(store=store)

    async def _noop_notify(episode_id: str, missing_csv: str) -> None:
        return None

    # Build an event emitter and subscribe the audit handler.
    class _FakeRuntime:
        class _Emitter:
            def __init__(self) -> None:
                self.handlers: list = []

            def on(self, ev, h):
                self.handlers.append(h)

        def __init__(self) -> None:
            self.emitter = _FakeRuntime._Emitter()

    rt = _FakeRuntime()
    check.audit_subscription(rt, notify=_noop_notify)
    assert rt.emitter.handlers, "audit handler did not subscribe"

    # Fire a `completed` transition from a purely-synchronous context
    # (no asyncio loop), which is exactly the case the RuntimeError
    # branch handles.
    event = type(
        "E",
        (),
        {"to_state": ScopeState.completed, "scope_id": "scope-abc"},
    )()
    rt.emitter.handlers[0](event)

    no_loop_spans = [
        s
        for s in setup_sc_exporter.get_finished_spans()
        if s.name == "loam.correction.audit_notify_no_loop"
    ]
    assert len(no_loop_spans) == 1
    attrs = dict(no_loop_spans[0].attributes or {})
    assert attrs.get("loam.correction.episode_id") == "ep-123"


def test_S2_site4_episode_refused_status_set_failure_is_captured(
    setup_sc_exporter, monkeypatch
) -> None:
    """Site 4 — status-set failure on the episode_refused span records
    a status_set_failed event on that same span instead of silently
    passing."""
    # Monkey-patch Status(...) to raise to simulate an OTel-SDK import
    # glitch / version mismatch.
    from opentelemetry.trace import status as st_mod

    class _BoomStatus:
        def __init__(self, *a, **kw):
            raise RuntimeError("status-import boom")

    monkeypatch.setattr(st_mod, "Status", _BoomStatus)

    sc_obs.episode_refused(
        episode_id="ep-x",
        reason="test_refusal",
        code=-32070,
        details=None,
    )

    refused_spans = [
        s
        for s in setup_sc_exporter.get_finished_spans()
        if s.name == "loam.correction.episode_refused"
    ]
    assert len(refused_spans) == 1
    events = refused_spans[0].events
    assert any(
        e.name == "status_set_failed"
        and dict(e.attributes or {}).get("exception_class") == "RuntimeError"
        for e in events
    )


def test_S2_site5_cost_refusal_caught_status_set_failure_is_captured(
    setup_sc_exporter, monkeypatch
) -> None:
    """Site 5 — mirror of Site 4 on the cost_refusal_caught span."""
    from opentelemetry.trace import status as st_mod

    class _BoomStatus:
        def __init__(self, *a, **kw):
            raise RuntimeError("status-import boom")

    monkeypatch.setattr(st_mod, "Status", _BoomStatus)

    sc_obs.cost_refusal_caught(
        episode_id="ep-cost",
        code=-32082,
        message="ceiling hit",
    )

    cost_spans = [
        s
        for s in setup_sc_exporter.get_finished_spans()
        if s.name == "loam.correction.cost_refusal_caught"
    ]
    assert len(cost_spans) == 1
    events = cost_spans[0].events
    assert any(
        e.name == "status_set_failed"
        and dict(e.attributes or {}).get("exception_class") == "RuntimeError"
        for e in events
    )
