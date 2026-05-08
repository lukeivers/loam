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

"""Replay primitives — Reading A (read-only playback).

Per Luke's ruling and proposal §"Replay": replay reconstructs the
ordered sequence of spans + events + attributes from stored records.
No re-execution; no LLM calls; the playback is a deterministic render
of what was observed.

Three replay primitives:
  - replay_session(session_id)     — interactive session timeline
  - replay_scope(scope_id)         — autonomous scope decision chain
  - replay_objective(objective_id) — every scope bound to objective

Session derivation: pOS does not yet have a session-management
primitive (research §16 q1; first-pass ruling: aggregator derives
session_id from `loam.session.id` attribute when present, falls back
to grouping turn-events within an idle window).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from .api import EventFilter, PromptCost, SpanFilter, TimeRange
from .schema import EventRecord, SpanRecord

if TYPE_CHECKING:
    from .api import QueryAPI


class CitedSpan(BaseModel):
    """A span citation — full record + a stable ID for follow-up."""

    span_id: str
    name: str
    component: str
    start_time: datetime
    duration_ms: float
    summary_attributes: dict[str, Any] = Field(default_factory=dict)


class SessionReplay(BaseModel):
    session_id: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    spans: list[SpanRecord] = Field(default_factory=list)
    events: list[EventRecord] = Field(default_factory=list)
    cost_summary: dict[str, PromptCost] = Field(default_factory=dict)

    @classmethod
    def build(cls, api: "QueryAPI", session_id: str) -> "SessionReplay":
        # Strategy: spans whose attributes contain `loam.session.id`
        # equal to session_id. Fallback when no such attribute exists:
        # treat session_id as a trace_id alias (caller convention).
        spans = api.find_spans(
            SpanFilter(attributes_match={"loam.session.id": session_id}),
            limit=10000,
        )
        # Filter by the attribute since the SQL ignores attributes_match.
        spans = [s for s in spans if s.attributes.get("loam.session.id") == session_id]
        if not spans:
            # Fallback: treat as trace_id
            spans = api.get_trace(session_id)
        spans.sort(key=lambda s: s.start_time_unix_nano)
        trace_ids = list({s.trace_id for s in spans})
        events: list[EventRecord] = []
        if trace_ids:
            events = api.find_events(EventFilter(trace_ids=trace_ids), limit=10000)
        events.sort(key=lambda e: e.time_unix_nano)
        started = None
        ended = None
        if spans:
            started = datetime.fromtimestamp(spans[0].start_time_unix_nano / 1e9, tz=timezone.utc)
            ended = datetime.fromtimestamp(spans[-1].end_time_unix_nano / 1e9, tz=timezone.utc)
        cost_window = TimeRange(start=started, end=ended) if started else None
        cost = api.cost_by_prompt(time_range=cost_window) if cost_window else {}
        return cls(
            session_id=session_id,
            started_at=started,
            ended_at=ended,
            spans=spans,
            events=events,
            cost_summary=cost,
        )


class ScopeReplay(BaseModel):
    scope_id: str
    root_span: SpanRecord | None = None
    spans: list[SpanRecord] = Field(default_factory=list)
    state_transitions: list[EventRecord] = Field(default_factory=list)
    cost_summary: dict[str, PromptCost] = Field(default_factory=dict)
    audit_entries: list[Any] = Field(default_factory=list)

    @classmethod
    def build(cls, api: "QueryAPI", scope_id: str) -> "ScopeReplay":
        # All spans carrying loam.scope.id == scope_id.
        all_spans = api.find_spans(
            SpanFilter(attributes_match={"loam.scope.id": scope_id}),
            limit=10000,
        )
        spans = [s for s in all_spans if s.attributes.get("loam.scope.id") == scope_id]
        spans.sort(key=lambda s: s.start_time_unix_nano)
        # Root span: the earliest one, or one whose name is invoke_scope
        root = None
        for s in spans:
            if "invoke_scope" in s.name:
                root = s
                break
        if root is None and spans:
            root = spans[0]
        # Pull all events from those spans' traces.
        trace_ids = list({s.trace_id for s in spans})
        events: list[EventRecord] = []
        if trace_ids:
            events = api.find_events(EventFilter(trace_ids=trace_ids), limit=10000)
        events.sort(key=lambda e: e.time_unix_nano)
        # State transitions: events whose name carries 'state' or 'transition'
        state_events = [
            e for e in events
            if "state" in e.name.lower() or "transition" in e.name.lower()
        ]
        # Cost summary scoped to scope_id.
        cost = {}
        if spans:
            start_dt = datetime.fromtimestamp(
                spans[0].start_time_unix_nano / 1e9, tz=timezone.utc
            )
            end_dt = datetime.fromtimestamp(
                spans[-1].end_time_unix_nano / 1e9, tz=timezone.utc
            )
            # cost_by_prompt is workspace-scoped; filter caller-side.
            cost = api.cost_by_prompt(time_range=TimeRange(start=start_dt, end=end_dt))
        # Audit entries scoped to this scope.
        audit = api.audit_search(scope_id=scope_id, limit=1000)
        return cls(
            scope_id=scope_id,
            root_span=root,
            spans=spans,
            state_transitions=state_events,
            cost_summary=cost,
            audit_entries=audit,
        )


class ObjectiveReplay(BaseModel):
    objective_id: str
    scope_replays: list[ScopeReplay] = Field(default_factory=list)
    criterion_evaluations: list[EventRecord] = Field(default_factory=list)
    status_trail: list[tuple[datetime, str]] = Field(default_factory=list)

    @classmethod
    def build(cls, api: "QueryAPI", objective_id: str) -> "ObjectiveReplay":
        # Spans where attribute loam.objective.id matches → scopes bound
        # to this objective. (objective-tracker emits this attribute on
        # bind_scope spans.)
        bind_spans = api.find_spans(
            SpanFilter(attributes_match={"loam.objective.id": objective_id}),
            limit=10000,
        )
        bind_spans = [s for s in bind_spans if s.attributes.get("loam.objective.id") == objective_id]
        scope_ids = []
        for s in bind_spans:
            sid = s.attributes.get("loam.scope.id")
            if sid and sid not in scope_ids:
                scope_ids.append(sid)
        replays = [ScopeReplay.build(api, sid) for sid in scope_ids]
        # Criterion evaluations: events whose name mentions 'criterion'.
        events: list[EventRecord] = []
        for s in bind_spans:
            events.extend(
                api.find_events(EventFilter(trace_ids=[s.trace_id]), limit=10000)
            )
        crit_events = [e for e in events if "criterion" in e.name.lower()]
        crit_events.sort(key=lambda e: e.time_unix_nano)
        # Status trail: pairs of (time, status) extracted from events.
        status_trail: list[tuple[datetime, str]] = []
        for e in events:
            status = e.attributes.get("loam.objective.status") or e.attributes.get("status")
            if status:
                status_trail.append(
                    (datetime.fromtimestamp(e.time_unix_nano / 1e9, tz=timezone.utc), str(status))
                )
        status_trail.sort(key=lambda t: t[0])
        return cls(
            objective_id=objective_id,
            scope_replays=replays,
            criterion_evaluations=crit_events,
            status_trail=status_trail,
        )
