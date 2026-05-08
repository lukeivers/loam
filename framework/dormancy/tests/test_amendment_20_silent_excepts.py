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

"""Amendment #20 — S2 silent-except bundle new-behaviour tests (sites 6-8).

Research doc: docs/plans/research/amendment-20-s2-silent-excepts-research.md.

Three new tests covering the three graceful-degradation silent-except sites:
  Site 6 — _any_paused_scope_user_relevant lookup failure emits scope_lookup_failed.
  Site 7 — reconcile_on_startup invalid-enum drop emits reconcile_restore_failed.
  Site 8 — episode_started paused_scope_ids attr-set failure captured as span event.
"""

from __future__ import annotations

from pathlib import Path

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
from loam.dormancy.component import ActiveEpisode
from loam.dormancy.policy import Policy

from .fakes import (
    FakeClock,
    FakeInvoker,
    FakeOrchestrator,
    FakeScope,
    FakeScopeRuntime,
    make_capture_channel,
)


@pytest.fixture
def setup_gd_exporter(monkeypatch):
    """Install an in-memory OTel exporter and swap the module tracer."""
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(
        gd_obs,
        "_TRACER",
        provider.get_tracer("loam.dormancy", "0.1.0"),
    )
    yield exporter
    exporter.clear()


def _build_component(tmp_path, *, rt=None):
    clock = FakeClock()
    cfg = DegradationConfig.model_validate(
        {
            **DegradationConfig().model_dump(),
            "state": {"sqlite_path": str(tmp_path / "deg.sqlite")},
        }
    )
    invoker = FakeInvoker([], default="OK")
    orch = FakeOrchestrator()
    rt = rt or FakeScopeRuntime()
    ch, _sent = make_capture_channel()
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
    return comp, orch, rt, clock


class _RaisingScopeRuntime(FakeScopeRuntime):
    """Scope runtime whose get(raising_id) raises; get(ok_id) returns a
    user-relevant scope. Used to exercise site 6's emit + continue."""

    def __init__(self, raising_id: str, ok_id: str) -> None:
        super().__init__()
        self._raising_id = raising_id
        self._ok_scope = FakeScope(
            scope_id=ok_id,
            constraints=("user_relevant_on_degradation=true",),
        )
        self.add_scope(self._ok_scope)

    def get(self, scope_id: str):
        if scope_id == self._raising_id:
            raise RuntimeError("scope lookup boom")
        return super().get(scope_id)


def test_S2_site6_any_paused_scope_user_relevant_surfaces_lookup_failures(
    tmp_path: Path, setup_gd_exporter
) -> None:
    """Site 6 — a raising scope lookup emits scope_lookup_failed and
    continues; the user-relevant scope is still observed."""
    rt = _RaisingScopeRuntime(raising_id="s-raise", ok_id="s-ok")
    comp, _orch, _rt, _clock = _build_component(tmp_path, rt=rt)
    ep = ActiveEpisode(
        episode_id="ep-relevance",
        mode=DegradationMode.down,
        signal="connection_error",
        policy=Policy.pause_all,
        started_at=1_000_000.0,
        paused_scope_ids=["s-raise", "s-ok"],
    )

    result = comp._any_paused_scope_user_relevant(ep)

    # User-relevant scope still seen even with one lookup failing.
    assert result is True

    failure_spans = [
        s
        for s in setup_gd_exporter.get_finished_spans()
        if s.name == "loam.dormancy.scope_lookup_failed"
    ]
    assert len(failure_spans) == 1
    attrs = dict(failure_spans[0].attributes or {})
    assert attrs.get("loam.dormancy.episode_id") == "ep-relevance"
    assert attrs.get("loam.dormancy.scope_id") == "s-raise"
    assert attrs.get("loam.dormancy.exception_class") == "RuntimeError"


async def test_S2_site7_reconcile_on_startup_surfaces_invalid_stored_enum_values(
    tmp_path: Path, setup_gd_exporter
) -> None:
    """Site 7 — a stored row with an enum-invalid mode/policy pair is
    dropped from the in-memory rebuild, and the drop is observable."""
    comp, orch, _rt, _clock = _build_component(tmp_path)

    # Seed store with a row that uses a valid mode (schema requires it)
    # but then monkey-patch get_episode to return a row with an
    # INVALID mode string — simulating schema drift on restart.
    comp.store.create_episode(
        episode_id="ep-drift",
        mode="down",
        signal="x",
        policy="pause_all",
        paused_scope_ids=[],
    )
    real_row = comp.store.get_episode("ep-drift")
    assert real_row is not None

    # Build a lookalike row with a bogus mode value.
    from loam.dormancy.state import EpisodeRow

    drifted = EpisodeRow(
        episode_id=real_row.episode_id,
        mode="not-a-real-mode",  # enum-invalid
        signal=real_row.signal,
        policy=real_row.policy,
        started_at=real_row.started_at,
        resolved_at=real_row.resolved_at,
        resolution_kind=real_row.resolution_kind,
        paused_scope_ids=list(real_row.paused_scope_ids),
        failed_scope_ids=list(real_row.failed_scope_ids),
        notification_sent_at=real_row.notification_sent_at,
        resume_notification_sent_at=real_row.resume_notification_sent_at,
        notification_threshold=real_row.notification_threshold,
    )

    # Build a custom reconcile plan directly hitting the case-1 branch.
    from loam.dormancy.state import ReconciliationPlan

    orch.paused = True
    # Patch unresolved_episodes to return the drifted row so reconcile()
    # produces case 1.
    original_unresolved = comp.store.unresolved_episodes
    original_get = comp.store.get_episode
    comp.store.unresolved_episodes = lambda: [drifted]  # type: ignore[assignment]
    comp.store.get_episode = (
        lambda eid: drifted if eid == "ep-drift" else original_get(eid)
    )  # type: ignore[assignment]
    try:
        plan = await comp.reconcile_on_startup(orchestrator_paused=True)
    finally:
        comp.store.unresolved_episodes = original_unresolved  # type: ignore[assignment]
        comp.store.get_episode = original_get  # type: ignore[assignment]

    assert plan.case == 1
    # The invalid row did NOT land in the in-memory dict.
    assert not any(
        getattr(ep, "episode_id", None) == "ep-drift"
        for ep in comp.active_episodes.values()
    )

    fail_spans = [
        s
        for s in setup_gd_exporter.get_finished_spans()
        if s.name == "loam.dormancy.reconcile_restore_failed"
    ]
    assert len(fail_spans) == 1
    attrs = dict(fail_spans[0].attributes or {})
    assert attrs.get("loam.dormancy.episode_id") == "ep-drift"
    assert attrs.get("loam.dormancy.mode_value") == "not-a-real-mode"
    assert attrs.get("loam.dormancy.exception_class") == "ValueError"


def test_S2_site8_episode_started_surfaces_paused_scope_ids_attr_failure(
    setup_gd_exporter, monkeypatch
) -> None:
    """Site 8 — a set_attribute failure on the paused_scope_ids attr
    adds a span event to the already-open span rather than silently
    passing."""
    # We monkey-patch the tracer's start_as_current_span to yield a span
    # whose set_attribute RAISES on the ids attr but succeeds on others,
    # so only the targeted set fails.
    from opentelemetry import trace as ot_trace

    real_tracer = gd_obs._TRACER

    class _WrappedSpan:
        def __init__(self, inner) -> None:
            self._inner = inner
            self.events: list[tuple[str, dict]] = []

        def set_attribute(self, key, value):
            if key == "loam.dormancy.paused_scope_ids":
                raise RuntimeError("attr-set boom")
            return self._inner.set_attribute(key, value)

        def add_event(self, name, attributes=None):
            self.events.append((name, dict(attributes or {})))
            return self._inner.add_event(name, attributes=attributes)

        def __getattr__(self, name):
            return getattr(self._inner, name)

    wrapped_holder: dict = {}

    from contextlib import contextmanager

    @contextmanager
    def _wrapping_start(span_name, *args, **kwargs):
        with real_tracer.start_as_current_span(span_name, *args, **kwargs) as inner:
            wrapped = _WrappedSpan(inner)
            wrapped_holder["span"] = wrapped
            yield wrapped

    class _WrappingTracer:
        def start_as_current_span(self, name, *args, **kwargs):
            return _wrapping_start(name, *args, **kwargs)

    monkeypatch.setattr(gd_obs, "_TRACER", _WrappingTracer())

    gd_obs.episode_started(
        episode_id="ep-attr",
        signal="connection_error",
        policy="pause_all",
        paused_scope_ids=["s1", "s2", "s3"],
        mode="down",
    )

    wrapped = wrapped_holder["span"]
    # The span saw a `paused_scope_ids_attr_failed` event with the
    # exception class + count.
    assert any(
        name == "paused_scope_ids_attr_failed"
        and attrs.get("exception_class") == "RuntimeError"
        and attrs.get("count") == 3
        for (name, attrs) in wrapped.events
    )
