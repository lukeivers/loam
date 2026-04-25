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


# ---- onboarding lifecycle (amendment #35) ---------------------------


def onboarding_render_event(*, handle: str, length: int) -> None:
    """One event per ``to_agent_md()`` invocation (AC35.7).

    Names the handle the renderer projected from + the rendered
    length (so audit can correlate render calls with downstream
    agent-file writes once amendment #37 lands the write surface).
    Emits whether or not a span is currently active.
    """
    with _tracer().start_as_current_span("pos.persona.onboarding.render") as span:
        span.add_event(
            "pos.persona.onboarding.render",
            {
                "pos.persona.onboarding.handle": handle,
                "pos.persona.onboarding.render.length": length,
            },
        )


def onboarding_question_event(
    *, handle: str, question_id: str, workspace_slug: str | None = None
) -> None:
    """One event per onboarding question dispatched (AC35.7)."""
    with _tracer().start_as_current_span("pos.persona.onboarding.question") as span:
        attrs: dict[str, Any] = {
            "pos.persona.onboarding.handle": handle,
            "pos.persona.onboarding.question_id": question_id,
        }
        if workspace_slug is not None:
            attrs["pos.persona.onboarding.workspace_slug"] = workspace_slug
        span.add_event("pos.persona.onboarding.question", attrs)


def onboarding_answer_event(
    *, handle: str, question_id: str, answer_length: int
) -> None:
    """One event per recorded answer (AC35.7).

    Records the answer's length, not its content — the answer body is
    workspace-supplied content (STATE.md rule 4); observability
    captures auditable metadata, not the prose itself.
    """
    with _tracer().start_as_current_span("pos.persona.onboarding.answer") as span:
        span.add_event(
            "pos.persona.onboarding.answer",
            {
                "pos.persona.onboarding.handle": handle,
                "pos.persona.onboarding.question_id": question_id,
                "pos.persona.onboarding.answer.length": answer_length,
            },
        )


def onboarding_writeback_event(
    *, handle: str, completed: bool, workspace_slug: str | None = None
) -> None:
    """One event per contract write-back (AC35.7).

    ``completed`` is True when the transcript was complete and the
    write-back also flipped ``is_starter`` to False; False on a
    partial write-back (incomplete transcript) where ``is_starter``
    remains True.
    """
    with _tracer().start_as_current_span("pos.persona.onboarding.writeback") as span:
        attrs: dict[str, Any] = {
            "pos.persona.onboarding.handle": handle,
            "pos.persona.onboarding.writeback.completed": completed,
        }
        if workspace_slug is not None:
            attrs["pos.persona.onboarding.workspace_slug"] = workspace_slug
        span.add_event("pos.persona.onboarding.writeback", attrs)


def onboarding_dev_intent_question_event(
    *, handle: str, workspace_slug: str | None = None
) -> None:
    """One event per dev-intent question dispatched (sub-plan A AC.A.7).

    Distinct from the generic ``onboarding_question_event`` so
    observability consumers can count dev-intent prompts without
    pattern-matching the question_id attribute. Fires once per
    starter session at the moment the dev-intent question is
    surfaced (currently: alongside the rest of the question batch
    in ``persist_elicitation_transcript``).
    """
    with _tracer().start_as_current_span(
        "pos.persona.onboarding.dev_intent_question"
    ) as span:
        attrs: dict[str, Any] = {
            "pos.persona.onboarding.handle": handle,
        }
        if workspace_slug is not None:
            attrs["pos.persona.onboarding.workspace_slug"] = workspace_slug
        span.add_event(
            "pos.persona.onboarding.dev_intent_question", attrs
        )


def onboarding_dev_intent_answer_event(
    *, handle: str, answer: str, workspace_slug: str | None = None
) -> None:
    """One event per dev-intent answer recorded (sub-plan A AC.A.7).

    ``answer`` is the normalised contract value (``"yes"`` /
    ``"no"``) — bounded vocabulary, not free-text user prose, so
    emitting it satisfies STATE.md rule 4 (the field carries
    framework-level state, not workspace-supplied content).
    """
    with _tracer().start_as_current_span(
        "pos.persona.onboarding.dev_intent_answer"
    ) as span:
        attrs: dict[str, Any] = {
            "pos.persona.onboarding.handle": handle,
            "pos.persona.onboarding.dev_intent.answer": answer,
        }
        if workspace_slug is not None:
            attrs["pos.persona.onboarding.workspace_slug"] = workspace_slug
        span.add_event(
            "pos.persona.onboarding.dev_intent_answer", attrs
        )


def onboarding_starter_flag_transition_event(
    *, handle: str, from_value: bool, to_value: bool
) -> None:
    """One event per ``is_starter`` transition (AC35.7).

    Fires only on actual transitions (from != to) so steady-state
    re-loads of a non-starter contract do not produce noise.
    """
    with _tracer().start_as_current_span(
        "pos.persona.onboarding.starter_flag_transition"
    ) as span:
        span.add_event(
            "pos.persona.onboarding.starter_flag_transition",
            {
                "pos.persona.onboarding.handle": handle,
                "pos.persona.onboarding.starter_flag.from": from_value,
                "pos.persona.onboarding.starter_flag.to": to_value,
            },
        )


# ---- tracker-context contributor (amendment #40) --------------------


def tracker_context_composed_event(
    *, handle: str, in_flight_count: int, truncated_count: int
) -> None:
    """One event per successful tracker-context contribution (AC40.x).

    Fires whether the contribution is empty (in_flight_count == 0,
    AC40.5) or non-empty (AC40.1). Non-zero ``truncated_count`` flags
    that the cap-guard elided some bullets (AC40.4).
    """
    with _tracer().start_as_current_span(
        "pos.persona.tracker_context.composed"
    ) as span:
        span.add_event(
            "pos.persona.tracker_context.composed",
            {
                "pos.persona.tracker_context.handle": handle,
                "pos.persona.tracker_context.in_flight_count": in_flight_count,
                "pos.persona.tracker_context.truncated_count": truncated_count,
            },
        )


def tracker_context_unavailable_event(
    *, handle: str, failure_class: str, detail: str
) -> None:
    """One event per tracker-context graceful-degradation (AC40.3).

    Fires when the tracker cannot be opened, the query fails, or any
    other tracker-side error renders the contributor unable to
    produce a populated block. ``failure_class`` names the exception
    class (e.g., ``OperationalError``, ``PermissionError``,
    ``FileNotFoundError``); ``detail`` names which path tripped
    (``tracker_open_failed`` | ``query_projection_view_failed``).
    """
    with _tracer().start_as_current_span(
        "pos.persona.tracker_context.unavailable"
    ) as span:
        span.add_event(
            "pos.persona.tracker_context.unavailable",
            {
                "pos.persona.tracker_context.handle": handle,
                "pos.persona.tracker_context.failure_class": failure_class,
                "pos.persona.tracker_context.detail": detail,
            },
        )
