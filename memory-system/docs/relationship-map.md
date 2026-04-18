# Memory-system — relationship map

How the memory component connects to the other pOS primitives, as
currently shipped and as designed to connect when those primitives
land. Every adjacent primitive is listed here along with the state of
its wiring today.

## Adjacent primitives matrix

| Primitive | Status | Memory's contact surface | How it wires in |
|-----------|--------|-------------------------|-----------------|
| **Scope-of-work runtime** | NOT BUILT | `src/scope.py::ScopeSource` protocol | Replace `MockScopeSource` with the real implementation at `MemoryAPI` construction — one line. |
| **Primary persona loader** | NOT BUILT | Retrieval is invoked in-turn by the persona | Persona calls `MemoryAPI.search(query, scope_ids=[current_scope], anchor_node_uuid=...)`. No changes to memory needed. |
| **Dispatch primitive** | NOT BUILT | `src/process_of_arrival.py::StreamLogProducer` protocol | Dispatch runtime implements `StreamLogProducer` and hands each completed log to a `ProcessOfArrivalReceiver`. Mock is replaced at the single wiring site. |
| **Observability aggregator** | NOT BUILT (A1 correction: NOT assumed) | `data/observability/*.jsonl` append-only files | Aggregator reads the three JSONL files (or tails them via an OTel collector). No online consumer is required; memory publishes without caring who subscribes. |
| **Self-upgrade framework** | NOT BUILT | `src/upgrade.py` functions — `snapshot`, `run_probe_set`, `compare`, `run_upgrade_harness` | Upgrade framework calls `snapshot(db)`, runs pip install + migrations, then runs the probe subprocess and calls `compare(pre, post)`. |
| **Event log** | NOT BUILT | N/A — memory does NOT write to an event log | If an event log is built later, it can subscribe to memory's observability emissions; memory has no direct dependency. |

## What memory provides to callers

Today:

- `MemoryAPI.ingest(...)` — the ingest surface, unified across D5–D10.
- `MemoryAPI.search(...)` — all four retrieval modes (semantic,
  multi-hop, context-aware, temporal) through one call.
- `MemoryAPI.list_scope(scope_id)` — enumerate a scope's episodes.
- `MemoryAPI.list_by_retention(cls)` — enumerate by retention class.
- `MemoryAPI.retention_class_of(episode_uuid)` — inspect class.
- JSONL files at `data/observability/` — spans, tokens, audit.
- Kuzu graph at `data/kuzu_db` — bitemporal edges with `valid_at`,
  `invalid_at`, `created_at`, `expired_at` plus the new
  `retention_class` column on Episodic.

## What memory depends on

Hard (build-time) dependencies:

- Graphiti 0.28.2 (`graphiti-core[anthropic,kuzu]>=0.28.2`),
  PINNED with the two KuzuDriver patches in `src/factory.py`.
- Kuzu ≥ 0.11.2.
- Anthropic SDK ≥ 0.39 (Claude via Max).
- Local Ollama with `nomic-embed-text` (default).

Runtime dependencies:

- Anthropic API key in `ANTHROPIC_API_KEY` (env var).
- Ollama reachable at `OLLAMA_BASE_URL` (default
  `http://localhost:11434/v1`).

## Cross-component invariants

- **Memory emits observability; it does not consume.** A future
  aggregator subscribes; memory ships shippable without one.
- **Memory uses scope_id but does not own it.** The scope primitive
  owns the definition, budgets, and success criteria; memory records
  the scope_id as a foreign key and enumerates by it.
- **Memory accepts retention class at ingest but does not dictate it.**
  The caller (primary persona, dispatch, direct invocation) chooses
  `normal`, `derived-only`, or `ephemeral` per ingest.
- **Memory does NOT invoke the primary persona.** Retrieval is a
  passive surface; the persona calls it, not the other way around.
- **Memory does NOT schedule work.** Scheduling is the orchestrator's
  concern; memory's durability matters for whatever the orchestrator
  writes into it.

## When each adjacent primitive lands

The wiring change at each landing is minimal because the abstraction
points were chosen deliberately during the full build:

```
scope-of-work primitive ─────►  replace MockScopeSource at MemoryAPI
                                 construction (single call site)

primary persona loader ──────►  no change to memory; caller binds
                                 persona-owned context (anchor_node_uuid,
                                 current scope_ids) into search calls

dispatch primitive ──────────►  dispatch_runtime.on_complete(log) ==
                                 receiver.receive(log); mock producer
                                 is removed

observability aggregator ────►  aggregator tails data/observability/*.jsonl
                                 (or an OTel collector is added); memory
                                 code unchanged

self-upgrade framework ──────►  framework wraps src/upgrade.py's
                                 snapshot + run_probe_set + compare
                                 into its upgrade pipeline
```
