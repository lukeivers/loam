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

"""OpenTelemetry emission for scope lifecycle (D5 / v1.1 R11).

The primitive emits OTel spans + events; no consumer is assumed to
exist (A1 correction). When no consumer is configured, the SDK's
default no-op tracer absorbs the calls — emission still succeeds.

Span structure (proposal §2.6):

  • One `invoke_scope` INTERNAL span per scope, opened on the first
    transition into `active` and closed on terminal transition.
  • Child `chat {model}` spans per LLM call (recorded via `debit`),
    standard GenAI convention.
  • Span events on the parent span at every state transition.

Attributes (proposal §2.6):

  • GenAI: gen_ai.agent.id, gen_ai.agent.name, gen_ai.agent.description,
    gen_ai.usage.input_tokens, gen_ai.usage.output_tokens,
    gen_ai.request.model
  • pOS-namespaced: loam.scope.id, loam.scope.parent_id,
    loam.scope.reversibility_class, loam.scope.budget.*.remaining,
    loam.scope.escalation.reason, loam.scope.success_criteria.*
"""

from __future__ import annotations

from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.trace import (
        SpanKind,
        Status,
        StatusCode,
        set_span_in_context,
    )
    _OTEL_AVAILABLE = True
except Exception:  # pragma: no cover -- never expected
    _OTEL_AVAILABLE = False


_TRACER_NAME = "loam.scope_of_work"


def get_tracer():
    if not _OTEL_AVAILABLE:
        return None
    return trace.get_tracer(_TRACER_NAME)


def start_invoke_scope_span(
    *,
    scope_id: str,
    parent_scope_id: str | None,
    owner_persona: str | None,
    goal: str,
    reversibility_class: str,
) -> Any:
    """Start (but do not enter as current) the scope's `invoke_scope` span.

    Returns the OTel Span object — caller stores it and calls
    `end_span(span)` on terminal transition. We do NOT use
    `start_as_current_span` because the span outlives a single asyncio
    task and the contextvars-based current-span attach/detach dance is
    not safe across task boundaries.
    """
    tracer = get_tracer()
    if tracer is None:
        return None
    attrs = {
        "gen_ai.agent.id": scope_id,
        "gen_ai.agent.name": owner_persona or "unspecified",
        "gen_ai.agent.description": goal,
        "loam.scope.id": scope_id,
        "loam.scope.reversibility_class": reversibility_class,
    }
    if parent_scope_id:
        attrs["loam.scope.parent_id"] = parent_scope_id
    return tracer.start_span(
        "invoke_scope",
        kind=SpanKind.INTERNAL,
        attributes=attrs,
    )


def end_span(span: Any | None) -> None:
    if span is None:
        return
    span.end()


def emit_chat_span(
    *,
    model: str,
    prompt_name: str | None,
    input_tokens: int,
    output_tokens: int,
    scope_id: str,
    parent_span: Any | None = None,
) -> None:
    tracer = get_tracer()
    if tracer is None:
        return
    span_name = f"chat {model}"
    attrs = {
        "gen_ai.request.model": model,
        "gen_ai.usage.input_tokens": input_tokens,
        "gen_ai.usage.output_tokens": output_tokens,
        "loam.scope.id": scope_id,
    }
    if prompt_name:
        attrs["loam.prompt.name"] = prompt_name
    parent_ctx = set_span_in_context(parent_span) if parent_span is not None else None
    span = tracer.start_span(
        span_name,
        kind=SpanKind.CLIENT,
        attributes=attrs,
        context=parent_ctx,
    )
    span.end()


def add_span_event(
    span: Any | None, name: str, attributes: dict[str, Any] | None = None
) -> None:
    if span is None:
        return
    span.add_event(name, attributes=attributes or {})


def set_span_attrs(span: Any | None, **attrs: Any) -> None:
    if span is None:
        return
    for k, v in attrs.items():
        if v is None:
            continue
        span.set_attribute(k, v)


def fail_span(span: Any | None, reason: str) -> None:
    if span is None or not _OTEL_AVAILABLE:
        return
    span.set_status(Status(StatusCode.ERROR, reason))


def emit_projection_parse_failure(
    *,
    scope_id: str,
    field: str,
    exception_class: str,
) -> None:
    """Fire-and-forget span for a projection-parse failure.

    Covers the two AC:none silent-except sites cleared by amendment #21
    (S3 silent-except bundle) — `triggers.py:active_seconds_elapsed`'s
    ISO-timestamp parse and `projection.py:apply_event`'s
    StateTransitioned time-accounting parse. The `field` attribute
    distinguishes the two call sites so an operator can filter by
    site when triaging projection-data-integrity issues.

    No caller-visible return; the callers keep their existing return
    values (stale-but-safe elapsed / None for apply_event), preserving
    their public contracts. The span IS the observable surface that
    the former silent `pass` branches lacked.
    """
    tracer = get_tracer()
    if tracer is None:
        return
    span = tracer.start_span(
        "loam.scope.projection_parse_failed",
        kind=SpanKind.INTERNAL,
        attributes={
            "loam.scope.id": scope_id,
            "loam.scope.projection_field": field,
            "exception.class": exception_class,
        },
    )
    span.set_status(Status(StatusCode.ERROR, "projection parse failed"))
    span.end()


def span_ids(span: Any | None) -> tuple[str | None, str | None]:
    """Return (trace_id_hex, span_id_hex) for a given span, if available."""
    if span is None or not _OTEL_AVAILABLE:
        return None, None
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return None, None
    return f"{ctx.trace_id:032x}", f"{ctx.span_id:016x}"


def current_span_ids() -> tuple[str | None, str | None]:
    """Best-effort current-span lookup. Falls back to (None, None) when
    no span is active in the current context — which is most call sites
    in the runtime now that we no longer attach the invoke_scope span
    via contextvars."""
    if not _OTEL_AVAILABLE:
        return None, None
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if not ctx.is_valid:
        return None, None
    return f"{ctx.trace_id:032x}", f"{ctx.span_id:016x}"
