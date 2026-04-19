# Structured Pydantic API Reference

The canonical query surface — `QueryAPI`. Every other surface (NL path, CLI) composes over this.

## Construction

```python
from pos_observability_aggregator import AggregatorConfig, open_store, QueryAPI

cfg = AggregatorConfig()           # defaults to ~/.pos/observability.duckdb
store = open_store(cfg)            # falls back to SQLite if duckdb unavailable
api = QueryAPI(store)
```

## Methods

### find_spans(filter, limit=100) → list[SpanRecord]

```python
from pos_observability_aggregator.api import SpanFilter, TimeRange
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)

# All scope-of-work errors in the last hour.
api.find_spans(SpanFilter(
    components=["scope_of_work"],
    status="ERROR",
    time_range=TimeRange(start=now - timedelta(hours=1), end=now),
))

# Spans bound to a specific scope.
api.find_spans(SpanFilter(scope_id="scope_42"))

# Spans whose name matches a regex.
api.find_spans(SpanFilter(name_pattern=r"ingest|rollup"))

# Spans matching attribute values exactly.
api.find_spans(SpanFilter(attributes_match={"pos.objective.id": "obj_99"}))

# Spans with at least one event of a given name.
api.find_spans(SpanFilter(has_event="state_changed"))

# Spans of a specific retention class (audit what's been dropped).
from pos_observability_aggregator import RetentionClass
api.find_spans(SpanFilter(retention_class=RetentionClass.DERIVED_ONLY))
```

### get_span(span_id) → SpanRecord | None

```python
api.get_span("a1b2c3d4e5f60001")
```

### get_trace(trace_id) → list[SpanRecord]

```python
# All spans in the trace, ordered by start time.
api.get_trace("0123456789abcdef0123456789abcdef")
```

### find_events(filter, limit=100) → list[EventRecord]

```python
from pos_observability_aggregator.api import EventFilter

# All events on a specific span.
api.find_events(EventFilter(span_ids=["a1b2c3d4e5f60001"]))

# All state-changed events in a trace.
api.find_events(EventFilter(
    trace_ids=["..."],
    name_exact="pos.scope.state_changed",
))
```

### cost_by_prompt(time_range=None, components=None, pricing=None) → dict[str, PromptCost]

v1.1 R12 — workspace-scoped cost attribution by `pos.prompt.type`.

```python
# All-time cost grouped by prompt name.
costs = api.cost_by_prompt()
for name, cost in costs.items():
    print(name, cost.input_tokens, cost.output_tokens, cost.call_count)

# Cost for memory-system in the last day.
api.cost_by_prompt(
    time_range=TimeRange(start=now - timedelta(days=1)),
    components=["memory_system"],
)

# With pricing for $-attribution.
api.cost_by_prompt(pricing={
    "claude-sonnet": (3.0, 15.0),     # $/M input, $/M output
    "claude-haiku":  (0.25, 1.25),
})
```

### audit_search(operation=None, scope_id=None, actor=None, time_range=None, limit=100) → list[AuditRecord]

```python
api.audit_search(operation="supersession_inferred")
api.audit_search(scope_id="scope_42", actor="memory_system")
```

### replay_session(session_id) → SessionReplay

Read-only playback of an interactive session timeline.

```python
rep = api.replay_session("sess_2026-04-19-12:30")
rep.started_at, rep.ended_at
for span in rep.spans: ...        # ordered by start_time
for event in rep.events: ...      # ordered by time
rep.cost_summary                  # dict[prompt_name, PromptCost]
```

Session ID derivation: spans carry `pos.session.id` attribute (set by primary-persona's monitor), or `session_id` is treated as a trace_id alias.

### replay_scope(scope_id) → ScopeReplay

Read-only playback of an autonomous scope's decision chain.

```python
rep = api.replay_scope("scope_42")
rep.root_span                     # the invoke_scope span
rep.spans                         # all descendants
rep.state_transitions             # state-changed events
rep.audit_entries                 # audit rows scoped to this scope
rep.cost_summary
```

### replay_objective(objective_id) → ObjectiveReplay

Read-only playback of every scope ever bound to an objective.

```python
rep = api.replay_objective("obj_99")
rep.scope_replays                 # list[ScopeReplay], one per bound scope
rep.criterion_evaluations         # events whose name carries 'criterion'
rep.status_trail                  # [(time, status), ...]
```

## Schema (input/output)

### SpanFilter

```python
class SpanFilter(BaseModel):
    trace_ids: list[str] | None = None
    components: list[str] | None = None
    name_pattern: str | None = None
    name_exact: str | None = None
    time_range: TimeRange | None = None
    attributes_match: dict[str, Any] | None = None
    has_event: str | None = None
    status: str | None = None             # OK | ERROR
    scope_id: str | None = None           # convenience for pos.scope.id
    retention_class: RetentionClass | None = None
```

### SpanRecord (output)

```python
class SpanRecord(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    tracer_name: str
    component: str
    kind: str
    start_time_unix_nano: int
    end_time_unix_nano: int
    duration_ns: int                     # computed property
    status: str                          # OK | ERROR | UNSET
    status_message: str | None
    attributes: dict[str, Any]
    retention_class: RetentionClass
    ingested_at: datetime
```

### PromptCost

```python
class PromptCost(BaseModel):
    prompt_name: str
    input_tokens: int
    output_tokens: int
    call_count: int
    estimated_usd: float
```

### Replay shapes

```python
class SessionReplay(BaseModel):
    session_id: str
    started_at: datetime | None
    ended_at: datetime | None
    spans: list[SpanRecord]
    events: list[EventRecord]
    cost_summary: dict[str, PromptCost]

class ScopeReplay(BaseModel):
    scope_id: str
    root_span: SpanRecord | None
    spans: list[SpanRecord]
    state_transitions: list[EventRecord]
    cost_summary: dict[str, PromptCost]
    audit_entries: list[AuditRecord]

class ObjectiveReplay(BaseModel):
    objective_id: str
    scope_replays: list[ScopeReplay]
    criterion_evaluations: list[EventRecord]
    status_trail: list[tuple[datetime, str]]
```
