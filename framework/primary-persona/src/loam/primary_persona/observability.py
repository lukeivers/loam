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
    return trace.get_tracer("loam.primary_persona")


# ---- spans -----------------------------------------------------------


@contextmanager
def loader_span(
    personas_dir: str, *, outcome: str, persona_count: int | None = None
) -> Iterator[trace.Span]:
    """Root span for one loader run (D9: loader runs produce spans with
    outcome loaded / failed + field)."""
    with _tracer().start_as_current_span("loam.persona.loader") as span:
        span.set_attribute("loam.persona.dir", personas_dir)
        span.set_attribute("loam.persona.load.outcome", outcome)
        if persona_count is not None:
            span.set_attribute("loam.persona.load.count", persona_count)
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
    with _tracer().start_as_current_span("loam.persona.authoring") as span:
        span.set_attribute("loam.persona.authoring.trigger_signal", signal)
        for k, v in attributes.items():
            if v is not None:
                span.set_attribute(k, v)
        yield span


@contextmanager
def authoring_step_span(step_name: str) -> Iterator[trace.Span]:
    """Child span per authoring step (style_harvest | domain_research |
    contract_synthesis | self_review)."""
    with _tracer().start_as_current_span(f"loam.persona.authoring.{step_name}") as span:
        span.set_attribute("loam.persona.authoring.step", step_name)
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
        "loam.persona.monitor.tick",
        {
            "loam.persona.monitor.tick_id": tick_id,
            "loam.persona.monitor.active": active,
            "loam.persona.monitor.pending": pending,
            "loam.persona.monitor.stuck": stuck,
            "loam.persona.monitor.finished": finished,
            "loam.persona.monitor.escalated": escalated,
            "loam.persona.monitor.failed": failed,
        },
    )


def monitor_injection_event(*, turn_id: str, token_estimate: int) -> None:
    """One event per UserPromptSubmit injection (D3 acceptance)."""
    span = trace.get_current_span()
    span.add_event(
        "loam.persona.monitor.inject",
        {
            "loam.persona.monitor.turn_id": turn_id,
            "loam.persona.monitor.tokens_est": token_estimate,
        },
    )


def self_review_verdict_event(*, iteration: int, verdict: str, reasons: str) -> None:
    """Authoring self-review verdicts are recorded as events on the
    parent span (D9 acceptance)."""
    span = trace.get_current_span()
    span.add_event(
        "loam.persona.authoring.self_review",
        {
            "loam.persona.authoring.iteration": iteration,
            "loam.persona.authoring.verdict": verdict,
            "loam.persona.authoring.reasons": reasons,
        },
    )


def introduction_event(
    *, new_handle: str, channel: str, outcome: str, reason: str | None = None
) -> None:
    """Introduction dispatch emits an event with handle and channel (D9)."""
    attrs: dict[str, Any] = {
        "loam.persona.introduction.handle": new_handle,
        "loam.persona.introduction.channel": channel,
        "loam.persona.introduction.outcome": outcome,
    }
    if reason:
        attrs["loam.persona.introduction.reason"] = reason
    with _tracer().start_as_current_span("loam.persona.introduction") as span:
        span.add_event("loam.persona.introduction.dispatched", attrs)


def retirement_event(*, handle: str, reason: str) -> None:
    """Retirement emits an event naming the persona and reason (D9)."""
    with _tracer().start_as_current_span("loam.persona.retirement") as span:
        span.add_event(
            "loam.persona.retired",
            {
                "loam.persona.retirement.handle": handle,
                "loam.persona.retirement.reason": reason,
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
    with _tracer().start_as_current_span("loam.persona.onboarding.render") as span:
        span.add_event(
            "loam.persona.onboarding.render",
            {
                "loam.persona.onboarding.handle": handle,
                "loam.persona.onboarding.render.length": length,
            },
        )


def onboarding_starter_flag_transition_event(
    *, handle: str, from_value: bool, to_value: bool
) -> None:
    """One event per ``is_starter`` transition (AC35.7).

    Fires only on actual transitions (from != to) so steady-state
    re-loads of a non-starter contract do not produce noise.
    """
    with _tracer().start_as_current_span(
        "loam.persona.onboarding.starter_flag_transition"
    ) as span:
        span.add_event(
            "loam.persona.onboarding.starter_flag_transition",
            {
                "loam.persona.onboarding.handle": handle,
                "loam.persona.onboarding.starter_flag.from": from_value,
                "loam.persona.onboarding.starter_flag.to": to_value,
            },
        )


# ---- conversational-onboarding grounding (amendment #50) -------------


def onboarding_grounding_persisted_event(
    *, handle: str, workspace_slug: str | None = None
) -> None:
    """One event per successful grounding write-back (AC.O.5 / AC.O.4
    cross-cutting).

    Fires after the contract / prompt.md / .claude/agents/<handle>.md
    triplet has been written; observability captures the structural
    completion of the captured-grounding write-back. The optional
    memory episode is reported separately via
    ``onboarding_grounding_episode_failed_event`` on failure.
    """
    with _tracer().start_as_current_span(
        "loam.persona.onboarding.grounding_persisted"
    ) as span:
        attrs: dict[str, Any] = {
            "loam.persona.onboarding.handle": handle,
        }
        if workspace_slug is not None:
            attrs["loam.persona.onboarding.workspace_slug"] = workspace_slug
        span.add_event(
            "loam.persona.onboarding.grounding_persisted", attrs
        )


def onboarding_grounding_episode_failed_event(
    *,
    handle: str,
    workspace_slug: str | None = None,
    stage: str,
    error: str,
) -> None:
    """One event per ``add_episode`` write-failure during
    ``persist_grounding`` (AC.O.5 fail-soft direction).

    The disk write-back already succeeded by the time this fires;
    the memory episode is best-effort. ``stage`` names which step
    failed (``factory`` | ``call`` | ``await``); ``error`` names
    the exception class + message tail.
    """
    with _tracer().start_as_current_span(
        "loam.persona.onboarding.grounding_episode_failed"
    ) as span:
        attrs: dict[str, Any] = {
            "loam.persona.onboarding.handle": handle,
            "loam.persona.onboarding.grounding_episode.stage": stage,
            "loam.persona.onboarding.grounding_episode.error": error,
        }
        if workspace_slug is not None:
            attrs["loam.persona.onboarding.workspace_slug"] = workspace_slug
        span.add_event(
            "loam.persona.onboarding.grounding_episode_failed", attrs
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
        "loam.persona.tracker_context.composed"
    ) as span:
        span.add_event(
            "loam.persona.tracker_context.composed",
            {
                "loam.persona.tracker_context.handle": handle,
                "loam.persona.tracker_context.in_flight_count": in_flight_count,
                "loam.persona.tracker_context.truncated_count": truncated_count,
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
        "loam.persona.tracker_context.unavailable"
    ) as span:
        span.add_event(
            "loam.persona.tracker_context.unavailable",
            {
                "loam.persona.tracker_context.handle": handle,
                "loam.persona.tracker_context.failure_class": failure_class,
                "loam.persona.tracker_context.detail": detail,
            },
        )
