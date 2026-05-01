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

"""OTel span emitters for cost governance.

Uses `trace.get_tracer("loam.cost_governance")` only — no TracerProvider
is constructed here (A1 correction, brief hard constraint). Routing is
the observability-aggregator's responsibility; this module is a pure
emitter. Span namespace: `loam.cost.*`.
"""

from __future__ import annotations

from typing import Any

from opentelemetry import trace


_TRACER = trace.get_tracer("loam.cost_governance", "0.1.0")


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
    with _TRACER.start_as_current_span("loam.cost.reservation_created") as span:
        _set(
            span,
            {
                "loam.cost.scope_id": scope_id,
                "loam.cost.session_id": session_id,
                "loam.cost.reserved_time_seconds": reserved_time,
                "loam.cost.reserved_tokens": reserved_tokens,
                "loam.cost.reserved_money_cents": reserved_money_cents,
            },
        )


def reservation_reconciled(
    *,
    scope_id: str,
    actual_time: int,
    actual_tokens: int,
    actual_money_cents: int,
) -> None:
    with _TRACER.start_as_current_span("loam.cost.reservation_reconciled") as span:
        _set(
            span,
            {
                "loam.cost.scope_id": scope_id,
                "loam.cost.actual_time_seconds": actual_time,
                "loam.cost.actual_tokens": actual_tokens,
                "loam.cost.actual_money_cents": actual_money_cents,
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
    with _TRACER.start_as_current_span("loam.cost.activation_refused") as span:
        _set(
            span,
            {
                "loam.cost.scope_id": scope_id,
                "loam.cost.ceiling_kind": ceiling_kind,
                "loam.cost.axis": axis,
                "loam.cost.window_kind": window_kind or "",
                "loam.cost.refusal_code": code,
                "loam.cost.refusal_reason": reason,
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
    with _TRACER.start_as_current_span("loam.cost.ceiling_warning") as span:
        _set(
            span,
            {
                "loam.cost.scope_id": scope_id,
                "loam.cost.ceiling_kind": ceiling_kind,
                "loam.cost.axis": axis,
                "loam.cost.window_kind": window_kind or "",
                "loam.cost.fraction": fraction,
                "loam.cost.projected": projected,
                "loam.cost.ceiling": ceiling,
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
    with _TRACER.start_as_current_span("loam.cost.ceiling_adjusted") as span:
        _set(
            span,
            {
                "loam.cost.ceiling_kind": ceiling_kind,
                "loam.cost.axis": axis,
                "loam.cost.window_kind": window_kind or "",
                "loam.cost.new_value": new_value if new_value is not None else -1,
                "loam.cost.adjust_reason": reason,
                "loam.cost.audit_record_id": audit_record_id,
            },
        )


def rollup_closed(
    *, window_kind: str, interval_end_unix: float, total_money_cents: int
) -> None:
    with _TRACER.start_as_current_span("loam.cost.rollup_closed") as span:
        _set(
            span,
            {
                "loam.cost.window_kind": window_kind,
                "loam.cost.interval_end_unix": interval_end_unix,
                "loam.cost.total_money_cents": total_money_cents,
            },
        )


def retention_pruned(
    *,
    reservations_pruned: int,
    sessions_pruned: int,
) -> None:
    with _TRACER.start_as_current_span("loam.cost.retention_pruned") as span:
        _set(
            span,
            {
                "loam.cost.reservations_pruned": reservations_pruned,
                "loam.cost.sessions_pruned": sessions_pruned,
            },
        )
