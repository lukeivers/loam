"""OTel emit helpers for the Dev/SDLC plugin (per plan §4
AC.OSS-M6.5).

Span namespace: `loam.dev_sdlc.<event>`. Attributes carry plain
strings; structured payloads serialise via the standard tracer
attribute conversion.

The plugin registers no provider; it consumes the workspace's
ambient tracer per `opentelemetry.trace.get_tracer`.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace


_TRACER_NAME = "loam.plugins.dev_sdlc"


def get_tracer() -> trace.Tracer:
    """Return the plugin's tracer (lazy bind so the workspace's
    provider is consulted at first use)."""
    return trace.get_tracer(_TRACER_NAME)


@contextmanager
def stage_advance_span(
    *,
    slug: str,
    from_stage: str | None,
    to_stage: str,
    methodology: str,
) -> Iterator[Any]:
    """Emit `loam.dev_sdlc.stage_advance` span around a stage advance
    operation. Attributes per plan §4 AC.OSS-M6.5."""
    tracer = get_tracer()
    with tracer.start_as_current_span("loam.dev_sdlc.stage_advance") as span:
        span.set_attribute("loam.dev_sdlc.slug", slug)
        span.set_attribute("loam.dev_sdlc.from_stage", from_stage or "")
        span.set_attribute("loam.dev_sdlc.to_stage", to_stage)
        span.set_attribute("loam.dev_sdlc.methodology", methodology)
        yield span
