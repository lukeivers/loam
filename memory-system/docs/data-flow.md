# Memory-system — data flows

Step-by-step traces for the three critical paths: ingest, search,
and the upgrade-fidelity harness.

## Ingest flow

```
                ┌──────────────────────────────────────────────┐
                │  caller: await memory.ingest(body, ...)      │
                └──────────────────┬───────────────────────────┘
                                   │
                                   v
                  ┌────────────────────────────────┐
                  │ D5 ephemerality.classify(...)  │
                  │ rubric from config/memory.yml  │
                  └──────────┬─────────────────────┘
                             │
                    ephemeral? ────yes──► audit:discarded ──► return (no_persist)
                             │
                             no
                             │
                             v
                  ┌────────────────────────────────┐
                  │ D6 scope_source.ensure(id)     │
                  │ (mock auto-registers)          │
                  └──────────┬─────────────────────┘
                             │
                             v
                  ┌────────────────────────────────┐
                  │ D10 retention.resolve(class)   │
                  └──────────┬─────────────────────┘
                             │
                    ephemeral? ────yes──► audit:ephemeral_retention ──► return (no_persist)
                             │
                             no
                             │
                             v
                  ┌────────────────────────────────┐
                  │ D7 emitter.span("memory.ingest")│
                  │ captures attributes + payload  │
                  └──────────┬─────────────────────┘
                             │
                             v
                  ┌────────────────────────────────┐
                  │ graphiti.add_episode()         │
                  │   • LLM: extract_nodes         │
                  │   • LLM: extract_edges         │
                  │   • Ollama: embed facts+summary│
                  │   • LLM: dedupe_nodes          │
                  │   • LLM: dedupe_edges          │
                  │   • Kuzu: write nodes+edges    │
                  └──────────┬─────────────────────┘
                             │
                             v
                  ┌────────────────────────────────┐
                  │ D10 retention.apply_plan(...)  │
                  │  • tag retention_class         │
                  │  • scrub content if derived-only│
                  └──────────┬─────────────────────┘
                             │
                             v
                  ┌────────────────────────────────┐
                  │ D7 record_llm_usage per prompt │
                  │ (delta from TokenUsageTracker) │
                  └──────────┬─────────────────────┘
                             │
                             v
                  return IngestResult(episode_uuid, ...)
```

## Search flow

```
                ┌──────────────────────────────────────────────┐
                │ caller: await memory.search(query, ..., at_time,
                │           scope_ids, anchor_node_uuid)        │
                └──────────────────┬───────────────────────────┘
                                   │
                                   v
                  ┌────────────────────────────────┐
                  │ D8 temporal.active_at(at_time) │
                  │ (only if at_time supplied)     │
                  └──────────┬─────────────────────┘
                             │
                             v
                  ┌────────────────────────────────┐
                  │ D7 emitter.span("memory.search")│
                  └──────────┬─────────────────────┘
                             │
                             v
                  ┌────────────────────────────────┐
                  │ graphiti.search(..., filters)  │
                  │  • Ollama: embed query         │
                  │  • Kuzu: FTS + HNSW hybrid     │
                  │  • RRF aggregate + optional    │
                  │    node-distance rerank        │
                  └──────────┬─────────────────────┘
                             │
                             v
                  return list[SearchHit]
```

## Upgrade harness flow

```
  PRE-UPGRADE PHASE
  ├─ build_memory(db_path=current)
  ├─ run_probe_set(memory, probe_set=test_set.json) → pre_results
  ├─ memory.close()                    ← release Kuzu lock
  └─ upgrade.snapshot(db_path)         → data/snapshots/pre-upgrade-<ts>

  UPGRADE PHASE (real framework's responsibility)
  └─ pip install --upgrade graphiti-core
     run pOS migrations
     restart memory service

  POST-UPGRADE PHASE (SUBPROCESS; avoids Kuzu file-lock contention)
  ├─ build_memory(db_path=current)     ← now graphiti 0.29.x, etc.
  ├─ run_probe_set(memory, probe_set)  → post_results
  └─ emit post_results as JSON on stdout

  COMPARE PHASE
  └─ upgrade.compare(pre_results, post_results)
       ├─ per-query: verdict_flipped, recall_delta, precision_delta,
       │             top_fact_overlap (Jaccard of top-5)
       └─ overall:   verdict_flip_fraction, over_tolerance_fraction,
                     passed=(drift_score <= max_drift_fraction)
```

## Chaos-durability flow (kill-mid-ingest)

```
  parent ──► _wipe_chaos_db()
  parent ──► spawn worker_ingest subprocess with 4 chaos episodes
  parent ──► wait for "WORKER_READY"
  parent ──► wait for first "INGESTED"
  parent ──► sleep 0.4s                ← let next ingest start
  parent ──► proc.send_signal(SIGKILL)
  parent ──► proc.wait()
  parent ──► spawn worker_count subprocess
           └─ returns episodes=1..N, edges=M
  parent ──► PASS if episodes ≥ 1 and ≤ len(CHAOS_EPISODES)
```

## Process-of-arrival flow

```
  real dispatch (or mock producer) emits StreamLog(dispatch_id, scope,
                                                    persona, outcome,
                                                    lines[])

  receiver.receive(log)
  ├─ summarise(stream_excerpt, log)
  │    └─ Claude (response_model = _StreamSummary)
  │       returns {objective, decisions[], reasoning, tools_used[], conclusion}
  ├─ emitter.span("process_of_arrival.ingest")
  ├─ memory.ingest(body=log.outcome, retention_class=NORMAL)
  │    → outcome_episode_uuid
  └─ memory.ingest(body=summary_formatted, retention_class=DERIVED_ONLY)
       → summary_episode_uuid

  acceptance:
    search("<topic>") → hits drawn from BOTH episodes
    summary's stored content is empty (scrubbed)
    outcome's stored content preserved
```
