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

"""OTel emission helpers for dormancy (D9).

Every detection event, FSM transition, policy dispatch, notification-
threshold crossing, and resume event produces an OTel span. Per A1
correction, emission succeeds with no consumer present — the default
SDK noop tracer silently accepts every call.

Span namespace: `loam.dormancy.*`.

v1.1 R12 compliance: narrative / judge / probe adapter calls carry
`loam.prompt.type` on their spans so per-prompt-type cost attribution
downstream matches scope-of-work's per-prompt view.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, TYPE_CHECKING

from opentelemetry import trace

if TYPE_CHECKING:  # pragma: no cover — hint only
    from .adapter import AdapterEvent
    from .errors import ClaudeAPIError

_TRACER = trace.get_tracer("loam.dormancy", "0.1.0")


# ---- generic helpers ---------------------------------------------------


@contextmanager
def operation_span(name: str, **attrs: Any) -> Iterator[trace.Span]:
    with _TRACER.start_as_current_span(name) as span:
        _apply_attrs(span, attrs)
        yield span


def emit_event(span: trace.Span | None, name: str, attrs: dict[str, Any]) -> None:
    if span is None:
        return
    clean = {k: v for k, v in attrs.items() if v is not None}
    try:
        span.add_event(name, attributes=clean)
    except Exception:
        span.add_event(name)


def _apply_attrs(span: trace.Span, attrs: dict[str, Any]) -> None:
    for k, v in attrs.items():
        if v is None:
            continue
        try:
            span.set_attribute(k, v)
        except Exception:
            span.set_attribute(k, str(v))


# ---- adapter spans -----------------------------------------------------


@contextmanager
def adapter_span(
    *,
    prompt_name: str,
    model: str,
    call_id: str,
) -> Iterator[trace.Span]:
    """Span around a single adapter.call invocation.

    Always carries `loam.prompt.type` so v1.1 R12 can aggregate
    per-prompt cost.
    """
    with _TRACER.start_as_current_span("loam.dormancy.claude_call") as span:
        span.set_attribute("loam.prompt.type", prompt_name)
        span.set_attribute("loam.prompt.name", prompt_name)
        span.set_attribute("loam.model", model)
        span.set_attribute("loam.call_id", call_id)
        yield span


def emit_adapter_event(
    span: trace.Span,
    event: "AdapterEvent",
    *,
    error: "ClaudeAPIError | None" = None,
) -> None:
    """Record the result of an adapter call on its span."""
    attrs: dict[str, Any] = {
        "loam.call.ok": event.ok,
        "loam.call.latency_seconds": event.latency_seconds,
    }
    if event.signal is not None:
        attrs["loam.dormancy.signal"] = event.signal.value
    if event.retry_after is not None:
        attrs["loam.retry_after_seconds"] = event.retry_after
    if event.status_code is not None:
        attrs["loam.http.status_code"] = event.status_code
    span.add_event("loam.dormancy.detection_event", attributes=attrs)
    if error is not None:
        span.record_exception(error)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))


# ---- mode-FSM spans ----------------------------------------------------


def fsm_transition(
    mode: str,
    from_state: str,
    to_state: str,
    trigger: str,
    **extra: Any,
) -> None:
    with _TRACER.start_as_current_span("loam.dormancy.fsm_transition") as span:
        span.set_attribute("loam.dormancy.mode", mode)
        span.set_attribute("loam.dormancy.from_state", from_state)
        span.set_attribute("loam.dormancy.to_state", to_state)
        span.set_attribute("loam.dormancy.trigger", trigger)
        _apply_attrs(span, extra)


# ---- episode spans -----------------------------------------------------


def episode_started(
    *,
    episode_id: str,
    signal: str,
    policy: str,
    paused_scope_ids: list[str],
    mode: str,
) -> None:
    with _TRACER.start_as_current_span("loam.dormancy.episode_started") as span:
        span.set_attribute("loam.dormancy.episode_id", episode_id)
        span.set_attribute("loam.dormancy.signal", signal)
        span.set_attribute("loam.dormancy.policy", policy)
        span.set_attribute("loam.dormancy.mode", mode)
        span.set_attribute("loam.dormancy.paused_scope_count", len(paused_scope_ids))
        # Amendment #20 — Site 8: replace silent fallback with a span
        # event on the already-open span so the attribute-set failure
        # (e.g. string too long for SDK limit) is observable.
        try:
            span.set_attribute(
                "loam.dormancy.paused_scope_ids", ",".join(paused_scope_ids)
            )
        except Exception as e:
            span.add_event(
                "paused_scope_ids_attr_failed",
                {
                    "exception_class": type(e).__name__,
                    "count": len(paused_scope_ids),
                },
            )


def episode_resolved(
    *,
    episode_id: str,
    duration_seconds: float,
    resolution_kind: str,
    resumed_scope_count: int = 0,
) -> None:
    with _TRACER.start_as_current_span("loam.dormancy.episode_resolved") as span:
        span.set_attribute("loam.dormancy.episode_id", episode_id)
        span.set_attribute("loam.dormancy.duration_seconds", duration_seconds)
        span.set_attribute("loam.dormancy.resolution_kind", resolution_kind)
        span.set_attribute(
            "loam.dormancy.resumed_scope_count", resumed_scope_count
        )


def policy_decision(
    *, policy: str, episode_id: str, mode: str, reason: str = ""
) -> None:
    with _TRACER.start_as_current_span("loam.dormancy.policy_decision") as span:
        span.set_attribute("loam.dormancy.policy", policy)
        span.set_attribute("loam.dormancy.episode_id", episode_id)
        span.set_attribute("loam.dormancy.mode", mode)
        if reason:
            span.set_attribute("loam.dormancy.reason", reason)


def probe_call(
    *, mode: str, result: str, attempt_n: int, latency_seconds: float
) -> None:
    with _TRACER.start_as_current_span("loam.dormancy.probe_call") as span:
        span.set_attribute("loam.dormancy.mode", mode)
        span.set_attribute("loam.dormancy.probe_result", result)
        span.set_attribute("loam.dormancy.probe_attempt", attempt_n)
        span.set_attribute("loam.dormancy.latency_seconds", latency_seconds)


def notification_dispatched(
    *,
    episode_id: str,
    channel: str,
    outcome: str,
    threshold_triggered: str,
    tier: int,
) -> None:
    with _TRACER.start_as_current_span(
        "loam.dormancy.notification_dispatched"
    ) as span:
        span.set_attribute("loam.dormancy.episode_id", episode_id)
        span.set_attribute("loam.dormancy.channel", channel)
        span.set_attribute("loam.dormancy.notification_outcome", outcome)
        span.set_attribute(
            "loam.dormancy.threshold_triggered", threshold_triggered
        )
        span.set_attribute("loam.notification.tier", tier)


# ---- Amendment #20 — S2 silent-except observability surfaces ----------
#
# Two emitters introduced by amendment #20 (2026-04-22 S2 silent-except
# bundle) to replace two silent `except ...: pass|continue` branches in
# component.py.


def scope_lookup_failed(
    *,
    episode_id: str,
    scope_id: str,
    exception_class: str,
) -> None:
    """Site 6 surface — `_any_paused_scope_user_relevant` scope lookup.

    A silent drop on a per-scope lookup failure could downgrade an
    episode's user-relevance and suppress notifications; this span
    makes the drop observable.
    """
    with _TRACER.start_as_current_span(
        "loam.dormancy.scope_lookup_failed"
    ) as span:
        span.set_attribute("loam.dormancy.episode_id", episode_id)
        span.set_attribute("loam.dormancy.scope_id", scope_id)
        span.set_attribute("loam.dormancy.exception_class", exception_class)


def reconcile_restore_failed(
    *,
    episode_id: str,
    mode_value: str,
    policy_value: str,
    exception_class: str,
) -> None:
    """Site 7 surface — `reconcile_on_startup` in-memory rebuild.

    A stored mode/policy value that no longer maps to an enum (schema
    drift across restarts) is silently dropped; this span surfaces the
    drop so an operator sees "startup reconciled N, 1 dropped-on-
    restore."
    """
    with _TRACER.start_as_current_span(
        "loam.dormancy.reconcile_restore_failed"
    ) as span:
        span.set_attribute("loam.dormancy.episode_id", episode_id)
        span.set_attribute("loam.dormancy.mode_value", mode_value)
        span.set_attribute("loam.dormancy.policy_value", policy_value)
        span.set_attribute("loam.dormancy.exception_class", exception_class)
