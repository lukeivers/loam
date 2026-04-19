# Relationship Map — How the Aggregator Sits Among pOS Components

## The seven sealed components and the aggregator

```
┌──────────────────────────────────────────────────────────────────┐
│                      Sealed pOS components                       │
│                                                                  │
│  scope-of-work       primary-persona      objective-tracker      │
│  orchestrator        graceful-degradation                        │
│       │                 │                       │                │
│       │                 │                       │                │
│       └─── OTel API ────┴───────────────────────┘                │
│                                                                  │
│  memory-system                                                   │
│       │                                                          │
│       └─── JSONL files (3 sinks)                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
                   Aggregator subscribes
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Observability aggregator                     │
│                                                                  │
│  ingest → store → query                                          │
└──────────────────────────────────────────────────────────────────┘
                         │
                         ▼
                 Consumers
                         │
   ┌─────────────────────┼──────────────────────────┐
   ▼                     ▼                          ▼
primary-persona     pos obs CLI            future UI / consumers
("show me why")     (operator tool)        (self-upgrade, etc.)
```

## Per-component contract

| Component               | Emission                              | A1 status |
|-------------------------|---------------------------------------|-----------|
| scope-of-work           | OTel via `pos.scope_of_work`          | unchanged |
| primary-persona         | OTel via `pos_v2.primary_persona`     | unchanged |
| objective-tracker       | OTel via `pos.objective_tracker`      | unchanged |
| orchestrator            | OTel via `pos.orchestrator`           | unchanged |
| graceful-degradation    | OTel via `pos.degradation`            | unchanged |
| memory-system           | JSONL: spans/tokens/audit             | unchanged |

A1 status "unchanged" is verified at every aggregator build by re-running each sealed component's full test suite. Baseline counts: scope-of-work 77 + 1 skipped, primary-persona 101, objective-tracker 86, orchestrator 56, graceful-degradation 93, memory-system 30 (in its own venv). Aggregator changes that drop any of these counts by even one are a halt-and-signal event.

## Hard dependencies

Aggregator depends on:
- The OTel Python SDK (`opentelemetry-api`, `opentelemetry-sdk`).
- The orchestrator's `~/.pos/bootstrap.py` workspace-hook convention (so `install_for_workspace` has somewhere to be called from).
- Memory-system's JSONL sink format (verified in `test_d2`'s format check; halt-and-signal if memory drifts).

Aggregator does NOT depend on:
- Any sealed component's internal API.
- Any specific persona implementation (pOS core ships zero personas — the aggregator's "show me why" is a capability surface, not a persona).
- An external collector, daemon, or hosted service.

## Soft dependencies (future)

- **Self-upgrade framework** (last Phase 2 component, not yet built). The aggregator's DuckDB store participates in pOS-wide upgrade-fidelity. v1.1 R1 semantic round-trip is verified against the aggregator's structured query surface.
- **Cost governance layer.** When that layer ships, it will read `cost_by_prompt` and act on thresholds. The aggregator already provides the read surface.

## What the aggregator provides to consumers

- **Primary persona:** `NLPath.answer(question) → CitedAnswer`. Used for "show me why" and "what happened at time T."
- **Operator (Luke):** `pos obs` CLI. Direct access without going through the persona.
- **Programs / scripts:** `QueryAPI`. Pydantic in, Pydantic out.

## What the aggregator does not provide

- A UI layer. Future component if needed.
- Multi-tenant isolation. pOS is single-user by design.
- A vendor-neutral observability stack. pOS is Claude-only by deliberate non-goal.
- Deterministic re-execution replay (Reading B). Out of scope per Luke's ruling.

## Cross-component invariants the aggregator enforces

- v1.1 R10 retention class — `derived-only` and `ephemeral` records have payload dropped at ingest. Verified per `test_d9_self_obs_and_privacy.py`.
- v1.1 R11 OTel internal trace format — both ingest paths normalise into the same canonical schema. The schema reflects the OTel span shape (trace_id, span_id, attributes, events).
- v1.1 R12 per-prompt-type cost attribution — `cost_by_prompt` is the structured surface; both LLM calls in the NL path are tagged so even the aggregator's own LLM cost is attributable.
- v1.1 R4 bundled documentation — this directory.
