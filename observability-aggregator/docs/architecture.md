# Architecture — Observability Aggregator

## High-level diagram

```
                    ┌────────────────────────────────────────────────────┐
                    │              Sealed pOS components                 │
                    │                                                    │
   scope-of-work ───┤  trace.get_tracer("pos.scope_of_work")             │
                    │   │                                                │
 primary-persona ───┤  trace.get_tracer("pos_v2.primary_persona")        │
                    │   │   (ProxyTracer; late-binding)                  │
objective-tracker ──┤  trace.get_tracer("pos.objective_tracker")         │
                    │   │                                                │
   orchestrator ────┤  trace.get_tracer("pos.orchestrator")              │
                    │   │                                                │
graceful-degradation┤  trace.get_tracer("pos.degradation")               │
                    │   │                                                │
                    │   ▼                                                │
                    │   global TracerProvider (installed by aggregator)  │
                    │   │                                                │
                    │   BatchSpanProcessor                               │
                    │   │                                                │
                    │   AggregatorSpanExporter                           │
                    │   │  (filters pos.aggregator.* — self-obs)         │
                    └───┼────────────────────────────────────────────────┘
                        │
                        ▼
               ┌──────────────────────┐
               │  ~/.pos/spool.jsonl  │   (durability buffer)
               │  (append-only)       │
               └──────────┬───────────┘
                          │
                          ▼
                ┌──────────────────────┐                ┌──────────────────────────┐
                │  SpoolDrainer        │                │  Memory JSONL tailers    │
                │  (cursor-tracked)    │                │  (cursor-tracked)         │
                │  filters self-obs    │                │                           │
                │  extracts tokens     │                │  spans.jsonl  → spans     │
                │  honours retention   │                │  tokens.jsonl → tokens    │
                └──────────┬───────────┘                │  audit.jsonl  → audit     │
                           │                            └──────────┬───────────────┘
                           │                                       │
                           ▼                                       ▼
                ┌──────────────────────────────────────────────────────────┐
                │                       STORE                              │
                │           DuckDB primary  /  SQLite fallback             │
                │                                                          │
                │   spans · span_events · tokens · audit                   │
                │   ingest_cursors                                         │
                │   daily_rollup · monthly_rollup · yearly_rollup          │
                │   meta                                                   │
                └──────────────────────┬───────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌────────────────────┐    ┌──────────────────────────┐    ┌──────────────────────┐
│   QueryAPI         │    │   NLPath                 │    │   CLI: pos obs       │
│   (Pydantic)       │    │   (two-LLM, cited)       │    │   (thin wrapper)     │
│                    │    │                          │    │                      │
│ find_spans         │    │ translate(question)      │    │ find-spans           │
│ get_trace          │    │   ↓ pos.aggregator.nl_   │    │ get-trace            │
│ get_span           │    │     translate            │    │ cost-by-prompt       │
│ find_events        │    │   pos.prompt.type=       │    │ replay-{session,     │
│ cost_by_prompt     │    │     obs-nl-translate     │    │   scope, objective}  │
│ audit_search       │    │   ↓                      │    │ audit-search         │
│ replay_session     │    │ execute(filter)          │    │ why "..."            │
│ replay_scope       │    │   ↓                      │    │                      │
│ replay_objective   │    │ format(rows, question)   │    │                      │
│                    │    │   ↓ pos.aggregator.nl_   │    │                      │
│                    │    │     format               │    │                      │
│                    │    │   pos.prompt.type=       │    │                      │
│                    │    │     obs-nl-format        │    │                      │
│                    │    │   ↓                      │    │                      │
│                    │    │ CitedAnswer (cites IDs)  │    │                      │
└────────────────────┘    └──────────────────────────┘    └──────────────────────┘

                       ┌──────────────────────────┐
                       │  RetentionJob (idempotent)│
                       │                          │
                       │  0-7d   full fidelity    │
                       │  7-30d  daily + top-N    │
                       │  30-365d monthly         │
                       │  365d+  yearly / audit   │
                       └──────────┬───────────────┘
                                  │
                                  ▼
                              the STORE
```

## Module map

```
observability-aggregator/
├── src/
│   ├── __init__.py            — public exports
│   ├── config.py              — AggregatorConfig + RetentionConfig + IngestConfig
│   ├── schema.py              — Pydantic record types + retention-class enforcement
│   ├── store.py               — DuckDB / SQLite parity store
│   ├── ingest.py              — OTel SpanExporter, SpoolDrainer, JSONL tailers,
│   │                            install_for_workspace bootstrap helper
│   ├── api.py                 — structured Pydantic QueryAPI
│   ├── replay.py              — Reading-A replay primitives
│   ├── retention.py           — RetentionJob (decaying tiers + retention class)
│   ├── nl_path.py             — translate / format / NLPath (rule-based default)
│   ├── nl_corpus.py           — 25-question evaluation corpus + accuracy harness
│   └── cli.py                 — pos obs CLI
├── tests/
│   ├── conftest.py            — fresh_otel_provider fixture, store fixtures
│   ├── test_d1_otel_ingestion.py
│   ├── test_d2_memory_jsonl_tailer.py
│   ├── test_d3_storage.py
│   ├── test_d4_query_api.py
│   ├── test_d5_nl_path.py
│   ├── test_d6_replay.py
│   ├── test_d7_retention.py
│   ├── test_d8_cli.py
│   └── test_d9_self_obs_and_privacy.py
└── docs/
    ├── prose-explanation.md
    ├── architecture.md          ← (this file)
    ├── data-flow.md
    ├── relationship-map.md
    ├── api-reference.md
    ├── nl-reference.md
    ├── cli-reference.md
    └── bootstrap-registration-guide.md
```

## Process model

The aggregator is library-shaped, not service-shaped. There is no daemon. The recommended deployment is to run it inside the orchestrator's asyncio process: the orchestrator's `~/.pos/bootstrap.py` calls `install_for_workspace(...)`, which installs the OTel TracerProvider and starts the ingest pipeline (spool drainer + memory tailers) as background threads. The aggregator's own writes are non-blocking; queries are synchronous on the calling thread.

Alternative deployments — peer process, lazy library — are described in the research document. The current build supports the in-orchestrator pattern; the others require thin glue but no architectural change.

## Failure isolation

- A failed store insert per row logs and continues — never fatal at the row level.
- A failed JSONL tailer tick logs and retries on next poll — the cursor doesn't advance past a malformed line until the line is logged-and-skipped.
- A SpanExporter failure returns SpanExportResult.FAILURE — OTel's BatchSpanProcessor retries.
- Spool corruption is contained: the drainer skips malformed lines and advances past them; valid lines downstream still ingest.
- Substrate-unavailable (DuckDB lib missing) falls back to SQLite at config-resolution time.
