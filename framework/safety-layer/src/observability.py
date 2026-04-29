"""OTel emission helpers for the safety layer.

Uses `trace.get_tracer("loam.safety_layer")` only — no TracerProvider is
constructed here (A16). The observability-aggregator's `install_for_workspace`
hook is responsible for routing spans; this module is a pure emitter.

Span namespace: `loam.safety.*`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace


_TRACER = trace.get_tracer("loam.safety_layer", "0.1.0")


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
    with _TRACER.start_as_current_span("loam.safety.scope_kill") as span:
        span.set_attribute("loam.safety.level", "scope")
        span.set_attribute("loam.safety.scope_id", scope_id)
        span.set_attribute("loam.safety.reason", reason)
        span.set_attribute("loam.safety.source", source)


def session_kill(
    *, reason: str, source: str, cancelled_count: int
) -> None:
    with _TRACER.start_as_current_span("loam.safety.session_kill") as span:
        span.set_attribute("loam.safety.level", "session")
        span.set_attribute("loam.safety.reason", reason)
        span.set_attribute("loam.safety.source", source)
        span.set_attribute("loam.safety.cancelled_count", cancelled_count)


def system_kill(
    *, reason: str, source: str, cancelled_count: int
) -> None:
    with _TRACER.start_as_current_span("loam.safety.system_kill") as span:
        span.set_attribute("loam.safety.level", "system")
        span.set_attribute("loam.safety.reason", reason)
        span.set_attribute("loam.safety.source", source)
        span.set_attribute("loam.safety.cancelled_count", cancelled_count)


def system_kill_cleared(*, reason: str) -> None:
    with _TRACER.start_as_current_span("loam.safety.system_kill_cleared") as span:
        span.set_attribute("loam.safety.reason", reason)


def system_kill_block_activation(*, scope_id: str) -> None:
    with _TRACER.start_as_current_span(
        "loam.safety.system_kill_block_activation"
    ) as span:
        span.set_attribute("loam.safety.scope_id", scope_id)


def ask_gate_fired(
    *,
    scope_id: str | None,
    spec_hash: str,
    action_classes: list[str],
    outcome: str,
) -> None:
    with _TRACER.start_as_current_span("loam.safety.ask_gate_fired") as span:
        if scope_id is not None:
            span.set_attribute("loam.safety.scope_id", scope_id)
        span.set_attribute("loam.safety.spec_hash", spec_hash)
        span.set_attribute("loam.safety.action_classes", ",".join(action_classes))
        span.set_attribute("loam.safety.gate_outcome", outcome)


def dangerous_op_gate_fired(
    *,
    scope_id: str | None,
    spec_hash: str,
    reasons: list[str],
    outcome: str,
) -> None:
    with _TRACER.start_as_current_span("loam.safety.dangerous_op_gate_fired") as span:
        if scope_id is not None:
            span.set_attribute("loam.safety.scope_id", scope_id)
        span.set_attribute("loam.safety.spec_hash", spec_hash)
        span.set_attribute("loam.safety.trigger_reasons", ",".join(reasons))
        span.set_attribute("loam.safety.gate_outcome", outcome)


def ask_decision_recorded(
    *, spec_hash: str, state: str, action_classes: list[str]
) -> None:
    with _TRACER.start_as_current_span("loam.safety.ask_decision_recorded") as span:
        span.set_attribute("loam.safety.spec_hash", spec_hash)
        span.set_attribute("loam.safety.state", state)
        span.set_attribute("loam.safety.action_classes", ",".join(action_classes))


def notification_dispatched(
    *, channel: str, outcome: str, kind: str
) -> None:
    with _TRACER.start_as_current_span("loam.safety.notification_dispatched") as span:
        span.set_attribute("loam.safety.channel", channel)
        span.set_attribute("loam.safety.notification_outcome", outcome)
        span.set_attribute("loam.safety.notification_kind", kind)


# ---- amendment #19: silent-except surface emitters -------------------
# Per the 2026-04-22 audit + classifier (amendment #19 research doc at
# docs/rebuild/plans/research/amendment-19-s1-silent-excepts-research.md),
# four silent-except sites inside the safety layer are replaced with
# observable-surface emitters. The reason-suffix / failed-id fields
# carry the structured signal; these spans carry the OTel signal. All
# four share the no-TracerProvider-construction discipline (A16).


def pause_activation_failed(
    *, level: str, reason: str, source: str, exception_class: str
) -> None:
    """Surfaces a `pause_activation` failure during kill_session /
    kill_system. Amendment #19 sites 1 + 2."""
    with _TRACER.start_as_current_span(
        "loam.safety.pause_activation_failed"
    ) as span:
        span.set_attribute("loam.safety.level", level)
        span.set_attribute("loam.safety.reason", reason)
        span.set_attribute("loam.safety.source", source)
        span.set_attribute("loam.safety.exception_class", exception_class)


def scope_cancel_failed_during_kill(
    *, level: str, scope_id: str, reason: str, exception_class: str
) -> None:
    """Surfaces a per-scope cancel failure inside the system-kill loop.
    The failed scope id is also recorded in
    ``KillEventRecord.failed_scope_ids`` so callers can distinguish
    "nothing to cancel" from "cancellation failed." Amendment #19
    site 3."""
    with _TRACER.start_as_current_span(
        "loam.safety.scope_cancel_failed_during_kill"
    ) as span:
        span.set_attribute("loam.safety.level", level)
        span.set_attribute("loam.safety.scope_id", scope_id)
        span.set_attribute("loam.safety.reason", reason)
        span.set_attribute("loam.safety.exception_class", exception_class)


def request_stop_failed(*, reason: str, exception_class: str) -> None:
    """Surfaces a `request_stop` failure at the tail of kill_system.
    The kill event + system-kill state row have already landed; this
    span captures that the orchestrator stop event did not fire.
    Amendment #19 site 4."""
    with _TRACER.start_as_current_span(
        "loam.safety.request_stop_failed"
    ) as span:
        span.set_attribute("loam.safety.reason", reason)
        span.set_attribute("loam.safety.exception_class", exception_class)


def persona_render_failed(*, kind: str, exception_class: str) -> None:
    """Surfaces a persona-render failure during ask-gate / dangerous-op
    notification dispatch. The un-rendered notification text is still
    sent — fail-closed invariant preserved. Amendment #19 sites 5 + 6."""
    with _TRACER.start_as_current_span(
        "loam.safety.persona_render_failed"
    ) as span:
        span.set_attribute("loam.safety.notification_kind", kind)
        span.set_attribute("loam.safety.exception_class", exception_class)
