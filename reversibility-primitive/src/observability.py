"""OTel span emitters for the reversibility primitive.

Uses `trace.get_tracer("pos.reversibility_primitive")` only — no
TracerProvider is constructed here (R22). Routing is the
observability-aggregator's responsibility; this module is a pure
emitter. Span namespace: `pos.reversibility.*`.
"""

from __future__ import annotations

from typing import Any

from opentelemetry import trace


_TRACER = trace.get_tracer("pos.reversibility_primitive", "0.1.0")


def _set(span: trace.Span, attrs: dict[str, Any]) -> None:
    for k, v in attrs.items():
        if v is None:
            continue
        try:
            span.set_attribute(k, v)
        except Exception:
            span.set_attribute(k, str(v))


def binding_registered(
    *, scope_id: str, handle: str, idempotency_key: str
) -> None:
    with _TRACER.start_as_current_span("pos.reversibility.binding_registered") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.handle": handle,
                "pos.reversibility.idempotency_key": idempotency_key,
            },
        )


def binding_replaced(
    *,
    scope_id: str,
    prior_handle: str,
    new_handle: str,
) -> None:
    with _TRACER.start_as_current_span("pos.reversibility.binding_replaced") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.prior_handle": prior_handle,
                "pos.reversibility.handle": new_handle,
            },
        )


def binding_redundant(*, scope_id: str, handle: str) -> None:
    """R6 audit-only emission — fully_reversible + binding-present.

    Audit span, not a block; helps workspaces see over-registration.
    """
    with _TRACER.start_as_current_span("pos.reversibility.binding_redundant") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.handle": handle,
            },
        )


def activation_refused(
    *,
    scope_id: str,
    reversibility_class: str,
    reason: str,
    code: int,
) -> None:
    with _TRACER.start_as_current_span("pos.reversibility.activation_refused") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.class": reversibility_class,
                "pos.reversibility.refusal_reason": reason,
                "pos.reversibility.refusal_code": code,
            },
        )


def activation_passed(
    *, scope_id: str, reversibility_class: str, path: str
) -> None:
    """Audit emission when the gate passes. `path` records WHY it
    passed (fully_reversible, binding_present, safety_approved)."""
    with _TRACER.start_as_current_span("pos.reversibility.activation_passed") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.class": reversibility_class,
                "pos.reversibility.pass_path": path,
            },
        )


def rollback_requested(
    *, scope_id: str, idempotency_key: str, reason: str
) -> None:
    with _TRACER.start_as_current_span("pos.reversibility.rollback_requested") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.idempotency_key": idempotency_key,
                "pos.reversibility.rollback_reason": reason,
            },
        )


def rollback_succeeded(
    *, scope_id: str, idempotency_key: str, handle: str
) -> None:
    with _TRACER.start_as_current_span("pos.reversibility.rollback_succeeded") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.idempotency_key": idempotency_key,
                "pos.reversibility.handle": handle,
            },
        )


def rollback_failed(
    *,
    scope_id: str,
    idempotency_key: str,
    handle: str | None,
    reason: str,
) -> None:
    with _TRACER.start_as_current_span("pos.reversibility.rollback_failed") as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.idempotency_key": idempotency_key,
                "pos.reversibility.handle": handle or "<unregistered>",
                "pos.reversibility.failure_reason": reason,
            },
        )


def rollback_idempotent_hit(
    *, scope_id: str, idempotency_key: str, prior_outcome: str
) -> None:
    with _TRACER.start_as_current_span(
        "pos.reversibility.rollback_idempotent_hit"
    ) as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.idempotency_key": idempotency_key,
                "pos.reversibility.prior_outcome": prior_outcome,
            },
        )


def path_chosen(
    *,
    chosen_class: str,
    alternatives_count: int,
    alternative_classes: list[str],
    chosen_index: int,
    reason: str,
    override: bool,
    downrank_warning: bool,
) -> None:
    with _TRACER.start_as_current_span("pos.reversibility.path_chosen") as span:
        _set(
            span,
            {
                "pos.reversibility.chosen_class": chosen_class,
                "pos.reversibility.alternatives_count": alternatives_count,
                "pos.reversibility.alternative_classes": ",".join(alternative_classes),
                "pos.reversibility.chosen_index": chosen_index,
                "pos.reversibility.choice_reason": reason,
                "pos.reversibility.override": override,
                "pos.reversibility.downrank_warning": downrank_warning,
            },
        )


def cascade_rollback_invoked(
    *, scope_id: str, parent_scope_id: str | None, idempotency_key: str
) -> None:
    with _TRACER.start_as_current_span(
        "pos.reversibility.cascade_rollback_invoked"
    ) as span:
        _set(
            span,
            {
                "pos.reversibility.scope_id": scope_id,
                "pos.reversibility.parent_scope_id": parent_scope_id or "",
                "pos.reversibility.idempotency_key": idempotency_key,
            },
        )
