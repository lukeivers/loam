# What we built and why — prose explanation (full build)

The pOS v2 memory system stores what the system has ever known so
the primary persona can ask for it later — the right thing, at the
right time, in the right context. "What it has known" means
conversations, decisions, research, work, observations; not just
structured records. "The right time" means distinguishing what was
true then from what is true now.

This document is the full-build story. The prototyping phase (D1–D4)
answered whether Graphiti on Kuzu with Claude-via-Max and local
Ollama embeddings could meet the spec; it could. The full build adds
the nine adaptation layers the spec requires on top of the raw
engine and ships them as one coherent Python module.

## The ten adaptations, one sentence each

1. **Ephemerality filter (D5)** — throws away transient telemetry at
   the ingest gate so memory never fills with CPU readings and UI
   scroll events.
2. **Scope-of-work mapper (D6)** — attributes every memory entry to
   the scope of work it belongs to, so retrieval can be scoped.
3. **Observability emission (D7)** — emits OTel spans, token rows,
   and audit entries to durable JSONL sinks, without assuming any
   consumer exists.
4. **Graphiti MCP hosting (D4, pre-existing)** — the long-lived
   FastAPI service holding the Kuzu connection, already shipped.
5. **Temporal-filter wrapper (D8)** — repairs graphiti-core's broken
   compound temporal filter under Kuzu so "what was true at T" works.
6. **Upgrade-fidelity harness (D9)** — replays a probe set pre- and
   post-upgrade and reports drift; snapshots the DB pre-upgrade for
   physical reversibility.
7. **Retention-class tagger (D10)** — lets privacy-sensitive sources
   store structured facts without leaving raw text (`derived-only`).
8. **Synthetic retrieval test set (D2, pre-existing)** — the
   fabricated Aldermere world and 44 Q/A pairs used to evaluate
   retrieval quality and drive the upgrade harness.
9. **Process-of-arrival capture (D11)** — summarises background
   dispatch reasoning streams via Claude and ingests them alongside
   outcomes, so memory preserves *how* a conclusion was reached.
10. **Bundled documentation (D13)** — this directory; prose,
    architecture, data flows, relationship map, chaos report.

## How the pieces connect

A caller constructs a `MemoryAPI(graphiti, scope_source, emitter)`
and calls `await memory.ingest(body, ...)` or
`await memory.search(query, ...)`. Inside `ingest`, the body passes
through the D5 ephemerality filter (discard or proceed), the D6
scope attribution (the caller's `scope_id` becomes Graphiti's
`group_id`), the D10 retention plan (`normal` / `derived-only` /
`ephemeral`), and the D7 span wrapping the whole operation. For
`search`, the D8 temporal wrapper translates an `at_time` argument
into a Kuzu-compatible `SearchFilters`; `scope_ids` are native; the
anchor (`anchor_node_uuid`) is Graphiti's `center_node_uuid` for
context-aware reranking.

D11 and D9 live one layer up. D11 is a receiver that takes
stream-of-consciousness logs from (eventually) the dispatch
primitive, summarises the stream via Claude, and calls `memory.ingest`
twice — once for the final outcome and once for the summary. D9 is
the harness that snapshots the DB, replays the test set pre- and
post-upgrade in separate subprocesses, and emits a drift report.

The four soft dependencies — scope-of-work primitive, primary persona
loader, dispatch primitive, observability aggregator — each have a
wiring point. Each is replaced at one construction site when its
primitive lands.

## What improved in the full build vs the prototype

- **Temporal retrieval works now.** Prototyping: temporal pass rate
  0.0% (the graphiti-core compound filter returned zero rows). Full
  build with D8: 66.7%, in line with semantic and multi_hop pass
  rates (69.2% and 53.8% respectively).
- **Ephemerality is gated at ingest** — a declared rubric, editable
  in YAML, not a general judgment call the extraction LLM has to
  make.
- **Every operation has an audit trail.** The prototyping phase had
  raw Graphiti tracing; the full build adds pOS-shaped JSONL sinks
  (spans, tokens, audit) that a future aggregator can subscribe to.
- **Retention classes make privacy-sensitive sources usable.** A
  financial note can be ingested as `derived-only`; the extracted
  facts persist, the prose does not.
- **Upgrades have a semantic safety net.** The prototype could only
  verify things worked today; the full build's upgrade harness
  measures drift when the framework version changes.
- **Durability is verified, not assumed.** Three chaos scenarios all
  pass on Kuzu at prototype scale; the report flags the
  longer-horizon scale chaos test as a future item.

## Headline numbers from the full-system run

From `data/runs/full_system_<ts>.json`:

- **Overall pass rate**: 63.6% (28/44 questions)
- **Semantic**: 69.2% (9/13)
- **Multi-hop**: 53.8% (7/13) — some variance from LLM-extraction
  non-determinism; within envelope
- **Context-aware**: 66.7% (6/9)
- **Temporal**: 66.7% (6/9) — **non-zero now, was 0% before D8**
- **Mean recall**: 83.7% across all questions
- **Mean precision@5**: 87.5%
- **Ingest time**: ~9.6 s/episode wall (dominated by Claude round-trips)

Cost (Haiku 4.5, from `data/runs/cost_baseline_full_<ts>.json`):

- Per episode: $0.0180 (~7.3 LLM calls, 11.6k in / 1.3k out tokens)
- Daily at 10 events: $0.18
- Weekly at 60: $1.08
- Monthly at 250: $4.51
- Yearly at 3000: $54.12
- 5-year at 15000: $270.58
- Process-of-arrival overhead per dispatch: ~$0.022 (summarisation +
  summary ingest)

Embedding cost is zero-dollar (local Ollama). Haiku remains the
right default — Sonnet would roughly triple the bill; Opus would
break it by 15×.

## What would make the memory component "complete"

All D5–D13 deliverables pass their acceptance criteria. The soft
dependencies' wiring points exist. The chaos scenarios pass at
prototype scale. The cost baseline is fresh. Test set pass rates
are non-zero across all four retrieval modes, with temporal
specifically repaired by D8.

The memory component is complete. Outstanding items for future
phases (outside this brief's scope):

- Wire the scope-of-work primitive when built (replace
  `MockScopeSource`).
- Wire the dispatch primitive when built (replace the mock producer
  with the real stream emitter).
- Build the observability aggregator when designed (subscribe to
  `data/observability/*.jsonl`).
- Build the self-upgrade framework when designed (call
  `src/upgrade.py` from its upgrade pipeline).
- Run a 250k-edge scale chaos test before long-term durability can
  be claimed at projection volume.
