# Memory-system prototype — architecture

This prototype tests three assumptions before the full memory-system
build proceeds. The shape:

```
                            ┌──────────────────────────────┐
                            │  caller (Python process)     │
                            │  — smoke_test.py             │
                            │  — eval_embeddings.py        │
                            │  — cost_baseline.py          │
                            │  — HTTP client to :9876      │
                            └──────────┬───────────────────┘
                                       │
                                       │  in-process: call factory.make_graphiti()
                                       │  out-of-process: HTTP /ingest, /search
                                       │
                                       v
                            ┌──────────────────────────────┐
                            │  Graphiti (graphiti-core     │
                            │  0.28.2)                     │
                            │  — add_episode               │
                            │  — search                    │
                            │  — token_tracker             │
                            └──┬─────────────┬─────────┬───┘
                               │             │         │
                  llm_client   │   embedder  │   graph_driver
                               │             │         │
                               v             v         v
              ┌────────────────────┐  ┌──────────┐  ┌────────────────┐
              │ Anthropic Claude   │  │ Ollama   │  │ Kuzu           │
              │ (Anthropic API,    │  │ (local,  │  │ (embedded,     │
              │  Max-budget       │  │  OpenAI- │  │  single file/  │
              │  funded)           │  │  compat) │  │  directory)    │
              │                    │  │          │  │                │
              │ claude-haiku-4-5   │  │ nomic-   │  │ data/kuzu_db   │
              │ for extraction,    │  │ embed-   │  │                │
              │ contradiction,     │  │ text     │  │ FTS indices,   │
              │ summarisation      │  │ (768d)   │  │ HNSW vector    │
              │                    │  │ OR       │  │ indices, edges │
              │                    │  │ bge-     │  │ + nodes        │
              │                    │  │ large    │  │                │
              │                    │  │ (1024d)  │  │                │
              └────────────────────┘  └──────────┘  └────────────────┘
                       │                                     │
                       │                                     │
                       │  (D4: TokenUsageTracker             │
                       │   per-prompt aggregation)           │
                       v                                     v
                  ┌─────────────────┐               ┌──────────────────┐
                  │ usage rows by   │               │ episodes,        │
                  │ prompt name     │               │ entities,        │
                  │ (extract_nodes, │               │ edges with       │
                  │  extract_edges, │               │ valid_at /       │
                  │  dedupe_nodes,  │               │ invalid_at /     │
                  │  ...)           │               │ created_at /     │
                  └─────────────────┘               │ expired_at       │
                                                    └──────────────────┘
```

## Two run shapes (both prove D1)

**Library mode** (used by `scripts/smoke_test.py`,
`scripts/eval_embeddings.py`, `scripts/cost_baseline.py`): the caller
imports `src.factory.make_graphiti()` directly. Single Python process
holds the Kuzu connection. Cleanest for batch / eval work.

**Service mode** (`src/service.py` + `launchd/`): a long-lived
FastAPI process holds the Graphiti instance behind `/health`,
`/ingest`, `/search`, `/token-usage`. Auto-start via launchd plist.
Restart-survival is provided by Kuzu's on-disk persistence — the
service can be killed and restarted, and previously-ingested episodes
are still queryable.

Both modes were exercised in this prototype to confirm the D1
acceptance: round-trip succeeds in library mode (`smoke_test.py`)
AND the service can be killed-and-restarted with previously-ingested
data still visible (verified via `/search` after a service kill).

## Data flow on `add_episode`

1. Caller submits an episode (text + reference_time + group_id).
2. Graphiti calls Claude (`extract_nodes.extract_text` prompt) to find
   entity candidates in the episode body.
3. Graphiti calls Claude again (`extract_edges.edge` prompt) to find
   relationships among the entities.
4. Graphiti calls Ollama embeddings on every new node summary and
   every new edge fact. Embeddings land in Kuzu's HNSW indices.
5. Graphiti calls Claude (`dedupe_nodes.nodes` and `dedupe_edges.edge`)
   to reconcile new entities against existing graph state.
6. New nodes/edges are written to Kuzu with bitemporal metadata
   (`created_at` = ingest time, `valid_at` = `reference_time` from the
   episode).

Token cost per episode, observed in this prototype on synthetic 800-
character episodes, is dominated by the extraction+dedupe pair (see
`docs/findings.md` for the numbers).

## Data flow on `search`

1. Caller submits a query string, optional `group_ids`, optional
   `center_node_uuid` (anchor for context-aware reranking), optional
   `search_filter` (used here for `valid_at` temporal filtering).
2. Graphiti embeds the query via Ollama.
3. Graphiti hybrid-searches Kuzu: FTS on `node_name_and_summary` +
   HNSW vector similarity on edge facts. Rerank via RRF.
4. If `center_node_uuid` is supplied, results are reranked by
   graph distance from that node.
5. Returned: a list of `EntityEdge` instances with `fact` text,
   `valid_at`/`invalid_at`/`created_at`, and source/target node UUIDs.

## What is NOT in this prototype

The full-build proposal lists nine adaptation layers wrapping
Graphiti. None are in this prototype:

- Ephemerality filter (#1) — every episode is ingested.
- Scope-of-work mapper (#2) — `group_id` is set but no scope primitive
  exists yet.
- Observability emission adapter (#3) — Graphiti's own OTel + token
  tracker are exposed but no pOS-side wrapping.
- Graphiti MCP hosting (#4) — FastAPI substitute proves the shape;
  the full MCP server lift comes later.
- Upgrade-fidelity test harness (#5) — out of scope.
- Retention-class tagger (#6) — `store_raw_episode_content=True`
  always.
- Process-of-arrival capture (#7) — out of scope.
- Synthetic retrieval test set (#8) — partial; the test set IS in this
  prototype (`data/test_set.json`) but Luke must approve labels before
  it is the upgrade gate.
- Bundled documentation (#9) — this directory.

The prototype's scope is exactly D1–D4 from the brief. The full-build
brief, when written, will commit to the nine layers.

## File map

```
memory-system/
  src/
    factory.py        # build a Graphiti with the chosen LLM + embedder + DB
    service.py        # FastAPI wrapper exposing /ingest /search /health
    __init__.py
  scripts/
    smoke_test.py     # D1 — round-trip an episode through Graphiti
    eval_canary.py    # D3 quick-sanity (5 episodes, 5 questions)
    eval_embeddings.py # D3 — full evaluation across embedding models
    cost_baseline.py  # D4 — per-episode token cost with projection
  data/
    scenario_world.md # D2 — fictional world description (Luke-readable)
    episodes.json     # D2 — 34 synthetic episodes
    test_set.json     # D2 — 44 Q/A pairs with proposed ground-truth labels
    runs/             # eval and cost outputs (gitignored)
    kuzu_db*          # Kuzu state (gitignored)
  docs/
    architecture.md   # this file
    findings.md       # what the prototypes revealed (the headline)
    assumptions.md    # the three assumptions and whether each held
  launchd/
    com.pos-v2.memory-graphiti.plist  # auto-start config
    README.md
  requirements.txt
  .env.example
  .env              # local secrets (gitignored)
  .gitignore
```
