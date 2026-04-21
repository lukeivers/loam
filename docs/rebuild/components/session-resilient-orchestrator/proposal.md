# Session-Resilient Orchestrator — Proposal

**Component:** Session-Resilient Orchestrator (first Phase 2 component)

**Status:** DRAFT — awaiting owner's review and approval before a handoff brief is drafted
**Against:** objectives spec v1.0 + v1.1 + v1.2 addenda
**Informed by:** `research-plan.md`, `research.md` (returned 2026-04-19 07:08 CDT, 1,362 lines). owner's approval of research recommendations 2026-04-19 07:11 CDT.

---

## Summary

Build the session-resilient orchestrator as a single long-lived Python asyncio process hosted by launchd on macOS (with a systemd-user parity path for Linux). The orchestrator is a stateless coordinator layered on top of Phase 1's event-sourced SQLite stores — durability comes from the primitives; the orchestrator owns only process-lifecycle state and cross-primitive coordination. The interactive Claude session is a peer process attaching via Unix-domain-socket JSON-RPC. The primary-persona layer's background-work monitor runs *inside* the orchestrator process and serves awareness to the session via pull-model IPC. `bind_scope` enforcement is the orchestrator's dispatch-layer responsibility before any scope activation. Graceful degradation remains a separate Phase 2 component; the orchestrator exposes only `pause_activation(reason) / resume_activation()` hooks. No Phase 1 component is amended.

## Direction

### Process model

- **Single long-lived Python asyncio process,** hosted by `launchd` as a user agent on macOS with `KeepAlive=true` and a throttle interval on crash-loops. A parallel `systemd-user` unit supplies Linux parity.
- **Stateless coordinator.** All durable state lives in Phase 1 primitives' existing event-sourced SQLite stores. The orchestrator owns only its own process-lifecycle state (heartbeats, compaction flags, bind-refused log) in a small local SQLite — distinct from Phase 1 stores.
- **Session is a peer process,** not hosted by the orchestrator. Interactive Claude attaches via Unix-domain-socket JSON-RPC. The socket path and wire format are pOS-core configuration; workspace authors do not implement it.

### Monitor-in-orchestrator

- The primary-persona layer's long-lived background-work monitor coroutine runs **inside the orchestrator process.** Justified by pyee-emitter locality (scope-of-work's emitter is in-process), stuck-detection state longevity, and compaction-survival needing a stable process for the loaded persona contract.
- The session pulls awareness via `GET /awareness?turn_id=T` over the IPC socket on every UserPromptSubmit. Pull-model; nothing is pushed at the session, so injection is deterministic rather than race-prone.

### `bind_scope` dispatch sequence

The orchestrator is the dispatch-layer boundary. Activation flow:

1. `activate_scope(scope_id, objective_id)` request arrives (from the session or an internal scheduler).
2. Orchestrator verifies the scope exists and is in `pending` state (query scope-of-work).
3. Orchestrator calls `tracker.bind_scope(scope_id, objective_id)`. On `UnresolvedObjectiveError` or `OrphanRootError`: record `bind_refused` event in local SQLite, emit OTel, return 409 to caller, scope stays pending.
4. On success: `scope_runtime.start(scope_id)`.
5. Emit `pos.orchestrator.scope_activated` span.

### Restart semantics (failure-class matrix)

| Failure class | Behaviour |
|---|---|
| Graceful orchestrator stop (SIGTERM) | Current work state flushes; heartbeats stop cleanly; restart resumes pending work from event logs |
| Kill mid-run (SIGKILL / SEGV / OOM) | launchd/systemd restarts within throttle window; orchestrator rebuilds state by replaying Phase 1 event logs; in-flight scopes either self-resume (if scope-of-work's event log still has them `in_progress`) or are marked failed with recoverable state |
| System restart (laptop reboot, Claude CLI exit) | launchd auto-starts orchestrator on login; tasks queued before shutdown resume cleanly |
| Claude API outage / rate-limit / garbage | Orchestrator pauses activation via the graceful-degradation component's hook; scopes in-flight are paused, not failed; resume on API recovery |
| Compaction event (interactive session) | Session signals PreCompact via IPC; orchestrator writes a `pending_compaction_restore` flag; session's next UserPromptSubmit triggers restoration from authoritative sources per primary-persona layer's D4 pattern |

### Graceful degradation — separate component

- **Decision from research (accepted):** graceful degradation is a separate Phase 2 component, not a sub-module of the orchestrator.
- Orchestrator exposes only `pause_activation(reason) / resume_activation()` hooks.
- The graceful-degradation component (Phase 2, to come after this one) decides when to call them — it owns LLM-judged policy (safe-mode narrative, user notification, threshold calls). Rationale: preserves A1 (no assumed consumer), keeps the orchestrator deterministic plumbing, and separates test surfaces cleanly.

### Orchestrator's own local SQLite

- Distinct from Phase 1 stores. Contains: heartbeats, compaction flags, bind-refused log, lifecycle events.
- Same event-sourced pattern as Phase 1 primitives; same upgrade-fidelity approach (v1.1 R1 semantic round-trip).
- Path: default `~/.pos/orchestrator.sqlite`, configurable.

### Workspace bootstrap convention

- Scope callback re-registration on orchestrator restart relies on a workspace-supplied `~/.pos/bootstrap.py` (workspace-configurable path). pOS core defines the contract (what functions/symbols the bootstrap must export); the workspace authors the file.
- Matches the "core is framework, workspace is content" pattern Phase 1 established.

---

## Deliverables

Ten deliverables D1–D10.

### D1. Orchestrator process skeleton

**Objective:** a Python asyncio process starts, runs an event loop, handles SIGTERM gracefully, and exits cleanly.
**Acceptance:** process starts; handles SIGTERM with a clean flush; heartbeat is written on interval; process exits with code 0 on graceful stop and non-zero on crash.

### D2. launchd + systemd-user process-supervision

**Objective:** the orchestrator auto-starts with the user session on macOS (launchd) and Linux (systemd-user); auto-restarts within a throttle window on crash.
**Acceptance:** launchd plist loads without errors; `launchctl kickstart` starts the orchestrator; SIGKILL to the process results in automatic restart within a bounded time; a rapid-crash loop is throttled. Equivalent behaviour via systemd-user unit file for Linux.

### D3. Unix-domain-socket JSON-RPC server

**Objective:** the orchestrator exposes a JSON-RPC server on a Unix-domain socket for the interactive session to attach to.
**Acceptance:** socket exists at configured path; a test client connects, sends a ping, receives a pong; disconnect and reconnect work cleanly; socket permissions are user-private (0600).

### D4. Monitor hosting

**Objective:** the primary-persona layer's background-work monitor coroutine runs inside the orchestrator process, subscribes to scope-of-work's pyee emitter, and serves awareness blocks via `GET /awareness?turn_id=T` over the IPC socket.
**Acceptance:** monitor starts with the orchestrator; pyee events from scope-of-work flow to the monitor in real time; `GET /awareness` returns a structured awareness block (≤1k tokens, six categories, ≤5 rows each); a session's UserPromptSubmit-driven pull returns within the declared latency budget (see D10 prototyping priority).

### D5. `bind_scope` dispatch layer

**Objective:** scope activation goes through the orchestrator; `bind_scope` is called before `scope_runtime.start`; failures are logged and surfaced per the sequence in the proposal.
**Acceptance:** `activate_scope(scope_id, objective_id)` call enforces the sequence; `UnresolvedObjectiveError` and `OrphanRootError` both result in a `bind_refused` event plus 409 return plus scope staying pending; successful binding results in `scope_activated` and scope-of-work's runtime activating the scope. Scope-of-work and objective-tracker are unamended.

### D6. Local SQLite for orchestrator state

**Objective:** the orchestrator owns a small local SQLite for its own process-lifecycle events (heartbeats, compaction flags, bind-refused log, lifecycle events), event-sourced, upgrade-fidelity-testable.
**Acceptance:** database exists at configured path; heartbeats write on interval; compaction flags persist through restart; bind-refused events are queryable; v1.1 R1 semantic round-trip upgrade test passes.

### D7. Restart-semantics behaviour

**Objective:** each failure class in the matrix above produces the declared behaviour; no data loss on graceful stop; in-flight work either self-resumes or is marked failed-with-recoverable-state within a bounded window.
**Acceptance:**
- Graceful SIGTERM: flush completes; restart resumes pending work from event logs; no data loss.
- SIGKILL: launchd/systemd restarts; orchestrator replays Phase 1 logs; in-flight scopes resume or are marked failed.
- System reboot: orchestrator auto-starts on login; pending work resumes.
- Claude API outage: `pause_activation(reason)` halts new activations; in-flight scopes pause (not fail); `resume_activation()` on recovery.
- Compaction: session signals PreCompact; orchestrator writes flag; session's next UserPromptSubmit triggers restoration from authoritative sources via the primary-persona D4 pattern.

### D8. Compaction-survival integration

**Objective:** the orchestrator participates in the compaction protocol via IPC with the session; PreCompact and post-compaction UserPromptSubmit handshake works end-to-end.
**Acceptance:** session-side compaction hook calls the orchestrator's IPC endpoint; orchestrator writes a `pending_compaction_restore` flag; on the next UserPromptSubmit, the session pulls restoration content and the monitor's awareness block; the five-item canonical survival list (persona, authority boundary, current scope context, pending decisions, recent corrections) is verifiably present in the restoration.

### D9. OTel observability emission

**Objective:** every orchestrator operation emits OTel spans/events per v1.1 R11.
**Acceptance:** process start/stop produce spans; `scope_activated`, `bind_refused`, `pause_activation`, `resume_activation`, `compaction_flag_set`, `compaction_restored` all emit with relevant attributes; heartbeats emit as metric events; emission succeeds with no consumer (A1 correction).

### D10. Bundled documentation + prototyping addendum

**Objective:** v1.1 R4 bundled docs, plus documentation of the two prototyping priorities surfaced by the research.
**Acceptance:**
- Prose explanation covering process model, IPC, monitor-hosting, dispatch-layer, restart-semantics.
- Architecture diagram showing orchestrator process + Phase 1 primitives + session + graceful-degradation hook points.
- Sequence diagrams for `bind_scope` flow and compaction-restore flow.
- Relationship map (consumes all four Phase 1 primitives; consumed by session + future graceful-degradation + future observability aggregator).
- One-page API reference for the IPC surface.
- **Prototyping addendum:** launchd auto-restart latency under SIGKILL/SEGV/OOM/rapid-crash; Unix-socket IPC p95 latency under load (awareness pulls must stay inside a 100 ms per-turn budget). These are measured as part of D7/D4 acceptance respectively.

---

## Spec coverage

| Criterion | Delivered by |
|---|---|
| v1.0 Session-resilience — work queued before session ends completes after restart | D1 + D5 + D7 |
| v1.0 Session-resilience — tasks survive system restart and resume cleanly | D2 + D7 |
| v1.0 Session-resilience — process killed mid-run self-heals or marked failed in bounded window | D2 + D7 |
| v1.0 Session-resilience — compaction preserves persona identity, active work, pending decisions | D8 (orchestrator side) + primary-persona layer's D4 pattern (session side) |
| v1.0 Observability — every action auditable | D9 |
| v1.1 R1 — semantic round-trip upgrade | D6 (orchestrator state); Phase 1 primitives handle their own |
| v1.1 R4 — bundled documentation | D10 |
| v1.1 R11 — OTel observability | D9 |
| Objective-tracker D4 dispatch-layer enforcement | D5 |
| STATE.md rule #7 — background-work awareness, structural | D4 (monitor-hosting) |
| Graceful-degradation hook surface for a separate component | `pause_activation` / `resume_activation` in D5 / D7 |

---

## Dependencies

### Hard dependencies

- **All four sealed Phase 1 components.** Memory, scope-of-work, primary-persona layer, objective tracker. Integration via their public APIs and emission surfaces. **No amendments** — if the build reveals a need, halt and signal.

### Soft dependencies (future consumers)

- Graceful-degradation component (next Phase 2) — calls `pause_activation / resume_activation`.
- Observability aggregator (later Phase 2) — consumes orchestrator OTel emissions alongside Phase 1 primitives'.
- Self-upgrade framework (later Phase 2) — orchestrator's local SQLite participates in the upgrade-fidelity story.

### Permitted runtime dependencies

- Python stdlib (`asyncio`, `sqlite3`, `uuid`, `dataclasses`, `socket`, `signal`)
- `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`, `PyYAML` (already in scope)
- Any other runtime library requires halt-and-signal.

---

## Assumptions (inference recorded — flagged so the builder can challenge)

1. **launchd is the primary platform; systemd-user is parity.** the owner's machine is a Mac (confirmed from earlier context); pOS is single-user local-first. If the builder finds platform-neutral machinery cleaner (e.g. a pure-Python supervisor wrapping the orchestrator), halt and flag.
2. **Unix-domain-socket JSON-RPC is the IPC substrate.** Research's recommendation; stdlib-only; reasonable performance. If the builder finds a measurably better substrate (e.g. `msgspec` for faster marshalling), halt and flag — any additional library requires halt-and-signal per rule 5.
3. **Workspace-supplied `~/.pos/bootstrap.py` is the callback re-registration mechanism.** pOS core defines the contract; workspaces author. Matches Phase 1's framework-vs-content pattern. If the builder finds a cleaner approach (e.g. declarative YAML instead of Python), halt and flag.

---

## Open questions for the owner

Three decisions sharpen the handoff brief. the primary persona has a lean on each.

1. **launchd throttle interval on rapid crashes.** Options: 10s (aggressive restart), 30s (research's lean), 60s (conservative). recommendation: **30s.** Matches reasonable macOS daemon defaults and gives time for a transient cause to clear before looping.

2. **Awareness-pull latency budget.** Research suggests ≤100 ms per-turn. If the prototype shows this is tight, is a hard ceiling preferred, or a soft target with degradation to cached values? recommendation: **hard ceiling with cache fallback.** If the live pull exceeds 100 ms, the session uses the last cached awareness block (stale but present) rather than blocking the turn.

3. **Bootstrap.py failure mode.** If `~/.pos/bootstrap.py` is missing or errors on orchestrator restart, options: (a) orchestrator refuses to start; (b) orchestrator starts in degraded mode (no callback re-registration); (c) orchestrator starts and logs a warning. recommendation: **(a) refuses to start** — matches the fail-closed posture of the primary-persona loader and avoids silent functional gaps.

Default to leans unless any reads wrong to you.

---

## What happens on approval

1. I draft the handoff brief for your review. Six the owner decisions are baked in from research (peer-session-via-Unix-socket, monitor-in-orchestrator, graceful-degradation-is-separate, `bind_scope` at dispatch layer, launchd+systemd supervision, local SQLite for orchestrator state). Plus the three the primary persona leans above on approval.
2. On your brief review, a general-purpose agent is dispatched.
3. Halt-on-deviation applies. Any Phase 1 amendment genuinely required → halt and surface.
