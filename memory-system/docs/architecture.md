# Memory-system — architecture (full build)

The pOS v2 memory system is a Python-native knowledge store built on
Graphiti (a temporal knowledge graph engine) with embedded Kuzu, using
Claude via Anthropic Max for all LLM-driven work and local Ollama for
embeddings. It adds ten adaptation layers on top of the raw Graphiti
engine to satisfy the pOS spec (objectives v1.0 + v1.1 addendum).

```
                             ┌────────────────────────────────────┐
                             │  caller (Python process / FastAPI) │
                             │  • scripts/eval_full_system.py     │
                             │  • scripts/poa_demo.py             │
                             │  • scripts/upgrade_harness_demo.py │
                             │  • HTTP client to :9876            │
                             └───────────────┬────────────────────┘
                                             │
                                             │ in-process: MemoryAPI
                                             │ out-of-process: HTTP /ingest /search
                                             │
                                             v
    ┌────────────────────────────────────────────────────────────────┐
    │                 src/memory.py — MemoryAPI                      │
    │                                                                │
    │  ingest(body, ..., scope_id, retention_class) -> IngestResult  │
    │  search(query, ..., at_time, anchor_node_uuid)  -> [SearchHit] │
    │  list_scope(scope_id) -> [EpisodeRef]                          │
    │  list_by_retention(cls) -> [EpisodeRef]                        │
    │                                                                │
    │  wires D5..D10 around graphiti.add_episode / .search           │
    └──┬────────────┬───────────┬────────────┬────────────┬──────────┘
       │            │           │            │            │
       v            v           v            v            v
  ┌────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │   D5   │  │   D6    │  │   D7    │  │   D8    │  │  D10    │
  │ephemer-│  │ scope   │  │ observ- │  │temporal │  │retention│
  │ality   │  │ mapper  │  │ ability │  │ wrapper │  │ tagger  │
  │filter  │  │ (mock)  │  │ emitter │  │         │  │         │
  └────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
       │            │           │            │            │
       │            │           │            │            │
       v            v           v            v            v
  ┌─────────────────────────────────────────────────────────────┐
  │               Graphiti (graphiti-core 0.28.2,               │
  │               PINNED with KuzuDriver patches)               │
  │  • add_episode  • search                                    │
  │  • TokenUsageTracker (feeds D7)                             │
  └───┬────────────────┬─────────────────────┬──────────────────┘
      │                │                     │
      v                v                     v
 ┌──────────┐   ┌──────────────┐       ┌──────────────────┐
 │Anthropic │   │   Ollama     │       │  Kuzu (embedded) │
 │ Claude   │   │ (local,      │       │  single-file DB  │
 │ Haiku 4.5│   │  OpenAI-     │       │  data/kuzu_db    │
 │ (Max)    │   │  compat)     │       │  FTS + HNSW      │
 └──────────┘   │  nomic-embed-│       │  bitemporal edges│
                │  text 768d   │       └──────────────────┘
                └──────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │  D9 upgrade harness  (src/upgrade.py)                        │
  │  • snapshot(db)  • run_probe_set(memory)  • compare(pre,post)│
  │  Runs OVER memory; not in the hot path.                      │
  └──────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │  D11 process-of-arrival  (src/process_of_arrival.py)         │
  │  Producer (mock) → Receiver → memory.ingest ×2               │
  │  • StreamLog.summarise (Claude) → derived-only episode       │
  │  • outcome → normal episode                                  │
  │  Soft dependency: real producer is the dispatch primitive.   │
  └──────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │  D12 chaos-durability  (scripts/chaos_durability.py)         │
  │  Three scenarios: kill-mid-ingest, kill-mid-query, WAL       │
  │  recovery. Runs as subprocesses to exercise Kuzu's file      │
  │  lock and WAL behaviour.                                     │
  └──────────────────────────────────────────────────────────────┘
```

## Pipeline on `memory.ingest(body, ...)`

1. **D5 ephemerality filter** (`src/ephemerality.py`): the rubric in
   `config/memory.yml` is applied. Sources matching the narrow
   exclusion set (CPU readings, ticking clocks, volatile UI state,
   transient telemetry) are discarded at the gate — no LLM calls, no
   persisted state. An audit entry (`D7`) records the discard.
   Everything else proceeds.

2. **D6 scope-of-work mapper** (`src/scope.py`): the caller-supplied
   `scope_id` is resolved through the `ScopeSource` interface (mock
   implementation today; real scope primitive later). The scope_id
   becomes Graphiti's `group_id`, so filtering by scope in retrieval is
   the native `group_ids` parameter. The mock auto-registers unseen
   scopes; a real implementation will reject them.

3. **D10 retention-class plan** (`src/retention.py`): the caller
   supplies `retention_class` (default: `normal`). `ephemeral`
   short-circuits — nothing persists beyond this call's return value.
   `derived-only` proceeds but the post-ingest step scrubs the raw
   text from the Episodic node.

4. **Graphiti extraction**: Graphiti's standard pipeline runs —
   `extract_nodes.extract_text` → `extract_edges.edge` →
   `dedupe_nodes.nodes` → `dedupe_edges.resolve_edge`. Claude Haiku
   4.5 is the LLM; Ollama embeds each new node summary and edge fact.
   Kuzu stores the result with bitemporal metadata.

5. **D10 post-ingest enforcement**: the episode is tagged with its
   retention class (new `retention_class` column added via
   `ALTER TABLE ADD IF NOT EXISTS` in `src/factory.prepare_graphiti`).
   For `derived-only`, the `content` field is scrubbed to empty.

6. **D7 observability emission** (`src/observability.py`): a span
   wraps the whole operation (inputs, outputs, episode_uuid, scope_id,
   retention_class, ephemerality rule). Token rows are written with
   per-prompt-type breakdown (satisfying v1.1 R12). Audit entries
   record supersession, retention decisions, cascade halts.

## Pipeline on `memory.search(query, ...)`

1. **D8 temporal-filter wrapper** (`src/temporal.py`): if `at_time` is
   supplied, the wrapper produces a Kuzu-compatible `SearchFilters`
   encoding *valid_at <= T AND (invalid_at > T OR invalid_at IS NULL)*.
   The wrapper exists because graphiti-core 0.28.2's compound inner
   list collapses the OR into an AND in Kuzu (see `src/temporal.py`
   docstring and `scripts/diag_temporal2.py` for the bug diagnosis).

2. **D6 scope filtering**: if `scope_ids` are supplied, they become
   Graphiti's `group_ids` parameter — native filtering, no additional
   query rewriting.

3. **Graphiti search**: hybrid FTS + HNSW on Kuzu, reranked by RRF,
   optionally node-distance-reranked via `center_node_uuid` for
   context-aware queries (v1.1 R9).

4. **D7 span**: every search emits a span with the query, scope_ids,
   anchor, at_time, and results_count.

## Which files contain which deliverables

| Deliverable | File(s) | Role |
|-------------|---------|------|
| D5 ephemerality filter | `src/ephemerality.py`, `config/memory.yml` | Rule-based exclusion at ingest. |
| D6 scope-of-work mapper | `src/scope.py` | Mock scope registry; wired-ready for real primitive. |
| D7 observability emission | `src/observability.py` | OTel-shaped spans, token rows, audit entries — JSONL sinks. |
| D8 temporal-filter wrapper | `src/temporal.py` | `active_at(T)`, `known_at_system_time(T)`, `valid_at_or_before(T)`. |
| D9 upgrade-fidelity harness | `src/upgrade.py`, `scripts/upgrade_harness_demo.py` | Snapshot, probe replay, drift compare. |
| D10 retention-class tagger | `src/retention.py`, `src/factory.py` | `ALTER TABLE ADD` column; per-episode tag + optional scrub. |
| D11 process-of-arrival | `src/process_of_arrival.py`, `scripts/poa_demo.py` | Stream summariser + dual ingest (outcome + reasoning). |
| D12 chaos-durability | `scripts/chaos_durability.py`, `scripts/_chaos_workers/*` (generated) | Subprocess SIGKILL + WAL recovery scenarios. |
| D13 bundled docs | `docs/*.md` | This file, prose-explanation, deliverables-d5-d13, data-flow, relationship-map, chaos-durability-report. |
| Wired-together API | `src/memory.py` (MemoryAPI) | Combines D5..D10 into one ingest+search surface. |

## Two run shapes (both produce identical behaviour)

**Library mode** (`MemoryAPI` constructed in-process): `src.factory.
make_graphiti()` builds the Graphiti instance; the caller wraps it
with `MemoryAPI(graphiti, scope_source=..., emitter=...)`. Tests,
evals, and the chaos runner use this shape. Kuzu holds a file-level
lock for the lifetime of the driver; the same process cannot re-open.

**Service mode** (`src/service.py` + `launchd/` plist): a long-lived
FastAPI process holds the Graphiti instance behind `/health`,
`/ingest`, `/search`, `/token-usage`. Auto-start via launchd. The
full build has not yet extended the service endpoints to cover
retention, scope listing, and upgrade endpoints — the library
surface is the reference; service endpoints are additive wrappers
when the dispatch primitive and HTTP consumers arrive.

## What is out of scope for this component

Per the brief, the following adjacent primitives are NOT memory's
scope and are NOT built here:

- **Scope-of-work primitive runtime** — D6 ships a mock that the real
  primitive replaces by swapping the `ScopeSource` injection.
- **Primary persona loader** — retrieval callers connect later.
- **Dispatch primitive** — D11 ships a receiver with a mock producer;
  real dispatch replaces the mock.
- **Observability aggregator** — D7 emits OTel spans without assuming
  any consumer exists (A1 correction).
- **Self-upgrade framework** — D9 ships standalone probe+compare
  machinery; the framework that actually runs the upgrade (pip
  install, schema migration, etc.) plugs into this harness when built.

## Why Graphiti + Kuzu, not something else

Reason unchanged from the prototyping phase (see `docs/prose-
explanation.md`): Graphiti is the only candidate surveyed that
natively implements bitemporal time-lock (v1.1 R5), pointered
supersession with audit edges (R6), and first-class namespace
partitioning (scope-of-work). Kuzu is the embedded graph DB Graphiti
targets out of the box. Neither was modified; both are stock, with
two documented local patches in `src/factory.py` for KuzuDriver bugs
in 0.28.2.
