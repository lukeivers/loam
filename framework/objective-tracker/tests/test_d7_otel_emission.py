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

"""D7 — OTel observability emission (v1.1 R11).

Acceptance (brief §D7):
- create, mark_achieved, mark_abandoned, re_open, bind_scope,
  evaluate_criterion all produce spans with relevant attributes
  (objective_id, authored_by, status, outcome).
- State-change events emitted as span events on the parent span.
- Emission succeeds with no consumer present (A1 correction).
"""

from __future__ import annotations

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from loam.objective_tracker.spec import ProseCriterion
from tests.conftest import make_child_spec, make_user_root_spec


@pytest.fixture
def otel_exporter():
    """Install an in-memory exporter so we can inspect emitted spans.

    We patch the module-level `_TRACER_PROVIDER` singleton and its
    `_TRACER_PROVIDER_SET_ONCE` sentinel so subsequent tests that do
    NOT use this fixture fall back to the SDK default (a no-op proxy).
    This avoids the "stale TracerProvider leaks across tests" problem
    seen when only restoring the reference without clearing the
    set-once flag.
    """
    import opentelemetry.trace as _ot

    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    prev_provider = _ot._TRACER_PROVIDER  # type: ignore[attr-defined]
    prev_once = _ot._TRACER_PROVIDER_SET_ONCE  # type: ignore[attr-defined]
    _ot._TRACER_PROVIDER = provider  # type: ignore[attr-defined]
    _ot._TRACER_PROVIDER_SET_ONCE = False  # type: ignore[attr-defined]
    try:
        yield exporter
    finally:
        # Force-shutdown the exporter's provider so no background
        # processors hang onto the test-created one.
        try:
            provider.shutdown()
        except Exception:
            pass
        _ot._TRACER_PROVIDER = prev_provider  # type: ignore[attr-defined]
        _ot._TRACER_PROVIDER_SET_ONCE = prev_once  # type: ignore[attr-defined]


async def test_emission_with_no_consumer_does_not_raise(tracker):
    """A1 correction — emission succeeds with no consumer configured."""
    proj = await tracker.create(make_user_root_spec())
    await tracker.start(proj.objective_id)
    await tracker.mark_achieved(proj.objective_id)
    # No exception = pass.


async def test_create_emits_span(tracker, otel_exporter):
    proj = await tracker.create(make_user_root_spec(goal="span-check"))
    spans = otel_exporter.get_finished_spans()
    create_spans = [s for s in spans if s.name == "objective_tracker.create"]
    assert len(create_spans) == 1
    attrs = dict(create_spans[0].attributes)
    assert attrs["loam.objective.id"] == proj.objective_id
    assert attrs["loam.objective.authored_by"] == "user"
    assert attrs["loam.objective.outcome"] == "success"


async def test_mark_achieved_emits_span_and_state_event(tracker, otel_exporter):
    proj = await tracker.create(make_user_root_spec())
    await tracker.start(proj.objective_id)
    otel_exporter.clear()
    await tracker.mark_achieved(proj.objective_id, evidence="done")
    spans = otel_exporter.get_finished_spans()
    ma = [s for s in spans if s.name == "objective_tracker.mark_achieved"]
    assert len(ma) == 1
    events = list(ma[0].events)
    assert any(e.name == "objective.status_changed" for e in events)


async def test_mark_abandoned_emits_span(tracker, otel_exporter):
    proj = await tracker.create(make_user_root_spec())
    otel_exporter.clear()
    await tracker.mark_abandoned(proj.objective_id, rationale="dropped")
    spans = otel_exporter.get_finished_spans()
    ab = [s for s in spans if s.name == "objective_tracker.mark_abandoned"]
    assert len(ab) == 1


async def test_re_open_emits_span(tracker, otel_exporter):
    proj = await tracker.create(make_user_root_spec())
    await tracker.start(proj.objective_id)
    await tracker.mark_achieved(proj.objective_id)
    otel_exporter.clear()
    await tracker.re_open(proj.objective_id, rationale="why")
    spans = otel_exporter.get_finished_spans()
    ro = [s for s in spans if s.name == "objective_tracker.re_open"]
    assert len(ro) == 1


async def test_bind_scope_emits_span(tracker, otel_exporter):
    root = await tracker.create(make_user_root_spec())
    otel_exporter.clear()
    await tracker.bind_scope("scope-42", root.objective_id)
    spans = otel_exporter.get_finished_spans()
    bs = [s for s in spans if s.name == "objective_tracker.bind_scope"]
    assert len(bs) == 1
    attrs = dict(bs[0].attributes)
    assert attrs["loam.scope.id"] == "scope-42"
    assert attrs["loam.objective.id"] == root.objective_id


async def test_evaluate_criterion_emits_span(tracker, otel_exporter):
    proj = await tracker.create(
        make_user_root_spec(
            criteria=(ProseCriterion(criterion_id="p", prose="x"),)
        )
    )
    otel_exporter.clear()
    await tracker.evaluate_criterion(
        proj.objective_id, criterion_id="p", result="met"
    )
    spans = otel_exporter.get_finished_spans()
    ev = [s for s in spans if s.name == "objective_tracker.evaluate_criterion"]
    assert len(ev) == 1
    attrs = dict(ev[0].attributes)
    assert attrs["loam.objective.criterion_id"] == "p"


async def test_error_path_emits_error_outcome(tracker, otel_exporter):
    """Illegal transitions should emit a span with outcome=error."""
    from loam.objective_tracker.errors import IllegalTransitionError

    proj = await tracker.create(make_user_root_spec())
    otel_exporter.clear()
    with pytest.raises(IllegalTransitionError):
        # achieved from proposed is illegal (must start first).
        await tracker.mark_achieved(proj.objective_id)
    spans = otel_exporter.get_finished_spans()
    ma = [s for s in spans if s.name == "objective_tracker.mark_achieved"]
    assert len(ma) == 1
    attrs = dict(ma[0].attributes)
    assert attrs["loam.objective.outcome"] == "error"
