# Observability Aggregator — Prose Explanation

The pOS observability aggregator is a single-user local-first trace store. Six pOS components emit OpenTelemetry spans; a seventh component (memory-system) emits hand-rolled JSONL. The aggregator subscribes to both surfaces, persists what they emit into one queryable store, and serves three query surfaces: a structured Pydantic API, a natural-language path ("show me why"), and a `pos obs` CLI.

The defining design constraint is the A1 correction held against every sealed component: none of them know the aggregator exists. Each component was built assuming no consumer; the aggregator's arrival must not amend any of them. The aggregator subscribes via mechanisms the components already provide — OpenTelemetry's late-binding TracerProvider for the six OTel emitters, and tail-on-disk for the memory JSONL sinks. No code change to any sealed component.

## What the aggregator stores

The store holds four shape-distinct record families:

- **Spans** — one row per OTel span. Trace ID, span ID, parent, name, tracer namespace, component label, kind, start/end times, status, attributes, retention class.
- **Span events** — one row per OTel event attached to a span. Used for state transitions, narrative-rendered notifications, supersession-inferred decisions, and similar.
- **Tokens** — one row per LLM call, keyed by `prompt_name` (the v1.1 R12 grouping key). Aggregated for cost-by-prompt views.
- **Audit** — free-text rationales written by memory-system (supersession, retention-class decisions) and graceful-degradation (narrative renders).

Plus three rollup tables (`daily_rollup`, `monthly_rollup`, `yearly_rollup`) populated by the retention job, and an `ingest_cursors` table that lets the JSONL tailers and OTel spool drainer resume on restart without double-ingestion.

## How ingest works

There are two ingest paths. Both write to the same store; both honour v1.1 R10 retention classes at the boundary so payload data is dropped before it ever lands in DuckDB.

**Path A — In-process OTel exporter via the orchestrator's `~/.pos/bootstrap.py` workspace hook.** The bootstrap calls `install_for_workspace(...)`, which installs a TracerProvider with a custom `AggregatorSpanExporter` that writes finished spans to a local JSONL spool file. Python OTel's `ProxyTracer` pattern means components can have already imported `trace.get_tracer(...)` at module-load time and the proxy still routes their spans through the provider that's installed when the first span actually opens. A separate spool-drainer thread reads the spool file and inserts rows into the store. The spool buffer survives aggregator restart — spans accumulated during downtime drain on next start.

**Path B — JSONL tailers for memory-system.** Memory writes `spans.jsonl`, `tokens.jsonl`, and `audit.jsonl` to its own observability sink directory. Three `JSONLTailer` instances watch those files, normalise each new record into the canonical Pydantic schema, and insert into the store. Each tailer persists a byte-offset cursor so a restart resumes where it left off; file truncation (memory-system data clear, log rotation) is detected and reset gracefully. Malformed lines are logged and skipped — never fatal.

The aggregator's own spans are filtered at the exporter and the spool drainer using a tracer-name prefix match (`pos.aggregator.*`). Without this filter, every NL query would emit translate/format spans which would be ingested which would generate more spans — an infinite observation loop. The filter makes the aggregator's emissions diagnosable via the on-disk spool but invisible to the store.

## Storage substrate

DuckDB is the primary substrate per Luke's approval as a net-new dependency. It is embedded, columnar, MIT-licensed, and matches the analytic query shapes the aggregator serves (time-range scans, group-by-prompt, trace-tree reconstruction). SQLite is the fallback substrate at identical schema — slower for analytic queries over 90+ days of data but stdlib-only, with parity verified by a synthetic-workload test. Substrate is chosen via `AggregatorConfig.substrate`.

## Decaying retention

Per Luke's brief decisions, retention is decaying-granularity:

- **0–7 days:** raw spans, events, attributes preserved at full fidelity.
- **7–30 days:** daily rollups (`daily_rollup`) plus the top-N longest spans per day kept raw (default N=20, workspace-tunable). The smoking-gun reserve.
- **30–365 days:** monthly rollups (`monthly_rollup`); raw spans pruned.
- **365+ days:** yearly rollups (`yearly_rollup`); audit-only at the workspace's cutoff.

The `RetentionJob` is idempotent — re-running it produces the same rollup tables. Each retention-tier transition has its own pruning step keyed off the configured boundaries. The job is invocable from any scheduling surface (asyncio task, orchestrator heartbeat hook, manual cron); the framework default is daily.

## Retention class — v1.1 R10 honoured at ingest

Every record carries a retention class — `normal`, `derived-only`, or `ephemeral`. The class is read from a `pos.retention.class` attribute on the source span (memory's records carry it as a top-level field; OTel components set it as a span attribute). Ingest applies the class strictly:

- `normal` → stored fully, payload preserved.
- `derived-only` → payload attributes (`inputs`, `outputs`, `prompt`, `completion`, etc.) dropped before insert. Structural metadata (tracer name, component, scope ID, span name, status, timing) preserved.
- `ephemeral` → only the class marker preserved. No payload, no extras, no status message.

Privacy verification: workloads producing `derived-only` and `ephemeral` records are tested for byte-level absence of payload text in the store. The test asserts both — payload absent from Pydantic-returned attributes and absent from the underlying database rows.

## Query surfaces

The structured Pydantic API is the canonical surface. Every other consumer composes over it. `find_spans(filter)`, `get_trace(trace_id)`, `get_span(span_id)`, `find_events(filter)`, `cost_by_prompt(window)`, `audit_search(...)`, plus three replay primitives — `replay_session(session_id)`, `replay_scope(scope_id)`, `replay_objective(objective_id)`. All inputs and outputs are Pydantic-validated.

The natural-language path is the "show me why" surface for the primary persona. A two-LLM-call pattern: `nl_translate(question)` produces a structured Pydantic filter; the filter is executed against the structured API; `nl_format(rows, question)` produces a cited natural-language answer with span IDs always carried through. Both calls carry `pos.prompt.type` attributes (`obs-nl-translate`, `obs-nl-format`) so the aggregator's own LLM cost shows up in `cost_by_prompt` — reflexive cost attribution per v1.1 R12. A rule-based translator is the default (deterministic, no external dependency, evaluated on a 25-question corpus at ≥80% accuracy); production deployments wire Claude-via-Max via the `llm_translate` and `llm_format` callables.

The `pos obs` CLI is a thin wrapper over the structured API — one subcommand per method, plus `pos obs why "<question>"` for the NL path. Output is JSON, pretty-printed by default; `--raw` for one-line.

## Replay — Reading A (read-only playback)

Per Luke's ruling, replay is read-only playback. `replay_session`, `replay_scope`, `replay_objective` reconstruct decision chains from stored records — no re-execution of LLM calls, no playback harness, no amendments to any sealed component. The user reads a transcript of what happened; if they want to dig deeper, every claim cites span IDs they can drill into.

Reading B (deterministic re-execution) is explicitly out of scope — it would require amending every LLM-calling sealed component to route through a playback substitution layer, violating A1.

## Self-observability and integration with primary persona

The aggregator emits its own OTel spans for ingest batches, queries, NL translate/format calls, retention runs. These are filtered out at ingest by tracer-name prefix match. They're observable via the on-disk `~/.pos/logs/aggregator.out` debug log if needed, but not stored — preventing recursion.

When the primary persona answers "why did you do X at time T," it calls the aggregator's NL surface, receives a cited Pydantic answer, and adapts the prose into its voice — but the citations carry through. Anti-deskilling principle: the user always sees the underlying span IDs, never just the narrative.

## What this component does NOT do

Not a UI layer. Not a hosted service. Not a multi-tenant observability platform. Not a deterministic-replay harness. Not a redaction service (privacy is enforced via retention class at ingest; explicit redaction patterns are a future addition). Not a vendor-neutral OpenTelemetry collector — pOS is Claude-only by deliberate non-goal.
