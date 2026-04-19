# Architecture

The tracker has four layers: the event log, the projection cache, the sidecar binding table, and the public API.

---

## Layer diagram

```
 ┌──────────────────────────────────────────────────────────────────┐
 │  Public API                  ObjectiveTracker (runtime.py)       │
 │  ─────────────────────       - create / decompose                │
 │                              - start / mark_achieved /           │
 │                                mark_abandoned / re_open          │
 │                              - evaluate_criterion                │
 │                              - bind_scope / get_binding          │
 │                              - list / list_by_root /             │
 │                                trace_to_root                     │
 │                              - subscribe_scope_emitter           │
 ├──────────────────────────────────────────────────────────────────┤
 │                                                                  │
 │  Projection Cache            objective_state  (store.py)         │
 │  ─────────────────────       rebuildable from events alone       │
 │                              │                                   │
 │                              │ fold(events) → projection         │
 │                              ▼                                   │
 │  Event Log (source of        objective_events                    │
 │  truth)                      ├── objective_created               │
 │                              ├── status_transitioned             │
 │                              ├── criterion_evaluated             │
 │                              ├── scope_bound                     │
 │                              └── parent_closed                   │
 │                                                                  │
 │  Sidecar                     scope_objective_binding             │
 │  (dispatch-layer gate)       (scope_id → objective_id)           │
 │                                                                  │
 ├──────────────────────────────────────────────────────────────────┤
 │  SQLite WAL (single file per tracker instance)                    │
 └──────────────────────────────────────────────────────────────────┘

             ▲                                    │
             │ pyee async fan-out                 │  OTel spans + events
             │ (subscribe / subscribe_all /       │  (pos.objective.*
             │  subscribe_scope_emitter)          │   pos.scope.*)
             │                                    ▼
   Consumers (ODD harnesses,            Tracing backend / no-op
    dispatch layer, self-correction     (A1: no consumer required)
    loop, observability aggregator)
```

---

## Why this shape

**Event log as source of truth (proposal §Persistence):** every state change is one typed event. `objective_created` carries the full spec payload (goal, parent_id, acceptance_criteria, time_bound, authored_by, owner, parent_close_policy). `status_transitioned` carries from/to status plus evidence and rationale. `criterion_evaluated` carries result, rationale, and source (`caller` vs `scope_success_auto`). `scope_bound` carries the scope id being bound. `parent_closed` carries the parent id and the applied policy.

**Projection cache (objective_state):** a flattened row per objective, rebuilt from events. Fields: goal, parent_id, authored_by, owner, status, time_bound_json, criteria_json, parent_close_policy, last_event_id, last_transition_at, criteria_latest_json. The cache is disposable — `drop_projection()` empties it, the runtime rebuilds from the event log. This is the round-trip fidelity guarantee (D8 / v1.1 R1).

**Sidecar binding table (scope_objective_binding):** one row per scope_id. The row records the objective_id bound to, the event_id of the binding event, and the binding timestamp. `upsert_binding` is used on re-bind (the sidecar holds the current binding, not a full history — the history lives in the event log as `scope_bound` events on the objective).

**SQLite WAL:** matches scope-of-work's pattern. Read-concurrent, write-serialised, one connection per tracker instance protected by a thread lock. Wrapped by `asyncio.Lock` at the runtime boundary so concurrent async callers can mutate different objectives simultaneously.

**OTel spans (observability.py):** one INTERNAL span per public operation. Attributes are namespaced `pos.objective.*` and `pos.scope.*`. State transitions are emitted as span events on the operation's span. `pos.objective.outcome = success | error` is set automatically — errors set it to `error` and mark the span status as error.

**pyee emitter:** two channels — `objective:{id}` (per-objective) and `*` (global). Consumers subscribe via `subscribe(objective_id, cb)` or `subscribe_all(cb)`. The tracker itself subscribes to scope-of-work's emitter (via `subscribe_scope_emitter`) to auto-evaluate `ScopeSuccessCriterion`.

---

## Invariants the runtime enforces

1. **Forest-of-trees structure.** `create` rejects a spec that names the new objective as its own parent. A child naming a nonexistent parent raises `UnresolvedObjectiveError`.
2. **User-authored terminal root.** `bind_scope` walks `trace_to_root`; if the terminal ancestor's `authored_by` is anything other than `"user"`, `OrphanRootError` is raised.
3. **Legal status transitions only.** `policies.py` defines the transition table. Attempting an illegal transition (e.g. `proposed → achieved` without an intermediate `active`) raises `IllegalTransitionError`.
4. **Mandatory rationale on `mark_abandoned` and `re_open`.** Empty or whitespace-only rationale raises `MissingRationaleError`.
5. **Unique criterion ids per objective.** `ObjectiveSpec` Pydantic-validates this at construction.
6. **TimeBound is mandatory** (Luke's decision). Omission raises `ValidationError`. TimeBound itself requires exactly one of `deadline` or `evergreen=True`.
