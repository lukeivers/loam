"""OTel emission helpers for the safety layer.

Uses `trace.get_tracer("pos.safety_layer")` only — no TracerProvider is
constructed here (A16). The observability-aggregator's `install_for_workspace`
hook is responsible for routing spans; this module is a pure emitter.

Span namespace: `pos.safety.*`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace


_TRACER = trace.get_tracer("pos.safety_layer", "0.1.0")


@contextmanager
def operation_span(name: str, **attrs: Any) -> Iterator[trace.Span]:
    with _TRACER.start_as_current_span(name) as span:
        _apply_attrs(span, attrs)
        yield span


def _apply_attrs(span: trace.Span, attrs: dict[str, Any]) -> None:
    for k, v in attrs.items():
        if v is None:
            continue
        try:
            span.set_attribute(k, v)
        except Exception:
            span.set_attribute(k, str(v))


def scope_kill(*, scope_id: str, reason: str, source: str) -> None:
    with _TRACER.start_as_current_span("pos.safety.scope_kill") as span:
        span.set_attribute("pos.safety.level", "scope")
        span.set_attribute("pos.safety.scope_id", scope_id)
        span.set_attribute("pos.safety.reason", reason)
        span.set_attribute("pos.safety.source", source)


def session_kill(
    *, reason: str, source: str, cancelled_count: int
) -> None:
    with _TRACER.start_as_current_span("pos.safety.session_kill") as span:
        span.set_attribute("pos.safety.level", "session")
        span.set_attribute("pos.safety.reason", reason)
        span.set_attribute("pos.safety.source", source)
        span.set_attribute("pos.safety.cancelled_count", cancelled_count)


def system_kill(
    *, reason: str, source: str, cancelled_count: int
) -> None:
    with _TRACER.start_as_current_span("pos.safety.system_kill") as span:
        span.set_attribute("pos.safety.level", "system")
        span.set_attribute("pos.safety.reason", reason)
        span.set_attribute("pos.safety.source", source)
        span.set_attribute("pos.safety.cancelled_count", cancelled_count)


def system_kill_cleared(*, reason: str) -> None:
    with _TRACER.start_as_current_span("pos.safety.system_kill_cleared") as span:
        span.set_attribute("pos.safety.reason", reason)


def system_kill_block_activation(*, scope_id: str) -> None:
    with _TRACER.start_as_current_span(
        "pos.safety.system_kill_block_activation"
    ) as span:
        span.set_attribute("pos.safety.scope_id", scope_id)


def ask_gate_fired(
    *,
    scope_id: str | None,
    spec_hash: str,
    action_classes: list[str],
    outcome: str,
) -> None:
    with _TRACER.start_as_current_span("pos.safety.ask_gate_fired") as span:
        if scope_id is not None:
            span.set_attribute("pos.safety.scope_id", scope_id)
        span.set_attribute("pos.safety.spec_hash", spec_hash)
        span.set_attribute("pos.safety.action_classes", ",".join(action_classes))
        span.set_attribute("pos.safety.gate_outcome", outcome)


def dangerous_op_gate_fired(
    *,
    scope_id: str | None,
    spec_hash: str,
    reasons: list[str],
    outcome: str,
) -> None:
    with _TRACER.start_as_current_span("pos.safety.dangerous_op_gate_fired") as span:
        if scope_id is not None:
            span.set_attribute("pos.safety.scope_id", scope_id)
        span.set_attribute("pos.safety.spec_hash", spec_hash)
        span.set_attribute("pos.safety.trigger_reasons", ",".join(reasons))
        span.set_attribute("pos.safety.gate_outcome", outcome)


def ask_decision_recorded(
    *, spec_hash: str, state: str, action_classes: list[str]
) -> None:
    with _TRACER.start_as_current_span("pos.safety.ask_decision_recorded") as span:
        span.set_attribute("pos.safety.spec_hash", spec_hash)
        span.set_attribute("pos.safety.state", state)
        span.set_attribute("pos.safety.action_classes", ",".join(action_classes))


def notification_dispatched(
    *, channel: str, outcome: str, kind: str
) -> None:
    with _TRACER.start_as_current_span("pos.safety.notification_dispatched") as span:
        span.set_attribute("pos.safety.channel", channel)
        span.set_attribute("pos.safety.notification_outcome", outcome)
        span.set_attribute("pos.safety.notification_kind", kind)
