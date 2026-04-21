# Research Plan — Session-Resilient Orchestrator

**Component:** Session-Resilient Orchestrator — the long-running process layer that binds scopes to objectives, activates them, monitors their execution, and survives session/system lifecycle events.
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for the orchestrator such that:

- Every v1.0 Session-resilient acceptance criterion can be honoured by a concrete implementation proposal (work survives session end; tasks survive system restart; process killed mid-run self-heals or is marked failed with recoverable state within a bounded window; compaction events preserve persona identity + active work + pending decisions).
- The orchestrator is the dispatch-layer boundary where objective-tracker's `bind_scope` enforcement happens before scope activation.
- Phase 1 primitives (memory, scope-of-work, primary-persona layer, objective tracker) compose cleanly without amendment — the orchestrator consumes their emission surfaces and drives their runtimes, but does not reach inside them.
- The decision of whether **graceful degradation** is a sub-module of the orchestrator or a separate Phase 2 component is answered with concrete rationale.

## Starting position

- **Phase 1 is closed.** All four primitives are sealed on `pos-v2`: memory, scope-of-work, primary-persona layer, objective tracker. Nothing in Phase 2 may amend sealed components without halt-and-signal.
- **No orchestrator exists yet.** Current pOS has `bin/orch` (Ruby) — explicitly not a reference implementation. The new pOS orchestrator is clean-slate Python.
- **Primary-persona layer includes the background-work monitor** — a long-lived asyncio coroutine. The orchestrator and the monitor both have long-running process claims; the research must clarify where the boundary is.
- **Scope-of-work and objective-tracker** both have pyee emitters the orchestrator can subscribe to, and SQLite event logs the orchestrator can query.
- **Python-native.** stdlib preferred; pydantic + pyee + opentelemetry + PyYAML already in scope.

## Questions the research must answer

### 1. Process model

1. What is the top-level process shape — a single long-running Python process (asyncio event loop) that hosts everything, a multi-process model with one supervisor and N workers, something else? Current pOS uses a Ruby orchestrator + dispatched subprocesses; new pOS is not constrained by that.
2. How does the orchestrator start and stop with the system — launchd on macOS (consistent with current pOS's platform), systemd on Linux, both, something platform-neutral? pOS is single-user and local-first per the non-goals; platform-specific machinery is acceptable.
3. What is the orchestrator's relationship to the interactive Claude session — does the orchestrator host the session, does the session attach to the orchestrator, are they peer processes, or is the session entirely separate from the orchestrator's long-running work?
4. How does the orchestrator relate to the primary-persona layer's background-work monitor — is the monitor a component *inside* the orchestrator, or a peer that subscribes to the orchestrator's emissions?

### 2. Dispatch layer — where `bind_scope` enforcement lives

5. Objective-tracker's D4 acceptance says "the workspace dispatch layer calls `tracker.bind_scope(scope_id, objective_id)` before activating any scope." The orchestrator is that dispatch layer. What is the concrete call-site sequence for activating a scope — request arrives, persona decides to run a scope, orchestrator calls `bind_scope`, scope-of-work runtime activates, scope runs to completion?
6. What is the failure behaviour when `bind_scope` raises (unresolved objective or orphan root) — the orchestrator refuses activation, records a failure event, and surfaces to the persona; or a different pattern?
7. Does the orchestrator act as a scheduling engine (queues of pending scopes, prioritisation, concurrency limits), or does scope-of-work's primitive already handle that, with the orchestrator being a thin wrapper?

### 3. Session-resilience and restart semantics

8. What does "work queued before a session ends completes after session restart without user intervention" mean concretely? Queued-where (scope-of-work's event log, a dedicated queue, orchestrator's own state)? Completes-how (orchestrator picks up where it left off by replaying the event log; scope-of-work's existing event-sourcing makes this tractable)?
9. What does system restart survival look like — the orchestrator's process is killed by system shutdown; on startup, it reads the event logs of memory / scope-of-work / objective-tracker and rebuilds enough state to resume pending work?
10. What is the self-healing threshold for "process killed mid-run" — how long before the orchestrator is considered dead, restarted automatically, and its in-flight work either resumed or marked failed? Launchd's KeepAlive and StartInterval are candidate mechanisms.

### 4. Compaction-event survival

11. Compaction survival is already partially owned by the primary-persona layer (replay-from-authoritative-sources pattern). What does the orchestrator add — does it participate in the compaction protocol, observe the PreCompact flag, re-inject anything, or does the persona layer own the full story?
12. What does the orchestrator do about mid-session compaction of the interactive session — pause in-flight scopes, record a resumable state marker, continue without interruption?

### 5. Graceful degradation (Phase 2 item) — fold in or separate?

13. When Claude API is down, rate-limited, or returning garbage, what does the orchestrator do? Options: (a) pause all scope execution and queue; (b) degrade to local-only operations (scopes that don't need LLM inference); (c) fall-through to fail mode; (d) notify user and await instruction.
14. Is graceful degradation a natural sub-module of the orchestrator (the orchestrator is where Claude calls route through) or a separate Phase 2 component that the orchestrator consumes? The research should recommend.
15. What is the user-facing signal when graceful degradation activates — per the spec's "user is informed before blast radius exceeds a declared threshold" acceptance, the primary persona needs a way to surface the degradation state.

### 6. Observability emission surface

16. The orchestrator aggregates emissions from all four Phase 1 primitives (OTel spans, events, heartbeats). What does the orchestrator itself emit that's distinct — scheduler events, dispatch-layer events, process-lifecycle events, session-lifecycle events?
17. Does the orchestrator expose a query API for observers (a future observability aggregator) to pull from, or is it purely push-based (every emission goes out, consumers subscribe)?

### 7. Scheduling, concurrency, prioritisation

18. Scope-of-work carries budget but no priority. Does the orchestrator introduce priority as a concept for queued scopes, or are scopes strictly FIFO?
19. What is the concurrency model — how many scopes can run simultaneously? Is that a declared orchestrator-wide limit, a per-persona limit, a per-scope-type limit?
20. How does the orchestrator handle long-running scopes that block the queue — preemption, time-slicing, suspension-and-resume?

### 8. Integration with primary-persona layer's monitor and authoring

21. The monitor is a long-lived asyncio coroutine inside the primary-persona layer. Does it run inside the orchestrator process, as a peer process, or as an in-session component?
22. When the primary persona's autonomous-authoring pipeline creates an authoring scope, does the orchestrator activate that scope (same as any other), or is there a special path?
23. When the monitor fires an escalation event, does the orchestrator act on it, or does the persona layer own that response?

## Constraints the research must respect

- **Python-native.** stdlib preferred; pydantic + pyee + opentelemetry + PyYAML permitted; anything else halt-and-signal.
- **No amendments to sealed Phase 1 components.** Memory, scope-of-work, primary-persona layer, objective tracker all stay as they are. If the build genuinely requires an amendment, halt-and-signal — do not silently modify.
- **Zero carryover from current pOS / the existing workspace.** `bin/orch` Ruby code is explicitly not a reference implementation. Platform machinery (launchd plists) is acceptable if platform-neutral alternatives are documented.
- **Max-first.** Orchestrator itself is mostly deterministic infrastructure; LLM inference in the orchestrator is unexpected. Where LLM inference is needed (e.g. the graceful-degradation safe-mode narrative), it uses Claude via Max.
- **No assumed downstream consumer (A1 correction).** Orchestrator emits OTel; consumers come later.
- **No personas in pOS core.** Framework code only.
- **Halt-on-deviation.** If any spec acceptance criterion cannot be satisfied under the approved direction, halt and surface.
- **ODD-compatible.** Each design recommendation traces to a spec objective; untestable options are noted and discarded.

## Deliverable — what the research document must contain

A markdown document at `components/session-resilient-orchestrator/research.md` with:

1. **Survey of existing patterns** — how other systems handle long-running task orchestration with session-survival semantics. Specifically survey: Temporal (workflow runtime), Celery + Redis (task queues), Python-native asyncio-based orchestrators (apscheduler, rocketry), launchd patterns for single-user local daemons, any AI-harness with a persistent-session story (Letta's server mode, Anthropic Agent SDK's session concept).
2. **Recommended design shape** — for each of the eight question groups, options considered, recommended option, rationale.
3. **Acceptance-criterion coverage** — mapping each v1.0 Session-resilient criterion and relevant v1.1 revisions to the piece of the design that delivers it. Any that cannot be satisfied surfaces as a halt.
4. **Graceful-degradation decision** — fold-in or separate component, with rationale.
5. **Process and platform specification** — how the orchestrator starts, runs, stops; launchd plist sketch; platform-neutral notes.
6. **Dispatch-layer sequence diagram** — the concrete call-site flow from "persona wants a scope" to "scope active and running" including `bind_scope`.
7. **Restart-semantics specification** — what state is preserved on each failure class (graceful stop, kill mid-run, system reboot, Claude outage).
8. **Integration map** with all four Phase 1 primitives.
9. **Complexity estimate** — AI-time, honest. Expected larger than the four Phase 1 primitives individually because this integrates them; ballpark 500–700 AI-minutes.
10. **Prototyping priorities** — any questions only a prototype can answer (likely: launchd auto-restart behaviour under adverse kill patterns, orchestrator-to-session handoff latency).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Agent reads the plan, performs the research, produces `research.md`, and returns. Halt-on-deviation applies throughout.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
