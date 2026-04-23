"""D7 — Observability emission adapter.

Memory emits structured OTel-shaped span records, token-usage rows,
and operation-audit entries. No downstream consumer is assumed (A1
correction in the brief): memory publishes; when the observability
aggregator is later designed, it subscribes.

Records are written as JSON Lines, one record per line. Three sinks:

  spans.jsonl  — one OTel span per memory operation (ingest, search,
                 classify_ephemeral, summarise_stream, etc.).
  tokens.jsonl — one row per LLM call with per-prompt-type breakdown.
                 Aggregation of these rows is what v1.1 R12
                 ("per-prompt-type cost attribution") asks for.
  audit.jsonl  — free-text audit events (supersession rationale,
                 retention-class decisions, cascade halts). These are
                 what a user or reviewer reads to answer "why did
                 memory do X."

Span format: a minimal OTel-compatible shape. We DO NOT pull in the
full OpenTelemetry SDK here — that would force a runtime dependency
on a consumer that does not yet exist. Instead we emit the spans in
the OTel v1.0 JSON encoding (trace_id, span_id, name, start/end time,
attributes) so a future OTel collector can ingest them as-is.

Why not an OTel exporter? The spec is explicit: memory emits durable
records without requiring a consumer. A collector is an online
consumer; the file-based sink is the durable contract. A collector
can later tail the file.
"""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import section


# ---- record shapes ---------------------------------------------------

def _trace_id() -> str:
    """16 bytes hex — OTel trace_id wire format."""
    return secrets.token_hex(16)


def _span_id() -> str:
    """8 bytes hex — OTel span_id wire format."""
    return secrets.token_hex(8)


def _now_ns() -> int:
    return time.time_ns()


@dataclass
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time_unix_nano: int
    end_time_unix_nano: int
    attributes: dict[str, Any]
    status: str = "OK"
    error: str | None = None


@dataclass
class TokenRow:
    trace_id: str
    span_id: str
    prompt_name: str
    model: str
    input_tokens: int
    output_tokens: int
    call_count: int
    at_iso: str
    scope_id: str | None = None


@dataclass
class AuditEntry:
    at_iso: str
    operation: str
    actor: str
    scope_id: str | None
    subject_uuid: str | None
    rationale: str
    extras: dict[str, Any] = field(default_factory=dict)


# ---- emitter ---------------------------------------------------------

class Emitter:
    """Append-only JSONL writer for the three sinks.

    The Emitter is a module-level singleton by convention (`default()`),
    but tests can construct their own to point at a temp dir. Every
    write is serialised under a lock so concurrent ingests don't
    interleave partial records.
    """

    def __init__(self, sink_dir: str | Path | None = None) -> None:
        cfg = section("observability")
        sink_cfg = cfg.get("sink") or {}
        self._dir = Path(sink_dir or sink_cfg.get("dir", "./data/observability"))
        self._spans_file = self._dir / sink_cfg.get("spans_file", "spans.jsonl")
        self._tokens_file = self._dir / sink_cfg.get("tokens_file", "tokens.jsonl")
        self._audit_file = self._dir / sink_cfg.get("audit_file", "audit.jsonl")
        self._emit_payloads = bool(cfg.get("emit_payloads", True))
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @property
    def emit_payloads(self) -> bool:
        return self._emit_payloads

    @property
    def sink_dir(self) -> Path:
        return self._dir

    # --- low-level writes ---

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        line = json.dumps(record, default=str) + "\n"
        with self._lock:
            with path.open("at", encoding="utf-8") as fh:
                fh.write(line)

    # --- span API ---

    def emit_span(self, span: SpanRecord) -> None:
        self._append(self._spans_file, asdict(span))

    def emit_token_row(self, row: TokenRow) -> None:
        self._append(self._tokens_file, asdict(row))

    def emit_audit(self, entry: AuditEntry) -> None:
        self._append(self._audit_file, asdict(entry))

    # --- convenience: context-managed span builder ---

    @contextmanager
    def span(
        self,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
        parent_span_id: str | None = None,
        trace_id: str | None = None,
    ) -> Iterator["SpanBuilder"]:
        """Measure a block, write a span on exit (success or failure).

        The context manager always writes a span — on an exception it
        sets status=ERROR and records the exception class name/message.
        """
        builder = SpanBuilder(
            emitter=self,
            name=name,
            trace_id=trace_id or _trace_id(),
            span_id=_span_id(),
            parent_span_id=parent_span_id,
            attributes=dict(attributes or {}),
        )
        try:
            yield builder
            builder.finalise(status="OK")
        except Exception as exc:  # noqa: BLE001 — we re-raise
            builder.finalise(status="ERROR", error=f"{type(exc).__name__}: {exc}")
            raise

    # --- query surface for local sanity / tests ---

    def read_spans(self) -> list[dict[str, Any]]:
        return _read_jsonl(self._spans_file)

    def read_tokens(self) -> list[dict[str, Any]]:
        return _read_jsonl(self._tokens_file)

    def read_audit(self) -> list[dict[str, Any]]:
        return _read_jsonl(self._audit_file)

    def per_prompt_cost(
        self,
        *,
        input_usd_per_mtok: float,
        output_usd_per_mtok: float,
    ) -> dict[str, dict[str, Any]]:
        """Aggregate token rows by prompt_name; return per-prompt cost.

        This is the materialised query for v1.1 R12 — per-prompt-type
        cost attribution. It is always computable from the tokens
        sink without requiring an online consumer.
        """
        per_prompt: dict[str, dict[str, Any]] = {}
        for row in self.read_tokens():
            p = row.get("prompt_name", "<unknown>")
            bucket = per_prompt.setdefault(
                p,
                {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "call_count": 0,
                    "estimated_usd": 0.0,
                },
            )
            bucket["input_tokens"] += int(row.get("input_tokens", 0))
            bucket["output_tokens"] += int(row.get("output_tokens", 0))
            bucket["call_count"] += int(row.get("call_count", 1))
        for p, bucket in per_prompt.items():
            bucket["estimated_usd"] = round(
                (bucket["input_tokens"] / 1_000_000) * input_usd_per_mtok
                + (bucket["output_tokens"] / 1_000_000) * output_usd_per_mtok,
                6,
            )
        return per_prompt


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("rt", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                # Amendment #21 S3 silent-except bundle: surface the
                # previously silent malformed-line drop via the module's
                # own durable audit channel (the D7 contract is JSONL-
                # only — no OTel SDK dep — so `record_audit` is the
                # right surface here). The `continue` remains; a
                # malformed line cannot be recovered at read time.
                record_audit(
                    operation="observability.jsonl_line_malformed",
                    actor="memory-system",
                    rationale=(
                        f"JSONDecodeError parsing line {line_no} of "
                        f"{path.name}"
                    ),
                    extras={
                        "path": str(path),
                        "line_no": line_no,
                        "exception_class": type(exc).__name__,
                        "message": str(exc),
                    },
                )
                continue
    return rows


@dataclass
class SpanBuilder:
    emitter: Emitter
    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    attributes: dict[str, Any]
    _start_ns: int = field(default_factory=_now_ns)

    def set_attr(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def set_payload(self, *, inputs: Any | None = None, outputs: Any | None = None) -> None:
        """Record operation inputs/outputs if emit_payloads is enabled.

        Payloads can be large; disabling them at the config level is
        the privacy-preserving path for a workspace that doesn't want
        raw text in observability records.
        """
        if self.emitter.emit_payloads:
            if inputs is not None:
                self.attributes["inputs"] = _safe_jsonable(inputs)
            if outputs is not None:
                self.attributes["outputs"] = _safe_jsonable(outputs)

    def finalise(self, *, status: str = "OK", error: str | None = None) -> None:
        span = SpanRecord(
            trace_id=self.trace_id,
            span_id=self.span_id,
            parent_span_id=self.parent_span_id,
            name=self.name,
            start_time_unix_nano=self._start_ns,
            end_time_unix_nano=_now_ns(),
            attributes=self.attributes,
            status=status,
            error=error,
        )
        self.emitter.emit_span(span)


def _safe_jsonable(value: Any) -> Any:
    """Reduce arbitrary objects to something json.dumps can handle.

    Truncates long strings at 4 KB so spans don't blow up the sink.
    """
    try:
        s = json.dumps(value, default=str)
    except TypeError:
        s = str(value)
    if len(s) > 4096:
        return s[:4096] + f"... <truncated, total {len(s)} chars>"
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return s


# ---- module-level singleton ------------------------------------------

_DEFAULT: Emitter | None = None
_DEFAULT_LOCK = threading.Lock()


def default_emitter() -> Emitter:
    global _DEFAULT
    if _DEFAULT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT is None:
                _DEFAULT = Emitter()
    return _DEFAULT


def reset_default_emitter(new: Emitter | None = None) -> Emitter:
    """Replace (or reset) the module singleton; tests use this."""
    global _DEFAULT
    with _DEFAULT_LOCK:
        _DEFAULT = new or Emitter()
    return _DEFAULT


# ---- convenience helpers used by other modules -----------------------

def record_llm_usage(
    *,
    prompt_name: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    call_count: int = 1,
    scope_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
    emitter: Emitter | None = None,
) -> None:
    """Write one token-usage row.

    `call_count` allows a single row to represent a batch of calls
    aggregated at the Graphiti `TokenUsageTracker` level.
    """
    em = emitter or default_emitter()
    em.emit_token_row(
        TokenRow(
            trace_id=trace_id or _trace_id(),
            span_id=span_id or _span_id(),
            prompt_name=prompt_name,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            call_count=call_count,
            at_iso=datetime.now(timezone.utc).isoformat(),
            scope_id=scope_id,
        )
    )


def record_audit(
    *,
    operation: str,
    actor: str,
    scope_id: str | None = None,
    subject_uuid: str | None = None,
    rationale: str,
    extras: dict[str, Any] | None = None,
    emitter: Emitter | None = None,
) -> None:
    em = emitter or default_emitter()
    em.emit_audit(
        AuditEntry(
            at_iso=datetime.now(timezone.utc).isoformat(),
            operation=operation,
            actor=actor,
            scope_id=scope_id,
            subject_uuid=subject_uuid,
            rationale=rationale,
            extras=extras or {},
        )
    )
