"""OTel span emitters for the Telegram interface.

A1 correction held — uses `trace.get_tracer("loam.telegram_interface")`
only. No TracerProvider constructed here. Routing is the
observability-aggregator's responsibility.

Span namespace: `loam.telegram.*`. Every outbound, inbound, fallback,
setup-step, allowlist-modification, and availability transition emits
exactly one span or event.
"""

from __future__ import annotations

from typing import Any, Iterable

from opentelemetry import trace


_TRACER = trace.get_tracer("loam.telegram_interface")


def _set(span: trace.Span, attrs: dict[str, Any]) -> None:
    for k, v in attrs.items():
        if v is None:
            continue
        try:
            span.set_attribute(k, v)
        except Exception:
            span.set_attribute(k, str(v))


def outbound_sent(
    *,
    path: str,  # "mcp_reply" | "bot_api" | "in_session_fallback" | "attention_md"
    chat_id: str | None,
    identity: str | None,
    bytes_sent: int,
) -> None:
    with _TRACER.start_as_current_span("loam.telegram.outbound_sent") as span:
        _set(
            span,
            {
                "telegram.path": path,
                "telegram.chat_id": chat_id,
                "telegram.identity": identity,
                "telegram.bytes_sent": bytes_sent,
            },
        )


def outbound_failed(
    *, path: str, chat_id: str | None, error_class: str, error_code: int
) -> None:
    with _TRACER.start_as_current_span("loam.telegram.outbound_failed") as span:
        _set(
            span,
            {
                "telegram.path": path,
                "telegram.chat_id": chat_id,
                "telegram.error_class": error_class,
                "telegram.error_code": error_code,
            },
        )


def inbound_received(
    *,
    chat_id: str,
    user_id: str,
    identity: str | None,
    authority_class: str | None,
    content_chars: int,
) -> None:
    with _TRACER.start_as_current_span("loam.telegram.inbound_received") as span:
        _set(
            span,
            {
                "telegram.chat_id": chat_id,
                "telegram.user_id": user_id,
                "telegram.identity": identity,
                "telegram.authority_class": authority_class,
                "telegram.content_chars": content_chars,
            },
        )


def inbound_rejected(*, user_id: str, reason: str) -> None:
    with _TRACER.start_as_current_span("loam.telegram.inbound_rejected") as span:
        _set(
            span,
            {"telegram.user_id": user_id, "telegram.reason": reason},
        )


def availability_probe(
    *,
    cached: bool,
    available: bool,
    latency_ms: float | None,
    failure_class: str | None,
) -> None:
    with _TRACER.start_as_current_span("loam.telegram.availability_probe") as span:
        _set(
            span,
            {
                "telegram.cached": cached,
                "telegram.available": available,
                "telegram.latency_ms": latency_ms,
                "telegram.failure_class": failure_class,
            },
        )


def availability_transition(*, from_state: str, to_state: str, reason: str) -> None:
    with _TRACER.start_as_current_span(
        "loam.telegram.availability_transition"
    ) as span:
        _set(
            span,
            {
                "telegram.from": from_state,
                "telegram.to": to_state,
                "telegram.reason": reason,
            },
        )


def fallback_triggered(*, reason: str, surfaces: Iterable[str]) -> None:
    with _TRACER.start_as_current_span("loam.telegram.fallback_triggered") as span:
        _set(
            span,
            {
                "telegram.reason": reason,
                "telegram.surfaces": ",".join(sorted(surfaces)),
            },
        )


def setup_step(*, step: int, status: str, detail: str | None = None) -> None:
    with _TRACER.start_as_current_span("loam.telegram.setup_step") as span:
        _set(
            span,
            {
                "telegram.setup.step": step,
                "telegram.setup.status": status,
                "telegram.setup.detail": detail,
            },
        )


def allowlist_modified(
    *, action: str, user_id: str, authority_class: str, actor: str
) -> None:
    with _TRACER.start_as_current_span("loam.telegram.allowlist_modified") as span:
        _set(
            span,
            {
                "telegram.allowlist.action": action,
                "telegram.user_id": user_id,
                "telegram.authority_class": authority_class,
                "telegram.actor": actor,
            },
        )


def allowlist_record_malformed(
    *, user_id: str, exception_class: str, missing_key: str | None
) -> None:
    """Fire-and-forget span for a malformed ``pos_identities`` record.

    Covers the AC:none silent-except site cleared by amendment #21
    (S3 silent-except bundle) in ``AccessFile.identities()``. A record
    that is missing a required key (``user_id`` / ``display_name`` /
    ``authority_class`` / ``added_at``) or is not a mapping was
    previously skipped silently — an operator could not distinguish
    "record corrupt" from "user unknown" on a ``lookup(...)`` miss.
    The span now carries the offending record's id and the missing
    key (when available from the ``KeyError``).
    """
    with _TRACER.start_as_current_span(
        "loam.telegram.allowlist_record_malformed"
    ) as span:
        _set(
            span,
            {
                "telegram.user_id": user_id,
                "exception.class": exception_class,
                "telegram.allowlist.malformed_key": missing_key or "<unknown>",
            },
        )


def confirmation_flow(
    *, action: str, identity: str, outcome: str, elapsed_s: float | None = None
) -> None:
    with _TRACER.start_as_current_span("loam.telegram.confirmation_flow") as span:
        _set(
            span,
            {
                "telegram.confirm.action": action,
                "telegram.confirm.identity": identity,
                "telegram.confirm.outcome": outcome,
                "telegram.confirm.elapsed_s": elapsed_s,
            },
        )
