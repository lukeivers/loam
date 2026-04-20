"""OTel span emitters for cost governance.

Uses `trace.get_tracer("pos.cost_governance")` only — no TracerProvider
is constructed here (A1 correction, brief hard constraint). Routing is
the observability-aggregator's responsibility; this module is a pure
emitter. Span namespace: `pos.cost.*`.
"""

from __future__ import annotations

from typing import Any

from opentelemetry import trace


_TRACER = trace.get_tracer("pos.cost_governance", "0.1.0")


def _set(span: trace.Span, attrs: dict[str, Any]) -> None:
    for k, v in attrs.items():
        if v is None:
            continue
        try:
            span.set_attribute(k, v)
        except Exception:
            span.set_attribute(k, str(v))


def reservation_created(
    *,
    scope_id: str,
    session_id: str,
    reserved_time: int | None,
    reserved_tokens: int | None,
    reserved_money_cents: int | None,
) -> None:
    with _TRACER.start_as_current_span("pos.cost.reservation_created") as span:
        _set(
            span,
            {
                "pos.cost.scope_id": scope_id,
                "pos.cost.session_id": session_id,
                "pos.cost.reserved_time_seconds": reserved_time,
                "pos.cost.reserved_tokens": reserved_tokens,
                "pos.cost.reserved_money_cents": reserved_money_cents,
            },
        )


def reservation_reconciled(
    *,
    scope_id: str,
    actual_time: int,
    actual_tokens: int,
    actual_money_cents: int,
) -> None:
    with _TRACER.start_as_current_span("pos.cost.reservation_reconciled") as span:
        _set(
            span,
            {
                "pos.cost.scope_id": scope_id,
                "pos.cost.actual_time_seconds": actual_time,
                "pos.cost.actual_tokens": actual_tokens,
                "pos.cost.actual_money_cents": actual_money_cents,
            },
        )


def activation_refused(
    *,
    scope_id: str,
    ceiling_kind: str,
    axis: str,
    window_kind: str | None,
    code: int,
    reason: str,
) -> None:
    with _TRACER.start_as_current_span("pos.cost.activation_refused") as span:
        _set(
            span,
            {
                "pos.cost.scope_id": scope_id,
                "pos.cost.ceiling_kind": ceiling_kind,
                "pos.cost.axis": axis,
                "pos.cost.window_kind": window_kind or "",
                "pos.cost.refusal_code": code,
                "pos.cost.refusal_reason": reason,
            },
        )


def ceiling_warning(
    *,
    scope_id: str,
    ceiling_kind: str,
    axis: str,
    window_kind: str | None,
    fraction: float,
    projected: int,
    ceiling: int,
) -> None:
    with _TRACER.start_as_current_span("pos.cost.ceiling_warning") as span:
        _set(
            span,
            {
                "pos.cost.scope_id": scope_id,
                "pos.cost.ceiling_kind": ceiling_kind,
                "pos.cost.axis": axis,
                "pos.cost.window_kind": window_kind or "",
                "pos.cost.fraction": fraction,
                "pos.cost.projected": projected,
                "pos.cost.ceiling": ceiling,
            },
        )


def ceiling_adjusted(
    *,
    ceiling_kind: str,
    axis: str,
    window_kind: str | None,
    new_value: int | None,
    reason: str,
    audit_record_id: int,
) -> None:
    with _TRACER.start_as_current_span("pos.cost.ceiling_adjusted") as span:
        _set(
            span,
            {
                "pos.cost.ceiling_kind": ceiling_kind,
                "pos.cost.axis": axis,
                "pos.cost.window_kind": window_kind or "",
                "pos.cost.new_value": new_value if new_value is not None else -1,
                "pos.cost.adjust_reason": reason,
                "pos.cost.audit_record_id": audit_record_id,
            },
        )


def rollup_closed(
    *, window_kind: str, interval_end_unix: float, total_money_cents: int
) -> None:
    with _TRACER.start_as_current_span("pos.cost.rollup_closed") as span:
        _set(
            span,
            {
                "pos.cost.window_kind": window_kind,
                "pos.cost.interval_end_unix": interval_end_unix,
                "pos.cost.total_money_cents": total_money_cents,
            },
        )


def retention_pruned(
    *,
    reservations_pruned: int,
    sessions_pruned: int,
) -> None:
    with _TRACER.start_as_current_span("pos.cost.retention_pruned") as span:
        _set(
            span,
            {
                "pos.cost.reservations_pruned": reservations_pruned,
                "pos.cost.sessions_pruned": sessions_pruned,
            },
        )
