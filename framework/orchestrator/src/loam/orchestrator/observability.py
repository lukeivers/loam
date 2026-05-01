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

"""OTel emission helpers for the orchestrator (D9).

Every orchestrator operation emits a span or event. Per brief A1
correction, emissions succeed with no consumer present — the default
SDK noop tracer silently accepts every call.

Span names follow the `loam.orchestrator.<verb>` convention.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace

_TRACER = trace.get_tracer("loam.orchestrator", "0.1.0")


@contextmanager
def operation_span(name: str, **attrs: Any) -> Iterator[trace.Span]:
    with _TRACER.start_as_current_span(name) as span:
        for k, v in attrs.items():
            if v is None:
                continue
            try:
                span.set_attribute(k, v)
            except Exception:
                # Be permissive on attribute types; OTel rejects some
                # non-scalar values depending on SDK version.
                span.set_attribute(k, str(v))
        yield span


def emit_event(span: trace.Span | None, name: str, attrs: dict[str, Any]) -> None:
    if span is None:
        return
    clean = {k: v for k, v in attrs.items() if v is not None}
    span.add_event(name, attributes=clean)


def process_start_span(**attrs: Any) -> trace.Span:
    """Start a long-lived `loam.orchestrator.process` span. Caller is
    responsible for ending it."""
    span = _TRACER.start_span("loam.orchestrator.process")
    for k, v in attrs.items():
        if v is None:
            continue
        try:
            span.set_attribute(k, v)
        except Exception:
            span.set_attribute(k, str(v))
    return span


def end_span(span: trace.Span | None) -> None:
    if span is not None:
        span.end()
