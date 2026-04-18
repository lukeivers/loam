# Relationship map — what subscribes to scope-of-work

This primitive is **foundational** — it ships with no consumers
required and no upstream dependencies inside pOS. Every other
component is downstream and subscribes via one of three surfaces:

1. The pyee emitter (`runtime.subscribe(scope_id, callback)` or
   `runtime.subscribe_all(callback)` for the global stream).
2. The OpenTelemetry stream (the standard tracer; consumers wire any
   OTLP-compatible exporter).
3. The query API (`runtime.get(scope_id)`, `runtime.list(filter)`,
   `runtime.per_prompt_costs()`).

## Today

| Component | Surface used | What it consumes |
|---|---|---|
| **memory-system** | `RealScopeSourceAdapter.get_scope` / `list_scopes` | Just the scope identity for `group_id` partitioning. No event stream, no budget data. |

## Future (named in the brief; not built yet)

| Component | Surface used | What it consumes |
|---|---|---|
| **Background-work monitor** (Phase 1, paired with primary-persona loader) | `runtime.list(states=[active, paused, escalated, ...], include_pending_extension=True)` | Polls for unclaimed / paused / escalated scopes so the primary persona never loses track of in-flight work. (STATE.md rule #7.) |
| **Primary persona loader** (Phase 1) | `list(owner_persona=...)` plus pyee subscription | Per-persona view of in-flight scopes; surfaces escalations to the user. |
| **Objective tracker** | bidirectional — reads `success_criteria`; writes `evaluate_success_criterion(...)` events | Links scopes to parent objectives; runs alignment checks at scope boundaries. |
| **Observability aggregator** | OTel exporter (file, Jaeger, Honeycomb) | Aggregates spans across components into a single replayable timeline. |
| **Cost governance** | pyee subscribe to `budget_debited`; `per_prompt_costs()` view | Enforces system-wide token/money ceilings; surfaces top-cost prompts (v1.1 R12). |
| **Safety layer** | bidirectional — writes default triggers (always-ask, irreversible-escalate) into scopes at creation; reads escalation events | Implements the always-ask list and the irreversible-blast-radius gate as scope-level triggers. |
| **Reversibility primitive** | reads `reversibility_class` field; writes compensation actions as scope events | Enforces reversibility-preferred selection between equivalent approaches. |
| **Self-correction loop** | pyee subscribe to scope failure events; writes correction events linking back to failures | Runs the four-part correction protocol on every failure. |
| **Channel-agnostic interaction (R13)** | pyee subscribe to escalation events | Routes notifications to the user's enabled channels. |

## What the primitive does NOT depend on

- No LLM client. The primitive does not dispatch LLM calls; the caller
  reports usage via `debit()`.
- No memory system. Memory depends on scopes, not the other way
  round.
- No specific persona content. Scopes carry an `owner_persona`
  string; the primitive is persona-agnostic.
- No specific OTel exporter. The default no-op tracer is fine; any
  consumer wires its own exporter.

## Layering

```
                   safety │ reversibility │ self-correction
                          │      │              │
                          ▼      ▼              ▼
                       [   triggers + events    ]
                       [        scope-of-work    ]   ← THIS COMPONENT
                       [   events / OTel / pyee  ]
                          │      │              │
                          ▼      ▼              ▼
            cost-gov │ obs-aggregator │ memory │ primary-persona-loader
```

Reading top-to-bottom: safety / reversibility / self-correction layers
**read** scope state and **write** triggers/events. The scope primitive
**publishes** state and event surfaces. Cost governance, observability
aggregation, memory, and the primary-persona loader **subscribe** to
those surfaces. None of the consumers know about each other; all the
coordination happens through the scope primitive's stable interfaces.
