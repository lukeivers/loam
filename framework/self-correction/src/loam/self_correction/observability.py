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

"""OTel span emitters for self-correction.

Uses `trace.get_tracer("loam.self_correction")` only — no TracerProvider
is constructed here (A1 correction, brief hard constraint). Span
namespace: `loam.correction.*` (Eve-inference #8 — kept; consistent with
the cost-governance parallel where tracer=`loam.cost_governance` and
spans=`loam.cost.*`).
"""

from __future__ import annotations

from typing import Any

from opentelemetry import trace


_TRACER = trace.get_tracer("loam.self_correction", "0.10.0")


def _set(span: trace.Span, attrs: dict[str, Any]) -> None:
    for k, v in attrs.items():
        if v is None:
            continue
        try:
            span.set_attribute(k, v)
        except Exception:
            span.set_attribute(k, str(v))


def trigger_received(
    *,
    trigger_id: str,
    source: str,
    scope_id: str | None,
    failure_class_hint: str | None,
) -> None:
    with _TRACER.start_as_current_span("loam.correction.trigger_received") as span:
        _set(
            span,
            {
                "loam.correction.trigger_id": trigger_id,
                "loam.correction.trigger_source": source,
                "loam.correction.scope_id": scope_id,
                "loam.correction.failure_class_hint": failure_class_hint,
            },
        )


def trigger_deduplicated(
    *, trigger_id: str, dedup_key: str, source: str
) -> None:
    with _TRACER.start_as_current_span("loam.correction.trigger_deduplicated") as span:
        _set(
            span,
            {
                "loam.correction.trigger_id": trigger_id,
                "loam.correction.dedup_key": dedup_key,
                "loam.correction.trigger_source": source,
            },
        )


def episode_opened(
    *,
    episode_id: str,
    correction_scope_id: str,
    parent_correction_id: str | None,
    failure_class: str,
) -> None:
    with _TRACER.start_as_current_span("loam.correction.episode_opened") as span:
        _set(
            span,
            {
                "loam.correction.episode_id": episode_id,
                "loam.correction.scope_id": correction_scope_id,
                "loam.correction.parent_correction_id": parent_correction_id,
                "loam.correction.failure_class": failure_class,
            },
        )


def episode_closed(
    *,
    episode_id: str,
    correction_scope_id: str,
    failure_class: str,
    records_present: int,
) -> None:
    with _TRACER.start_as_current_span("loam.correction.closed") as span:
        _set(
            span,
            {
                "loam.correction.episode_id": episode_id,
                "loam.correction.scope_id": correction_scope_id,
                "loam.correction.failure_class": failure_class,
                "loam.correction.records_present": records_present,
            },
        )


def episode_refused(
    *,
    episode_id: str,
    reason: str,
    code: int,
    details: dict[str, Any] | None = None,
) -> None:
    with _TRACER.start_as_current_span("loam.correction.episode_refused") as span:
        _set(
            span,
            {
                "loam.correction.episode_id": episode_id,
                "loam.correction.refusal_reason": reason,
                "loam.correction.refusal_code": code,
                **(details or {}),
            },
        )
        # Amendment #20 — Site 4: replace silent fallback with a span
        # event on the already-open span so the OTel-SDK/import failure
        # is observable. The span's primary attrs still land; only the
        # ERROR-status marker is lost, which the event now captures.
        try:
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, reason))
        except Exception as e:
            span.add_event(
                "status_set_failed",
                {"exception_class": type(e).__name__},
            )


def cascade_escalated(
    *,
    kind: str,
    failure_class: str | None,
    parent_correction_id: str | None,
    depth: int | None,
    window_count: int | None,
) -> None:
    with _TRACER.start_as_current_span("loam.correction.cascade_escalated") as span:
        _set(
            span,
            {
                "loam.correction.cascade_kind": kind,
                "loam.correction.failure_class": failure_class,
                "loam.correction.parent_correction_id": parent_correction_id,
                "loam.correction.depth": depth,
                "loam.correction.window_count": window_count,
            },
        )


def cost_refusal_caught(
    *,
    episode_id: str,
    code: int,
    message: str,
) -> None:
    with _TRACER.start_as_current_span("loam.correction.cost_refusal_caught") as span:
        _set(
            span,
            {
                "loam.correction.episode_id": episode_id,
                "loam.correction.cost_refusal_code": code,
                "loam.correction.cost_refusal_message": message,
            },
        )
        # Amendment #20 — Site 5: same pattern as Site 4 (episode_refused).
        try:
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, message))
        except Exception as e:
            span.add_event(
                "status_set_failed",
                {"exception_class": type(e).__name__},
            )


def record_part_persisted(
    *,
    episode_id: str,
    record_type: str,
) -> None:
    with _TRACER.start_as_current_span("loam.correction.record_persisted") as span:
        _set(
            span,
            {
                "loam.correction.episode_id": episode_id,
                "loam.correction.record_type": record_type,
            },
        )


# ---- Amendment #20 — S2 silent-except observability surfaces ----------
#
# Three emitters introduced by amendment #20 (2026-04-22 S2 silent-except
# bundle) to replace three silent `except ...: pass|continue` branches
# across triggers.py and completion_check.py. Each emitter is the minimum
# observable surface for its site's named concern (research doc §2).


def span_attribute_lookup_failed(
    *,
    trigger_source: str,
    attribute_name: str,
    exception_class: str,
) -> None:
    """Site 1 surface — `build_trigger_from_span` scope-id lookup failed.

    Preserves `scope_id=None` default; the dedup-degradation signal is
    now observable instead of silently breaking dedup.
    """
    with _TRACER.start_as_current_span(
        "loam.correction.span_attribute_lookup_failed"
    ) as span:
        _set(
            span,
            {
                "loam.correction.trigger_source": trigger_source,
                "loam.correction.attribute_name": attribute_name,
                "loam.correction.exception_class": exception_class,
            },
        )


def poll_tick(
    *,
    poller_name: str,
    interval_seconds: int,
) -> None:
    """Site 2 surface — `OTelAnomalyPoller.run_forever` timeout iteration.

    Fires once per timeout-driven loop iteration (the designed
    sleep-with-early-wake control flow via `asyncio.wait_for` +
    `_stopped.wait()`). Liveness is now observable.
    """
    with _TRACER.start_as_current_span("loam.correction.poll_tick") as span:
        _set(
            span,
            {
                "loam.correction.poller_name": poller_name,
                "loam.correction.poll_interval_seconds": interval_seconds,
            },
        )


def audit_notify_no_loop(
    *,
    episode_id: str,
) -> None:
    """Site 3 surface — `audit_subscription` one-on-one notify dropped.

    The `episode_refused` span already fired upstream; this emitter
    captures that the async notification was dropped because no running
    loop existed to schedule it on.
    """
    with _TRACER.start_as_current_span(
        "loam.correction.audit_notify_no_loop"
    ) as span:
        _set(
            span,
            {"loam.correction.episode_id": episode_id},
        )
