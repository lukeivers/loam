# Relationship map

The tracker sits at the bottom of the Phase 1 dependency graph. Nothing sits below it; several components sit above it.

---

## Dependencies

### Hard — none

The tracker depends on `pydantic`, `pyee`, `opentelemetry`, `PyYAML`, and the Python stdlib. It does **not** depend on:

- Scope-of-work
- Memory system
- Primary-persona layer
- Any workspace-specific persona

Its SQLite database is separate from scope-of-work's.

### Soft — consumers

```
                       ┌───────────────────────┐
                       │  Objective Tracker    │
                       │  (this component)     │
                       └───────┬───────────────┘
                               │
     ┌────────────────┬────────┴────────┬──────────────────┐
     │                │                 │                  │
     ▼                ▼                 ▼                  ▼
 Scope-of-work   ODD test         Primary-persona    Self-correction
 dispatch        harnesses        authoring          loop (future)
 layer                            pipeline
 (consumer       (consumer        (consumer          (consumer of
  of bind_scope)  of list / eval   of create —       abandonment
                  / re_open)       persona handles   events)
                                   flow in as
                                   authored_by)

                 ┌───────────────────────┐
                 │  Observability         │
                 │  aggregator (future)   │
                 └───────────────────────┘
                   consumer of OTel spans
```

---

## Per-consumer contract

### Scope-of-work dispatch layer

**How it consumes:** calls `tracker.bind_scope(scope_id, objective_id)` before activating any scope; calls `tracker.is_scope_bound(scope_id)` as a guard.

**Tracker guarantees:** `bind_scope` raises `UnresolvedObjectiveError` for unknown objectives and `OrphanRootError` for chains that do not terminate at `authored_by == "user"`. Scope-of-work itself is **not** modified.

**Integration point:** the workspace dispatch layer (not yet designed as of Phase 1 completion). A minimal test dispatcher is included in D4 integration tests as the shape reference.

---

### Primary-persona authoring pipeline

**How it consumes:** when a persona authors a new objective as part of decomposing work, it calls `tracker.create(spec)` with `spec.authored_by` set to its own handle.

**Tracker guarantees:** the handle is stored verbatim; `list(authored_by=handle)` returns every objective that persona authored.

---

### ODD test harnesses

**How they consume:** `list_by_root(root_id, with_unchecked_criteria=True)` → walk unchecked criteria → run registered predicates → push results via `evaluate_criterion`. On failure, `re_open(parent_id, rationale=...)` then `create(new_child_spec)` for re-extension.

**Tracker guarantees:** evaluations persist as events with caller-supplied source tags; criteria history is queryable.

---

### Self-correction loop (future)

**How it consumes:** subscribes via `tracker.subscribe_all(cb)` for `status_transitioned` events transitioning INTO `abandoned`.

**Tracker guarantees:** every abandonment emits both an event on the pyee channel and a persisted `status_transitioned` with the rationale string.

---

### Observability aggregator (future)

**How it consumes:** reads OTel spans via any configured tracer provider (OTLP collector, local exporter, etc.).

**Tracker guarantees:** every public operation emits an INTERNAL span with `loam.objective.*` attributes. No consumer is required for emission to succeed (A1 correction).

---

## What the tracker does NOT consume

- It does not read scope-of-work's SQLite database.
- It does not import memory-system code or its schemas.
- It does not read or write primary-persona state files.
- It does not query the persona loader's registry to validate handles.

This is deliberate: the tracker is foundational. Coupling it to consumers would turn the primitive into a hub, defeating the foundational posture.
