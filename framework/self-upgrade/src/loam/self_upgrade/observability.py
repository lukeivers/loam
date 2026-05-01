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

"""OTel span emission for the self-upgrade framework (v1.1 R11).

The framework emits spans at every stage so the observability
aggregator can ingest them:

- ``loam.upgrade.started``
- ``loam.upgrade.pre_snapshot_complete``
- ``loam.upgrade.pre_probe_complete``
- ``loam.upgrade.pause_activation``
- ``loam.upgrade.drain_complete``
- ``loam.upgrade.sigterm_complete``
- ``loam.upgrade.swap_complete``
- ``loam.upgrade.orchestrator_boot``
- ``loam.upgrade.post_probe_complete``
- ``loam.upgrade.clauses_verified``
- ``loam.upgrade.accepted``
- ``loam.upgrade.rolled_back``
- ``loam.upgrade.rollback_failed``

Dependency injection: the tracer is acquired lazily via
``opentelemetry.trace.get_tracer`` so tests can install a custom
provider without hot-patching this module.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

_TRACER_NAME = "loam.self_upgrade"


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
