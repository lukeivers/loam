"""OpenTelemetry emission for the objective tracker (D7 / v1.1 R11).

The primitive emits OTel spans and events; no consumer is assumed to
exist (A1 correction — emission succeeds with no consumer present).
When no consumer is configured, the SDK's default no-op tracer
absorbs the calls.

Span structure:

  • One INTERNAL span per operation (`create`, `mark_achieved`,
    `mark_abandoned`, `re_open`, `bind_scope`, `evaluate_criterion`).
  • State-change events emitted as span events on the operation's span.

Attributes (pOS-namespaced):

  • loam.objective.id
  • loam.objective.parent_id
  • loam.objective.authored_by
  • loam.objective.status
  • loam.objective.outcome   (success / error)
  • loam.objective.criterion_id
  • loam.scope.id            (on bind_scope)
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanKind, Status, StatusCode
    _OTEL_AVAILABLE = True
except Exception:  # pragma: no cover
    _OTEL_AVAILABLE = False


_TRACER_NAME = "loam.objective_tracker"


def get_tracer():
    if not _OTEL_AVAILABLE:
        return None
    return trace.get_tracer(_TRACER_NAME)


@contextmanager
def operation_span(
    name: str, **attrs: Any
) -> Iterator[Any]:
    """Open and auto-close an INTERNAL span for one tracker operation.

    Yields the span (or None when OTel isn't available). Sets a
    loam.objective.outcome = "success" attribute by default; callers
    can override to "error" by calling `mark_span_error(span, reason)`
    before context exit.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    filtered = {k: v for k, v in attrs.items() if v is not None}
    span = tracer.start_span(name, kind=SpanKind.INTERNAL, attributes=filtered)
    span.set_attribute("loam.objective.outcome", "success")
    try:
        yield span
    except Exception as exc:
        span.set_attribute("loam.objective.outcome", "error")
        span.set_status(Status(StatusCode.ERROR, str(exc)))
        span.end()
        raise
    else:
        span.end()


def add_event(span: Any | None, name: str, attributes: dict[str, Any] | None = None) -> None:
    if span is None:
        return
    span.add_event(name, attributes=attributes or {})


def set_attrs(span: Any | None, **attrs: Any) -> None:
    if span is None:
        return
    for k, v in attrs.items():
        if v is None:
            continue
        span.set_attribute(k, v)


def mark_span_error(span: Any | None, reason: str) -> None:
    if span is None or not _OTEL_AVAILABLE:
        return
    span.set_attribute("loam.objective.outcome", "error")
    span.set_status(Status(StatusCode.ERROR, reason))


def span_ids(span: Any | None) -> tuple[str | None, str | None]:
    if span is None or not _OTEL_AVAILABLE:
        return None, None
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return None, None
    return f"{ctx.trace_id:032x}", f"{ctx.span_id:016x}"
