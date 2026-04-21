# Research Plan — Observability Aggregator

**Component:** Observability Aggregator — the consumer that subscribes to every sealed component's OTel emissions, stores them durably, serves queries including the spec's "why did you do X at time T," and supports session replay.
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for the observability aggregator such that:

- Every v1.0 Observability acceptance criterion can be honoured by a concrete implementation proposal — every action has an auditable record with full context; past sessions replay the decision chain end-to-end; "why did you do X at time T" queries return cited answers.
- The aggregator consumes every sealed component's OTel emissions without requiring amendment to any of them. A1 correction held: each component emits expecting no consumer, and this component is the consumer that lands.
- v1.1 R11 OTel-native format is the internal trace format (already emitted); v1.1 R12 per-prompt-type cost is already emitted by the components — the aggregator makes it queryable at workspace scope rather than per-component scope.
- The replay story is concrete: given a session ID and a timestamp, reconstruct the set of decisions + their citing context, rendered for human consumption.

## Starting position

- **Seven sealed components on `pos-v2`** — memory, scope-of-work, primary-persona layer, objective tracker, orchestrator, graceful-degradation, plus Phase-1's test infrastructure. All emit OTel spans, events, and metric-style heartbeats with `pos.*` namespaces.
- **No consumer exists yet.** Each component's test suite verifies emission succeeds with no consumer (A1 correction) — now the aggregator lands as the consumer.
- **Orchestrator and graceful-degradation each own their own small SQLite** for process-lifecycle state. The aggregator's store is different in purpose — it's the system-wide observability archive, not per-component state.
- **Python 3.13 dev target, `pos-v2` branch, permitted deps unchanged** (stdlib + pydantic + pyee + opentelemetry + PyYAML).
- **No amendments to any sealed component.** Aggregator subscribes via OTel's standard exporter/collector protocols.

## Questions the research must answer

### 1. Ingestion pattern

1. What's the subscription mechanism — an OpenTelemetry Collector instance, a direct in-process OTel SpanProcessor/LogRecordProcessor that feeds a storage layer, a pull-model API the aggregator polls, or a push-based gRPC/HTTP listener?
2. The components currently emit with `opentelemetry-api` + `opentelemetry-sdk` only. Do they need a collector-exporter added (e.g. OTLP), or is there a no-network in-process subscription path?
3. How does the aggregator survive component restart — if memory emits during a brief aggregator downtime, is the emission lost, buffered, or re-emitted on next consumer startup?

### 2. Storage

4. What's the storage substrate? Options: dedicated SQLite (consistent with Phase 1/2 pattern); DuckDB (columnar — faster analytic queries over long time ranges); a purpose-built trace store (Jaeger, Tempo); append-only log files with an index. For a single-user local-first pOS, which is the right trade-off?
5. What's the retention policy? Options: retain everything forever; tier by age (last 90 days full-fidelity, older rolled into summary); configurable per-event-type. The spec is silent — what default matches the "knowledge-is-valuable / extremely-ephemeral-only-discarded" posture from v1.1 R2?
6. What's the schema — flat table with OTel fields as columns, normalised (traces, spans, events, attributes as separate tables), or JSONB per record with extracted indexes on common query dimensions (timestamp, trace_id, attribute names)?

### 3. Query surface

7. What's the query API for "why did you do X at time T" — a structured query DSL over spans and events, free-text search with NL-to-SQL translation via Claude, a hybrid (structured filters + text-search body)?
8. How does the aggregator surface cost attribution (v1.1 R12) at workspace level — sum of `pos.prompt.type=<name>` tokens across components, grouped by time range?
9. What's the API for session replay — given a session_id, return the ordered chain of spans + events + associated inputs/outputs that reconstruct the session? What's a "session" exactly — an interactive session (session the user types into) or a scope execution (a unit of autonomous work)?
10. Who calls the query surface — the primary persona on "show me why" requests, the user directly via a CLI, a future UI layer, all three?

### 4. Replay semantics

11. What does "replay reproduces the decision chain" mean concretely — a deterministic re-execution against recorded inputs (true replay), or a faithful reconstruction of what was observed (read-only playback)? The latter is cheaper and sufficient for the spec; the former is more useful for debugging but forbiddingly complex.
12. Are there replay primitives (replay span hierarchy; replay per-scope; replay per-objective) that should be exposed, and what does each look like in the query API?

### 5. Retention + pruning + archival

13. How does the aggregator handle size growth? At steady state with all seven components emitting every operation, what's the projected growth rate for a typical pOS user? The research should estimate.
14. Is there a summarisation / roll-up strategy — turn month-old detail into week-level summaries so historical queries still work but storage stays bounded?
15. How does pruning interact with v1.1 R1 semantic round-trip upgrade — if a user upgrades pOS at time T, must the aggregator's pre-upgrade records survive the upgrade?

### 6. Privacy and retention class

16. Components emit sensitive content (memory's actual knowledge graph writes; scope-of-work's scope goals and results; persona-layer's authoring decisions). The aggregator stores all of this. How does retention class (v1.1 R10 per-episode retention class on memory) propagate to the aggregator's storage — do sensitive spans carry a `pos.retention.class` attribute the aggregator honours when pruning/summarising?
17. Is there a redaction path — specific attribute values that should be masked before storage (e.g. API keys accidentally in tool call args)? Deterministic pattern match + optional LLM-judge?

### 7. Observability of the observability aggregator

18. Does the aggregator emit its own OTel (subscribing to itself would create an infinite loop or just a silent skip)? What does self-observability look like — lifecycle events, ingestion rates, query latencies?
19. Where does the aggregator run — inside the orchestrator process (like the monitor), as a peer process, as a separate daemon with its own launchd supervision? Each has implications for startup order and failure isolation.

### 8. Integration with primary-persona "show me why" queries

20. v1.1 R4's bundled-docs principle means the aggregator's query surface must be usable by a non-technical user. "Show me why you did X at time T" should land naturally in the primary persona's conversational surface. What does the persona-to-aggregator call shape look like — the persona calls the aggregator, receives a structured result, and formats it for the user conversationally?
21. How does this interact with anti-deskilling (v1.0 user-facing principle) — the "show me why" surface is deliberately designed to teach the user how the system thinks, not just produce an answer.

## Constraints the research must respect

- **Python-native.** stdlib preferred; permitted runtime deps unchanged. Anything else halt-and-signal.
- **No amendments to any of the seven sealed components.** Aggregator subscribes via standard OTel mechanisms; if the build reveals an amendment is needed, halt-and-signal.
- **Zero carryover from current pOS.** Current-pOS logging machinery is not a reference.
- **Max-first.** LLM inference inside the aggregator is unexpected but acceptable for "why did you do X" natural-language translation — uses Claude via Max.
- **A1 correction held rigorously.** Every sealed component was built assuming no consumer; the aggregator arriving does not require them to know about it.
- **No personas in pOS core.**
- **Halt-on-deviation.** Surface rather than invent.
- **ODD-compatible** — every recommendation traces to a spec objective; untestable options noted.
- **v1.1 R10 retention class must be honoured** — derived-only and ephemeral episodes have different aggregator storage implications than normal ones.

## Deliverable — what the research document must contain

A markdown document at `components/observability-aggregator/research.md` with:

1. **Survey of existing patterns** — OTel Collector architecture; Jaeger/Tempo/Loki storage patterns; DuckDB for analytic observability; single-user local-first tracing patterns; LangSmith/LangFuse single-tenant architectures; OpenTelemetry SpanProcessor in-process patterns.
2. **Recommended design shape** — for each of the eight question groups, options considered, recommended option, rationale.
3. **Acceptance-criterion coverage** — mapping each v1.0 Observability criterion and relevant v1.1 revisions to design pieces.
4. **Ingestion architecture** — in-process subscription vs OTLP collector, with rationale based on pOS being single-user local-first.
5. **Storage schema sketch** — concrete table layout with partitioning/indexing strategy, size projections for a typical user.
6. **Query API specification** — structured filter + text-search; per-scope / per-objective / per-session replay primitives; cost-attribution aggregation endpoint.
7. **Retention/pruning strategy** — default retention policy; summarisation roll-ups; workspace tunability.
8. **Privacy + retention-class propagation** — how v1.1 R10 retention class interacts with aggregator storage.
9. **Dependency map** — consumed emissions from all seven sealed components; consumers of the aggregator's query surface (primary persona "show me why" endpoint; future UI; user CLI).
10. **Complexity estimate** — AI-time, honest. Expected comparable to graceful-degradation or slightly larger; ballpark 350–500 AI-minutes.
11. **Prototyping priorities** — questions only a prototype can answer (ingestion backpressure under load; query latency with 6 months of retained data; NL-to-structured-query accuracy).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies throughout.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
