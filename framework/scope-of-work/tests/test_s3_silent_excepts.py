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

"""Amendment #21 — S3 silent-except bundle — scope-of-work surfaces.

Covers Sites 1 and 2:
  * ``src/triggers.py::active_seconds_elapsed`` silent parse failure.
  * ``src/projection.py::apply_event`` silent parse failure on
    StateTransitioned time-accounting.

Each test asserts:
  * The new ``loam.scope.projection_parse_failed`` span fires with
    the expected ``loam.scope.projection_field`` attribute.
  * Existing behaviour is preserved (the caller sees the same return
    value / post-condition it would have under the pre-amendment
    silent-``pass`` branch).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from loam.scope_of_work.events import StateTransitioned
from loam.scope_of_work.projection import ScopeProjectionData, apply_event
from loam.scope_of_work.spec import ScopeState
from loam.scope_of_work.triggers import active_seconds_elapsed


@pytest.fixture(scope="module")
def otel_exporter():
    exporter = InMemorySpanExporter()
    current = trace.get_tracer_provider()
    if hasattr(current, "add_span_processor"):
        # Another test (e.g. test_d5_otel_emission) already installed a
        # TracerProvider at module scope — we cannot override it
        # (OTel rejects re-registration), so attach an additional
        # SimpleSpanProcessor to the existing provider.
        current.add_span_processor(SimpleSpanProcessor(exporter))
    else:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
    return exporter


def _spans_named(exporter, name):
    return [s for s in exporter.get_finished_spans() if s.name == name]


def test_active_seconds_elapsed_surfaces_parse_failure(otel_exporter):
    """Site 1: a malformed ``active_started_at`` previously silently
    returned the stale ``active_cumulative_seconds``; the fix emits
    ``loam.scope.projection_parse_failed`` while preserving the stale
    fallback return value.
    """
    otel_exporter.clear()
    proj = ScopeProjectionData(scope_id="scope-site1")
    proj.state = ScopeState.active
    proj.active_started_at = "not-a-timestamp"
    proj.active_cumulative_seconds = 42

    result = active_seconds_elapsed(proj, now=datetime.now(timezone.utc))

    # Existing-behaviour preservation: the caller still receives the
    # stale cumulative value.
    assert result == 42

    # Observable surface: the new span fires with the expected field.
    spans = _spans_named(otel_exporter, "loam.scope.projection_parse_failed")
    matches = [
        s for s in spans
        if dict(s.attributes).get("loam.scope.projection_field")
        == "active_started_at"
    ]
    assert len(matches) == 1, (
        f"expected exactly one projection-parse-failure span for "
        f"active_started_at; got {[dict(s.attributes) for s in spans]}"
    )
    attrs = dict(matches[0].attributes)
    assert attrs["loam.scope.id"] == "scope-site1"
    assert attrs["exception.class"] == "ValueError"


def test_apply_event_state_transitioned_surfaces_parse_failure(otel_exporter):
    """Site 2: a malformed ``created_at`` on a StateTransitioned event
    previously silently skipped the time-accounting delta; the fix
    emits ``loam.scope.projection_parse_failed`` while preserving the
    ``proj.active_started_at = None`` post-condition and the state
    transition itself.
    """
    otel_exporter.clear()
    proj = ScopeProjectionData(scope_id="scope-site2")
    proj.state = ScopeState.active
    proj.active_started_at = "2026-04-22T00:00:00+00:00"
    proj.first_activated_at = "2026-04-22T00:00:00+00:00"

    event = StateTransitioned(
        event_id=1,
        scope_id="scope-site2",
        from_state=ScopeState.active,
        to_state=ScopeState.paused,
        created_at="not-a-timestamp",
        pause_reason="test",
    )
    apply_event(proj, event)

    # Existing-behaviour preservation.
    assert proj.active_started_at is None
    assert proj.state == ScopeState.paused

    # Observable surface.
    spans = _spans_named(otel_exporter, "loam.scope.projection_parse_failed")
    matches = [
        s for s in spans
        if dict(s.attributes).get("loam.scope.projection_field")
        == "StateTransitioned.active_started_at_or_created_at"
    ]
    assert len(matches) == 1, (
        f"expected exactly one projection-parse-failure span for "
        f"StateTransitioned; got {[dict(s.attributes) for s in spans]}"
    )
    attrs = dict(matches[0].attributes)
    assert attrs["loam.scope.id"] == "scope-site2"
    assert attrs["exception.class"] == "ValueError"
