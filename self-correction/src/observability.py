"""OTel span emitters for self-correction.

Uses `trace.get_tracer("pos.self_correction")` only — no TracerProvider
is constructed here (A1 correction, brief hard constraint). Span
namespace: `pos.correction.*` (Eve-inference #8 — kept; consistent with
the cost-governance parallel where tracer=`pos.cost_governance` and
spans=`pos.cost.*`).
"""

from __future__ import annotations

from typing import Any

from opentelemetry import trace


_TRACER = trace.get_tracer("pos.self_correction", "0.1.0")


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
    with _TRACER.start_as_current_span("pos.correction.trigger_received") as span:
        _set(
            span,
            {
                "pos.correction.trigger_id": trigger_id,
                "pos.correction.trigger_source": source,
                "pos.correction.scope_id": scope_id,
                "pos.correction.failure_class_hint": failure_class_hint,
            },
        )


def trigger_deduplicated(
    *, trigger_id: str, dedup_key: str, source: str
) -> None:
    with _TRACER.start_as_current_span("pos.correction.trigger_deduplicated") as span:
        _set(
            span,
            {
                "pos.correction.trigger_id": trigger_id,
                "pos.correction.dedup_key": dedup_key,
                "pos.correction.trigger_source": source,
            },
        )


def episode_opened(
    *,
    episode_id: str,
    correction_scope_id: str,
    parent_correction_id: str | None,
    failure_class: str,
) -> None:
    with _TRACER.start_as_current_span("pos.correction.episode_opened") as span:
        _set(
            span,
            {
                "pos.correction.episode_id": episode_id,
                "pos.correction.scope_id": correction_scope_id,
                "pos.correction.parent_correction_id": parent_correction_id,
                "pos.correction.failure_class": failure_class,
            },
        )


def episode_closed(
    *,
    episode_id: str,
    correction_scope_id: str,
    failure_class: str,
    records_present: int,
) -> None:
    with _TRACER.start_as_current_span("pos.correction.closed") as span:
        _set(
            span,
            {
                "pos.correction.episode_id": episode_id,
                "pos.correction.scope_id": correction_scope_id,
                "pos.correction.failure_class": failure_class,
                "pos.correction.records_present": records_present,
            },
        )


def episode_refused(
    *,
    episode_id: str,
    reason: str,
    code: int,
    details: dict[str, Any] | None = None,
) -> None:
    with _TRACER.start_as_current_span("pos.correction.episode_refused") as span:
        _set(
            span,
            {
                "pos.correction.episode_id": episode_id,
                "pos.correction.refusal_reason": reason,
                "pos.correction.refusal_code": code,
                **(details or {}),
            },
        )
        try:
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, reason))
        except Exception:
            pass


def cascade_escalated(
    *,
    kind: str,
    failure_class: str | None,
    parent_correction_id: str | None,
    depth: int | None,
    window_count: int | None,
) -> None:
    with _TRACER.start_as_current_span("pos.correction.cascade_escalated") as span:
        _set(
            span,
            {
                "pos.correction.cascade_kind": kind,
                "pos.correction.failure_class": failure_class,
                "pos.correction.parent_correction_id": parent_correction_id,
                "pos.correction.depth": depth,
                "pos.correction.window_count": window_count,
            },
        )


def cost_refusal_caught(
    *,
    episode_id: str,
    code: int,
    message: str,
) -> None:
    with _TRACER.start_as_current_span("pos.correction.cost_refusal_caught") as span:
        _set(
            span,
            {
                "pos.correction.episode_id": episode_id,
                "pos.correction.cost_refusal_code": code,
                "pos.correction.cost_refusal_message": message,
            },
        )
        try:
            from opentelemetry.trace.status import Status, StatusCode
            span.set_status(Status(StatusCode.ERROR, message))
        except Exception:
            pass


def record_part_persisted(
    *,
    episode_id: str,
    record_type: str,
) -> None:
    with _TRACER.start_as_current_span("pos.correction.record_persisted") as span:
        _set(
            span,
            {
                "pos.correction.episode_id": episode_id,
                "pos.correction.record_type": record_type,
            },
        )
