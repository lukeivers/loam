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

"""pOS v2 — Observability Aggregator.

Single-user local-first trace store. Subscribes to every sealed
component's emission surface without amending any of them:

  - Six OTel-emitting components (scope-of-work, primary-persona,
    objective-tracker, orchestrator, dormancy, plus test
    infra) flow through a custom SpanProcessor + SpanExporter
    registered via the orchestrator's `~/.loam/bootstrap.py` workspace
    hook. Python OTel's late-binding ProxyTracer routes them
    automatically.

  - Memory-system's three hand-rolled JSONL sinks
    (spans.jsonl, tokens.jsonl, audit.jsonl) flow through a tailer
    that translates them into the canonical schema.

Storage: DuckDB primary at `~/.loam/observability.duckdb`; SQLite
fallback mode selectable via config.

Query surface: structured Pydantic API (canonical), NL path via
Claude-via-Max ("show me why"), `pos obs` CLI.

Retention: decaying granularity (0-7d full / 7-30d daily + top-N raw
/ 30-365d monthly / 365d+ yearly). v1.1 R10 retention classes
honoured at ingest: `normal` stored fully; `derived-only` drops
payload at ingest; `ephemeral` stub-only.

Self-observability: aggregator emits `loam.aggregator.*` spans;
filtered at ingest to prevent recursion.

A1 correction held: no sealed component knows about this aggregator.
"""

from .config import AggregatorConfig
from .schema import (
    SpanRecord,
    EventRecord,
    AuditRecord,
    TokenRecord,
    RetentionClass,
)
from .store import Store, open_store
from .api import QueryAPI, SpanFilter, EventFilter
from .ingest import IngestionPipeline, register_otel_provider, install_for_workspace
from .replay import (
    SessionReplay,
    ScopeReplay,
    ObjectiveReplay,
)

__all__ = [
    "AggregatorConfig",
    "SpanRecord",
    "EventRecord",
    "AuditRecord",
    "TokenRecord",
    "RetentionClass",
    "Store",
    "open_store",
    "QueryAPI",
    "SpanFilter",
    "EventFilter",
    "IngestionPipeline",
    "register_otel_provider",
    "install_for_workspace",
    "SessionReplay",
    "ScopeReplay",
    "ObjectiveReplay",
]
