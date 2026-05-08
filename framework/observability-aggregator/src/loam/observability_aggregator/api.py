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

"""Structured Pydantic query API (Surface 1 — canonical).

Every other surface (NL path, CLI) composes over this. Pydantic
validates input and output; the store handles SQL.

Methods (per brief D4):
  - find_spans(filter)          → list[SpanRecord]
  - get_trace(trace_id)         → list[SpanRecord] (full trace tree)
  - get_span(span_id)           → SpanRecord | None
  - find_events(filter)         → list[EventRecord]
  - cost_by_prompt(window)      → dict[prompt_name, PromptCost]
  - replay_session(session_id)  → SessionReplay
  - replay_scope(scope_id)      → ScopeReplay
  - replay_objective(objective_id) → ObjectiveReplay
  - audit_search(...)           → list[AuditRecord]
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Sequence

from pydantic import BaseModel

from .schema import (
    AuditRecord,
    EventRecord,
    RetentionClass,
    SpanRecord,
)
from .store import Store


# ---- query input schemas ----------------------------------------------

class TimeRange(BaseModel):
    start: datetime | None = None
    end: datetime | None = None


class SpanFilter(BaseModel):
    trace_ids: list[str] | None = None
    components: list[str] | None = None
    name_pattern: str | None = None  # regex applied to span.name
    name_exact: str | None = None
    time_range: TimeRange | None = None
    attributes_match: dict[str, Any] | None = None  # exact attr equality
    has_event: str | None = None  # filter spans with an event of this name
    status: str | None = None  # OK | ERROR
    scope_id: str | None = None  # convenience: matches loam.scope.id attr
    retention_class: RetentionClass | None = None


class EventFilter(BaseModel):
    trace_ids: list[str] | None = None
    span_ids: list[str] | None = None
    name_pattern: str | None = None
    name_exact: str | None = None
    time_range: TimeRange | None = None


# ---- query output schemas ---------------------------------------------

class PromptCost(BaseModel):
    prompt_name: str
    input_tokens: int
    output_tokens: int
    call_count: int
    estimated_usd: float = 0.0


# ---- the query API ----------------------------------------------------

class QueryAPI:
    """Structured query surface over the store."""

    def __init__(self, store: Store) -> None:
        self.store = store

    # ---- spans ----

    def find_spans(self, f: SpanFilter, limit: int = 100) -> list[SpanRecord]:
        # Use an inflated SQL limit when we have post-filters so
        # in-process attribute matching does not silently truncate
        # legitimate hits past the SQL limit.
        sql_limit = limit if not f.attributes_match and not f.has_event and not f.name_pattern else max(limit * 5, 500)
        sql, params = self._spans_sql(f, sql_limit)
        rows = self.store.fetch(sql, params)
        spans = [self._row_to_span(r) for r in rows]
        # In-process post-filters: attributes_match, has_event, name_pattern, scope_id.
        if f.scope_id:
            spans = [s for s in spans if s.attributes.get("loam.scope.id") == f.scope_id]
        if f.attributes_match:
            spans = [
                s for s in spans
                if all(s.attributes.get(k) == v for k, v in f.attributes_match.items())
            ]
        if f.name_pattern:
            pattern = re.compile(f.name_pattern)
            spans = [s for s in spans if pattern.search(s.name)]
        if f.has_event:
            # Per-span event presence check via a single grouped query.
            ids = [s.span_id for s in spans]
            if ids:
                placeholders = ", ".join("?" for _ in ids)
                rows = self.store.fetch(
                    f"SELECT DISTINCT span_id FROM span_events WHERE name = ? AND span_id IN ({placeholders})",
                    [f.has_event, *ids],
                )
                with_event = {r[0] for r in rows}
                spans = [s for s in spans if s.span_id in with_event]
        return spans[:limit]

    def get_span(self, span_id: str) -> SpanRecord | None:
        rows = self.store.fetch(
            "SELECT * FROM spans WHERE span_id = ?",
            (span_id,),
        )
        if not rows:
            return None
        return self._row_to_span(rows[0])

    def get_trace(self, trace_id: str) -> list[SpanRecord]:
        rows = self.store.fetch(
            "SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time_unix_nano",
            (trace_id,),
        )
        return [self._row_to_span(r) for r in rows]

    def find_events(self, f: EventFilter, limit: int = 100) -> list[EventRecord]:
        clauses, params = [], []
        if f.trace_ids:
            placeholders = ", ".join("?" for _ in f.trace_ids)
            clauses.append(f"trace_id IN ({placeholders})")
            params.extend(f.trace_ids)
        if f.span_ids:
            placeholders = ", ".join("?" for _ in f.span_ids)
            clauses.append(f"span_id IN ({placeholders})")
            params.extend(f.span_ids)
        if f.name_exact:
            clauses.append("name = ?")
            params.append(f.name_exact)
        if f.time_range:
            if f.time_range.start:
                clauses.append("time_unix_nano >= ?")
                params.append(int(f.time_range.start.timestamp() * 1e9))
            if f.time_range.end:
                clauses.append("time_unix_nano <= ?")
                params.append(int(f.time_range.end.timestamp() * 1e9))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"SELECT * FROM span_events{where} ORDER BY time_unix_nano LIMIT ?"
        params.append(limit)
        rows = self.store.fetch(sql, params)
        out = [self._row_to_event(r) for r in rows]
        if f.name_pattern:
            pattern = re.compile(f.name_pattern)
            out = [e for e in out if pattern.search(e.name)]
        return out

    # ---- audit ----

    def audit_search(
        self,
        operation: str | None = None,
        scope_id: str | None = None,
        actor: str | None = None,
        time_range: TimeRange | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        clauses, params = [], []
        if operation:
            clauses.append("operation = ?")
            params.append(operation)
        if scope_id:
            clauses.append("scope_id = ?")
            params.append(scope_id)
        if actor:
            clauses.append("actor = ?")
            params.append(actor)
        if time_range:
            if time_range.start:
                clauses.append("at_time >= ?")
                params.append(self.store._iso(time_range.start))
            if time_range.end:
                clauses.append("at_time <= ?")
                params.append(self.store._iso(time_range.end))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"SELECT * FROM audit{where} ORDER BY at_time DESC LIMIT ?"
        params.append(limit)
        rows = self.store.fetch(sql, params)
        return [self._row_to_audit(r) for r in rows]

    # ---- cost (v1.1 R12) ----

    def cost_by_prompt(
        self,
        time_range: TimeRange | None = None,
        components: list[str] | None = None,
        pricing: dict[str, tuple[float, float]] | None = None,
    ) -> dict[str, PromptCost]:
        """Aggregate token rows by prompt_name across all components.

        v1.1 R12: workspace-scoped cost attribution. The pricing map
        is optional and lets the caller compute estimated_usd
        per-model: `{model: (input_usd_per_mtok, output_usd_per_mtok)}`.
        Without pricing, estimated_usd is 0.0.
        """
        clauses, params = [], []
        if time_range:
            if time_range.start:
                clauses.append("at_time >= ?")
                params.append(self.store._iso(time_range.start))
            if time_range.end:
                clauses.append("at_time <= ?")
                params.append(self.store._iso(time_range.end))
        if components:
            placeholders = ", ".join("?" for _ in components)
            clauses.append(f"component IN ({placeholders})")
            params.extend(components)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = (
            f"SELECT prompt_name, model, "
            f"SUM(input_tokens), SUM(output_tokens), SUM(call_count) "
            f"FROM tokens{where} GROUP BY prompt_name, model"
        )
        rows = self.store.fetch(sql, params)
        out: dict[str, PromptCost] = {}
        for prompt_name, model, in_tok, out_tok, calls in rows:
            existing = out.get(prompt_name)
            in_tok = int(in_tok or 0)
            out_tok = int(out_tok or 0)
            calls = int(calls or 0)
            estimated = 0.0
            if pricing and model in pricing:
                inp_price, out_price = pricing[model]
                estimated = (in_tok / 1_000_000) * inp_price + (out_tok / 1_000_000) * out_price
            if existing is None:
                out[prompt_name] = PromptCost(
                    prompt_name=prompt_name,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    call_count=calls,
                    estimated_usd=round(estimated, 6),
                )
            else:
                out[prompt_name] = PromptCost(
                    prompt_name=prompt_name,
                    input_tokens=existing.input_tokens + in_tok,
                    output_tokens=existing.output_tokens + out_tok,
                    call_count=existing.call_count + calls,
                    estimated_usd=round(existing.estimated_usd + estimated, 6),
                )
        return out

    # ---- replay ----

    def replay_session(self, session_id: str):
        from .replay import SessionReplay
        return SessionReplay.build(self, session_id)

    def replay_scope(self, scope_id: str):
        from .replay import ScopeReplay
        return ScopeReplay.build(self, scope_id)

    def replay_objective(self, objective_id: str):
        from .replay import ObjectiveReplay
        return ObjectiveReplay.build(self, objective_id)

    # ---- internal: SQL builders & row marshalling ----

    def _spans_sql(self, f: SpanFilter, limit: int) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if f.trace_ids:
            placeholders = ", ".join("?" for _ in f.trace_ids)
            clauses.append(f"trace_id IN ({placeholders})")
            params.extend(f.trace_ids)
        if f.components:
            placeholders = ", ".join("?" for _ in f.components)
            clauses.append(f"component IN ({placeholders})")
            params.extend(f.components)
        if f.name_exact:
            clauses.append("name = ?")
            params.append(f.name_exact)
        if f.status:
            clauses.append("status = ?")
            params.append(f.status)
        if f.retention_class:
            clauses.append("retention_class = ?")
            params.append(f.retention_class.value)
        if f.time_range:
            if f.time_range.start:
                clauses.append("start_time_unix_nano >= ?")
                params.append(int(f.time_range.start.timestamp() * 1e9))
            if f.time_range.end:
                clauses.append("start_time_unix_nano <= ?")
                params.append(int(f.time_range.end.timestamp() * 1e9))
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"SELECT * FROM spans{where} ORDER BY start_time_unix_nano LIMIT ?"
        params.append(limit)
        return sql, params

    @staticmethod
    def _columns_spans() -> list[str]:
        return [
            "trace_id", "span_id", "parent_span_id", "name", "tracer_name",
            "component", "kind", "start_time_unix_nano", "end_time_unix_nano",
            "duration_ns", "status", "status_message", "attributes",
            "retention_class", "ingested_at",
        ]

    @staticmethod
    def _columns_events() -> list[str]:
        return [
            "event_id", "span_id", "trace_id", "name", "time_unix_nano",
            "attributes", "retention_class", "ingested_at",
        ]

    @staticmethod
    def _columns_audit() -> list[str]:
        return [
            "audit_id", "at_time", "operation", "actor", "scope_id",
            "subject_uuid", "rationale", "extras",
        ]

    def _row_to_span(self, row: Sequence[Any]) -> SpanRecord:
        cols = self._columns_spans()
        d = dict(zip(cols, row))
        attrs_raw = d.get("attributes")
        attrs = json.loads(attrs_raw) if isinstance(attrs_raw, str) else (attrs_raw or {})
        ingested = d.get("ingested_at")
        if isinstance(ingested, str):
            try:
                ingested = datetime.fromisoformat(ingested)
            except ValueError:
                ingested = datetime.now(timezone.utc)
        elif ingested is None:
            ingested = datetime.now(timezone.utc)
        return SpanRecord(
            trace_id=d["trace_id"],
            span_id=d["span_id"],
            parent_span_id=d.get("parent_span_id"),
            name=d["name"],
            tracer_name=d["tracer_name"],
            component=d["component"],
            kind=d.get("kind") or "INTERNAL",
            start_time_unix_nano=int(d["start_time_unix_nano"]),
            end_time_unix_nano=int(d["end_time_unix_nano"]),
            status=d.get("status") or "UNSET",
            status_message=d.get("status_message"),
            attributes=attrs,
            retention_class=RetentionClass(d.get("retention_class") or "normal"),
            ingested_at=ingested,
        )

    def _row_to_event(self, row: Sequence[Any]) -> EventRecord:
        cols = self._columns_events()
        d = dict(zip(cols, row))
        attrs_raw = d.get("attributes")
        attrs = json.loads(attrs_raw) if isinstance(attrs_raw, str) else (attrs_raw or {})
        ingested = d.get("ingested_at")
        if isinstance(ingested, str):
            try:
                ingested = datetime.fromisoformat(ingested)
            except ValueError:
                ingested = datetime.now(timezone.utc)
        elif ingested is None:
            ingested = datetime.now(timezone.utc)
        return EventRecord(
            span_id=d["span_id"],
            trace_id=d["trace_id"],
            name=d["name"],
            time_unix_nano=int(d["time_unix_nano"]),
            attributes=attrs,
            retention_class=RetentionClass(d.get("retention_class") or "normal"),
            ingested_at=ingested,
        )

    def _row_to_audit(self, row: Sequence[Any]) -> AuditRecord:
        cols = self._columns_audit()
        d = dict(zip(cols, row))
        extras_raw = d.get("extras")
        extras = json.loads(extras_raw) if isinstance(extras_raw, str) else (extras_raw or {})
        at = d.get("at_time")
        if isinstance(at, str):
            try:
                at = datetime.fromisoformat(at)
            except ValueError:
                at = datetime.now(timezone.utc)
        return AuditRecord(
            at_time=at,
            operation=d["operation"],
            actor=d["actor"],
            scope_id=d.get("scope_id"),
            subject_uuid=d.get("subject_uuid"),
            rationale=d["rationale"],
            extras=extras,
        )
