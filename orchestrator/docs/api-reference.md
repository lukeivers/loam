# API Reference — IPC Surface

Wire: newline-delimited JSON-RPC over a Unix-domain socket at
`~/.pos/orchestrator.sock` (configurable via `OrchestratorConfig`).

Every method below is `{"id": <string>, "method": "<name>",
"params": <object>}` in; `{"id": <same>, "result": <object>}` out
on success; `{"id": <same>, "error": {"code": <int>, "message":
<str>, "data": <any?>}}` on failure.

## `ping`

Liveness check.

- **params:** `{}`
- **result:** `{"pong": true, "ts": <float seconds since epoch>}`

## `status`

Snapshot of orchestrator process state.

- **params:** `{}`
- **result:**
  ```
  {
    "started_at":              "<iso-8601 UTC>",
    "uptime_seconds":          <float>,
    "pid":                     <int>,
    "tick_id":                 <int>,
    "paused":                  <bool>,
    "paused_reason":           <string | null>,
    "compaction_flag_pending": <bool>
  }
  ```

## `awareness`

Pull the background-work awareness block for a session turn.

- **params:** `{"turn_id": "<string>"}`
- **result:** a structured awareness block —
  ```
  {
    "turn_id":            <string>,
    "generated_at":       "<iso-8601>",
    "active":             [ <row>, ... ],   # ≤5
    "pending_decision":   [ ... ],          # ≤5
    "stuck":              [ ... ],          # ≤5
    "recently_finished":  [ ... ],          # ≤5
    "escalated":          [ ... ],          # ≤5
    "failed":             [ ... ],          # ≤5
    "stale":              <bool>,
    "stale_reason":       "<string>",       # only when stale=true
    "cache_age_ms":       <int>
  }
  ```
- Latency policy: 100 ms hard ceiling with cache fallback. If the
  live pull exceeds the ceiling or the monitor raises, the response
  is the last cached block with `stale: true`.

## `activate_scope`

Dispatch-layer scope activation. Enforces `bind_scope` before
`scope_runtime.start`.

- **params:** `{"scope_id": "<string>", "objective_id": "<string>"}`
- **result:**
  ```
  {
    "scope_id":      "<string>",
    "objective_id":  "<string>",
    "binding":       { "bound_event_id": <int>, ... }
  }
  ```
- **errors:**
  - `-32020` — scope not in pending/proposed state; `data:
    {scope_id, state}`
  - `-32030` — orchestrator paused
  - `409`    — bind refused; `data: {scope_id, objective_id,
    cause_kind: "UnresolvedObjectiveError" | "OrphanRootError",
    event_id}`

## `pause`

Halt new activations (typically called by the graceful-degradation
component when Claude API health drops).

- **params:** `{"reason": "<string>"}`
- **result:** `{"paused": true, "reason": "<string>"}`

## `resume`

Restore normal activation.

- **params:** `{}`
- **result:** `{"paused": false}`

## `mark_precompact`

PreCompact hook. Called from the session's PreCompact handler to
tell the orchestrator to remember: after compaction, the next
UserPromptSubmit needs restoration.

- **params:** `{"session_id": "<string | null>"}`
- **result:** `{"flag_event_id": <int>, "pending": true}`

## `consume_compaction`

Post-compaction handshake. Called on the first UserPromptSubmit
after compaction. Returns the five-item canonical survival payload
if the flag is set, else `{"pending": false}`.

- **params:** `{"session_id": "<string | null>"}`
- **result (flag pending):**
  ```
  {
    "persona_identity":       { "handle", "given_name", "contract_version" },
    "authority_boundary":     { "tier_a", "tier_b", "tier_c", "tier_d" },
    "current_scope_context":  [ <scope summary>, ... ],
    "pending_decisions":      [ <scope summary>, ... ],
    "recent_corrections":     [ <correction>, ... ],
    "restored_at":            "<iso-8601>"
  }
  ```
- **result (no flag):** `{"pending": false}`

## `local_event_count`

Diagnostic: count of events of a given type in the local SQLite.

- **params:** `{"event_type": "<string | null>"}`
- **result:** `{"count": <int>}`
