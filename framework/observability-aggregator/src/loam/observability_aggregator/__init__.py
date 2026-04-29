"""pOS v2 — Observability Aggregator.

Single-user local-first trace store. Subscribes to every sealed
component's emission surface without amending any of them:

  - Six OTel-emitting components (scope-of-work, primary-persona,
    objective-tracker, orchestrator, graceful-degradation, plus test
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
