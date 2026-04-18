# Architecture — event-sourced FSM + event log + projection cache

## One-paragraph summary

The scope-of-work primitive is an event-sourced finite state machine
on top of a SQLite WAL event log. Every mutation — state transitions,
budget debits, observer changes, trigger fires, extension requests —
is appended as a typed event. Current state is a derived projection,
cached in a second table for fast queries and rebuildable from the
event log alone. The runtime fans events out to in-process observers
via `pyee.AsyncIOEventEmitter` and to OpenTelemetry spans/events via
the standard SDK. No external service is required for the primitive
to function; it survives restart, cross-process coordination is
event-log polling, and the full state can be replayed for upgrade-
fidelity verification.

## Component diagram

```
                 ┌─────────────────────────────────────────────┐
                 │              Caller (workspace)             │
                 │   create / start / debit / cancel / etc.    │
                 └───────────────────┬─────────────────────────┘
                                     │  async API
                                     ▼
            ┌────────────────────────────────────────────────────┐
            │                   ScopeRuntime                     │
            │ ┌──────────────────────────────────────────────┐   │
            │ │         per-scope asyncio.Lock map           │   │
            │ └──────────────────────────────────────────────┘   │
            │           │                       │                │
            │           ▼                       ▼                │
            │   ┌──────────────┐    ┌──────────────────────┐     │
            │   │  Projector   │◀───│      EventStore      │     │
            │   │ events→state │    │  SQLite WAL +        │     │
            │   │              │    │  scope_events table  │     │
            │   └──────────────┘    └──────────────────────┘     │
            │           │                       ▲                │
            │           │                       │ append         │
            │           ▼                       │                │
            │   ┌──────────────┐    ┌──────────────────────┐     │
            │   │ scope_state  │    │  Trigger evaluator   │     │
            │   │  projection  │    │  (per-event scan)    │     │
            │   │     cache    │    └──────────────────────┘     │
            │   └──────────────┘                                 │
            │           │                                        │
            │           ▼                                        │
            │   ┌──────────────────────────┐                     │
            │   │  pyee AsyncIOEventEmitter│  →  observers       │
            │   └──────────────────────────┘                     │
            │   ┌──────────────────────────┐                     │
            │   │  OpenTelemetry tracer    │  →  spans / events  │
            │   └──────────────────────────┘                     │
            │   ┌──────────────────────────┐                     │
            │   │ pending-extension files  │  →  human surfacing │
            │   └──────────────────────────┘                     │
            └────────────────────────────────────────────────────┘
```

## Data layout (SQLite)

### `scope_events` — append-only source of truth

| column | type | notes |
|---|---|---|
| event_id | INTEGER PK AUTOINCREMENT | monotonic, used as checkpoint id |
| scope_id | TEXT NOT NULL | indexed |
| kind | TEXT NOT NULL | discriminator (`scope_created`, `state_transitioned`, etc.) |
| payload | TEXT NOT NULL | JSON-serialised typed event body |
| created_at | TEXT NOT NULL | ISO-8601 UTC |

Indexes: `(scope_id, event_id)` for per-scope replay; `(kind, event_id)`
for query patterns like "all extension requests".

### `scope_state` — projection cache

Rebuildable from `scope_events` alone. Holds the current
projection of every scope: state, parent, owner persona, last_event_id,
budget caps + consumed + extended counters per axis, observer JSON,
trigger JSON, pending extension axis, and timing bookkeeping
(`active_started_at`, `active_cumulative_seconds`).

Why a cache and not a derived view? Two reasons: (a) `list()` queries
filtering by state benefit from a real index that views can't expose
in SQLite; (b) the upgrade-fidelity test (D7) compares **projection
rows**, so persisting them gives the diff a tangible target.

## Event sourcing — the upgrade story

Because state is derived, an upgrade that changes the projector code
can be tested against the entire historical event log:

1. **Pre-upgrade:** capture every scope's current `scope_state` row to
   a probe file. Snapshot the SQLite database file (physical
   reversibility).
2. **Upgrade:** swap in the new projector code.
3. **Post-upgrade:** run the new projector against the unchanged
   `scope_events` table. Compare the rebuilt `scope_state` rows
   against the captured probes. Any field difference is drift; drift
   above the threshold fails the upgrade.

This is the v1.1 R1 semantic round-trip test, instantiated for the
scope-of-work primitive.

## Concurrency model

- **In-process:** `asyncio.TaskGroup` is the recommended primitive for
  spawning child scopes' workers. The runtime itself uses one
  `asyncio.Lock` per scope to serialise mutations.
- **Cross-process:** the event log is the queue. A second process
  reading the same SQLite file polls `scope_events` for new entries
  with `event_id > last_seen` and fans them out to its own observers.
  See `ScopeRuntime.poll_external_events()` for the helper.

## Failure modes considered

- **Process crash mid-event-write.** SQLite WAL with `synchronous=FULL`
  guarantees the write either lands fully or not at all. On restart,
  the projector replays from `scope_events` and the scope_state cache
  is regenerated.
- **Refund larger than original debit.** Projector clamps consumed at
  zero — never negative.
- **Observer callback raises.** pyee absorbs the exception; the
  primitive continues. Errors surface in the OTel span events.
- **Extension request never answered.** Per Luke's decision: the
  scope stays paused indefinitely. A per-scope `expires_at` override
  is a future addition, not a default.
- **Cross-process coordinator missed an event.** `events_since(id)`
  is idempotent; the late-arriving consumer catches up.

## Why SQLite over alternatives (recap from research)

- **Graphiti/Kuzu (memory's substrate):** wrong substrate for
  operational state; couples scope durability to memory release
  cadence. Rejected.
- **Append-only JSONL log:** no indexed queries, can't filter by
  state without full file scan. Rejected.
- **PostgreSQL:** network dependency, overkill for single-user.
  Rejected.
- **Pickled Python files:** not durable across schema changes,
  not queryable. Rejected on first principles.
