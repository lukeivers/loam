# Research — Observability Aggregator

**Component:** Observability Aggregator — the consumer that subscribes to every
sealed component's OTel emissions, stores them durably, serves queries
(including "why did you do X at time T"), and supports session replay.
**Phase:** Phase 2, third component.
**Status:** `research_in_progress` — research document only. No proposal, no
brief, no implementation.
**Authored by:** general-purpose research agent, 2026-04-19, under the plan
Approved.

---

## Table of contents

1. Preamble — constraints, halt conditions, failure surfaces
2. Survey of existing patterns (plan §1)
3. Ingestion architecture — recommendation and rationale (plan §2)
4. Storage substrate — recommendation and rationale (plan §3)
5. Storage schema sketch (plan §3, §5)
6. Query API specification (plan §4)
7. Replay semantics — decision and primitives (plan §5)
8. Retention, pruning, retention-class propagation (plan §6, §7)
9. Privacy and redaction (plan §7)
10. Self-observability and process placement (plan §8, §9)
11. Integration with primary-persona "show me why" queries (plan §10, §11)
12. Acceptance-criterion coverage matrix
13. Dependency map
14. Complexity estimate
15. Prototyping priorities — questions only a prototype can answer
16. Open questions surfaced to the owner

---

## 1. Preamble — what this document is and is not

This is a research document answering the eight question groups in
`research-plan.md`. It is not a proposal. It does not commit to an
implementation shape; it identifies a recommended shape per question group,
names the trade-offs, and flags everything that should not proceed without
decision recorded.

### Halt-on-deviation signals surfaced in this document

Throughout this document, any place where the research believes a spec
criterion is either (a) unsatisfiable under the permitted dependencies, (b)
unsatisfiable without amending a sealed component, or (c) deviating from
the research plan in any way, is explicitly flagged as **HALT SIGNAL**. No
such signal is raised lightly. The summary at §16 consolidates them.

Three halt signals exist in this research; one is a **hard halt** (requires
decision recorded before any proposal), two are **soft flags** (the research
proposes an answer and the owner may accept, amend, or reject):

1. **Soft flag.** Recommend adding `duckdb` as a net-new dependency for the
   storage substrate, justified in §4. Builder cannot add it silently.
2. **Soft flag.** Memory-system's existing JSONL sinks (spans, tokens,
   audit) are not OTLP-encoded — they use a hand-rolled minimal OTel-compat
   shape. The aggregator treats them as a distinct ingestion source with a
   trivial translator, rather than asking memory to re-encode. No memory
   amendment required.
3. **Hard halt — needs decision recorded before proposal.** Replay semantics.
   The research recommends read-only playback (faithful reconstruction)
   rather than deterministic re-execution (true replay). The recommendation
   is defensible under the spec, but the spec phrasing "replay the decision
   chain end-to-end" is ambiguous enough that the owner should confirm before we
   commit.

### Core constraints held in mind throughout

- **A1 correction.** Every sealed component was built assuming no consumer.
  The aggregator must subscribe via the OTel API's existing late-binding
  `TracerProvider` mechanism, by tailing on-disk JSONL for memory-system, or
  via the workspace-supplied `~/.pos/bootstrap.py` hook (which is
  workspace-owned, not sealed-component-owned). No recommendation in this
  document modifies any sealed component.
- **Python-native, stdlib + pydantic + pyee + opentelemetry-api/sdk +
  PyYAML.** Anything else is a halt signal. DuckDB is called out as a soft
  flag; no other net-new dep is proposed.
- **Single-user local-first.** No multi-tenant, no horizontal scale, no
  external object store, no hosted service. All recommendations favour
  simplicity and low-resource footprint.
- **Max-first.** The only LLM inference inside the aggregator is the NL→
  structured query translation for "show me why"; uses Claude via the
  existing Max subscription.
- **v1.1 R10 retention class.** `derived-only` and `ephemeral` memory
  episodes constrain what the aggregator can persist about them. See §8.
- **pOS core ships zero personas.** This component ships zero persona
  content; the "show me why" integration is a *capability* the primary-
  persona layer consumes, not a baked-in persona.

---

## 2. Survey of existing patterns

### 2.1 OpenTelemetry Collector architecture

The OpenTelemetry Collector is the vendor-neutral reference consumer for
OTel emissions. It is a separate long-running process that receives spans,
metrics, and logs, runs them through a pipeline of processors (batching,
filtering, sampling, attribute manipulation), and exports them to
downstream storage.

For a single-user pOS, the Collector's advantages (vendor independence,
tail sampling, multi-backend fan-out, load-shedding) are all concerns we
don't have. Its disadvantages (adds a Go binary as a system dependency,
requires its own supervision, OTLP network receiver adds a port surface,
operational overhead) are costs we'd pay for no benefit.

The research recommends **against** the Collector for pOS: the overhead is
not proportional to the scale. Direct in-process subscription is cheaper
and simpler.

([OpenTelemetry Collector docs](https://opentelemetry.io/docs/collector/),
[SigNoz collector vs exporter
guide](https://signoz.io/guides/opentelemetry-collector-vs-exporter/))

### 2.2 OTel Python SpanProcessor / SpanExporter pattern

The OTel Python SDK exposes two extension points relevant here:

- **SpanProcessor** — invoked on span start and span end. Can attach,
  enrich, or inspect spans. Built-in implementations: `SimpleSpanProcessor`
  (synchronous, passes each span to an exporter on end) and
  `BatchSpanProcessor` (batches + asynchronous). Custom processors are a
  single class implementing `on_start`, `on_end`, `shutdown`,
  `force_flush`.
- **SpanExporter** — receives batches of finished spans. Implementations
  in the ecosystem: `ConsoleSpanExporter`, `InMemorySpanExporter` (test),
  file exporter, OTLP gRPC / HTTP, Jaeger, Zipkin, vendor exporters.

Critical late-binding property: as of modern OTel Python, `trace.get_tracer()`
returns a `ProxyTracer` when no provider is installed. The proxy delegates
to whatever provider is registered at the time of a span call. This means
the aggregator can register its `TracerProvider` (with a
`BatchSpanProcessor` + custom exporter) *after* sealed components have
already imported their tracers — emissions still route correctly. The
sealed components do not need to know about the aggregator.

Historical gotcha: in older Python SDK versions, calling `get_tracer`
before registering a provider bound a permanent no-op tracer. The current
SDK (>= 1.25, which the components require) implements the proxy pattern
and this gotcha is resolved.

([OpenTelemetry Python
docs](https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.export.html),
[How to fix no-tracer-provider warnings](https://oneuptime.com/blog/post/2026-02-06-fix-no-tracer-provider-configured-warnings/view),
[Late binding proxy pattern](https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-api/src/opentelemetry/trace/__init__.py))

### 2.3 OTLP File Exporter (JSONL) and tail-ingestion

The OpenTelemetry Protocol defines a **file exporter** that writes OTLP
JSON records, one record per line, in `.jsonl` format. A consumer can tail
the file and ingest. Two caveats from the spec:

1. Records in the file are not guaranteed to be time-ordered.
2. Timestamps are not guaranteed monotonic.

Both are fine for archival ingestion — the consumer orders by
`start_time_unix_nano` at query time, not ingestion time.

The memory-system's existing emission shape (hand-rolled minimal
OTel-compatible JSON with `trace_id`, `span_id`, `name`, `start/end` nanos,
`attributes`) is close to but not identical to the OTLP JSON encoding. A
trivial translator at the aggregator's ingestion boundary normalises both
paths into the aggregator's canonical schema.

([OTel file exporter
spec](https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/))

### 2.4 Jaeger / Tempo / Loki storage comparison

- **Jaeger** — requires Cassandra or Elasticsearch for production; ships
  an in-memory option for demos. Heavy dependency footprint; indexing cost
  rises with volume. Rejected for pOS: the storage backend alone is
  heavier than the rest of pOS combined.
- **Grafana Tempo** — custom TempoDB format, optimised for object storage
  (S3/GCS/Azure). Local filesystem is supported but deliberately not
  recommended by the project. Architecture assumes Grafana as the query
  surface. Rejected: hosted-style object store + Grafana dependency is
  enterprise footprint.
- **Loki** — optimised for logs, not traces. Chunked index; assumes
  Prometheus/Grafana stack. Not the right shape for span-tree queries.

None of the three fit single-user local-first. They exist for scale we
don't have.

([Grafana Tempo vs Jaeger](https://last9.io/blog/grafana-tempo-vs-jaeger/),
[Jaeger
alternatives](https://www.dash0.com/comparisons/jaeger-alternatives-for-tracing))

### 2.5 LangSmith / LangFuse single-tenant architectures

These are the closest analogues to the aggregator's job — they exist to
store LLM traces for a developer or a single workspace.

- **LangSmith self-hosted** — PostgreSQL + Redis + ClickHouse. Requires
  an Enterprise license. Not viable.
- **Langfuse self-hosted** (open source, MIT) — ClickHouse for trace
  storage, Redis for queues, S3 for object storage. Architecture:
  batched-in-at-the-edge, async-worker-to-OLAP. This is enterprise-shaped;
  the minimum viable footprint is several containers and at least 8 GB
  RAM. Rejected for pOS: three new services, none of them stdlib, for a
  single local user.

Relevant pattern learned: both systems normalise the LLM call into a
schema with `trace_id`, `span_id`, `parent_span_id`, `prompt`, `input`,
`output`, `latency`, `token counts`. The aggregator can borrow the
semantics without borrowing the stack.

([Langfuse self-hosting](https://langfuse.com/self-hosting),
[Langfuse vs LangSmith](https://langfuse.com/faq/all/langsmith-alternative))

### 2.6 DuckDB for analytic observability

DuckDB is the emerging embedded analytical database — single file, no
daemon, no network port, columnar storage with vectorised query engine.
It is to analytical queries what SQLite is to OLTP: small, local, Python-
friendly, open source (MIT).

Relevant ecosystem:
- A DuckDB **OTLP community extension** exists (`read_otlp_traces()`,
  `read_otlp_logs()`, ClickHouse-inspired schemas) that reads OTLP JSON
  directly. We would not use the extension (extra surface to manage), but
  its existence confirms that DuckDB is a recognised pattern for OTel
  storage.
- Multiple write-ups advocate DuckDB + Parquet as a low-cost OpenTelemetry
  "lakehouse" pattern.

DuckDB's pros for pOS:

- Embeds in-process; same install surface as SQLite.
- Columnar storage compresses span attributes (JSON blobs, repeated
  strings) far better than row-oriented SQLite.
- SQL engine handles the analytic query shapes we need (time-range scans,
  group-by-prompt-name, trace-tree reconstruction) with fewer indexes.
- No network surface; no supervisor cost.

DuckDB's cons:

- **Net-new dependency.** The permitted list is stdlib + pydantic + pyee
  + opentelemetry-api/sdk + PyYAML. DuckDB is not on that list.
- Younger than SQLite; write-durability story is good but has fewer
  years of battle-testing.
- The write workload (high-rate append) is less its sweet spot than
  analytical reads; we would need to batch writes (every few seconds or
  every N spans).

Recommendation: **propose DuckDB as the storage substrate and explicitly
surface it as a soft flag for the owner to approve or reject.** Fallback
substrate (SQLite) is feasible but slower at analytic queries over 90+
days of retained data.

([DuckDB observability
overview](https://neogeografia.wordpress.com/2023/08/02/observability-and-log-analytics-with-duckdb/),
[DuckDB OTLP
extension](https://duckdb.org/community_extensions/extensions/otlp),
[DuckDB + Parquet + Iceberg
lakehouse](https://clay.fyi/blog/cheap-opentelemetry-lakehouses-parquet-duckdb-iceberg/))

### 2.7 In-process SpanProcessor patterns from ecosystem

Custom SpanProcessor patterns (seen in PostHog, Uptrace, OneUptime write-
ups): enrich spans with cost, filter sensitive attributes, route to
multiple exporters. These are all directly available to the aggregator; we
can layer a custom processor that extracts token usage onto a tokens view
at ingest time without changing the exporter contract.

([OneUptime — custom span
processors](https://oneuptime.com/blog/post/2026-01-30-opentelemetry-span-processors/view),
[OneUptime — business-specific
attributes](https://oneuptime.com/blog/post/2026-02-06-otel-custom-span-processor-business-attributes/view))

### 2.8 Text-to-SQL / NL-to-structured-query for observability

The spec's "why did you do X at time T" query is a natural-language
question over a structured trace store. The pattern is well-established:

- Existing text-to-SQL stacks (LangChain SQL agent, MLflow examples,
  Ragas evaluation) use an LLM to translate NL to SQL given the schema
  as context, then execute the SQL against the database.
- Accuracy reliability pattern: constrain the model to a subset (whitelisted
  tables, whitelisted functions), validate the SQL against an AST parser
  before execution, and run in a read-only transaction.
- Observability framework for reliability: log the NL query, the generated
  SQL, the execution result, and any parsing errors — ironically,
  observability of the observability query surface.

([Bag of Words — reliable text-to-SQL observability](https://dev.to/bagofwords/building-reliable-ai-analysts-an-observability-framework-for-text-to-sql-systems-25ln),
[MLflow NL-to-SQL example](https://mlflow.org/blog/from-natural-language-to-sql),
[Text-to-SQL LLM accuracy comparison](https://aimultiple.com/text-to-sql))

---

## 3. Ingestion architecture — recommendation and rationale

### 3.1 The ingestion challenge — two emission shapes, one consumer

The seven sealed components emit in two distinct shapes:

1. **Six components emit via the OTel Python API** (scope-of-work,
   primary-persona, objective-tracker, orchestrator, graceful-degradation,
   plus Phase-1 test infrastructure). They call
   `trace.get_tracer("pos.<namespace>")` and produce spans and events via
   the global `TracerProvider`. Without a provider installed, emissions
   silently no-op. With a provider installed, emissions route through its
   processors and exporters.
2. **Memory-system emits directly to JSONL files** on disk — three sinks
   (`spans.jsonl`, `tokens.jsonl`, `audit.jsonl`) under
   `./data/observability/`. The format is a hand-rolled minimal
   OTel-compatible JSON shape (not OTLP JSON). The A1 correction is held
   by design: a future aggregator reads the JSONL files, no online
   consumer required.

The aggregator must handle both. Both are already defined by the sealed
components and must be consumed as-is.

### 3.2 Options considered

**Option A — OTel Collector as a separate process.**
Route the six OTel-emitting components through an OTLP exporter to a
Collector binary that persists to the aggregator's storage. Rejected: adds
a Go binary to pOS as a supervised system dependency, adds a network
listener, and gives us nothing we couldn't do in-process. The A1 property
is preserved (components just emit; Collector absorbs whether or not
storage is writable), but the cost is not worth it for a single-user local
system.

**Option B — In-process custom SpanProcessor + SpanExporter.**
Register a workspace-supplied `TracerProvider` in
`~/.pos/bootstrap.py` (the orchestrator's workspace bootstrap hook that
already exists for scope-runtime callback registration). The provider
installs a `BatchSpanProcessor` that feeds a custom `SpanExporter`, which
writes to the aggregator's storage. Because OTel Python's `get_tracer()`
returns a ProxyTracer with late binding, the six components route their
emissions through this exporter automatically once the provider is
installed — no amendment to any sealed component.

**Option C — File-tail only.**
Have every component (including the six OTel emitters) write OTLP JSONL
to disk, then have the aggregator tail all files. Rejected: would require
amending the six OTel-emitting components to add an
`OTLPJsonFileSpanExporter`. A1 correction forbids that amendment.
(Workspace bootstrap could install the exporter, which is workspace-level
and not a sealed-component amendment — but adds I/O overhead without
benefit over Option B.)

**Option D — Pull-model API.**
Aggregator polls each component for new spans via a query API. Rejected:
no component exposes such an API; doing so would require amendment.

### 3.3 Recommendation — Option B with file-tail for memory

- **For the six OTel-emitting components:** workspace bootstrap
  (`~/.pos/bootstrap.py` — already the hook where the orchestrator expects
  workspace code to register callbacks) installs a global
  `TracerProvider` with a `BatchSpanProcessor` wired to the aggregator's
  custom exporter. The aggregator's component process either lives in the
  orchestrator's Python address space (registering at startup) or owns the
  bootstrap itself.
- **For memory-system:** the aggregator tails the three JSONL sinks
  (`spans.jsonl`, `tokens.jsonl`, `audit.jsonl`) under memory's
  `data/observability/` directory, normalising each record shape into the
  aggregator's canonical schema at ingest. Memory runs as a library inside
  whichever process ingests; its JSONL sinks are the durable surface.
- **A1 correction held.** None of the seven components know about the
  aggregator. The six OTel components emit via the standard tracer; the
  tracer routes to whatever provider the workspace has configured, or
  no-ops if none. Memory writes to its JSONL files, independent of whether
  anything is reading them.

### 3.4 Handling aggregator downtime

The ingestion path must survive the aggregator being stopped, crashing,
or restarting. Three component cases:

1. **Six OTel components while aggregator is running.** The
   `BatchSpanProcessor` buffers up to `max_queue_size` spans (default
   2048) before dropping. If the custom exporter's `export()` call returns
   `FAILURE`, the batch is retried per OTel SDK semantics.
2. **Six OTel components while aggregator is stopped.** Two sub-cases:
   - If the aggregator lives in the same process as the orchestrator (and
     orchestrator is up): the exporter writes to a local spool file (a
     per-process append-only JSONL) and a background flusher replays it
     into the store. The spool file is the durable buffer.
   - If the aggregator is a separate process and the orchestrator is up:
     the processor's exporter becomes a thin writer to the spool file.
     The aggregator consumes from the spool.
3. **Memory-system while aggregator is stopped.** Memory's JSONL files
   accumulate unchanged. On aggregator restart, the tail resumes from a
   persisted byte offset. No records are lost.

**Recommendation:** aggregator runs inside the orchestrator process
(section 10.2 makes the case), with a spool-file buffer between the
in-process exporter and the store. On aggregator store failure, the
spool persists; on orchestrator restart, the spool drains on first boot.

### 3.5 A1 correction — why this design holds

The claim is that none of the seven sealed components need to know about
the aggregator. Three verifications:

1. **OTel Python late-binding proxy.** The six components import
   `opentelemetry.trace` and call `get_tracer()`. They receive a proxy
   that delegates to whichever provider is currently registered. Installing
   a provider at workspace bootstrap (before any component dispatches the
   first span) or later (the proxy picks it up on next use) makes their
   emissions land in the aggregator's exporter with zero code change on
   their side.
2. **Memory's file sinks.** Memory writes to its own JSONL files whether
   or not anyone reads them. A tailer running inside the aggregator is a
   read-side consumer; memory has no coupling to it.
3. **Workspace bootstrap hook.** Orchestrator's `~/.pos/bootstrap.py` is
   workspace code, not sealed-component code. Installing the TracerProvider
   there is workspace configuration — not an amendment.

No amendment to any of the seven components is required. **If the build
reveals otherwise, halt.**

### 3.6 Memory sink shape — soft flag

Memory emits its spans as hand-rolled minimal JSON — not OTLP JSON
encoding. Specifically memory's records have top-level `trace_id`,
`span_id`, `name`, etc., whereas OTLP JSON wraps them in
`resourceSpans[].scopeSpans[].spans[]`.

The aggregator accommodates this via a translator at ingest. No memory
amendment is needed; the translator is the aggregator's job. Flagging
this as a soft issue because a future memory-system maintenance window
could align memory's sink format with OTLP JSON for a cleaner contract.
Not required; not blocking.

---

## 4. Storage substrate — recommendation and rationale

### 4.1 Requirements the substrate must satisfy

- **Durable.** Survives process restart, crash, power loss.
- **Analytic.** Time-range scans (hours, days, months) with group-by
  aggregation need to return in sub-second time for a year of retained
  data at pOS-scale volume.
- **Low resource.** Single user, typical laptop; not a production database
  tier. Idle RAM footprint <100 MB, idle CPU <1%.
- **Local.** No network surface, no container, no hosted service.
- **SQL surface.** The NL→structured-query path generates SQL; having SQL
  as the native query language avoids needing a custom parser.
- **Pip-installable.** Python-native or stdlib-embeddable.

### 4.2 Options considered

| Option | Local | SQL | Analytic | Dep posture | Verdict |
|--------|------|-----|----------|-------------|---------|
| **Stdlib only (JSONL + Python reads)** | yes | no | no | zero | Rejected — query latency unacceptable past ~day |
| **SQLite** | yes | yes | row-oriented, slow on analytic | stdlib | Viable — slower on time-range scans |
| **DuckDB** | yes | yes | columnar, fast analytic | net-new dep | Recommended — matches the workload |
| **Jaeger / Tempo / Loki** | effectively no | vendor-specific | yes | heavy containers | Rejected |
| **Postgres / ClickHouse** | requires service | yes | yes | heavy dep | Rejected |

### 4.3 Recommendation — DuckDB, with SQLite as the fallback

**Primary recommendation: DuckDB.**

Rationale:
- Columnar storage compresses spans (heavily repeating attribute names
  and string values) 5-10× more efficiently than SQLite row storage.
- Vectorised query engine runs time-range + group-by queries over months
  of data in milliseconds, versus SQLite's slower-by-default behaviour on
  the same shape.
- Same install story as SQLite (single binary wheel, no daemon, no port).
- SQL interface matches the NL→structured-query path.
- MIT-licensed; mature enough in 2026 for single-user production use.

Trade-off surfaced:

- **Net-new dependency.** Soft flag to the owner. The permitted list is stdlib
  + pydantic + pyee + opentelemetry-api/sdk + PyYAML. Builder cannot add
  DuckDB silently.
- If the owner rejects DuckDB, the fallback is **SQLite**. SQLite is stdlib
  and works; the aggregator would have to lean more heavily on indexes
  and pre-aggregated rollup tables to hit sub-second query latency at
  scale. The research does not recommend SQLite as the primary, but it is
  not blocked by it.

### 4.4 Size projections

Rough envelope for a pOS user running an interactive session ~2 hours/day
plus background autonomous work ~4 hours/day:

- Scope-of-work: ~50 scopes/day × 4 events/scope × ~1 KB/event → 200 KB/day.
- Primary-persona: ~20 tick events + ~2 authoring/introduction/
  retirement events + per-turn injection events → ~50 KB/day.
- Objective-tracker: ~20 operations/day × ~0.5 KB/op → 10 KB/day.
- Orchestrator: ~100 heartbeats + 20 process events + 5 bind events →
  ~20 KB/day.
- Graceful-degradation: usually zero; during incidents, ~100 events/hour.
  Budget ~10 KB/day amortised.
- Memory-system: ~100 ingests/day × (1 span + 3–8 token rows + 1 audit
  entry) × ~1 KB → ~1 MB/day (dominated by raw-text payloads in span
  attributes).
- Aggregator's own self-observability: ~20 KB/day.

**Daily total: ~1.3 MB raw (memory dominates).**

At 90-day full-fidelity retention: ~120 MB raw.

DuckDB columnar compression typically achieves 3–5× on span-shaped data;
real footprint ~30–40 MB for 90 days. SQLite with indexes would land
closer to 150–200 MB for the same period.

At 12-month retention: ~1.5 GB raw → 300–500 MB DuckDB. Easily local-disk
viable; still worth a rollup strategy (§8) for query performance, not
space.

### 4.5 Why not keep memory's JSONL as the source of truth?

Alternative considered: the three memory JSONL files already exist; why
not just make the aggregator a query engine on top of those files plus
the six OTel components' on-disk spool?

Because:
- The six OTel components do not own durable on-disk sinks. Giving them
  one (the spool) is fine as a buffer, but a spool is not a query target —
  unordered, no index, grows unbounded.
- Analytic queries over JSONL require loading all of it into memory (or
  reading sequentially). Over months of retained data, this is too slow.
- The aggregator needs cross-component joins (e.g. find scopes that
  dispatched LLM calls that failed, during a degradation episode) —
  impossible without a relational query layer.

The durable store's role is not to *replace* component sinks. It is to
*aggregate* them into a queryable index. Component sinks remain the
durable publisher; the store is the aggregated index.

---

## 5. Storage schema sketch

The schema is normalised into four tables plus the token view. All tables
are DuckDB; each can be expressed in SQLite with one or two extra
indexes.

### 5.1 `spans` — one row per span

```
spans
  trace_id             VARCHAR NOT NULL        -- 32 hex chars
  span_id              VARCHAR PRIMARY KEY     -- 16 hex chars
  parent_span_id       VARCHAR
  name                 VARCHAR NOT NULL        -- e.g. pos.scope.invoke_scope
  tracer_name          VARCHAR NOT NULL        -- e.g. pos.scope_of_work
  component            VARCHAR NOT NULL        -- scope_of_work | primary_persona
                                               -- | objective_tracker | orchestrator
                                               -- | degradation | memory_system
  kind                 VARCHAR                 -- INTERNAL | CLIENT | ...
  start_time_unix_nano BIGINT NOT NULL
  end_time_unix_nano   BIGINT NOT NULL
  duration_ns          BIGINT AS (end_time_unix_nano - start_time_unix_nano) VIRTUAL
  status               VARCHAR                 -- OK | ERROR | UNSET
  status_message       VARCHAR
  attributes           JSON                    -- full attribute bag
  retention_class      VARCHAR                 -- normal | derived-only | ephemeral
                                               -- (inherited from span attrs; see §8)
  ingested_at          TIMESTAMP
```

Indexes (DuckDB zone-map + SQLite explicit):
- (`start_time_unix_nano`) — range scans.
- (`trace_id`) — tree reconstruction.
- (`name`) — group-by-span-name (latency, count).
- (`component`) — per-component views.

### 5.2 `span_events` — one row per event on a span

```
span_events
  event_id               BIGINT PRIMARY KEY AUTOINCREMENT
  span_id                VARCHAR NOT NULL REFERENCES spans(span_id)
  trace_id               VARCHAR NOT NULL
  name                   VARCHAR NOT NULL        -- e.g. pos.scope.state_changed
  time_unix_nano         BIGINT NOT NULL
  attributes             JSON
  ingested_at            TIMESTAMP
```

Indexes: (`trace_id`, `time_unix_nano`), (`name`).

### 5.3 `token_rows` — per-LLM-call cost attribution (v1.1 R12)

Populated from memory's `tokens.jsonl` and from `gen_ai.usage.*` attributes
on `chat {model}` spans from scope-of-work / graceful-degradation /
primary-persona.

```
token_rows
  row_id               BIGINT PRIMARY KEY AUTOINCREMENT
  trace_id             VARCHAR
  span_id              VARCHAR                  -- span that produced the call
  prompt_name          VARCHAR NOT NULL         -- v1.1 R12 grouping key
  model                VARCHAR NOT NULL
  input_tokens         INTEGER NOT NULL
  output_tokens        INTEGER NOT NULL
  call_count           INTEGER DEFAULT 1
  at_time              TIMESTAMP NOT NULL
  scope_id             VARCHAR
  component            VARCHAR                  -- inferred from tracer_name
  ingested_at          TIMESTAMP
```

### 5.4 `audit` — free-text rationale (memory's audit.jsonl; orchestrator's bind_refused with rationale; graceful-degradation narratives)

```
audit
  audit_id             BIGINT PRIMARY KEY AUTOINCREMENT
  at_time              TIMESTAMP NOT NULL
  operation            VARCHAR NOT NULL         -- e.g. supersession_inferred
  actor                VARCHAR NOT NULL         -- e.g. memory_system
  scope_id             VARCHAR
  subject_uuid         VARCHAR
  rationale            TEXT NOT NULL            -- the prose answer to "why"
  extras               JSON
  ingested_at          TIMESTAMP
```

Indexes: (`at_time`), (`scope_id`), (`operation`).

### 5.5 `ingest_cursors` — byte-offset / event-id checkpoints per source

Tracks the tail position per source file or per spool. A restart reads
from the cursor.

```
ingest_cursors
  source_id            VARCHAR PRIMARY KEY      -- e.g. "memory:spans"
  source_path          VARCHAR                  -- file path
  byte_offset          BIGINT NOT NULL
  last_record_time     TIMESTAMP
  updated_at           TIMESTAMP
```

### 5.6 Derived views for common queries

- `v_cost_by_prompt` — `GROUP BY prompt_name` over `token_rows` with
  input/output sums and estimated USD (workspace config supplies model
  pricing).
- `v_cost_by_prompt_daily` — same, windowed per day.
- `v_scope_tree` — recursive CTE that walks `parent_span_id` from a root
  span.
- `v_session_timeline` — spans ordered by `start_time_unix_nano` filtered
  to a given session_id (scope-of-work's `pos.session.id` attribute or
  derived from parent trace root).

### 5.7 Why not per-component tables?

Considered: one table per component, matching each sealed component's
emission namespace. Rejected — cross-component queries (the common case —
"what did orchestrator do while this degradation episode was active")
require union-all. A single `spans` table indexed by `component` is both
simpler and faster for the core query shape.

---

## 6. Query API specification

The aggregator exposes three query surfaces, matching three distinct
consumer archetypes.

### 6.1 Surface 1 — Structured query (Python, for programmatic callers)

Pydantic-typed query interface, returns pydantic-typed results. Used by
the primary persona, by scripts, and by the CLI.

```python
class SpanFilter(BaseModel):
    trace_ids: list[str] | None
    components: list[str] | None        # "scope_of_work" etc.
    name_pattern: str | None            # glob or regex
    time_range: tuple[datetime, datetime] | None
    attributes_match: dict[str, Any] | None   # exact attr equality
    has_event: str | None               # filter spans that have an event named X
    status: str | None                  # OK | ERROR

class QueryAPI:
    def find_spans(self, f: SpanFilter, limit: int = 100) -> list[Span]: ...
    def get_trace(self, trace_id: str) -> TraceTree: ...
    def get_span(self, span_id: str) -> Span | None: ...
    def find_events(self, f: EventFilter, limit: int = 100) -> list[Event]: ...
    def cost_by_prompt(
        self,
        time_range: tuple[datetime, datetime] | None = None,
        components: list[str] | None = None,
    ) -> dict[str, PromptCost]: ...
    def replay_session(self, session_id: str) -> SessionReplay: ...
    def replay_scope(self, scope_id: str) -> ScopeReplay: ...
    def replay_objective(self, objective_id: str) -> ObjectiveReplay: ...
    def audit_search(
        self,
        operation: str | None = None,
        scope_id: str | None = None,
        time_range: tuple[datetime, datetime] | None = None,
    ) -> list[AuditEntry]: ...
```

This is the canonical surface. All other surfaces compose over it.

### 6.2 Surface 2 — Natural language ("show me why you did X at time T")

The NL path is a small orchestration that uses Claude (via Max) to
translate user questions into structured queries.

**Shape:**

```
user NL question
   │
   ▼
┌────────────────────────────────┐
│ NL→structured-query prompt     │     [LLM call — Claude via Max]
│   inputs: NL question,         │
│           abbreviated schema,   │
│           enumerated filter    │
│           vocabulary           │
│   outputs: SpanFilter /        │
│            EventFilter /       │
│            replay_* call       │
└────────────────────────────────┘
   │ structured filter
   ▼
Structured query surface (§6.1) → rows
   │
   ▼
┌────────────────────────────────┐
│ Explanation-format prompt      │     [LLM call — Claude via Max]
│   inputs: rows, original       │
│           question             │
│   outputs: natural-language    │
│            answer with cited   │
│            span IDs            │
└────────────────────────────────┘
   │
   ▼
Final explanation (cited)
```

Two LLM calls per query: translation + formatting. Both carry a
`pos.prompt.type` attribute (`aggregator.nl_translate`,
`aggregator.nl_format`) so the aggregator's own cost is visible in the
per-prompt-type view — v1.1 R12 honoured reflexively.

**Reliability controls:**
- The translation LLM is constrained to emit one of a small set of
  structured outputs — it produces JSON matching one of the Pydantic
  query shapes, not free SQL. This prevents SQL injection and bounds the
  query surface.
- If translation fails validation, the aggregator returns a fallback
  message ("I couldn't parse that as a query — try 'show me spans where
  scope_id = X' or 'show me spans between T1 and T2'") rather than
  executing something unsafe.
- The translation prompt includes a one-paragraph schema description
  maintained by the aggregator (not hand-edited per-query).

**Anti-deskilling integration (v1.0):** the "show me why" surface is
specifically designed to teach. Formatting prompts include a convention
that every answer cites the source spans by name and ID, so the user
learns the vocabulary as they use it. This is the surface where
anti-deskilling and observability meet.

### 6.3 Surface 3 — CLI

A small `pos obs` CLI wraps Surface 1 for direct user access without
going through the primary persona:

- `pos obs trace <trace_id>` — dump a trace tree.
- `pos obs session <session_id>` — session replay JSON.
- `pos obs cost --by prompt --since 7d` — cost aggregation.
- `pos obs scope <scope_id>` — scope replay.
- `pos obs search "NL question"` — invokes the NL path (§6.2).
- `pos obs recent --component orchestrator --limit 50` — span browsing.

CLI output is JSON by default, with `--pretty` for table render.

### 6.4 Replay primitives (in Surface 1 shape)

Three primitives, each returning a structured timeline. Definition of
session, scope, and objective below.

```python
class SessionReplay(BaseModel):
    session_id: str
    started_at: datetime
    ended_at: datetime | None
    spans: list[Span]          # ordered by start_time
    events: list[Event]        # ordered by time
    cost_summary: dict[str, PromptCost]

class ScopeReplay(BaseModel):
    scope_id: str
    root_span: Span
    spans: list[Span]          # all descendants in the trace tree
    state_transitions: list[Event]   # scope state events
    cost_summary: dict[str, PromptCost]

class ObjectiveReplay(BaseModel):
    objective_id: str
    scope_bindings: list[ScopeReplay]  # scopes bound to this objective
    criterion_evaluations: list[Event]
    status_trail: list[tuple[datetime, str]]
```

### 6.5 What is a "session"?

The research-plan asks this explicitly. After reading the sealed
components, the research recommends the following definition:

A **session** is a continuous block of interactive user activity — one
open Claude CLI / desktop / Telegram DM — bounded by start (user-first-
prompt) and end (explicit close or idle-timeout). It is distinct from a
**scope** (a unit of autonomous work, which may span sessions or run
entirely background) and from a **trace** (an OTel concept, the tree of
spans rooted at one operation).

The mapping:
- A session typically correlates with a set of related traces — one per
  user turn, plus any background work initiated during the session that
  continues after.
- A session ID is a workspace-level attribute carried on spans as
  `pos.session.id`. Not yet emitted by any sealed component — but the
  primary-persona layer's `monitor_injection_event` is per-turn, and
  turn→session is a workspace-level concept. The aggregator can derive
  session-from-turn via its own session tracker.

**Open question for the owner:** should the aggregator derive session_id from
a session-management primitive (not yet built), or define its own
convention (e.g. group turn-events within an idle window of N minutes
into the same session)? Surfaced as §16 question 1. A convention is
workable for now.

### 6.6 Who calls the query surface?

The plan asks. All three consumer archetypes exist:
- **Primary persona** — calls Surface 1 and Surface 2 on user requests
  of the form "why did you X?" or "show me what happened at time T."
  The persona formats the result into its voice and returns it to the
  user. Anti-deskilling principle: the persona always cites the span
  IDs so the user can follow up.
- **User via CLI** — `pos obs` for direct inspection when the user wants
  the raw data rather than a persona summary.
- **Future UI layer** — not yet designed; calls Surface 1.

---

## 7. Replay semantics — decision and primitives

### 7.1 Two readings of "replay the decision chain"

The spec text (v1.0 Observability addition):

> The user can replay a session's decisions; the system can answer "why
> did you do X at time T."

Two readings exist:

**Reading A — Read-only playback.** Reconstruct, from stored records, the
ordered set of decisions the system made during a session, with their
cited inputs and outputs. The user reads a transcript of what happened.
No re-execution; the facts are exactly what was observed.

**Reading B — Deterministic re-execution.** Given a session's recorded
inputs, feed them back into the system and run it again, producing a new
output stream. The user observes the system making the decisions again.
Requires either (a) LLMs to be fully deterministic across time (they are
not), or (b) the aggregator to record every LLM output verbatim and
replay *inputs* through a playback harness that substitutes recorded
outputs for live LLM calls.

### 7.2 The research recommends Reading A — read-only playback

Reasoning:

1. **The spec criterion is satisfied by Reading A.** "Replay the decision
   chain" and "why did you do X at time T" both require reconstruction,
   not re-execution. The acceptance criterion explicitly says the
   reconstructible chain is the deliverable.
2. **Reading B is forbiddingly complex for pOS Phase 2.** It requires:
   (a) the aggregator recording every LLM input and output byte-for-byte
   (including full prompts, tool use loops, streaming chunks),
   (b) a playback harness that intercepts every LLM call in the
   sealed components and substitutes a recorded response, (c) amendments
   to every sealed component that makes an LLM call to route through
   that harness. Several of these violate A1 (amendment required). Plus
   the scope-of-work spec does not record LLM inputs at the granularity
   re-execution demands; only output tokens and `gen_ai.usage.*`
   attributes are captured on the `chat {model}` spans.
3. **The debugging value of Reading B is thin for single-user pOS.** It
   matters at scale (reproduce a flaky test, catch an LLM regression);
   it is not the shape of pOS's audit needs. The user's need is "tell
   me what happened and why," not "show me it happen again."

**Halt-and-signal this decision to the owner before proposal.** The research
interprets the spec toward Reading A, but the owner's explicit acknowledgment
is warranted before the proposal commits. See §16 question 3.

### 7.3 What Reading A produces

Given a session / scope / objective ID, the replay surface returns:

- **Ordered timeline** of spans with their start/end times, names, and
  attributes (decision inputs and outputs).
- **Events on each span** (state transitions, detection events,
  self-review verdicts) with their timestamps.
- **Audit entries** associated with the same scope / time range — the
  prose rationales for decisions.
- **Cost summary** per-prompt-type aggregated across the timeline.
- **Cited span IDs** — every element is traceable back to its source
  span in the aggregator's store, so the user can drill deeper.

The timeline is the deliverable. Rendering (human-readable prose vs
machine JSON) is a formatting concern layered on top.

### 7.4 Replay primitives exposed

Three named primitives in Surface 1 (see §6.4):

- `replay_session(session_id)` — returns the full ordered interaction
  and its background work.
- `replay_scope(scope_id)` — returns the decision chain of one
  autonomous scope, including sub-scope branches.
- `replay_objective(objective_id)` — returns every scope bound to that
  objective across its lifetime, with the criterion-evaluation history.

Each returns a `*Replay` pydantic model. The primary persona and the CLI
format it for consumption; the model itself is the stable interface.

---

## 8. Retention, pruning, retention-class propagation

### 8.1 Default retention — tiered

The spec is silent on retention policy. The v1.1 R2 accrual posture
("save everything except extremely ephemeral") suggests a default that
leans toward retain; but observability at every-span granularity over
years will grow.

Recommended default retention tier:

- **0–90 days: full fidelity.** All spans, events, audit entries, token
  rows preserved byte-for-byte. This matches memory-system's default
  retention window and the broader pOS posture of "recent is accessible."
- **90 days – 18 months: rolled up.** Per-day aggregations for cost
  (`cost_by_prompt_daily`), per-day event histograms, per-scope summaries
  retained; raw span attributes discarded for records where
  `retention_class = normal`. Retention-class `derived-only` records keep
  their structured facts; `ephemeral` records are not present in any tier
  (see §8.3).
- **> 18 months: rollups only + audit trail.** Only daily cost aggregations,
  scope/objective summaries, and audit entries whose `actor = user`
  survive. Everything else is pruned.

All thresholds workspace-configurable in a single YAML section:

```yaml
observability:
  retention:
    full_fidelity_days: 90
    rollup_days: 540          # 18 months
    permanent_audit: user_initiated
```

### 8.2 Rollup / summarisation strategy

A daily rollup job (scheduled via orchestrator's scheduling surface, not
cron — pOS framework rule) produces:

- `cost_by_prompt_daily` — materialised aggregation of `token_rows`.
- `scope_summary_daily` — per-scope counts, cost, outcomes.
- `component_summary_daily` — per-component span counts, error rates.
- `audit_by_day` — audit entry count per operation type.

Rollup tables are additive; raw tables are pruned on their own schedule.
Rollup runs are idempotent (re-running produces the same aggregation),
so the job tolerates restart/crash.

### 8.3 v1.1 R10 retention class propagation — the hard constraint

Memory's `retention-class` values (`normal`, `derived-only`, `ephemeral`)
have concrete aggregator implications.

**Memory's spans already carry retention class as an attribute** (from
memory-system's ingest path, on both the `ingest` span and the resulting
span tree). The aggregator honours this attribute on ingestion:

- `retention_class = normal` — full-fidelity storage, standard tiering.
- `retention_class = derived-only` — store the span (operation-level
  record: what happened, when, with what scope_id and cost) but **drop
  the `inputs` and `outputs` payload attributes** that carry raw text.
  Structured metadata is preserved; raw text is not.
- `retention_class = ephemeral` — store only a minimal audit stub
  (operation name, timestamp, scope_id; no attributes, no payload). The
  span exists in the aggregator only as a fact that "an ephemeral
  operation happened here"; no inspectable content. If a downstream
  query is asked to reconstruct an ephemeral episode, the answer is
  "this was an ephemeral operation; no record retained."

The spec for ephemeral ("allows immediate extraction for context but
does not persist") is honoured: the aggregator's minimal stub is the
audit-level "this happened," not persisted content. Flagged for owner's
confirmation at §16 question 4 — the alternative is to drop ephemeral
records entirely and store nothing. The research recommends the minimal
stub because "this happened at time T" is itself useful context even when
the content is ephemeral.

**Non-memory components do not carry a retention class today.** Their
spans default to `normal`. If a future component wants to mark its
emissions as `derived-only` or `ephemeral`, it sets the
`pos.retention.class` attribute on the span; the aggregator honours it
uniformly. This is an attribute contract, not a component amendment —
nothing breaks if no other component ever uses it.

### 8.4 Size projections revisited

With the tiering above and DuckDB columnar compression:

- 90 days full-fidelity: ~30–40 MB
- 540 days rollup-only: ~60–80 MB
- 540+ days audit-only: ~5–10 MB/year

Steady state after 2 years: ~130 MB. Single-digit GB even at 5-year
runway. Laptop-viable by a wide margin.

### 8.5 Upgrade interaction (v1.1 R1 semantic round-trip)

Under v1.1 R1, upgrades must preserve semantic round-trip equivalence —
pre-upgrade probe queries must return equivalent answers post-upgrade.
The aggregator's role:

- Raw span / event / audit / token data is content, not schema. It
  survives upgrades by default.
- Schema version is tracked in a `meta` table. Migrations are forward-
  only; a destructive migration requires a named migration path per the
  upgrade spec.
- The aggregator's own query surface is the probe target — the upgrade
  harness replays N representative queries (e.g. "cost for prompt X in
  the last 7 days," "spans in trace T") and compares results pre/post.

### 8.6 Workspace tunability

One YAML section in a single config file. Every retention knob is there:

```yaml
observability:
  retention:
    full_fidelity_days: 90
    rollup_days: 540
    permanent_audit: user_initiated
  storage:
    substrate: duckdb | sqlite       # decision recorded (§16 q2)
    path: ~/.pos/observability.db
  ingest:
    memory_sink_dir: ../memory-system/data/observability
    spool_path: ~/.pos/obs_spool.jsonl
    batch_size: 512
    batch_interval_seconds: 2
  redaction:
    patterns_path: ~/.pos/obs_redaction.yaml
```

---

## 9. Privacy and redaction

### 9.1 Sensitive content the aggregator stores

From surveying the seven components' emissions:

- **Memory system** — raw knowledge graph writes (episode text, sensitive
  personal content), extraction inputs, extraction outputs. The
  `emit_payloads: true` config surfaces these on spans; workspace can
  disable. Audit sink has supersession rationales and retention-class
  decisions.
- **Scope-of-work** — scope goals and result text if included as span
  attributes by the caller.
- **Primary-persona** — authoring contracts, self-review verdict text,
  introduction text (which may include personal tone-of-voice
  observations).
- **Orchestrator** — bind refusals include `cause_message` text.
- **Graceful-degradation** — narrative text rendered by Claude when
  explaining an outage; may include session context.
- **Objective-tracker** — objective text.

All of this is private. The aggregator stores it locally in a user-owned
file; no network egress. But accidental leakage into logs, debug dumps,
or the NL query surface must be prevented.

### 9.2 Redaction approach — deterministic pattern match, opt-in LLM judge

Two-layer redaction at ingestion:

- **Layer 1 — deterministic patterns.** A workspace-supplied YAML file
  (`~/.pos/obs_redaction.yaml`) lists regex patterns that are masked
  before attributes are written to the aggregator. Built-in patterns for
  obvious cases (strings matching `sk-...` or `ANTHROPIC_API_KEY` or
  email addresses). User-extensible.
- **Layer 2 — optional LLM judge.** Off by default. If on, at ingestion
  time, the aggregator sends a sample of span payloads through a
  lightweight Claude judge that flags additional PII. Layer 2 adds cost
  and latency; it is opt-in for users with high-sensitivity workloads.

Redaction is irreversible. Once a value is masked before storage, the
original is not recoverable from the aggregator. The component's own
sink (memory's JSONL; orchestrator's SQLite) retains the unredacted
original. The aggregator is the redacted view.

### 9.3 Retention class is not a privacy surface

Retention class (`normal`, `derived-only`, `ephemeral`) governs what the
aggregator persists, not whether the content is sensitive. Redaction is
the orthogonal privacy surface. Both apply; they answer different
questions.

---

## 10. Self-observability and process placement

### 10.1 Does the aggregator emit its own OTel?

Yes, but under a simple rule: the aggregator's own tracer uses a
namespace (`pos.aggregator.*`) and the aggregator's exporter filters out
spans in this namespace at ingest to prevent a feedback loop.

What it emits:

- `pos.aggregator.ingest_batch` — per-batch span with batch size, source,
  latency.
- `pos.aggregator.query` — per-query span with surface (structured / NL
  / CLI), latency, row count.
- `pos.aggregator.nl_translate` / `pos.aggregator.nl_format` — the two
  LLM calls for Surface 2. These carry `pos.prompt.type` so their cost
  is visible in the per-prompt-type view.
- `pos.aggregator.rollup` — per-rollup-job span with input rows,
  output rows, duration.
- `pos.aggregator.prune` — per-prune-job span with records dropped per
  table.

Ingest-time filter: spans whose `tracer_name` is `pos.aggregator.*` and
whose `ingest source` is the in-process OTel exporter are dropped *from
the ingest path* but logged to `~/.pos/logs/aggregator.out` so the
aggregator's own behaviour is diagnosable. Alternative considered: emit
aggregator spans to a separate sink (a small self-log file) and read them
as first-class records. Either works; the filter-in-ingest approach is
simpler.

### 10.2 Where does the aggregator run?

Three options:

1. **Inside the orchestrator process.** The aggregator is a module the
   orchestrator imports and initialises at startup. The TracerProvider is
   installed in the orchestrator's bootstrap, and the aggregator's
   ingestion runs as an asyncio task within the orchestrator's event
   loop.
2. **As a peer Python process, supervised by launchd/systemd.** Separate
   process with its own lifecycle. Communicates with the orchestrator
   via IPC for queries.
3. **As a lazy, query-on-demand library.** No always-running process —
   the aggregator is imported by anything that needs it, and it tails
   sinks on demand. Requires a background writer only for rollup and
   prune.

**Recommendation: Option 1 — inside the orchestrator process.**

Reasoning:
- Orchestrator already runs the primary-persona layer's
  `BackgroundWorkMonitor` (by prior architectural decision). Running the
  aggregator in the same process follows the established pattern.
- The OTel TracerProvider installed in the orchestrator covers every
  component imported by the orchestrator. There are no separate Python
  processes to coordinate.
- Single process = single failure domain. Existing graceful-degradation
  pause/resume hooks already exist; the aggregator inherits them.
- The aggregator is low-throughput (1–2 MB/day). It does not warrant its
  own process.

Trade-off: an aggregator crash crashes the orchestrator. Mitigation:
the ingest task is isolated with `try/except` at the top level, and
ingestion failures are spooled for retry rather than raised into the
orchestrator's main loop. Rollup and prune run on the orchestrator's
scheduled-task surface and are likewise isolated.

Memory-system's tail ingestion runs as another asyncio task in the same
process. Memory runs as a library (not a separate process); its JSONL
files are on disk; the tailer reads them. No coordination needed beyond
the cursor table.

---

## 11. Integration with primary-persona "show me why" queries

### 11.1 What the primary persona needs

From v1.1 R4 (bundled docs) + v1.0 anti-deskilling: the "show me why"
surface is part of the primary persona's conversational loop. The user
asks "why did you do X at time T?" and the persona answers with cited
facts.

The persona does not implement the query logic. It calls the aggregator's
NL surface (§6.2) and formats the result in its voice.

### 11.2 The call shape

```
user: "why did memory mark Alice's address as superseded yesterday?"
      │
      ▼
primary persona
  │ capability: observability.why(...)
  │ invokes aggregator.surface2_nl(question)
  ▼
aggregator
  │ translate(question, schema) → SpanFilter(operation="supersession_inferred",
  │                                          actor="memory_system",
  │                                          attributes_match={"subject": "Alice"},
  │                                          time_range=yesterday)
  │ execute filter → audit rows + linked spans
  │ format(rows, question) → cited prose
  ▼
primary persona
  │ receives cited prose
  │ adapts to its voice (preserving citations)
  │ returns to user
  ▼
user sees: persona voice + cited facts + span IDs they can drill into
```

The persona does not bypass the aggregator's formatting. The aggregator's
NL formatter produces the substance with citations; the persona's voice
is the wrapper.

### 11.3 Anti-deskilling integration

Per v1.0 anti-deskilling: every explanation teaches. The "show me why"
surface is where this is most visible.

Conventions the aggregator enforces:

- Every NL formatter output cites span IDs.
- The formatter prompt includes: "name the component, name the operation,
  name the rule/attribute that governed the decision. If a user follow-up
  is likely, suggest the next query."
- The CLI surface shows the same citations so the user can learn by
  reading.

This is the anti-deskilling four-component structure
(`what/why/where/how to change`) applied per-answer. Aggregator enforces
structure; persona adapts voice.

---

## 12. Acceptance-criterion coverage matrix

### 12.1 v1.0 Observability criteria (§"Significant additions" item 3 + audit §"Observability")

| Criterion | How the design satisfies it |
|-----------|-----------------------------|
| "Every autonomous action produces an auditable record" | Every sealed component emits spans; aggregator's ingest captures all into `spans`. Unit test: dispatch an autonomous scope; reconstruct the scope's action from aggregator records alone. |
| "The user can replay a session's decisions" | `replay_session(session_id)` — Surface 1 primitive; Surface 2 NL path for conversational access. |
| "The system can answer 'why did you do X at time T'" | Surface 2 NL path; formatter prompt structured to cite source spans. |
| Audit §Observability: "audit log completeness is verified by a sampled test that reconstructs a given action from its record alone" | Reconstruction test: given a span_id, the aggregator returns actor + timestamp + objective_id (via scope→objective binding) + inputs + outputs + tool calls. |

### 12.2 v1.1 deltas — Observability-relevant criteria

| Rev | Criterion | Coverage |
|-----|-----------|----------|
| R4 | Bundled docs for every component | Aggregator ships bundled docs alongside its module per the framework's Architectural-layer principle. |
| R10 | Per-episode retention class | Ingestion honours `pos.retention.class` attribute; `derived-only` drops payload, `ephemeral` retains minimal stub. |
| R11 | OTel as internal trace format | Aggregator's canonical schema is OTel-shape normalised from OTLP JSON and from memory's hand-rolled shape. |
| R12 | Per-prompt-type cost attribution | `cost_by_prompt` Surface 1 query; `v_cost_by_prompt` and `v_cost_by_prompt_daily` views. |

### 12.3 Cross-cutting — single action reconstruction

The canonical reconstruction test: given an autonomous action (say, a
memory ingest triggered from a scope dispatched by the primary persona),
the aggregator returns:

- `actor` — from `tracer_name` → `component`.
- `timestamp` — from `start_time_unix_nano`.
- `objective cited` — from `pos.scope.id` → scope's
  `parent_objective_id` (via objective-tracker's `bind_scope` span).
- `inputs` / `outputs` — from the span's `inputs` / `outputs` attributes
  (if `emit_payloads` is enabled on the source component; memory
  emits by default, configurable).
- `tool calls` — child spans of `kind=CLIENT` under the action's root
  span.

Every field traces to an observable record in the aggregator's store.
Verified in a test by dispatching a representative action and querying
the aggregator alone.

### 12.4 What this design does **not** cover

- **"Replay reproduces the decision chain" as deterministic re-execution**
  (Reading B in §7.1) — not covered. The design covers Reading A only.
  Flagged as halt-signal §16 q3.
- **Session-ID derivation** — there is no session-management primitive
  yet. The aggregator derives session_id from turn-grouping; if the owner
  wants a strict session primitive later, the aggregator adapts. Flagged
  as open question §16 q1.

---

## 13. Dependency map

### 13.1 Consumed emissions (inputs)

| Source | Transport | Shape | Notes |
|--------|-----------|-------|-------|
| scope-of-work | OTel in-process | spans (`pos.scope.*`), events, `chat {model}` child spans | Late-bound TracerProvider |
| primary-persona | OTel in-process | spans (`pos.persona.*`), events | Late-bound |
| objective-tracker | OTel in-process | spans (`pos.objective.*`), events | Late-bound |
| orchestrator | OTel in-process | spans (`pos.orchestrator.*`), events | Late-bound |
| graceful-degradation | OTel in-process | spans (`pos.degradation.*`), events | Late-bound; carries `pos.prompt.type` for v1.1 R12 |
| memory-system | JSONL file tail | `spans.jsonl`, `tokens.jsonl`, `audit.jsonl` | Hand-rolled minimal OTel-compat JSON; aggregator translates |
| (test infrastructure) | OTel in-process | spans in test namespace | Filtered out at ingest if not production |

### 13.2 Consumed APIs (process-level)

- Orchestrator's `~/.pos/bootstrap.py` hook (workspace-owned; not a
  sealed-component amendment).
- Orchestrator's scheduling surface for rollup / prune jobs (existing
  `LocalStateStore.append` event model extends naturally).

### 13.3 Consumers of the aggregator's query surface (outputs)

| Consumer | Surface |
|----------|---------|
| Primary persona (v1.1 R4 bundled-docs / "show me why") | Surface 1 (Python) + Surface 2 (NL) |
| User via CLI (`pos obs`) | Surface 3 |
| Future UI layer | Surface 1 |
| Self-upgrade framework (v1.1 R1 probe queries) | Surface 1 |
| Graceful-degradation (already reads `per_prompt_costs()` from scope-of-work; may later want aggregated view) | Surface 1 |
| Cost-governance layer (future) | Surface 1 (`cost_by_prompt`) |

### 13.4 Data-stores created by the aggregator

- `~/.pos/observability.db` (DuckDB or SQLite) — primary store.
- `~/.pos/obs_spool.jsonl` — durability buffer between in-process
  exporter and store.
- `~/.pos/logs/aggregator.out` — aggregator's own operational log (not
  ingested into itself).

---

## 14. Complexity estimate

The plan asks for an honest AI-time estimate. Comparable to graceful-
degradation (largest component so far) or slightly larger, in the 350–500
AI-minute ballpark.

Component-by-component:

| Workstream | AI-minutes |
|-----------|------------|
| Ingestion: OTel TracerProvider + custom SpanProcessor + SpanExporter | 40 |
| Ingestion: memory JSONL tailer with cursor table | 35 |
| Ingestion: spool file + drain-on-restart | 30 |
| Storage: DuckDB (or SQLite) schema + migrations | 40 |
| Storage: retention class honouring at ingest | 25 |
| Query Surface 1: Pydantic API + DuckDB queries + replay primitives | 60 |
| Query Surface 2: NL path (translate + format prompts + validators) | 50 |
| Query Surface 3: `pos obs` CLI | 25 |
| Retention: rollup job + prune job + scheduling | 40 |
| Privacy: redaction patterns + workspace YAML + tests | 25 |
| Self-observability: own span emission + ingest filter | 15 |
| Integration: bootstrap registration; orchestrator hosting | 25 |
| Documentation: architecture, data-flow, prose explanation, relationship map (v1.1 R4) | 35 |
| Testing: acceptance criterion coverage + reconstruction test + replay tests + NL accuracy tests | 60 |
| **Total** | **~505 AI-minutes** |

Slightly above the plan's 350–500 upper bound. The overage is driven by
the NL-path accuracy harness + replay primitive tests. If the owner deems the
NL surface optional for the first-pass build, ~50 minutes drops out and
the number lands firmly in the plan's ballpark.

This is AI-time, not human-engineer-time, per STATE.md rule 15 anchoring.

---

## 15. Prototyping priorities — questions only a prototype answers

1. **Ingestion backpressure under load.** What happens when
   `BatchSpanProcessor` batches arrive faster than DuckDB writes? Two
   dimensions to measure: (a) the default batch-processor queue size
   (2048) is too small for burst ingests; what queue size is right for
   pOS? (b) Does the spool file actually drain fast enough to keep up
   with steady-state emission, or does it grow? Run: dispatch 10 concurrent
   scopes each making 50 LLM calls; measure time-to-ingest p50/p95/p99.
2. **Query latency with 6 months of retained data.** At projected volume
   (~250 MB DuckDB, ~800K spans), does `cost_by_prompt` for the last 30
   days return in <500ms? Does `replay_scope` for a scope with 200 child
   spans return in <1s? DuckDB is the bet; verify it holds.
3. **NL-to-structured-query accuracy.** On a held-out set of 30
   representative user questions, what fraction does the translation
   prompt convert correctly? Hit rate < 70% is a proposal-failing number
   and motivates either a more constrained grammar or a larger model.
4. **JSONL tailer correctness under aggressive log rotation.** Memory's
   sinks are append-only; the tailer watches byte-offset. Does it survive
   memory-system being restarted, its files being cleared manually, or
   the directory being recreated? Simulate and measure.
5. **Retention-class ingest honouring.** Dispatch a scope that ingests
   one `normal`, one `derived-only`, one `ephemeral` episode. Query the
   aggregator — are the raw payloads correctly absent for the non-normal
   ones? Is `list_by_retention` preserving the correct class marker?
6. **Aggregator-in-orchestrator-process isolation.** Kill the DuckDB
   connection from under the aggregator mid-ingest. Does the orchestrator
   survive? Does the spool retain the in-flight batch? Does recovery
   work on next start?
7. **LLM-judge redaction accuracy.** If layer 2 redaction is enabled,
   how often does it false-positive (flag non-sensitive strings) or
   false-negative (miss API keys)? Only a prototype tells.

---

## 16. Open questions surfaced to the owner

Three halt-signals, three open questions. In order of urgency:

### Halt-signal — Hard halt

**Q3. Replay semantics: Reading A (read-only playback) or Reading B
(deterministic re-execution)?**

Research recommends Reading A (§7.2). Spec text is ambiguous enough that
the owner should confirm before proposal. Reading B requires amendments to
sealed components and is much more expensive.

### Halt-signal — Soft flag

**Q2. Storage substrate: add DuckDB as a net-new dependency?**

Research recommends DuckDB (§4.3). Permitted dep list is stdlib +
pydantic + pyee + opentelemetry-api/sdk + PyYAML. DuckDB is not on the
list. Fallback is SQLite (stdlib) if DuckDB is rejected; SQLite works,
but will be slower at analytic queries over months of retained data.

**Q4. Ephemeral retention: minimal stub or nothing at all?**

Research recommends minimal stub — a record of "an ephemeral operation
happened at time T under scope X, no content retained" (§8.3). Alternative
is to drop ephemeral records entirely. The v1.1 R10 text ("does not
persist") supports either; the research reads the stub as additive to
what R10 requires, not conflicting with it.

### Open questions — non-halting

**Q1. Session-ID derivation.**

Primary-persona's monitor emits `monitor_injection_event` per turn; no
session primitive exists. Options:

- (a) Aggregator derives session_id by grouping turn events within an
  idle window (default 30 min).
- (b) Primary-persona layer emits `pos.session.id` on spans; aggregator
  reads directly (this requires a session concept in primary-persona,
  not currently there).
- (c) Wait for a future session-management primitive and don't provide
  session replay in the first pass.

Research recommends (a) for the first pass — workable, implementable in
the aggregator without amending anything. Flags (b) or (c) as cleaner
long-term.

### Optional scope trim

**Q5. Is the NL surface (Surface 2) required for the first-pass build?**

The spec's "why did you do X" requirement can be met via Surface 1 +
persona formatting in the persona's own voice, bypassing the aggregator's
NL translate/format prompts. If the owner's goal is smallest first version,
Surface 2 drops out and ~50 AI-minutes go with it. If the goal is the
full anti-deskilling surface, Surface 2 stays.

---

## 17. Summary of recommendations

1. **Ingestion:** in-process custom SpanProcessor + SpanExporter
   registered via workspace `~/.pos/bootstrap.py` for the six OTel
   components; JSONL tailer for memory-system. No sealed-component
   amendment.
2. **Storage:** DuckDB with SQLite fallback. DuckDB requires owner's
   approval as a net-new dependency.
3. **Query surface:** three layers — structured Pydantic API (canonical),
   NL path with Claude via Max (anti-deskilling "show me why"), CLI.
4. **Replay semantics:** read-only playback (Reading A). Requires the owner's
   confirmation.
5. **Retention:** three-tier (90 days full / 540 days rollup / longer
   audit-only), workspace-configurable.
6. **Retention class:** honour at ingest; `derived-only` drops payloads;
   `ephemeral` keeps minimal stub.
7. **Process placement:** inside the orchestrator process, asyncio
   tasks for ingest + rollup + prune.
8. **Self-observability:** aggregator emits `pos.aggregator.*` spans;
   filter-in-ingest to prevent feedback.
9. **Privacy:** deterministic-pattern redaction at ingest; LLM-judge
   redaction as opt-in layer 2.
10. **Primary-persona integration:** persona calls aggregator's Surface 2
    for "show me why" requests; aggregator produces cited prose; persona
    adapts voice; spans IDs cited throughout to preserve anti-deskilling.
11. **Complexity:** ~505 AI-minutes. Slightly above the plan's 350–500
    ceiling; Surface 2 is the marginal 50 minutes and can be deferred if
    wanted the first-pass smaller.

---

## Sources

- [OpenTelemetry Python — SpanProcessor and exporter pipeline](https://opentelemetry-python.readthedocs.io/en/latest/sdk/trace.export.html)
- [DeepWiki — SpanProcessor and pipeline](https://deepwiki.com/open-telemetry/opentelemetry-python/3.3-spanprocessor-and-pipeline)
- [OpenTelemetry — Collector](https://opentelemetry.io/docs/collector/)
- [OpenTelemetry — Collector architecture](https://opentelemetry.io/docs/collector/architecture/)
- [OpenTelemetry — Collector configuration](https://opentelemetry.io/docs/collector/configuration/)
- [OpenTelemetry — OTLP File Exporter specification](https://opentelemetry.io/docs/specs/otel/protocol/file-exporter/)
- [OpenTelemetry Python — Late-binding proxy tracer](https://github.com/open-telemetry/opentelemetry-python/blob/main/opentelemetry-api/src/opentelemetry/trace/__init__.py)
- [OneUptime — Custom SpanProcessor patterns](https://oneuptime.com/blog/post/2026-01-30-opentelemetry-span-processors/view)
- [OneUptime — Business-specific span attributes](https://oneuptime.com/blog/post/2026-02-06-otel-custom-span-processor-business-attributes/view)
- [OneUptime — No Tracer Provider warnings fix](https://oneuptime.com/blog/post/2026-02-06-fix-no-tracer-provider-configured-warnings/view)
- [Johal.in — OpenTelemetry Python span attribute filtering 2026](https://johal.in/opentelemetry-python-traces-span-attribute-filtering-2026/)
- [SigNoz — Collector vs Exporter](https://signoz.io/guides/opentelemetry-collector-vs-exporter/)
- [Last9 — Collector vs Exporter](https://last9.io/blog/opentelemetry-collector-vs-exporter/)
- [SigNoz — Jaeger vs Tempo](https://signoz.io/blog/jaeger-vs-tempo/)
- [Last9 — Grafana Tempo vs Jaeger](https://last9.io/blog/grafana-tempo-vs-jaeger/)
- [Dash0 — Jaeger alternatives 2026](https://www.dash0.com/comparisons/jaeger-alternatives-for-tracing)
- [DuckDB — OTLP community extension](https://duckdb.org/community_extensions/extensions/otlp)
- [neogeografia — DuckDB observability and log analytics](https://neogeografia.wordpress.com/2023/08/02/observability-and-log-analytics-with-duckdb/)
- [Clay Smith — Cheap OpenTelemetry lakehouses with DuckDB](https://clay.fyi/blog/cheap-opentelemetry-lakehouses-parquet-duckdb-iceberg/)
- [Langfuse — Self-hosting](https://langfuse.com/self-hosting)
- [Langfuse — Self-hosting infrastructure](https://deepwiki.com/langfuse/langfuse-docs/9-self-hosting-infrastructure)
- [Langfuse — vs LangSmith](https://langfuse.com/faq/all/langsmith-alternative)
- [LangChain — Self-host LangSmith on Kubernetes](https://docs.langchain.com/langsmith/kubernetes)
- [MLflow — From Natural Language to SQL](https://mlflow.org/blog/from-natural-language-to-sql)
- [Bag of Words — Observability framework for text-to-SQL](https://dev.to/bagofwords/building-reliable-ai-analysts-an-observability-framework-for-text-to-sql-systems-25ln)
- [AIMultiple — Text-to-SQL LLM accuracy](https://aimultiple.com/text-to-sql)
- [OpenTelemetry — Traces concepts](https://opentelemetry.io/docs/concepts/signals/traces/)
- [SigNoz — Trace ID vs Span ID](https://signoz.io/comparisons/opentelemetry-trace-id-vs-span-id/)
