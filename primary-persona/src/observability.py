"""OTel span / event helpers for the primary-persona layer (D9).

Per v1.1 R11: components emit OpenTelemetry spans and events; the
observability aggregator (a separate component, not yet built)
subscribes. Per the A1 correction: emission succeeds with no consumer
present.

Every operation in this layer emits at least one event. The helpers
below are thin wrappers around `opentelemetry.trace` so the rest of
the code reads as intent ("loader_span", "monitor_tick_event")
rather than raw span plumbing.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace


def _tracer() -> trace.Tracer:
    """Resolve the tracer on every call.

    Resolving the tracer lazily means tests (and any harness) can
    install a TracerProvider before the first emission lands; a
    module-level `_TRACER = trace.get_tracer(...)` binds early and
    cannot pick up a later provider.
    """
    return trace.get_tracer("pos_v2.primary_persona")


# ---- spans -----------------------------------------------------------


@contextmanager
def loader_span(
    personas_dir: str, *, outcome: str, persona_count: int | None = None
) -> Iterator[trace.Span]:
    """Root span for one loader run (D9: loader runs produce spans with
    outcome loaded / failed + field)."""
    with _tracer().start_as_current_span("pos.persona.loader") as span:
        span.set_attribute("pos.persona.dir", personas_dir)
        span.set_attribute("pos.persona.load.outcome", outcome)
        if persona_count is not None:
            span.set_attribute("pos.persona.load.count", persona_count)
        yield span


@contextmanager
def monitor_span(name: str, **attributes: Any) -> Iterator[trace.Span]:
    """Generic span wrapper used by monitor tick / injection paths."""
    with _tracer().start_as_current_span(name) as span:
        for k, v in attributes.items():
            if v is not None:
                span.set_attribute(k, v)
        yield span


@contextmanager
def authoring_span(signal: str, **attributes: Any) -> Iterator[trace.Span]:
    """Parent span for an authoring pipeline run (D9)."""
    with _tracer().start_as_current_span("pos.persona.authoring") as span:
        span.set_attribute("pos.persona.authoring.trigger_signal", signal)
        for k, v in attributes.items():
            if v is not None:
                span.set_attribute(k, v)
        yield span


@contextmanager
def authoring_step_span(step_name: str) -> Iterator[trace.Span]:
    """Child span per authoring step (style_harvest | domain_research |
    contract_synthesis | self_review)."""
    with _tracer().start_as_current_span(f"pos.persona.authoring.{step_name}") as span:
        span.set_attribute("pos.persona.authoring.step", step_name)
        yield span


# ---- events ----------------------------------------------------------


def monitor_tick_event(
    *,
    tick_id: int,
    active: int,
    pending: int,
    stuck: int,
    finished: int,
    escalated: int,
    failed: int,
) -> None:
    """One event per monitor tick (D3 acceptance)."""
    span = trace.get_current_span()
    span.add_event(
        "pos.persona.monitor.tick",
        {
            "pos.persona.monitor.tick_id": tick_id,
            "pos.persona.monitor.active": active,
            "pos.persona.monitor.pending": pending,
            "pos.persona.monitor.stuck": stuck,
            "pos.persona.monitor.finished": finished,
            "pos.persona.monitor.escalated": escalated,
            "pos.persona.monitor.failed": failed,
        },
    )


def monitor_injection_event(*, turn_id: str, token_estimate: int) -> None:
    """One event per UserPromptSubmit injection (D3 acceptance)."""
    span = trace.get_current_span()
    span.add_event(
        "pos.persona.monitor.inject",
        {
            "pos.persona.monitor.turn_id": turn_id,
            "pos.persona.monitor.tokens_est": token_estimate,
        },
    )


def self_review_verdict_event(*, iteration: int, verdict: str, reasons: str) -> None:
    """Authoring self-review verdicts are recorded as events on the
    parent span (D9 acceptance)."""
    span = trace.get_current_span()
    span.add_event(
        "pos.persona.authoring.self_review",
        {
            "pos.persona.authoring.iteration": iteration,
            "pos.persona.authoring.verdict": verdict,
            "pos.persona.authoring.reasons": reasons,
        },
    )


def introduction_event(
    *, new_handle: str, channel: str, outcome: str, reason: str | None = None
) -> None:
    """Introduction dispatch emits an event with handle and channel (D9)."""
    attrs: dict[str, Any] = {
        "pos.persona.introduction.handle": new_handle,
        "pos.persona.introduction.channel": channel,
        "pos.persona.introduction.outcome": outcome,
    }
    if reason:
        attrs["pos.persona.introduction.reason"] = reason
    with _tracer().start_as_current_span("pos.persona.introduction") as span:
        span.add_event("pos.persona.introduction.dispatched", attrs)


def retirement_event(*, handle: str, reason: str) -> None:
    """Retirement emits an event naming the persona and reason (D9)."""
    with _tracer().start_as_current_span("pos.persona.retirement") as span:
        span.add_event(
            "pos.persona.retired",
            {
                "pos.persona.retirement.handle": handle,
                "pos.persona.retirement.reason": reason,
            },
        )
