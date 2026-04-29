# Architecture

## Process model

The orchestrator is a single long-lived Python asyncio process.
Durability lives in the Phase 1 primitives' event-sourced SQLite stores;
the orchestrator itself is a stateless coordinator that rebuilds its
working set from those logs on every cold start.

```
                                       ┌─────────────────────────────┐
                                       │   launchd                   │
                                       │   (auto-start, restart on   │
                                       │   crash, 30s throttle)      │
                                       └──────────────┬──────────────┘
                                                      │ spawns
                                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│ orchestrator process (Python asyncio)                            │
│                                                                  │
│  ┌─────────────────┐   ┌──────────────────┐                      │
│  │ ScopeRuntime    │   │ ObjectiveTracker │                      │
│  │ (Phase 1)       │──▶│ subscribe_scope  │                      │
│  └────────┬────────┘   └──────────────────┘                      │
│           │ pyee emitter                                         │
│           ▼                                                      │
│  ┌──────────────────────┐                                        │
│  │ BackgroundWorkMonitor│  Phase 1 (primary-persona)             │
│  │ coroutine + tick loop│                                        │
│  └──────────┬───────────┘                                        │
│             │ on_user_prompt(turn_id)                            │
│             ▼                                                    │
│  ┌──────────────────────┐      ┌──────────────────────┐          │
│  │ IPC server           │─────▶│ LocalStateStore      │          │
│  │ Unix-domain socket   │      │ ~/.loam/              │          │
│  │ JSON-RPC             │      │   orchestrator.sqlite│          │
│  └──────────┬───────────┘      │ (event-sourced)      │          │
│             │                   └──────────────────────┘          │
│             │                                                    │
│  pause_activation / resume_activation hooks (for future          │
│  graceful-degradation component — no policy here)                │
└─────────────┼────────────────────────────────────────────────────┘
              │ JSON-RPC over Unix socket
              │ (0600, ~/.loam/orchestrator.sock)
              ▼
┌─────────────────────────────────────────┐
│ interactive Claude session (peer)        │
│ — UserPromptSubmit calls GET /awareness  │
│ — PreCompact calls mark_precompact       │
│ — post-compaction first prompt calls     │
│   consume_compaction                     │
└──────────────────────────────────────────┘
```

## IPC

Wire format: newline-delimited JSON. One JSON envelope per line.

Request:  `{"id": "<string>", "method": "<name>", "params": {...}}`
Response: `{"id": "<string>", "result": <any>}`
Error:    `{"id": "<string>", "error": {"code": <int>, "message": <str>}}`

Error codes:
- `-32600` invalid request
- `-32601` method not found
- `-32602` invalid params
- `-32603` internal error
- `-32010` bootstrap refused (orchestrator startup)
- `-32020` scope not pending (activate_scope)
- `-32030` orchestrator paused (activate_scope when paused)
- `409`    bind refused (activate_scope failed bind_scope)

Permissions: the socket is created at startup with mode `0600`
(user-private). Orphaned socket files from a crashed previous run
are removed during `IPCServer.start`.

## Monitor hosting

The primary-persona layer's `BackgroundWorkMonitor` coroutine runs
inside this process (Luke's decision from the proposal). Rationale:

- scope-of-work's pyee emitter is in-process; cross-process fan-out
  would require a second durable queue.
- Stuck-detection state is longer-lived than a single session turn.
- Compaction-survival needs a stable host for the loaded persona
  contract + recent-corrections provider wiring.

Session turns pull awareness via `GET /awareness?turn_id=T` on every
UserPromptSubmit. Pull-model; nothing is pushed at the session, so
injection is deterministic rather than race-prone.

### 100 ms hard ceiling with cache fallback

Brief §D4: live pull completes within 100 ms p95 on a representative
workload. The orchestrator runs the monitor snapshot on a worker
thread so `asyncio.wait_for` honours the timeout even if the
snapshot is CPU-bound. On exceedance:

- If a cached block exists, the session receives it with
  `stale: true` and a `cache_age_ms`.
- If no cache is available, an empty block marked stale is returned
  so the session never blocks.

Luke's ruling: hard ceiling with cache fallback, not a soft target.

## Dispatch-layer: `bind_scope` enforcement

Activation flow:

1. `activate_scope(scope_id, objective_id)` — from session or
   internal scheduler.
2. Orchestrator verifies the scope exists and is in the pre-active
   state (scope-of-work calls this `proposed`; brief prose calls it
   "pending" — same semantics).
3. Orchestrator calls `tracker.bind_scope(scope_id, objective_id)`.
   On `UnresolvedObjectiveError` or `OrphanRootError`:
   - record `bind_refused` event in local SQLite
   - emit OTel span event
   - return 409 to caller; scope stays in its pre-active state
4. On success: `scope_runtime.start(scope_id)`
5. Emit `loam.orchestrator.scope_activated` span event.

## Restart semantics

| Failure class | Behaviour |
|---|---|
| SIGTERM | clean flush; heartbeats stop; restart resumes pending work from Phase 1 event logs |
| SIGKILL | launchd restarts within throttle; orchestrator replays Phase 1 logs; in-flight scopes self-resume or mark failed |
| Reboot | auto-starts on login; pending work resumes |
| API outage | `pause_activation` halts new activations; in-flight pause (not fail); `resume_activation` restores |
| Compaction | session signals PreCompact via IPC; flag written; post-compaction UserPromptSubmit triggers restoration from authoritative sources |

## Local SQLite

Distinct from Phase 1 stores. Path: `~/.loam/orchestrator.sqlite`
(configurable). Event-sourced; the same pattern as Phase 1. Types:

- `process_started` / `process_stopped` / `process_crashed`
- `heartbeat`
- `bind_refused`
- `scope_activated`
- `pause_activation` / `resume_activation`
- `compaction_flag_set` / `compaction_restored`
- `bootstrap_refused`

v1.1 R1 semantic round-trip upgrade: pre-upgrade probe (total,
histogram, latest payload keys, schema version) survives an event
replay into a fresh database unchanged. Test: `test_d6_local_state.py`.

## Workspace bootstrap — fail-closed

Scope callback re-registration on restart relies on a workspace-
supplied `~/.loam/bootstrap.py` exposing `def register(orchestrator)`.
Luke's ruling: missing or erroring bootstrap → orchestrator refuses
to start (exit 2 for missing, 3 for error). Matches the primary-
persona loader's fail-closed posture.
