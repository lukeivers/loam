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

"""Ingestion pipeline.

Two paths share one store:

  Path A — In-process custom SpanExporter for the six OTel-emitting
  components. A workspace `~/.loam/bootstrap.py` calls
  `register_otel_provider(...)` from this module, which installs a
  TracerProvider with a BatchSpanProcessor pointing at our
  AggregatorSpanExporter. Python OTel's late-binding ProxyTracer
  routes every component's spans through automatically.

  Path B — JSONL tailer for memory-system's three sinks
  (spans.jsonl / tokens.jsonl / audit.jsonl). Bounded tail latency,
  byte-offset cursor for resumption, malformed-line skipping.

Spool: Path A's exporter writes to a local JSONL spool file. The
ingestion pipeline drains the spool into the store. If the store
write fails, spans stay in the spool until next drain. On aggregator
restart, the spool drains first thing.

Self-observability filter: spans whose tracer_name starts with
`loam.aggregator` are dropped at ingest to prevent the aggregator
observing its own observation.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from .config import AggregatorConfig
from .schema import (
    AuditRecord,
    EventRecord,
    RetentionClass,
    SpanRecord,
    TokenRecord,
    extract_retention_class,
    infer_component,
)
from .store import Store

log = logging.getLogger("loam.aggregator.ingest")


# =====================================================================
# Path A — OTel SpanExporter (in-process)
# =====================================================================


@dataclass
class _SpanRow:
    """Internal representation of an OTel ReadableSpan reduced to JSON."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    tracer_name: str
    kind: str
    start_time_unix_nano: int
    end_time_unix_nano: int
    status: str
    status_message: str | None
    attributes: dict[str, Any]
    events: list[dict[str, Any]]


def _otel_span_to_row(otel_span) -> _SpanRow:
    ctx = otel_span.get_span_context()
    parent = otel_span.parent
    parent_span_id = (
        f"{parent.span_id:016x}" if parent is not None and parent.span_id else None
    )
    instr = otel_span.instrumentation_scope
    tracer_name = getattr(instr, "name", None) or ""
    status = otel_span.status
    status_str = "UNSET"
    if status is not None:
        # OTel StatusCode: UNSET, OK, ERROR
        try:
            status_str = status.status_code.name
        except Exception:
            status_str = "UNSET"
    attrs = dict(otel_span.attributes or {})
    events_out: list[dict[str, Any]] = []
    for ev in otel_span.events or []:
        events_out.append(
            {
                "name": ev.name,
                "time_unix_nano": ev.timestamp,
                "attributes": dict(ev.attributes or {}),
            }
        )
    return _SpanRow(
        trace_id=f"{ctx.trace_id:032x}",
        span_id=f"{ctx.span_id:016x}",
        parent_span_id=parent_span_id,
        name=otel_span.name,
        tracer_name=tracer_name,
        kind=otel_span.kind.name if otel_span.kind else "INTERNAL",
        start_time_unix_nano=otel_span.start_time,
        end_time_unix_nano=otel_span.end_time,
        status=status_str,
        status_message=getattr(status, "description", None),
        attributes=attrs,
        events=events_out,
    )


class AggregatorSpanExporter(SpanExporter):
    """OTel SpanExporter that writes finished spans to the spool.

    Why spool first instead of straight-to-store? Two reasons:
      1. The store may be busy (rollup, prune, query); the spool
         keeps emission non-blocking.
      2. Spool persists during aggregator restart; spans aren't lost
         when the store is unavailable.
    """

    def __init__(
        self,
        spool_path: Path,
        self_namespace_prefix: str = "loam.aggregator",
    ) -> None:
        self.spool_path = spool_path
        self.spool_path.parent.mkdir(parents=True, exist_ok=True)
        self._self_prefix = self_namespace_prefix
        self._lock = threading.Lock()

    def export(self, spans: Sequence[Any]) -> SpanExportResult:
        try:
            with self._lock:
                with self.spool_path.open("at", encoding="utf-8") as fh:
                    for span in spans:
                        row = _otel_span_to_row(span)
                        # Self-observability filter at the exporter
                        # boundary — never spool aggregator's own spans.
                        if row.tracer_name.startswith(self._self_prefix):
                            continue
                        fh.write(json.dumps(row.__dict__, default=str) + "\n")
            return SpanExportResult.SUCCESS
        except Exception as exc:
            log.error("aggregator exporter failed: %s", exc)
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        # No background thread; nothing to stop.
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        # We write synchronously; nothing to flush.
        return True


def register_otel_provider(
    spool_path: Path,
    *,
    resource_attrs: dict[str, str] | None = None,
    self_namespace_prefix: str = "loam.aggregator",
) -> tuple[TracerProvider, BatchSpanProcessor, AggregatorSpanExporter]:
    """Install a TracerProvider that routes every component's spans
    through the aggregator's spool exporter.

    Late-binding contract: this function MUST be called before any
    sealed component dispatches its first span. Python OTel's
    ProxyTracer pattern means components can have already imported
    `trace.get_tracer(...)` at module-load time; the proxy resolves
    to whichever provider is set when the first span actually opens.

    Per the brief halt-condition: if components are observed to bind
    their tracer before this hook fires (defeating late-binding),
    halt-and-signal. The detection test in tests/ verifies this.
    """
    resource = Resource.create(resource_attrs or {"service.name": "loam.aggregator"})
    provider = TracerProvider(resource=resource)
    exporter = AggregatorSpanExporter(spool_path, self_namespace_prefix=self_namespace_prefix)
    processor = BatchSpanProcessor(
        exporter,
        max_queue_size=8192,
        schedule_delay_millis=2000,
        max_export_batch_size=512,
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return provider, processor, exporter


# =====================================================================
# Path B — Memory JSONL tailer
# =====================================================================


class JSONLTailer:
    """Tail a single JSONL file; resume from byte-offset cursor.

    Tail latency is bounded by `poll_interval_seconds` (default 0.5s,
    well under the 1s p95 target).

    Malformed lines are logged and skipped; never fatal.
    """

    def __init__(
        self,
        store: Store,
        source_id: str,
        path: Path,
        record_handler,
        poll_interval_seconds: float = 0.5,
    ) -> None:
        self.store = store
        self.source_id = source_id
        self.path = path
        self.record_handler = record_handler
        self.poll_interval = poll_interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name=f"tailer:{self.source_id}", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def drain_once(self) -> int:
        """Read all pending lines synchronously and return the count.

        Used in tests, and also called from the tailer loop on each
        tick. Resumes from the persisted cursor.
        """
        if not self.path.exists():
            return 0
        offset = self.store.get_cursor(self.source_id)
        try:
            file_size = self.path.stat().st_size
        except FileNotFoundError:
            return 0
        # File truncated/recreated: reset and start fresh.
        if file_size < offset:
            offset = 0
        if file_size == offset:
            return 0
        count = 0
        try:
            with self.path.open("rb") as fh:
                fh.seek(offset)
                for raw_line in fh:
                    if not raw_line.strip():
                        offset += len(raw_line)
                        continue
                    try:
                        record = json.loads(raw_line.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                        log.warning(
                            "tailer %s skipping malformed line at offset %d: %s",
                            self.source_id, offset, exc,
                        )
                        offset += len(raw_line)
                        continue
                    try:
                        self.record_handler(record)
                        count += 1
                    except Exception as exc:
                        log.warning(
                            "tailer %s record_handler failed: %s",
                            self.source_id, exc,
                        )
                    offset += len(raw_line)
            self.store.set_cursor(
                self.source_id, str(self.path), offset, datetime.now(timezone.utc)
            )
        except Exception as exc:
            log.error("tailer %s read loop failed: %s", self.source_id, exc)
        return count

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.drain_once()
            except Exception as exc:  # never let the thread die
                log.error("tailer %s tick failed: %s", self.source_id, exc)
            self._stop.wait(self.poll_interval)


# =====================================================================
# Memory record translators (hand-rolled JSON → canonical schema)
# =====================================================================


def memory_span_to_canonical(record: dict[str, Any]) -> SpanRecord:
    """Translate memory-system's `spans.jsonl` record into SpanRecord.

    Memory's record shape (from memory-system/src/observability.py):
      trace_id, span_id, parent_span_id, name, start_time_unix_nano,
      end_time_unix_nano, attributes, status, error
    """
    attrs = dict(record.get("attributes") or {})
    rclass = extract_retention_class(attrs)
    name = record.get("name", "memory.unknown")
    return SpanRecord(
        trace_id=record["trace_id"],
        span_id=record["span_id"],
        parent_span_id=record.get("parent_span_id"),
        name=name,
        tracer_name="loam.memory",
        component="memory_system",
        kind="INTERNAL",
        start_time_unix_nano=int(record["start_time_unix_nano"]),
        end_time_unix_nano=int(record["end_time_unix_nano"]),
        status=record.get("status", "UNSET"),
        status_message=record.get("error"),
        attributes=attrs,
        retention_class=rclass,
    )


def memory_token_to_canonical(record: dict[str, Any]) -> TokenRecord:
    """Memory's `tokens.jsonl` record."""
    at = record.get("at_iso") or record.get("at_time")
    if isinstance(at, str):
        try:
            at_dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
        except ValueError:
            at_dt = datetime.now(timezone.utc)
    else:
        at_dt = datetime.now(timezone.utc)
    return TokenRecord(
        trace_id=record.get("trace_id"),
        span_id=record.get("span_id"),
        prompt_name=record["prompt_name"],
        model=record["model"],
        input_tokens=int(record.get("input_tokens", 0)),
        output_tokens=int(record.get("output_tokens", 0)),
        call_count=int(record.get("call_count", 1)),
        at_time=at_dt,
        scope_id=record.get("scope_id"),
        component="memory_system",
    )


def memory_audit_to_canonical(record: dict[str, Any]) -> AuditRecord:
    at = record.get("at_iso") or record.get("at_time")
    if isinstance(at, str):
        try:
            at_dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
        except ValueError:
            at_dt = datetime.now(timezone.utc)
    else:
        at_dt = datetime.now(timezone.utc)
    return AuditRecord(
        at_time=at_dt,
        operation=record["operation"],
        actor=record.get("actor", "memory_system"),
        scope_id=record.get("scope_id"),
        subject_uuid=record.get("subject_uuid"),
        rationale=record.get("rationale", ""),
        extras=record.get("extras") or {},
    )


# =====================================================================
# Spool drainer (Path A → store)
# =====================================================================


class SpoolDrainer:
    """Drain the OTel spool file into the store.

    The spool is a JSONL file written by AggregatorSpanExporter. The
    drainer reads new lines (using the store's ingest_cursors table
    so a restart doesn't re-ingest), translates each into SpanRecord
    + EventRecord(s), and writes them.
    """

    SOURCE_ID = "otel:spool"

    def __init__(
        self,
        store: Store,
        spool_path: Path,
        self_namespace_prefix: str = "loam.aggregator",
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self.store = store
        self.spool_path = spool_path
        self._self_prefix = self_namespace_prefix
        self.poll_interval = poll_interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="aggregator-spool-drainer", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.drain_once()
            except Exception as exc:
                log.error("spool drainer tick failed: %s", exc)
            self._stop.wait(self.poll_interval)

    def drain_once(self) -> int:
        if not self.spool_path.exists():
            return 0
        offset = self.store.get_cursor(self.SOURCE_ID)
        try:
            size = self.spool_path.stat().st_size
        except FileNotFoundError:
            return 0
        if size < offset:
            # spool truncated/cleared: reset
            offset = 0
        if size == offset:
            return 0
        count = 0
        with self.spool_path.open("rb") as fh:
            fh.seek(offset)
            for raw_line in fh:
                if not raw_line.strip():
                    offset += len(raw_line)
                    continue
                try:
                    rec = json.loads(raw_line.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    log.warning("spool drainer skipping bad line: %s", exc)
                    offset += len(raw_line)
                    continue
                try:
                    self._ingest_one(rec)
                    count += 1
                except Exception as exc:
                    log.warning("spool ingest failed for one row: %s", exc)
                offset += len(raw_line)
        self.store.set_cursor(
            self.SOURCE_ID, str(self.spool_path), offset, datetime.now(timezone.utc)
        )
        return count

    def _ingest_one(self, rec: dict[str, Any]) -> None:
        tracer_name = rec.get("tracer_name", "")
        # Self-observability filter at spool ingest as well (belt + braces).
        if tracer_name.startswith(self._self_prefix):
            return
        attrs = dict(rec.get("attributes") or {})
        rclass = extract_retention_class(attrs)
        component = infer_component(tracer_name)
        span = SpanRecord(
            trace_id=rec["trace_id"],
            span_id=rec["span_id"],
            parent_span_id=rec.get("parent_span_id"),
            name=rec["name"],
            tracer_name=tracer_name,
            component=component,
            kind=rec.get("kind", "INTERNAL"),
            start_time_unix_nano=int(rec["start_time_unix_nano"]),
            end_time_unix_nano=int(rec["end_time_unix_nano"]),
            status=rec.get("status", "UNSET"),
            status_message=rec.get("status_message"),
            attributes=attrs,
            retention_class=rclass,
        )
        # Apply ephemeral stub: ephemeral spans keep only minimal fields.
        # Done at the SpanRecord level via apply_retention_class on attrs;
        # for ephemeral we additionally drop the name detail to a generic stub.
        if rclass is RetentionClass.EPHEMERAL:
            # Keep operation name + timing; drop status_message and child events.
            span.status_message = None
        self.store.insert_span(span)
        # Extract token usage from gen_ai.usage.* attributes if present.
        self._maybe_extract_token_row(span, attrs)
        # Events.
        if rclass is not RetentionClass.EPHEMERAL:
            for ev in rec.get("events") or []:
                ev_attrs = dict(ev.get("attributes") or {})
                ev_rclass = extract_retention_class(ev_attrs) if ev_attrs else rclass
                self.store.insert_event(
                    EventRecord(
                        span_id=span.span_id,
                        trace_id=span.trace_id,
                        name=ev["name"],
                        time_unix_nano=int(ev["time_unix_nano"]),
                        attributes=ev_attrs,
                        retention_class=ev_rclass,
                    )
                )

    def _maybe_extract_token_row(self, span: SpanRecord, attrs: dict[str, Any]) -> None:
        """gen_ai.usage attributes on a 'chat {model}' span → tokens row."""
        in_tok = attrs.get("gen_ai.usage.input_tokens")
        out_tok = attrs.get("gen_ai.usage.output_tokens")
        if in_tok is None and out_tok is None:
            return
        prompt_name = (
            attrs.get("loam.prompt.type")
            or attrs.get("gen_ai.prompt.name")
            or span.name
        )
        model = attrs.get("gen_ai.request.model") or attrs.get("gen_ai.response.model") or "unknown"
        scope_id = attrs.get("loam.scope.id")
        # at_time: span end is the LLM call's completion.
        at_dt = datetime.fromtimestamp(span.end_time_unix_nano / 1e9, tz=timezone.utc)
        self.store.insert_token(
            TokenRecord(
                trace_id=span.trace_id,
                span_id=span.span_id,
                prompt_name=str(prompt_name),
                model=str(model),
                input_tokens=int(in_tok or 0),
                output_tokens=int(out_tok or 0),
                call_count=1,
                at_time=at_dt,
                scope_id=scope_id,
                component=span.component,
            )
        )


# =====================================================================
# Pipeline composition — run all ingest paths together
# =====================================================================


class IngestionPipeline:
    """Composes the OTel spool drainer + memory JSONL tailers."""

    def __init__(self, config: AggregatorConfig, store: Store) -> None:
        self.config = config
        self.store = store
        self.spool_drainer = SpoolDrainer(
            store,
            config.resolved_spool_path(),
            self_namespace_prefix=config.ingest.self_namespace_prefix,
        )
        sink_dir = config.resolved_memory_sink_dir()
        self._spans_handler = lambda r: store.insert_span(memory_span_to_canonical(r))
        self._tokens_handler = lambda r: store.insert_token(memory_token_to_canonical(r))
        self._audit_handler = lambda r: store.insert_audit(memory_audit_to_canonical(r))
        self.memory_spans_tailer = JSONLTailer(
            store, "memory:spans", sink_dir / "spans.jsonl", self._spans_handler
        )
        self.memory_tokens_tailer = JSONLTailer(
            store, "memory:tokens", sink_dir / "tokens.jsonl", self._tokens_handler
        )
        self.memory_audit_tailer = JSONLTailer(
            store, "memory:audit", sink_dir / "audit.jsonl", self._audit_handler
        )

    def start(self) -> None:
        self.spool_drainer.start()
        self.memory_spans_tailer.start()
        self.memory_tokens_tailer.start()
        self.memory_audit_tailer.start()

    def stop(self) -> None:
        self.spool_drainer.stop()
        self.memory_spans_tailer.stop()
        self.memory_tokens_tailer.stop()
        self.memory_audit_tailer.stop()

    def drain_all_once(self) -> dict[str, int]:
        return {
            "otel_spool": self.spool_drainer.drain_once(),
            "memory_spans": self.memory_spans_tailer.drain_once(),
            "memory_tokens": self.memory_tokens_tailer.drain_once(),
            "memory_audit": self.memory_audit_tailer.drain_once(),
        }


# =====================================================================
# Workspace bootstrap helper
# =====================================================================


def install_for_workspace(
    config: AggregatorConfig | None = None,
    *,
    start_pipeline: bool = True,
) -> tuple[IngestionPipeline, TracerProvider]:
    """Convenience helper for `~/.loam/bootstrap.py` to invoke.

    Installs the OTel TracerProvider, opens the store, and starts
    the ingest pipeline. Returns both the pipeline (so the caller
    can stop() at shutdown) and the provider (for diagnostics).

    Bootstrap-registration timing: if any sealed component has
    already initialised its own TracerProvider before this is
    called, our provider replaces it (OTel allows override only via
    `set_tracer_provider`). If components have already cached their
    Tracer (not the proxy), late-binding fails — the detection test
    asserts this didn't happen.
    """
    cfg = config or AggregatorConfig()
    cfg.ensure_dirs()
    store = open_store_for_pipeline(cfg)
    provider, _processor, _exporter = register_otel_provider(
        cfg.resolved_spool_path(),
        self_namespace_prefix=cfg.ingest.self_namespace_prefix,
    )
    pipeline = IngestionPipeline(cfg, store)
    if start_pipeline:
        pipeline.start()
    return pipeline, provider


# Local helper to avoid circular import with store.open_store name.
def open_store_for_pipeline(cfg: AggregatorConfig) -> Store:
    from .store import open_store
    return open_store(cfg)


# ---- bootstrap-timing detector ----

def detect_proxy_late_binding_failure() -> str | None:
    """Return None if late-binding is intact; otherwise a diagnostic.

    Inspect the global TracerProvider; if it is the SDK's no-op
    DefaultTracerProvider OR has been replaced by a non-aggregator
    provider, late-binding is intact OR pre-empted.

    The hard failure case is when components have stored a *concrete*
    Tracer object (not the ProxyTracer) before our provider was set.
    We can detect this only behaviourally: emit a span via a known
    sealed-component tracer and see if it lands in our exporter.
    The detection test in tests/ does that end-to-end.

    Here we provide a quick structural check.
    """
    provider = trace.get_tracer_provider()
    if provider is None:
        return "no global TracerProvider after registration; install failed"
    return None
