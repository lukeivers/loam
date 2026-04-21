# Session-Resilient Orchestrator — Research

**Component:** Session-resilient orchestrator — the long-running process layer
that binds scopes to objectives, activates them, monitors their execution, and
survives session/system lifecycle events.
**Status:** DRAFT — research document; awaits owner's review.
**Authored by:** research Agent. **Date:** 2026-04-19.
**Research plan:** `research-plan.md` in this directory.

---

## 0. Executive summary

The orchestrator is recommended as **a single long-lived Python process built
on asyncio**, hosted by launchd on macOS (with platform-neutral notes for
systemd). It is the workspace dispatch layer — it owns `bind_scope`
enforcement, activates scopes, observes their lifecycle through scope-of-work's
pyee emitter, and hosts the primary-persona layer's background-work monitor as
an in-process coroutine.

Session resilience is achieved by **rehydrating from the three Phase 1 event
stores** (scope-of-work, objective-tracker, memory-observability) on cold
start. The orchestrator keeps no authoritative state of its own; the only
persistent state it owns is a small checkpoint table (`last_event_id` per
store) written through its own SQLite file. Every primitive already persists
full event history; the orchestrator is a stateless coordinator on top of
them.

Graceful degradation is recommended as a **separate Phase 2 component**, not a
sub-module. The orchestrator ships a narrow degradation-hook interface
(`pause_activation(reason)` / `resume_activation()`) that a future Graceful-
Degradation component calls. Rationale: the orchestrator is deterministic
plumbing, and Claude-API health-checking is policy with an LLM-judged
surface area; keeping them separate preserves the orchestrator's no-LLM-inside
posture and aligns with the "no assumed downstream consumer" (A1) pattern.

The interactive Claude session is a **separate process** from the
orchestrator. They communicate via the orchestrator's local IPC surface (Unix
domain socket carrying line-delimited JSON) **and** through the same
event-sourced SQLite stores the orchestrator writes. The primary-persona
layer's monitor coroutine runs **inside the orchestrator process**; when a
session turn needs an awareness block it calls `GET /awareness?turn_id=...`
over the IPC socket. Placement inside the orchestrator is the single most
load-bearing decision in the design and is defended at length in section 2.4.

Implementation is estimated at **600–750 AI-minutes**, larger than any Phase 1
primitive because every Phase 1 surface must be integrated and three new
concerns are introduced here: process lifecycle, session/orchestrator
separation, and restart semantics.

---

## 1. Survey of existing patterns

This section surveys how other systems solve long-running task orchestration
with session-survival semantics. Each entry answers: what durability model is
used, what restart semantics are offered, what adjacent patterns are
borrowable, what to reject.

### 1.1 Temporal (durable execution engine)

Temporal is the current state-of-the-art for durable workflows. Workflow
mutations are appended to an event history; on worker crash, a new worker
replays the history to reach the previous state, then continues. Execution is
"effectively once" for workflow logic, "at-least-once" for activities (with
idempotency keys to suppress duplicates). Workflows can sleep for days, weeks,
or months, because the event history is the source of truth — workers are
stateless replayers.

**Borrowable:** the **event-replay-from-history** pattern is exactly what
Phase 1 already ships. Scope-of-work's `projection` module rebuilds state from
`scope_events`; objective-tracker's projector does the same. The orchestrator
gets restart-survival "for free" by leaning on these projectors rather than
persisting its own view of the world.

**Reject:** Temporal the service. It requires a server, workers, Cassandra /
Postgres, a CLI, and a Go/Python SDK that injects determinism constraints on
user code (workflows must avoid non-determinism: random numbers, clock reads,
direct network calls, etc.). This is overkill for a single-user local-first
harness, and its dependency footprint is far outside the permitted list
(`stdlib + pydantic + pyee + opentelemetry + PyYAML`).

**Takeaway:** keep the Temporal *idea* (event-sourced history, replay-based
recovery). Build it with the stdlib, not the platform.

### 1.2 Celery + Redis

Celery is the dominant Python distributed task queue. Tasks are placed on a
broker (Redis / RabbitMQ / SQS); workers claim them, execute, acknowledge.
Durability hinges on `task_acks_late=True` (ack after completion) and
`task_reject_on_worker_lost=True` (requeue if worker crashes). A visibility
timeout bounds how long a task can be in-flight before the broker redelivers.

**Borrowable:** the **visibility-timeout / stale-task detection** idea maps
cleanly to scope-of-work's `is_stuck` rule (`elapsed > 2 × expected, no state
events since start`). The orchestrator can rely on that rule rather than
inventing its own timeout machinery.

**Reject:** Redis and its queue model. Redis is "more susceptible to data loss
on abrupt termination" (docs), and introducing a second persistence store
alongside SQLite event logs is unjustified complexity. The broker/worker split
also presumes horizontal scale the pOS single-user design never needs.

**Takeaway:** there is no queue. Scope state *is* the queue (scopes in `active`
are what's running; scopes in `pending` are what's queued); the orchestrator
polls/subscribes rather than dequeues.

### 1.3 APScheduler

APScheduler is a Python library (not a service) that runs scheduled jobs on
an asyncio, threading, or gevent event loop. It offers four job stores
(memory, SQLAlchemy, MongoDB, Redis) and survives restart when configured with
a persistent store — "when the scheduler is restarted, it will run all the
jobs it should have run while it was offline."

**Borrowable:** the **in-process scheduler** model. The orchestrator can host
an APScheduler-shaped scheduling loop directly — no external service, no
broker, no worker pool. The "catch up on missed runs" behaviour is the
semantics the orchestrator needs for timed triggers (scope escalations,
heartbeat checks).

**Reject:** APScheduler itself as a dependency. Its persistence uses pickle
(opaque schema, upgrade-fragile), which violates v1.1 R1's upgrade-fidelity
requirement. Phase 1 already ships an event-sourced store with durable schema
— use that, not pickled job tables.

**Takeaway:** build the scheduling loop directly on `asyncio`. Store scheduled
jobs (if any) as events in scope-of-work's event log (a `TriggerFired` or a
new `ScheduledActivationDue` event), not as pickle blobs.

### 1.4 Rocketry

Rocketry is a statement-based scheduling framework ("run every Monday at 10am
unless X"). It coexists with asyncio and provides a declarative task
definition. It has no built-in durability; schedules live in Python code.

**Borrowable:** the **declarative-scheduling language** idea is the right
shape for future cron-like user configuration. Not in scope for Phase 2.

**Reject:** Rocketry as a dependency. Not on the permitted list. Its lack of
persistence means Rocketry alone cannot meet session-resilience.

**Takeaway:** the orchestrator exposes a scheduling API that a future
config-driven scheduler component can consume.

### 1.5 launchd idioms for single-user local daemons

macOS's native service manager. Per-user services are registered as "launchd
user agents" via a plist under `~/Library/LaunchAgents/`. Key knobs:

- `KeepAlive = true` — always restart on exit.
- `KeepAlive = { SuccessfulExit: false }` — only restart on non-zero exit.
- `ThrottleInterval = N` — minimum seconds between restart attempts (default
  10). Rapid-restart crash loops are throttled.
- `RunAtLoad = true` — start when the user logs in.
- `StandardOutPath` / `StandardErrorPath` — file-based log capture.

User agents run only while the user is logged in — this matches pOS's
single-user posture exactly.

**Borrowable:** plist + `KeepAlive` is the right supervisor for the
orchestrator. A well-behaved orchestrator exits cleanly on `SIGTERM` and lets
launchd restart it on crash. The "throttle interval" provides crash-loop
safety without custom code.

**Reject:** nothing — launchd is the right platform primitive.

**Takeaway:** section 5 includes a plist sketch. Linux equivalent is a
user-level systemd unit (`~/.config/systemd/user/`), functionally identical.

### 1.6 Letta's server mode

Letta runs agents as persistent server-side services, not library calls. All
state (memory, messages, reasoning, tool calls) persists in Postgres. Agents
have their own execution loops that survive client disconnect, and the
"background execution" mode offers resumable streams.

**Borrowable:** the **agent-as-long-running-server** separation from the
client. pOS already has this shape in its Phase 1 design — primary-persona
layer's monitor is the background-awareness function; the orchestrator hosts
it; the session is the client. Letta confirms the shape scales to production.

**Reject:** Postgres + Kubernetes as dependencies. Letta optimises for
multi-tenant horizontal scale; pOS is single-user, single-machine.

**Takeaway:** the division of responsibility — "agent lives in the server, UI
attaches" — is correct. In pOS the "server" is the orchestrator and the
"attach" is the interactive Claude session over a local socket.

### 1.7 Anthropic Agent SDK session patterns

The Managed Agents / Agent SDK V2 session model treats the **Session** as a
persistent append-only event log of everything that happened: user messages,
model reasoning, tool calls, results. Harness crash is recovered via
`wake(sessionId)` — a new harness process reads the event log and resumes from
the last event. `emitEvent(id, event)` writes, `getEvents()` reads positional
slices.

**Borrowable:** this is the **same event-log-as-truth** pattern as Temporal,
but scoped to an agent session. The pOS orchestrator's session-resilience
story should be recognisable to anyone who has used this SDK: scopes are
defined by their event log; a new orchestrator process can resume any scope
by replaying events.

**Reject:** the SDK itself as framework. pOS builds its own session-like
surface on top of Phase 1 event stores rather than binding to the SDK's
session model, because:

1. The permitted dep list does not include the Agent SDK runtime.
2. pOS's "session" is an interactive Claude-CLI session plus zero or many
   parallel scopes; it is broader than a single agent session.

**Takeaway:** adopt the vocabulary — "session as event log," "wake to
resume" — and implement it with Phase 1 primitives.

### 1.8 Synthesis — what pOS can borrow, what it must not

| Concern | Borrow from | What it looks like in pOS |
|---|---|---|
| Durability model | Temporal, Agent SDK | Event-sourced SQLite per-primitive (already in Phase 1); orchestrator replays on boot |
| Scheduler | APScheduler (shape, not lib) | asyncio task running inside the orchestrator process |
| Supervisor | launchd (macOS) / systemd (Linux) | User-level service with `KeepAlive=true`, `ThrottleInterval=30` |
| Session/agent split | Letta, Agent SDK | Session process attaches to orchestrator over Unix domain socket |
| Restart semantics | Temporal, Agent SDK | `wake()`-equivalent is `orchestrator_boot()` — replay event logs |

What to reject: external brokers (Redis, RabbitMQ), external state stores
(Postgres, Mongo), framework-level determinism constraints (Temporal-SDK
style), pickle persistence (APScheduler default), and any library outside the
permitted list.

---

## 2. Recommended design shape

Each subsection covers one of the eight research-plan question groups:
options considered, recommended option, rationale.

### 2.1 Process model (Question group 1, Q1)

**Options considered.**

- (A) Single long-running Python asyncio process hosting everything — scope
  runtime, objective tracker, monitor, scheduler, IPC server.
- (B) Supervisor + N workers — orchestrator process spawns worker subprocesses
  for scope execution.
- (C) Thread-per-scope inside one process.
- (D) Entirely in-session (no separate orchestrator process; everything runs
  inside the interactive Claude CLI process).

**Recommendation: (A) single asyncio process.**

**Rationale.**

1. **The primitives are already event-sourced.** Scope-of-work and
   objective-tracker both persist every mutation to SQLite with WAL. The
   orchestrator does not need to provide durability; it consumes the primitive
   durability. This removes the usual reason to favour a multi-process model
   (isolated worker memory), because a crash does not lose work — the event
   log holds it.
2. **Single-user, local-first.** Horizontal scale is an explicit non-goal. No
   worker-pool pattern earns its complexity for one user on one machine.
3. **Phase 1 is asyncio-native.** `ScopeRuntime.create/start/...` are
   coroutines; the monitor is an asyncio task; objective-tracker's `bind_scope`
   is a coroutine. Forcing a multi-process split would require either IPC
   round-trips for every primitive call or duplicate primitive instances per
   process — both add failure modes without benefit.
4. **Permitted dep list excludes heavyweight IPC libraries.** A multi-process
   model with clean IPC typically wants `grpc`, `multiprocessing`'s shared
   managers, or a message bus; none are permitted. Single-process avoids the
   question.
5. **Option (D) — everything in session — is rejected** because it sacrifices
   the foundational session-resilience property: when the session process
   dies, every scope dies with it. The orchestrator exists precisely so work
   outlives the session.

**Known risks and mitigations.**

- **CPU-bound work blocks the event loop.** Mitigation: scope execution is
  I/O-bound by construction (LLM calls are network-bound; scope-of-work debits
  are fast SQLite writes). If CPU-bound work arises later, `asyncio.to_thread`
  or a threadpool handles it without restructuring the process model.
- **One crash kills everything.** Mitigation: launchd `KeepAlive=true`
  restarts the process; the event-log rehydration path restores state.

### 2.2 Boot, shutdown, platform integration (Q2)

**Recommendation: launchd on macOS, user-agent plist; systemd-user on Linux.
Platform-neutral packaging via a `pos-orchestrator` CLI.**

The orchestrator is invoked as `pos-orchestrator start` (foreground) /
`pos-orchestrator daemon` (backgrounded, for development). launchd or systemd
runs the foreground form and handles supervision.

- **Boot sequence:** parse config → open SQLite stores (scope, objective,
  optional memory pointer) → rebuild scope state projection via
  `ScopeRuntime(db_path)` (existing behaviour) → construct `ObjectiveTracker`
  and wire `subscribe_scope_emitter` → start background-work monitor → start
  IPC server on Unix domain socket → signal readiness (write a PID file or
  emit a "ready" span).
- **Shutdown sequence:** on `SIGTERM`, stop the IPC server first (reject new
  client requests with a shutdown code), drain in-flight IPC calls with a
  5-second grace, cancel the monitor's tick loop (it will finish its current
  tick), flush OTel buffers, close SQLite connections, exit 0.

Boot is idempotent because rebuilding the projection from the event log is
idempotent (projectors are pure functions over events).

### 2.3 Orchestrator–session boundary (Q3)

**Options considered.**

- (I) Orchestrator hosts the session — the interactive Claude CLI runs as a
  subprocess owned by the orchestrator.
- (II) Session hosts the orchestrator — Claude CLI spawns the orchestrator as
  a child on first interactive run.
- (III) Peer processes — both start independently; they discover each other
  via a well-known socket path.

**Recommendation: (III) peer processes.**

**Rationale.**

1. **Session lifetime is human-driven; orchestrator lifetime is
   infrastructure-driven.** the owner closes the terminal when the owner is done thinking
   for the day; the orchestrator keeps scopes alive through the night. Binding
   the orchestrator to a session-owned process tree means closing the terminal
   kills background work — the exact failure mode the spec forbids.
2. **Session can reconnect.** If the orchestrator restarts (launchd), the
   next interactive turn finds it via the well-known socket. No "lost parent"
   state to reconcile.
3. **Claude Code / the interactive CLI is a black box we do not control.**
   Using it as a parent process for a long-running daemon would be fragile
   and upgrade-hostile. Better: the CLI invokes a small in-session adapter
   that speaks to the orchestrator over the socket.
4. **Option (I) is a common mistake; it is the shape current pOS's
   `bin/orch` aspires to**, and is explicitly not a reference implementation
   per the brief.

**Discovery:** the orchestrator writes `~/.pos/run/orchestrator.sock` at boot.
The session adapter opens it. If the socket is missing, the session reports
"orchestrator unreachable" as a structured event — no auto-spawning.

### 2.4 Monitor placement (Q4, Q21)

This is the load-bearing decision flagged in the research plan. The
background-work monitor is a long-lived asyncio coroutine that (a) subscribes
to scope-of-work's pyee emitter, (b) ticks every 30s for stuck detection, (c)
produces an awareness block on `on_user_prompt(turn_id)`. Where it runs
determines session-resilience, awareness freshness, and the entire
orchestrator–session contract.

**Options considered.**

- (α) Monitor runs inside the orchestrator process; session requests the
  awareness block over IPC when a turn arrives.
- (β) Monitor runs as a peer process; orchestrator and session both subscribe
  to its output.
- (γ) Monitor runs in-session; boots at session start, subscribes to
  scope-of-work pyee, dies at session end.

**Recommendation: (α) — monitor runs inside the orchestrator.**

**Rationale.**

1. **Scope-of-work's pyee emitter is in-process.** The `AsyncIOEventEmitter`
   delivers events on the emitting process's event loop; cross-process
   subscription requires polling `poll_external_events()` against the
   `scope_events` table. A monitor that wants *low-latency* per-event
   awareness must share the process with scope-of-work. Since the orchestrator
   hosts scope-of-work, the monitor lives with it.
2. **The monitor's stuck-detection and awareness accumulation must survive
   session resets.** Under (γ), the monitor's in-memory awareness state is
   lost every time the session ends. Under (β), the peer process adds a
   third service to supervise for no real benefit. Under (α), the monitor's
   state is a function of scope-of-work state, which the orchestrator
   already persists.
3. **The awareness block is cheap to compute on demand.** Under (α), the
   session's `UserPromptSubmit` hook calls
   `GET /awareness?turn_id=T` over the socket; the orchestrator calls
   `monitor.on_user_prompt(T)`; the monitor returns the AwarenessBlock. The
   monitor already caps at ≤1k tokens — one IPC round-trip is comfortable.
4. **Compaction-survival payload is similarly computed on demand.** When the
   session's `PreCompact` hook fires, the session asks the orchestrator for
   the survival payload via IPC (`GET /compaction-survival`); the
   orchestrator calls `compaction.consume_survival_payload(...)` using the
   loaded contract + scope list + memory provider.
5. **The persona contract is loaded inside the orchestrator.** Because
   `PersonaLoader.load()` reads disk and validates, it is cheap to run on
   orchestrator boot and keep a cached `LoadedPersona`. The session never
   touches the contract directly; it asks the orchestrator for identity,
   authority, etc. This puts the authoritative persona identity in one place
   rather than duplicated in every session.

**Cross-reference:** the primary-persona layer's `BackgroundWorkMonitor` is
designed as a long-lived asyncio task with a callback-based pyee subscription
and a tick loop. Nothing in that design assumes it runs in-session; the
import `from scope_of_work.runtime import ScopeRuntime` (monitor.py:31)
establishes that it needs access to a `ScopeRuntime` instance. The
orchestrator owns that instance.

**Open sub-question:** is there a use case for the awareness block to
auto-push to the session rather than be pulled? Answer: no, and the research
plan doesn't require it. The session's `UserPromptSubmit` hook pulls on each
turn; pushing would require the orchestrator to know which session is active,
adding coupling for no benefit.

### 2.5 Dispatch layer and `bind_scope` enforcement (Q5, Q6, Q7)

**The orchestrator is the workspace dispatch layer.** Objective-tracker's D4
acceptance specifies "the workspace dispatch layer calls
`tracker.bind_scope(scope_id, objective_id)` before activating any scope." No
other component in Phase 1 / Phase 2 takes this role. Putting the enforcement
anywhere else (scope-of-work, session, a shim) either:

- Violates "no amendments to sealed Phase 1 components" (if we try to push it
  into scope-of-work), or
- Allows a session to activate scopes without enforcement (if we leave it in
  the session).

**Concrete call-site sequence for activating a scope:**

```
caller (session or internal trigger) →
  orchestrator.activate_scope(scope_id, objective_id) [IPC or direct]
    ↓
  orchestrator asserts: scope exists in scope-of-work, state ∈ {pending, paused}
    ↓
  orchestrator calls tracker.bind_scope(scope_id, objective_id)
    ├── success → ScopeBound event persisted, binding table updated
    └── raises UnresolvedObjectiveError / OrphanRootError
           ↓
         orchestrator records a bind_refused event in its own event store,
         emits OTel span pos.orchestrator.bind_refused,
         returns error to caller. Scope stays in its current state.
    ↓ (on bind success)
  orchestrator calls scope_runtime.start(scope_id)
    ├── success → scope transitions to active, OTel invoke span opened
    └── raises (illegal transition, etc.) → orchestrator records dispatch_failed,
         bind_scope event is left in place (orphan binding) — this is
         acceptable because binding is monotonic per the tracker's contract;
         a paired event is sufficient for observability.
    ↓ (on start success)
  orchestrator emits a scope_activated event on its own pyee emitter
  (for any peer observers, e.g. future graceful-degradation)
    ↓
  scope runs to completion via its registered callback; scope-of-work's
  runtime emits state events; monitor consumes them; orchestrator is
  passive until another dispatch call arrives.
```

**Failure behaviour on `bind_scope` raise (Q6): the orchestrator refuses
activation, persists a `bind_refused` event, surfaces a structured error to
the caller.** No retry; the caller (session or cascade) must resolve the
objective (author it) before retrying. This is the correct default because
`OrphanRootError` specifically means "this scope is descendant of a non-user
objective root" — retrying does not fix the ancestry.

**Q7 — scheduling engine or thin wrapper?** **Thin wrapper, plus a small
scheduling loop for timed triggers.**

The orchestrator is *not* a full scheduling engine (no priority queues, no
complex constraints). Scope-of-work already owns:

- Pending extension handling (scopes that exhaust budget are auto-paused).
- Budget exhaustion policies (`request_extension`, `halt_and_signal`,
  `throttle`).
- Trigger fire semantics.
- Cascade-to-children on parent cancel.

What the orchestrator adds:

- `activate_scope(scope_id, objective_id)` — binds then starts.
- `activate_pending()` — a periodic pass that looks for scopes stuck in
  `pending` longer than a threshold and surfaces them (no auto-activate; the
  cause is almost always an authoring gap).
- A timer loop for scope-of-work `deadline` triggers (if a scope has a
  wall-clock deadline trigger, the orchestrator sleeps until that time and
  calls `scope_runtime.evaluate_success_criterion(...)` or equivalent to
  fire the trigger). This is the one place the orchestrator owns scheduling:
  otherwise it is reactive.

**Concurrency and prioritisation (Q18, Q19, Q20).** Phase 2 punts on
priority. Scopes are activated in the order the caller requests them; within a
scope, budget governs its behaviour. Concurrency is "as many scopes as the
event loop can drive without starving"; the orchestrator does not impose a
global concurrency cap in Phase 2. Rationale:

- Pair of risks: either the orchestrator over-schedules (Claude rate limit
  returns the failure; scope marks failed) or under-schedules (latency
  increases but correctness is preserved). The over-schedule path is
  already handled by scope-of-work's budget-exhaustion / failure events.
  Adding a cap now is premature optimisation.
- A future prioritisation component can consume scope-of-work's `owner_persona`
  and `budget` fields and impose whatever priority it wants — the
  orchestrator exposes the hooks.

**Q20 — long-running scopes that block the queue.** There is no queue; there
are many concurrent scopes. Long-running scopes do not block anyone else. A
*single* scope that does CPU-bound work would starve the event loop; the
mitigation is the scope's implementation uses `asyncio.to_thread` — not the
orchestrator's problem.

### 2.6 Session-resilience and restart semantics (Q8, Q9, Q10)

**Q8 — "work queued before a session ends completes after session restart."**

"Queued" is either (a) a scope in `pending` waiting to be activated, or (b) a
scope in `active` whose callback is running. Both are durable:

- A `pending` scope is a `ScopeCreated` event in `scope_events` and no
  subsequent `StateTransitioned` event. On orchestrator boot, the projection
  rebuilds and the scope is visible to `list(states=[pending])`. A startup
  pass (`activate_pending()`) surfaces it.
- An `active` scope is a scope whose last event is a `StateTransitioned →
  active`. The orchestrator's boot sequence walks `list(states=[active])`
  and, for each, checks whether the scope has an in-process callback to
  resume (if the scope stored a resumable-state marker) or is in "active but
  nothing running" (in which case the orchestrator marks it `failed` with
  `reason="orchestrator_restart_lost_callback"` — this is the bounded-window
  fail-mode required by the spec). See restart-semantics section 7 for
  details.

No session intervention is needed for (a). For (b), "without user
intervention" is preserved because the failure marker is automatic; the spec
allows "fail with recoverable state" as an alternative to "self-heal."

**Q9 — system restart survival.** Laptop reboot kills the orchestrator
process. On next login, launchd re-launches it. Boot sequence rebuilds
projection from the event log; all scopes visible exactly as before reboot.
Memory, objective-tracker, scope-of-work all survive because their stores are
WAL-journaled SQLite files. No additional orchestrator work needed.

**Q10 — self-heal threshold.** The orchestrator exposes a configurable
`heartbeat_stale_seconds` (default **300s / 5 minutes**). Mechanism:

- The orchestrator writes a heartbeat row (`orchestrator_heartbeat` table)
  every 60s.
- On boot, the orchestrator compares the last heartbeat timestamp against
  `now`. If the gap exceeds `heartbeat_stale_seconds`, the orchestrator's
  boot path is the "cold restart" path: every scope in `active` is examined
  to decide resume vs fail. If the gap is below, the boot is "warm" and
  active scopes are re-examined but not auto-failed.
- launchd's `ThrottleInterval=30` prevents crash loops. launchd does not
  provide "mark failed if the process has been down >X" — the orchestrator
  does that itself on its first boot after the gap.

**The self-heal semantics for individual scopes on cold restart:**

- If a scope's last event is `StateTransitioned → active` and the wall-clock
  gap exceeds `max_scope_silence_seconds` (default **2 × expected_duration**,
  same rule as `is_stuck`), mark the scope `failed` with
  `reason="orchestrator_cold_restart"`, emit a cascade halt if the scope had
  children with `TERMINATE` policy. This uses scope-of-work's existing
  `cancel` / `fail` APIs — no amendments.
- If a scope has `resumable=true` in its spec constraints (a caller-set hint,
  not a sealed field), the orchestrator attempts to re-invoke the scope's
  registered callback with a resume flag. This is opt-in and conservative.

### 2.7 Compaction-event survival (Q11, Q12)

**Q11 — what does the orchestrator add.** The primary-persona layer owns the
replay-from-authoritative-sources pattern (`CompactionSurvivor`). The
orchestrator's contribution:

- **Hosting the compaction-survival machinery in a stable process.** The
  `PersonaLoader` is instantiated in the orchestrator; the contract is
  loaded once at boot; the `CompactionSurvivor` uses that loaded contract
  as its identity source. Without a stable process, the contract is
  re-loaded per session and drift is possible (the session could have a
  stale contract cached). With the orchestrator, the contract is reloaded
  only on orchestrator boot or explicit `reload` IPC call.
- **Exposing a compaction-survival IPC endpoint.** The session's `PreCompact`
  hook fires, the session calls
  `POST /compaction-survival?turn_id=T&flag=set`; the next `UserPromptSubmit`
  calls `GET /compaction-survival?turn_id=T` which consumes the flag and
  returns the survival payload. This keeps flag state in the orchestrator's
  SQLite (so cross-session or cross-restart the flag is not lost).
- **Observability.** The orchestrator emits `pos.orchestrator.compaction_handoff`
  spans wrapping the pre-compact flag set and the survival payload delivery.

**Q12 — mid-session compaction of the interactive session.** The compaction
is the session's event; the session's PreCompact hook fires. The orchestrator
does *not* pause scopes on session compaction: compaction affects the
session's context window, not the orchestrator's event loop. The monitor's
awareness block will continue to be updated; the session simply asks for a
fresh one on the next turn.

If the owner decides later that some scopes should pause on session compaction,
that is a workspace policy, not an orchestrator concern. The hook exists
(compaction flag) — the policy can read it.

### 2.8 Integration with primary-persona layer's authoring (Q22, Q23)

**Q22 — authoring scope activation path.** When the primary persona's
autonomous-authoring pipeline creates a new specialist-authoring scope, the
scope is activated through the same path as any other scope: bind to its
parent objective (the authoring objective, which terminates at a user root),
then start. Nothing special. The authoring pipeline itself runs inside the
scope; the orchestrator has no role in its four-step internals.

**Q23 — monitor escalation event ownership.** When scope-of-work's monitor
detects a stuck scope and raises an escalation, the primary-persona layer
converts this into a user-facing message (via the introduction / notification
surface). The orchestrator's role is passive: it hosts the monitor, which
uses the persona's communication surface. The orchestrator does not
autonomously escalate — "escalate" is a persona authority, not an
infrastructure authority.

---

## 3. Graceful-degradation decision

**Recommendation: separate Phase 2 component, not a sub-module of the
orchestrator.**

### 3.1 Options considered

- (X) Fold degradation into the orchestrator. `activate_scope` becomes
  aware of Claude health; on degradation, it pauses new activations and
  optionally pauses in-flight scopes.
- (Y) Separate Graceful-Degradation component that subscribes to
  orchestrator emissions and calls a narrow `pause_activation / resume_activation`
  API on the orchestrator.
- (Z) Shared library — a `degradation` Python module imported by both the
  orchestrator and other consumers.

### 3.2 Recommended option: Y

### 3.3 Rationale

1. **Different failure models.** The orchestrator's failure surface is
   process-lifecycle (crash, restart, shutdown). Graceful-degradation's
   failure surface is remote-LLM health (rate-limit, 5xx, garbage responses,
   model down). Mixing them conflates two debug surfaces and puts LLM policy
   inside what should be deterministic infrastructure.
2. **LLM judgement lives in graceful-degradation, not the orchestrator.**
   Detecting "Claude is returning garbage" is not a keyword match on HTTP
   codes — it is a judgement call that the spec's acceptance criterion
   implies ("user is informed before blast radius exceeds a declared
   threshold"). That judgement is itself LLM-inferred work, which violates
   the "no LLM inside the orchestrator" constraint if folded in.
3. **The A1 pattern applies.** Phase 1 primitives emit observability without
   assuming a consumer. The orchestrator should emit activation events and
   `claude_call_result` events; graceful-degradation consumes them and
   decides to pause. If graceful-degradation is never built, the orchestrator
   functions without degraded handling — degraded handling simply does not
   exist.
4. **Testing separation.** The orchestrator's tests are deterministic
   integration tests against scope-of-work + objective-tracker; graceful-
   degradation's tests must simulate Claude outages, which is a different
   test shape and harness (fault injection).
5. **A narrow interface is cheap to define.** The orchestrator exposes
   `pause_activation(reason: str)` and `resume_activation()` — two calls.
   When paused, `activate_scope` raises `ActivationPaused(reason)` and
   records a `bind_refused` event with `reason_class=degradation`. Scopes
   already `active` keep running; whether to pause them is graceful-
   degradation's call (and it does so by sending scope-of-work a
   `scope_runtime.pause(scope_id, reason="degradation")` for each).

### 3.4 User-facing signal

When graceful-degradation activates, the primary-persona layer (via the
monitor and the communication channel) surfaces the degradation state — same
surface used for any other escalation. The orchestrator does not own the
user-facing narrative; it emits the machine signal that graceful-degradation
converts to a persona message. This matches the spec's acceptance: "user is
informed before blast radius exceeds a declared threshold."

### 3.5 Sub-module vs separate component — summary

- The orchestrator provides the *hook*; graceful-degradation provides the
  *policy*.
- Separating them means graceful-degradation can be designed and shipped
  independently, as its own Phase 2 component, on its own timeline, without
  blocking the orchestrator.

---

## 4. Acceptance-criterion coverage map

This section maps each Session-resilient acceptance criterion from the
objectives spec (v1.0 + v1.1 + v1.2) to the piece of the design that
delivers it. Where a criterion cannot be satisfied without a halt signal,
that is flagged in section 12.

### 4.1 Session-resilience criteria (v1.0 + addenda)

| # | Criterion (paraphrased) | Delivered by |
|---|-----|-----|
| SR1 | Work queued before session ends completes after restart without user intervention | §2.6 — queued scope is a `pending` event; `activate_pending()` on boot surfaces it; no user intervention required |
| SR2 | Tasks survive system restart (laptop reboot, Claude CLI exit) and resume cleanly | §2.2 + §7 — launchd `RunAtLoad=true` re-launches orchestrator; boot replays event logs |
| SR3 | Process killed mid-run either self-heals OR is marked failed with recoverable state within a bounded window | §2.6 Q10 + §7 — `heartbeat_stale_seconds` + `max_scope_silence_seconds`; bounded 5-minute self-heal window |
| SR4 | Compaction events preserve persona identity, active work items, pending decisions | §2.7 — CompactionSurvivor hosted in orchestrator; payload computed on demand from authoritative sources |

### 4.2 Graceful-degradation criteria (separate component, but orchestrator must provide hooks)

| # | Criterion (paraphrased) | Delivered by |
|---|-----|-----|
| GD1 | Simulated 1-hour Claude outage does not corrupt in-flight scope state | §3 + §2.5 — orchestrator's `pause_activation` pauses dispatch; in-flight scopes either complete or pause via scope-of-work's existing mechanisms |
| GD2 | Sessions resume cleanly once upstream returns | §3 — `resume_activation` lifts the pause; scope state is unchanged throughout |
| GD3 | User informed before blast radius exceeds declared threshold | Delivered by **graceful-degradation component**, not the orchestrator (see §3) |

### 4.3 v1.1 R11 — observability criteria

| # | Criterion | Delivered by |
|---|-----|-----|
| R11 | pOS observability exposes OTel as internal-operation trace format | §9 — orchestrator emits OTel spans/events on every operation; uses default no-op tracer if no consumer |
| A1 | No assumed downstream consumer | §3.3 point 3 — graceful-degradation separate; orchestrator functions without any consumer wired |

### 4.4 Objective-tracker D4 — bind_scope enforcement

| # | Criterion | Delivered by |
|---|-----|-----|
| D4 | Workspace dispatch layer calls `tracker.bind_scope(...)` before activating any scope | §2.5 — `activate_scope` calls `bind_scope` as its first step; binding is guarded and ordered before `scope_runtime.start` |

### 4.5 Primary-persona survival-list criteria (v1.0)

| # | Criterion | Delivered by |
|---|-----|-----|
| S1 | Compaction preserves persona identity | §2.4 — loaded contract in orchestrator; `GET /compaction-survival` returns it |
| S2 | Compaction preserves active work items | Scope list from scope-of-work on demand |
| S3 | Compaction preserves pending decisions | Paused-awaiting-extension scopes via `list(include_pending_extension=True)` |
| S4 | Compaction preserves recent corrections | Via memory-system `RecentCorrectionsProvider` callable wired at orchestrator construction |
| S5 | Compaction preserves authority boundary | Loaded contract's `authority_boundary` field |

### 4.6 STATE.md rule #7 — background-work awareness

| # | Criterion | Delivered by |
|---|-----|-----|
| ST7 | Interactive session never loses awareness of active background work | §2.4 — monitor hosted in orchestrator; awareness block delivered on every UserPromptSubmit via IPC |

No criterion in the Session-resilient family is flagged as unsatisfiable.

---

## 5. Process and platform specification

### 5.1 launchd plist sketch (macOS)

Written to `~/Library/LaunchAgents/com.pos.orchestrator.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.pos.orchestrator</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/&lt;user&gt;/.pos/venv/bin/python</string>
    <string>-m</string>
    <string>pos_orchestrator</string>
    <string>start</string>
    <string>--config</string>
    <string>/Users/&lt;user&gt;/.pos/config.yaml</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ThrottleInterval</key>
  <integer>30</integer>
  <key>StandardOutPath</key>
  <string>/Users/&lt;user&gt;/.pos/log/orchestrator.out.log</string>
  <key>StandardErrorPath</key>
  <string>/Users/&lt;user&gt;/.pos/log/orchestrator.err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>POS_HOME</key>
    <string>/Users/&lt;user&gt;/.pos</string>
  </dict>
  <key>WorkingDirectory</key>
  <string>/Users/&lt;user&gt;/.pos</string>
</dict>
</plist>
```

**Knobs explained:**

- `RunAtLoad=true` — start on login.
- `KeepAlive=true` — restart on any exit. (Can be narrowed to
  `SuccessfulExit=false` if we want graceful shutdown to remain down — in
  Phase 2 we want restart-on-anything because the orchestrator is the
  always-on substrate.)
- `ThrottleInterval=30` — crash-loop safety. Gives the operator 30 seconds
  to `launchctl unload` if the process is genuinely broken and looping.
- Log paths are file-based; the orchestrator also emits OTel, which can be
  exported separately.

### 5.2 systemd-user unit (Linux parity)

Written to `~/.config/systemd/user/pos-orchestrator.service`:

```
[Unit]
Description=pOS Orchestrator
After=default.target

[Service]
ExecStart=%h/.pos/venv/bin/python -m pos_orchestrator start --config %h/.pos/config.yaml
Restart=always
RestartSec=30
StandardOutput=append:%h/.pos/log/orchestrator.out.log
StandardError=append:%h/.pos/log/orchestrator.err.log
Environment=POS_HOME=%h/.pos

[Install]
WantedBy=default.target
```

Enabled via `systemctl --user enable pos-orchestrator`. Functional parity
with launchd, same knobs.

### 5.3 CLI and directory layout

```
~/.pos/
├── config.yaml                     # orchestrator config (socket path, DB paths, heartbeats)
├── run/
│   └── orchestrator.sock           # Unix domain socket; session attaches here
├── log/
│   ├── orchestrator.out.log
│   └── orchestrator.err.log
├── db/
│   ├── scope_of_work.sqlite        # scope-of-work event store
│   ├── objective_tracker.sqlite    # objective tracker event store
│   └── orchestrator.sqlite         # orchestrator's own small store (heartbeats, compaction flags)
└── venv/                           # isolated Python env (stdlib + permitted deps)
```

CLI:

- `pos-orchestrator start` — foreground run (used by launchd / systemd).
- `pos-orchestrator status` — read heartbeat, report uptime, print active
  scope count.
- `pos-orchestrator reload` — send `SIGHUP`; the orchestrator re-reads
  persona contract and config.
- `pos-orchestrator halt-cascade <scope_id>` — convenience wrapper for
  operator use.

### 5.4 IPC protocol (orchestrator ↔ session)

Line-delimited JSON over Unix domain socket. Minimal endpoints:

- `GET /awareness?turn_id=T` → `AwarenessBlock` JSON.
- `GET /compaction-survival?turn_id=T&flag=set|consume` → flag management
  + payload on consume.
- `POST /activate {scope_id, objective_id}` → `{result: "activated"|"refused", reason?}`.
- `GET /status` → `{uptime, active_scope_count, heartbeat_age}`.
- `POST /pause-activation {reason}` — called by graceful-degradation.
- `POST /resume-activation` — called by graceful-degradation.
- `GET /persona` → loaded contract summary (identity, authority boundary
  for compaction-survival use).

Protocol is deliberately trivial; it can be replaced by a richer channel
(gRPC, HTTP) in a later phase without changing orchestrator internals.

---

## 6. Dispatch-layer sequence diagram

```
SESSION PROCESS                    ORCHESTRATOR PROCESS
───────────────                    ────────────────────

user asks persona "do X"
  │
  ▼
primary persona decides
to run scope S under
objective O
  │
  ├── session adapter: POST /activate {scope_id=S, objective_id=O}
  │                           │
  │                           ▼
  │                    orchestrator.activate_scope(S, O):
  │                           │
  │                           ├── read scope_runtime.get(S) → check exists + pending
  │                           │     └── missing → respond 404 "scope unknown"
  │                           │
  │                           ├── tracker.bind_scope(S, O):
  │                           │     │
  │                           │     ├── objective ancestry walked
  │                           │     ├── terminal root check: authored_by == "user"?
  │                           │     │
  │                           │     ├── ok → ScopeBound event appended
  │                           │     │         binding row written
  │                           │     │         pyee fan-out to subscribers
  │                           │     │
  │                           │     └── raise OrphanRootError / UnresolvedObjectiveError
  │                           │         │
  │                           │         ▼
  │                           │   orchestrator records bind_refused event
  │                           │   emits OTel pos.orchestrator.bind_refused
  │                           │   respond 409 with structured error
  │                           │
  │                           ├── scope_runtime.start(S):
  │                           │     │
  │                           │     ├── legal transition pending→active
  │                           │     ├── StateTransitioned event appended
  │                           │     ├── OTel invoke span opened
  │                           │     ├── pyee event fan-out
  │                           │     │      └── monitor sees state event, updates awareness
  │                           │     └── projection cache updated
  │                           │
  │                           └── emit pos.orchestrator.scope_activated event
  │                              respond 200 {result: "activated"}
  │
  ◀──────── response ──────── │
  │
  ▼
session reports to user
  │
  ... meanwhile ...
  │
  orchestrator's scope callback runs (registered via
  scope_runtime.register_callback(handle, fn) at boot);
  the callback makes LLM calls, debits budget via
  scope_runtime.debit(...), evaluates success criteria.
  │
  ▼
on scope complete / fail / cancel:
  │
  ├── StateTransitioned event appended
  ├── monitor sees event, updates its internal state
  ├── tracker auto-evaluates success criteria (via subscribe_scope_emitter)
  └── observers notified via pyee

next user turn:
  │
  ├── session adapter: GET /awareness?turn_id=T
  │                           │
  │                           ▼
  │                    monitor.on_user_prompt(T)
  │                           │
  │                    returns AwarenessBlock (≤ 1k tokens)
  │
  ◀──────── block ──────── │
  │
  ▼
session injects block into next Claude turn
```

The diagram makes visible that:

- Every scope activation is preceded by a bind, which is preceded by an
  objective-tracker walk that enforces the root-user invariant.
- The monitor's awareness block is pulled per-turn by the session, not
  pushed.
- Scope execution is asynchronous relative to the dispatch call — the
  activate response returns as soon as the scope enters `active`, not when
  it completes.

---

## 7. Restart-semantics specification

### 7.1 Failure classes

| Class | Trigger | Orchestrator behaviour |
|---|---|---|
| **Graceful stop** | `SIGTERM` from launchd / user | Drain IPC, cancel monitor, flush OTel, close DB, exit 0. On next boot: warm start (no auto-fail of active scopes). |
| **Kill mid-run** | `SIGKILL`, segfault, OOM | Process exits immediately. launchd restarts. On next boot: orchestrator reads heartbeat; if gap > 5 min → cold start; else warm start. |
| **System reboot** | Laptop restart | Process exits with system. launchd re-launches on next login. Treated as cold start (heartbeat gap is large). |
| **Claude outage** | API returning 5xx / garbage | **Does not affect orchestrator process lifecycle.** Handled by graceful-degradation component; orchestrator may receive `pause_activation` call. |

### 7.2 Warm start vs cold start

- **Warm start** (`heartbeat_age < heartbeat_stale_seconds`, default 300s):
  rebuild projection, re-examine active scopes but do not auto-fail them;
  the callback registration for each active scope is re-attempted once; if
  that succeeds the scope continues. (Whether a callback *can* be
  re-registered depends on whether the scope spec carried a resume token
  — most scopes are fire-and-forget work that completed before the brief
  outage.)
- **Cold start** (`heartbeat_age ≥ heartbeat_stale_seconds`): rebuild
  projection, walk every active scope, apply the rule:
  - scope has `resumable=true` in constraints AND `last_state_event_age <
    max_scope_silence_seconds` → attempt resume.
  - else → `scope_runtime.fail(scope_id, reason="orchestrator_cold_restart")`.

### 7.3 State preserved per class

| State | Graceful stop | Kill mid-run | System reboot | Claude outage |
|---|---|---|---|---|
| Scope definitions | ✓ (event log) | ✓ | ✓ | ✓ |
| Scope state | ✓ (projection rebuilt) | ✓ | ✓ | ✓ |
| Objective bindings | ✓ (event log) | ✓ | ✓ | ✓ |
| Memory | ✓ (Kuzu durable) | ✓ | ✓ | ✓ |
| In-flight scope callback | ✓ if graceful | ✗ (scope marked failed) | ✗ (marked failed) | ✓ (paused) |
| Monitor awareness history | ✗ (rebuilt from scope state) | ✗ | ✗ | ✓ |
| Loaded persona contract | ✗ (reloaded) | ✗ | ✗ | ✓ |
| Compaction flag | ✓ (orchestrator SQLite) | ✓ | ✓ | ✓ |

Monitor awareness is not authoritative — it is a derived view — so losing
its in-memory history on restart is acceptable. It rebuilds on the first
tick after boot from `scope_runtime.list(...)`.

### 7.4 Bounded-window guarantee

The spec requires "self-heals or is marked failed with recoverable state
within a bounded window." The bound in this design:

- `heartbeat_stale_seconds = 300` (5 min) — upper bound on "did we die."
- `ThrottleInterval = 30` — upper bound on launchd's restart latency.
- Boot rehydration is O(event_log_size); for realistic scales (< 10k events
  per store) this is sub-second.
- Total window from kill to either resumed or failed: **< 6 minutes** on a
  typical cold restart, dominated by `heartbeat_stale_seconds`.

The 5-minute default is tunable; 5 minutes matches the Anthropic prompt
cache TTL, which is why the research plan's ScheduleWakeup guidance uses
that number. For pOS's spec this is ample.

---

## 8. Integration map with Phase 1 primitives

### 8.1 Scope-of-work

**How the orchestrator uses it:**
- Constructs one `ScopeRuntime(db_path=~/.pos/db/scope_of_work.sqlite)` at
  boot.
- Subscribes the monitor to `runtime.subscribe_all(monitor.on_scope_event)`.
- Calls `runtime.start`, `runtime.cancel`, `runtime.fail` as part of
  `activate_scope` / `halt_cascade`.
- Registers scope callbacks via `runtime.register_callback(handle, fn)` —
  the handles point to callable coroutines the workspace supplies; the
  orchestrator's job is to hold the registration, not to author the
  callbacks.
- Calls `runtime.poll_external_events()` periodically (once per tick, or
  on cross-process notification) to pick up events written by other
  processes that happened to touch the same DB — this is rare in the
  single-process design but preserves cross-process safety.

**Amendments needed:** none.

### 8.2 Objective tracker

**How the orchestrator uses it:**
- Constructs one `ObjectiveTracker(db_path=~/.pos/db/objective_tracker.sqlite)`
  at boot.
- Calls `tracker.subscribe_scope_emitter(scope_runtime.emitter)` once to
  enable auto-evaluation of `ScopeSuccessCriterion`.
- Calls `tracker.bind_scope(scope_id, objective_id)` inside `activate_scope`.
- Does *not* author objectives — objective authoring is a workspace
  concern (user or persona). The orchestrator only binds.

**Amendments needed:** none.

### 8.3 Memory system

**How the orchestrator uses it (minimal):**
- Does not import `memory-system` directly.
- Accepts a `RecentCorrectionsProvider` callable at construction; this is
  supplied by the session adapter or a workspace wiring file. When the
  compaction-survival payload is built, the provider is invoked.
- Optionally subscribes to memory's observability JSONL files (future;
  no requirement in Phase 2).

**Amendments needed:** none. The provider-callable pattern is already the
primary-persona layer's integration shape; the orchestrator reuses it.

### 8.4 Primary-persona layer

**How the orchestrator uses it:**
- At boot, constructs one `PersonaLoader` pointed at the workspace's
  `personas/` directory; calls `loader.load()`; stores the resulting
  `LoadedPersona` list; identifies the primary persona (the one flagged
  `role: primary` in its contract, per the layer's contract).
- Constructs one `BackgroundWorkMonitor(scope_runtime)`; calls
  `monitor.start()`.
- Constructs one `CompactionSurvivor(loaded_primary, scope_runtime,
  recent_corrections_provider)`; exposes via IPC.
- Constructs `CreationTriggerDetector` and `AuthoringPipeline` (these are
  the autonomous-authoring halves); the orchestrator does not drive them
  — the primary persona does — but hosts them so their state survives
  session resets.
- Constructs `IntroductionDispatcher` with the orchestrator's channel
  registry (session-local channels forward via IPC back to the session;
  external channels like Telegram are the channel-agnostic-interaction
  component's responsibility — future).

**Amendments needed:** none. The layer was designed to be hosted; the
orchestrator is the host.

### 8.5 Integration diagram

```
                ┌──────────────────────────────────────────┐
                │           ORCHESTRATOR PROCESS            │
                │                                          │
                │  ┌───────────────────┐                   │
                │  │ IPC server        │◀── Unix socket ───┼── SESSION PROCESS
                │  │ (asyncio streams) │                   │
                │  └─────────┬─────────┘                   │
                │            │                             │
                │            ▼                             │
                │  ┌──────────────────────┐                │
                │  │ activate / awareness │                │
                │  │ / compaction /       │                │
                │  │ status endpoints     │                │
                │  └──────┬──────┬────────┘                │
                │         │      │                         │
                │   ┌─────▼──┐ ┌─▼───────┐                 │
                │   │Scope   │ │Objective│                 │
                │   │Runtime │ │ Tracker │                 │
                │   └────┬───┘ └────┬────┘                 │
                │        │          │                     │
                │        │ pyee     │                     │
                │        ▼          │                     │
                │   ┌────────────┐  │                     │
                │   │ Monitor    │  │                     │
                │   │ (always-on)│  │                     │
                │   └────────────┘  │                     │
                │                    │                    │
                │   ┌────────────────▼──┐                 │
                │   │ CompactionSurvivor│                 │
                │   └────────────────┬──┘                 │
                │                    │                    │
                │   ┌────────────────▼──┐                 │
                │   │ PersonaLoader     │                 │
                │   │ + creation-trig   │                 │
                │   │ + authoring pipe  │                 │
                │   └───────────────────┘                 │
                │                                          │
                │   ┌───────────────────┐                  │
                │   │ OTel emission     │ ─ no consumer req│
                │   └───────────────────┘                  │
                └──────────────────────────────────────────┘
                          │              │
                   ~/.pos/db/ SQLite stores (WAL):
                   scope_of_work.sqlite
                   objective_tracker.sqlite
                   orchestrator.sqlite (heartbeat, compaction flag, own events)
                          │
                          ▼
                   Memory (Graphiti/Kuzu) — accessed via provider callable only
```

---

## 9. Observability emission surface

The orchestrator emits its own OTel spans and events *in addition to* what
Phase 1 primitives already emit. All emissions follow v1.1 R11 and the A1
pattern (no consumer assumed).

### 9.1 Orchestrator-specific spans

- `pos.orchestrator.boot` — wraps the full boot sequence; attributes include
  `warm_start` / `cold_start`, `heartbeat_age_seconds`, scope counts
  rehydrated per state.
- `pos.orchestrator.shutdown` — wraps graceful shutdown; includes drain
  durations.
- `pos.orchestrator.activate_scope` — per-activation; attributes include
  `scope_id`, `objective_id`, `bind_result`, `start_result`.
- `pos.orchestrator.bind_refused` — emitted as an event (not a span) when
  `bind_scope` raises; attributes include the error class and scope /
  objective IDs.
- `pos.orchestrator.compaction_handoff` — wraps PreCompact flag set through
  to survival payload delivery.
- `pos.orchestrator.monitor_tick` — already emitted by the monitor; the
  orchestrator does not double-emit.
- `pos.orchestrator.heartbeat` — per-60s heartbeat span with negligible
  payload.
- `pos.orchestrator.ipc_request` — per request; attributes include the
  endpoint and outcome. (Privacy-sensitive parameters omitted.)
- `pos.orchestrator.pause_activation` / `resume_activation` — emitted when
  graceful-degradation toggles the gate.

### 9.2 Orchestrator-specific events

- `orchestrator.scope_activated` / `orchestrator.scope_activation_refused` —
  fan out on the orchestrator's own pyee emitter so peers (e.g. graceful-
  degradation) can subscribe.
- `orchestrator.bind_refused` — records each refusal with structured
  reason for audit.
- `orchestrator.heartbeat_written` — heartbeat telemetry.
- `orchestrator.cold_start` / `orchestrator.warm_start` — single boot event.

### 9.3 Query API (for observers)

The orchestrator is primarily push-based (OTel + pyee). It exposes a
minimal pull API for inspection:

- `GET /status` (IPC) — uptime, scope counts, heartbeat freshness.
- `GET /recent-events?since=T` (IPC) — drain recent orchestrator events.
- No direct SQLite exposure; consumers read the event log files if they
  want the raw record.

---

## 10. Complexity estimate

**Total: 600–750 AI-minutes.**

Breakdown (AI-time per §task-orchestration.md rule 15):

| Task | Estimate |
|---|---|
| Process model skeleton (asyncio main, CLI, plist/unit files) | 30–45 min |
| SQLite store for orchestrator-local state (heartbeats, compaction flag, bind_refused log) | 30–45 min |
| Boot sequence (open stores, rebuild projection, warm/cold decision) | 60–90 min |
| IPC server (Unix socket, line-delimited JSON, endpoints) | 60–90 min |
| `activate_scope` dispatch path (bind → start, error handling, events) | 45–60 min |
| Integration with scope-of-work (`register_callback`, subscribe, cross-process polling) | 30–45 min |
| Integration with objective-tracker (`bind_scope` + emitter subscription) | 15–30 min |
| Integration with primary-persona layer (host loader, monitor, compaction-survivor, authoring) | 60–90 min |
| Compaction survival IPC endpoint + flag state | 30–45 min |
| Awareness block IPC endpoint | 15–30 min |
| Observability: orchestrator-specific spans and events | 30–45 min |
| Scheduling loop for timed triggers (wall-clock deadlines) | 30–45 min |
| `pause_activation` / `resume_activation` hooks for graceful-degradation | 15–30 min |
| Warm/cold restart semantics + self-heal logic | 45–60 min |
| Tests: boot recovery, dispatch-layer contract, compaction handoff, heartbeat staleness, graceful-degradation hooks | 90–120 min |
| Documentation bundle (v1.1 R4): prose, architecture, relationship map, data flow, restart-semantics doc, plist sketch, systemd unit | 60–90 min |

Larger than Phase 1 components because this one integrates four primitives,
introduces process-lifecycle concerns, and carries the restart-semantics
ownership of the whole system. The 600–750 band is honest; the upper bound
protects against launchd plist oddities (the prototyping priority below) and
IPC edge cases.

---

## 11. Prototyping priorities

Two questions are best answered by prototype rather than reasoning. These
should be spiked before the full build commits to a final design:

### 11.1 launchd auto-restart behaviour under adverse kills

**Question:** does launchd's `KeepAlive=true` + `ThrottleInterval=30`
reliably resurrect the orchestrator across (a) SIGKILL, (b) SIGSEGV, (c)
OOM kill, (d) repeated rapid crashes? What's the actual restart latency?

**Prototype:** a tiny Python process that prints boot time + PID, with a
panic flag to exit via each of the above. Run under a test plist, trigger
each failure class 10 times, measure restart latency and confirm no missed
restarts.

**Why prototype:** launchd behaviour under OOM and rapid-crash conditions
is notoriously under-documented (one of the cited sources flags precisely
this). Depending on the answer, the heartbeat-stale default may need to
change (currently 300s; if launchd actually takes 5 min to restart a
crashy service, the default is too aggressive).

**Effort:** 60–90 min.

### 11.2 Orchestrator-to-session IPC latency under load

**Question:** Does a Unix-domain-socket JSON-RPC over asyncio streams
deliver the awareness block within the 100ms budget per turn? (Session
turn adds 100ms at most; Claude's turn-start latency is already
200–500ms, so 100ms IPC overhead is the upper bound.)

**Prototype:** stub orchestrator that returns a 1KB awareness block on
`GET /awareness`; session-side client opens socket, issues 1000
sequential requests, measure p50/p95/p99.

**Why prototype:** the IPC design is load-bearing for session responsiveness.
If latency exceeds budget under realistic load (monitor tick running, scope
events fanning out), we may need to batch or push — either of which changes
the protocol shape.

**Effort:** 30–60 min.

---

## 12. Halt signals raised during research

Per STATE.md rule 2 and the research-plan's halt-on-deviation rule, this
section flags anything that the research revealed as structurally at odds
with the constraints. Two items surface here; both are advisory, neither is
a blocking halt.

### 12.1 **Advisory — acceptable.** Orchestrator-local SQLite store

The orchestrator writes a small SQLite file (`~/.pos/db/orchestrator.sqlite`)
for heartbeats, compaction flags, and `bind_refused` events. This is not an
amendment to any Phase 1 primitive (orchestrator is Phase 2), but it does
introduce a fourth SQLite store on disk. the owner may prefer this be folded
into scope-of-work or written as append-only JSONL. The recommendation
keeps it separate because:
- Heartbeats and compaction flags are orchestrator-internal state; mixing
  them with scope events would muddy scope-of-work's semantics.
- JSONL would work but loses `ORDER BY event_id` without a file-scan.

**No halt — surfacing for owner's review during proposal authoring.**

### 12.2 **Advisory — acceptable.** Scope callback registration is
workspace-local

The orchestrator holds registered scope callbacks (via
`scope_runtime.register_callback`). On orchestrator restart, the workspace
must re-register its callbacks before any `active` scope can resume. This
is consistent with scope-of-work's existing design, but it means the
orchestrator's "warm start" resume is only as good as the workspace
providing a `bootstrap.py` that re-registers callbacks on startup. The
orchestrator can invoke a `~/.pos/bootstrap.py` if present, as a
convention.

**No halt — surfacing the convention.**

### 12.3 **No blocking halts raised.**

Every v1.0 session-resilient criterion, every v1.1 R11 OTel requirement,
and every v1.2 primary-persona integration lands cleanly in the
recommended design with no amendment to Phase 1 components.

---

## 13. Open questions for the owner

A short list of questions where owner's judgment is cleanly determinative
for the proposal. Defaults are recommended answers; the owner may accept or
override.

1. **Heartbeat stale default (5 min) — acceptable?** Default is 300 s.
   Lower values mean faster cold-start detection but more aggressive
   failure marking on brief network hiccups; higher values mean more
   patience for transient blips. **Recommended: 300s.**

2. **IPC protocol — line-delimited JSON or something richer?** Richer
   (gRPC, MCP) would cost a new dependency. JSON over stream stays within
   stdlib. **Recommended: line-delimited JSON for Phase 2; revisit if a
   future component needs richer semantics.**

3. **Orchestrator-owned SQLite store — fold in or keep separate?** See
   §12.1. **Recommended: keep separate.**

4. **`KeepAlive=true` vs `SuccessfulExit=false`?** Former restarts on any
   exit; latter restarts only on crash. Graceful stops for
   maintenance/reconfig become more awkward under the former. **Recommended:
   `KeepAlive=true` for Phase 2; revisit when upgrade tooling lands.**

5. **Scope callback re-registration — convention file `~/.pos/bootstrap.py`,
   or explicit API?** See §12.2. **Recommended: convention file; explicit
   API can be added later without breaking changes.**

6. **Priority scheduling — punt to future?** Phase 2 does not impose scope
   priority. **Recommended: punt. Revisit when a prioritisation need is
   observed, not before.**

---

## Sources

- [Temporal durable execution overview](https://temporal.io/blog/what-is-durable-execution)
- [Temporal workflow execution docs](https://docs.temporal.io/workflow-execution)
- [Celery optimization and durability](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)
- [Celery task resilience guide](https://blog.gitguardian.com/celery-tasks-retries-errors/)
- [APScheduler user guide (3.x)](https://apscheduler.readthedocs.io/en/3.x/userguide.html)
- [Rocketry documentation](https://rocketry.readthedocs.io/en/stable/)
- [launchd.info — tutorial](https://www.launchd.info/)
- [launchd.plist man page](https://www.manpagez.com/man/5/launchd.plist/)
- [Letta core concepts](https://docs.letta.com/core-concepts/)
- [Claude Managed Agents / Agent SDK session pattern](https://www.anthropic.com/engineering/managed-agents)
- [aiosqlite — asyncio bridge to sqlite3](https://github.com/omnilib/aiosqlite) (referenced for stdlib-equivalent pattern; not a permitted dep in Phase 2 — orchestrator uses sync sqlite3 with a threadpool or blocking IO at boot)
