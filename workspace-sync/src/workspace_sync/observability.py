"""OTel span emission for the workspace-sync framework (v1.1 R11).

The component emits spans during a sync run so the observability
aggregator can ingest them. Salient names:

- ``pos.sync.started``
- ``pos.sync.merge_gate.resolution`` (per-conflict; AC.WS.11)
- ``pos.sync.merge_gate.summary``    (one per run; AC.WS.11)
- ``pos.sync.staged``
- ``pos.sync.applied``
- ``pos.sync.discarded``

Dependency injection: the tracer is acquired lazily via
``opentelemetry.trace.get_tracer`` so tests can install a custom
provider without hot-patching this module.

Salvaged from `self-upgrade/src/self_upgrade/observability.py` with
the tracer-name renamed `pos.self_upgrade` → `pos.workspace_sync` so
spans emitted from this component are namespaced separately from the
A-mode self-upgrade flow.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

_TRACER_NAME = "pos.workspace_sync"


def get_tracer():
    return trace.get_tracer(_TRACER_NAME)


@contextmanager
def span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[Span]:
    tracer = get_tracer()
    with tracer.start_as_current_span(
        name, kind=SpanKind.INTERNAL, attributes=attributes or {}
    ) as s:
        try:
            yield s
        except Exception as exc:
            s.set_status(Status(StatusCode.ERROR, str(exc)))
            s.record_exception(exc)
            raise


def emit_event(span_obj: Span, name: str, attrs: dict[str, Any] | None = None) -> None:
    span_obj.add_event(name, attributes=attrs or {})
