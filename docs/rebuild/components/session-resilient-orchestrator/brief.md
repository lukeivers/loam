# Handoff Brief — Session-Resilient Orchestrator

**Component:** Session-Resilient Orchestrator (first Phase 2 component)
**For:** general-purpose Agent (builder)
**Authored by:** the primary persona
**Status:** DRAFT — awaiting owner's review before dispatch
**Against:** `proposal.md` (approved 2026-04-19 07:23 CDT, all three open questions resolved per the primary persona's leans)
**Spec:** objectives spec v1.0 + v1.1 + v1.2 addenda

---

## Objective

Deliver a production-ready session-resilient orchestrator for the new pOS. Build deliverables D1–D10 from the proposal. The orchestrator ships as a single long-lived Python asyncio process on the `pos-v2` branch. It is the dispatch-layer boundary where `bind_scope` enforcement lives, the host of the primary-persona layer's background-work monitor coroutine, and the mechanism by which Phase 1 primitives (memory, scope-of-work, primary-persona layer, objective tracker) compose into a running pOS. No Phase 1 component is amended. Graceful degradation remains a separate Phase 2 component; this build exposes only the `pause_activation` / `resume_activation` hooks.

---

## Hard constraints

1. **Implementation language:** Python.
2. **Branch discipline:** `pos-v2`. Work lives under `pos-v2/orchestrator/` (mirror the pattern `memory-system/`, `scope-of-work/`, `primary-persona/`, `objective-tracker/` use). No modifications to `main`.
3. **No amendments to sealed Phase 1 components.** Memory, scope-of-work, primary-persona layer, objective tracker all stay as they are. The orchestrator integrates via their public APIs and emission surfaces. If the build genuinely requires an amendment, halt and signal.
4. **Zero carryover from current pOS.** `bin/orch` (Ruby) is not a reference. launchd plists and systemd-user units are acceptable platform machinery — document platform-neutral notes where possible.
5. **Permitted runtime dependencies:** Python stdlib (`asyncio`, `sqlite3`, `uuid`, `dataclasses`, `socket`, `signal`, `pathlib`, `json`), `pydantic`, `pyee`, `opentelemetry-api`, `opentelemetry-sdk`, `PyYAML`. Test-only (pytest, pytest-asyncio) permitted per STATE.md rule #8. Any other runtime library requires halt-and-signal.
6. **Max-first.** Orchestrator itself is deterministic infrastructure; no LLM inference expected inside it. If a scenario genuinely needs LLM inference, use Claude via Max.
7. **No personas shipped in pOS core.** Framework code only. A build-time check must fail if any persona directory appears in the orchestrator's paths.
8. **No assumed downstream consumer (A1 correction).** Orchestrator emits OTel; no consumer assumed. The graceful-degradation component (separate) calls the orchestrator's hooks when built.
9. **Halt-on-deviation.** Silent deviation is forbidden.
10. **Bundled documentation per v1.1 R4.** Ships at `orchestrator/docs/`.

## rulings recorded baked into this brief

- **Process model:** single long-lived Python asyncio process; launchd (macOS, user agent) + systemd-user (Linux) for auto-start / restart.
- **launchd throttle interval on rapid crashes: 30 seconds.** Same behaviour on systemd-user.
- **Session is a peer process** attaching via Unix-domain-socket JSON-RPC. Orchestrator does not host the session; session does not host the orchestrator.
- **Primary-persona layer's background-work monitor runs inside the orchestrator process.** Session pulls awareness via `GET /awareness?turn_id=T` on every UserPromptSubmit.
- **Awareness-pull latency: 100 ms hard ceiling with cache fallback.** If the live pull exceeds 100 ms, the session uses the last cached awareness block (stale but present) rather than blocking the turn.
- **Graceful degradation is a separate Phase 2 component.** The orchestrator exposes only `pause_activation(reason)` / `resume_activation()` hooks. No degradation-policy logic in this build.
- **`bind_scope` enforcement is the orchestrator's dispatch-layer responsibility.** Full sequence: `activate_scope(scope_id, objective_id)` → verify scope pending → `tracker.bind_scope()` → on failure log `bind_refused` + 409 + scope stays; on success `scope_runtime.start()` + emit activation span.
- **Orchestrator owns a small local SQLite** at `~/.pos/orchestrator.sqlite` (configurable path) for its own process-lifecycle state — distinct from Phase 1 stores. Event-sourced; v1.1 R1 semantic round-trip upgrade passes.
- **Workspace bootstrap convention:** scope callback re-registration on restart relies on a workspace-supplied `~/.pos/bootstrap.py`. pOS core defines the contract; workspace authors the file. **On missing or erroring bootstrap: orchestrator refuses to start** (fail-closed, matching the primary-persona loader's posture).

---

## Deliverables

Ten deliverables D1–D10 as named in the proposal. Each has an objective and acceptance criteria in objective terms; none prescribe implementation method, file layout, module names, class hierarchies, or function signatures beyond the API surface the proposal has sketched.

### D1. Orchestrator process skeleton

**Objective:** a Python asyncio process starts, runs an event loop, handles SIGTERM gracefully, exits cleanly, writes heartbeats on interval.
**Acceptance:**
- Process starts and runs a main event loop.
- SIGTERM triggers a clean flush (all in-flight async work completes or is checkpointed) followed by exit code 0.
- Crash produces non-zero exit code.
- Heartbeat writes to the local SQLite on a configured interval.

### D2. launchd + systemd-user process supervision

**Objective:** orchestrator auto-starts with the user session; auto-restarts within the 30-second throttle window on crash.
**Acceptance:**
- launchd plist loads without errors; `launchctl kickstart` starts the orchestrator.
- SIGKILL to the process produces automatic restart within the bounded window (30 s throttle honoured).
- A rapid-crash loop (crash → immediate re-crash) is throttled, not infinite-looped.
- Equivalent behaviour via systemd-user unit file for Linux.

### D3. Unix-domain-socket JSON-RPC server

**Objective:** the orchestrator exposes a JSON-RPC server on a Unix-domain socket for the interactive session to attach to.
**Acceptance:**
- Socket exists at configured path (default `~/.pos/orchestrator.sock`); permissions are user-private (0600).
- A test client connects, sends a ping, receives a pong; round-trip p95 latency <10 ms on local loopback.
- Disconnect and reconnect work cleanly; orphaned socket files are removed on startup.

### D4. Monitor hosting

**Objective:** the primary-persona layer's background-work monitor coroutine runs inside the orchestrator process, subscribes to scope-of-work's pyee emitter, and serves awareness blocks via `GET /awareness?turn_id=T` over the IPC socket. 100 ms hard-ceiling with cache-fallback latency policy.
**Acceptance:**
- Monitor starts with the orchestrator; pyee events from scope-of-work flow in real time.
- `GET /awareness?turn_id=T` returns a structured awareness block (≤1k tokens, six categories, ≤5 rows each).
- Live pull completes within 100 ms p95 on a representative workload; on exceedance, the endpoint returns the last cached block with a `stale: true` marker rather than blocking.
- Cached block is refreshed on every successful live pull; staleness window is recorded.

### D5. `bind_scope` dispatch layer

**Objective:** scope activation goes through the orchestrator; `bind_scope` is called before `scope_runtime.start`; failures logged and surfaced per the proposal sequence.
**Acceptance:**
- `activate_scope(scope_id, objective_id)` enforces the sequence: verify scope pending → `bind_scope` → on success start scope.
- `UnresolvedObjectiveError` and `OrphanRootError` both result in `bind_refused` event to local SQLite, OTel emission, 409 return, scope staying pending.
- Successful binding results in `scope_activated` span and scope-of-work's runtime activating the scope.
- Integration test confirms scope-of-work (77 tests) and objective-tracker (86 tests) are unchanged and still pass.

### D6. Local SQLite for orchestrator state

**Objective:** orchestrator owns a local SQLite at `~/.pos/orchestrator.sqlite` (configurable) for its own process-lifecycle events — event-sourced, upgrade-fidelity-testable, separate from Phase 1 stores.
**Acceptance:**
- Database exists at configured path on first start.
- Tables cover: heartbeats, compaction flags, bind-refused log, lifecycle events (start/stop/crash).
- Event-sourced pattern matches Phase 1 primitives' pattern.
- v1.1 R1 semantic round-trip upgrade test passes (probe set captured pre-upgrade, replayed post-upgrade, drift below threshold).

### D7. Restart-semantics behaviour

**Objective:** each failure class produces the declared behaviour per the proposal matrix.
**Acceptance:** tested cases —
- Graceful SIGTERM: flush completes; restart resumes pending work from Phase 1 event logs; no data loss.
- SIGKILL: launchd/systemd restarts within throttle; orchestrator rebuilds state by replaying Phase 1 logs; in-flight scopes either self-resume (if `in_progress` in scope-of-work's log) or are marked failed with recoverable state within a bounded window.
- System reboot simulation: orchestrator auto-starts on login; pending work resumes.
- Claude API outage simulation: `pause_activation(reason)` halts new activations; in-flight scopes pause rather than fail; `resume_activation()` on recovery restores normal operation.
- Compaction simulation: session signals PreCompact via IPC; orchestrator writes `pending_compaction_restore` flag; session's next UserPromptSubmit triggers restoration from authoritative sources per primary-persona layer's D4 pattern.

### D8. Compaction-survival integration

**Objective:** orchestrator participates in the compaction protocol via IPC with the session; PreCompact and post-compaction UserPromptSubmit handshake works end-to-end.
**Acceptance:**
- Session-side compaction hook calls the orchestrator's IPC endpoint on PreCompact.
- Orchestrator writes `pending_compaction_restore` flag to local SQLite.
- On next UserPromptSubmit, the session pulls restoration content; the five-item canonical survival list (persona identity, authority boundary, current scope context, pending decisions, recent corrections) is verifiably present and correctly sourced (persona identity from contract.yaml, scope context from scope-of-work, etc.).
- Flag is cleared after successful restoration.

### D9. OTel observability emission

**Objective:** every orchestrator operation emits OTel spans/events per v1.1 R11.
**Acceptance:**
- Process start/stop produce spans with relevant attributes.
- `scope_activated`, `bind_refused`, `pause_activation`, `resume_activation`, `compaction_flag_set`, `compaction_restored` all emit with relevant attributes.
- Heartbeats emit as metric events.
- Emission succeeds with no consumer present (A1 correction).
- Workspace bootstrap-refuses-to-start failure emits a distinct span/event so the cause is observable.

### D10. Bundled documentation + prototyping addendum

**Objective:** v1.1 R4 human-readable documentation plus explicit measurement of the two prototyping priorities from research.
**Acceptance:**
- Prose explanation covering process model, IPC, monitor hosting, dispatch-layer, restart-semantics.
- Architecture diagram showing orchestrator + Phase 1 primitives + session + graceful-degradation hook points.
- Sequence diagrams for `bind_scope` flow and compaction-restore flow.
- Relationship map (consumes all four Phase 1 primitives; consumed by session + future graceful-degradation + future observability aggregator).
- One-page API reference for the IPC surface.
- **Measurement addendum:** launchd auto-restart latency measurements under SIGKILL/SEGV/OOM/rapid-crash, and Unix-socket IPC p95 latency measurements under a representative workload. Measurements are part of D2 and D4 acceptance respectively; this bundle captures them in documentation form.

---

## Dependencies

### Hard dependencies

- **All four sealed Phase 1 components** via public APIs and emission surfaces — no amendments.

### Soft dependencies (future consumers — not required to ship this build)

- Graceful-degradation component (next Phase 2 after this) — calls `pause_activation` / `resume_activation`.
- Observability aggregator (later Phase 2) — consumes orchestrator OTel emissions.
- Self-upgrade framework (later Phase 2) — orchestrator's local SQLite participates in pOS-wide upgrade-fidelity story.

### Permitted runtime dependencies

As enumerated in hard constraints. No additional libraries without halt-and-signal.

---

## Halt conditions

Halt and return with a named failure signal if:

- Any hard constraint cannot be honoured.
- A spec acceptance criterion is discovered unsatisfiable under the approved direction.
- Any Phase 1 amendment genuinely required — do not modify silently; surface the conflict.
- An additional runtime dependency appears necessary — surface; do not add.
- Any ambiguity requiring an invented constraint not in owner's words.
- launchd auto-restart or Unix-socket IPC latency measurements reveal the approved targets (30 s throttle; 100 ms ceiling) are unachievable on the owner's platform — surface rather than silently relaxing.

Halts return control to the primary persona, who reviews with the owner. The proposal is adjusted; execution resumes against the revised version.

---

## Return format

On completion, return a summary (≤700 words) covering:

1. Which deliverables D1–D10 completed, which halted.
2. Which spec criteria now pass (cite v1.0 behaviour or v1.1 revision).
3. Confirmation that scope-of-work's 77 tests and objective-tracker's 86 tests still pass (no Phase 1 amendment). Memory and primary-persona layer tests should likewise still pass.
4. Test counts on the orchestrator itself.
5. launchd auto-restart latency measurements for SIGKILL/SEGV/OOM/rapid-crash.
6. Unix-socket IPC p95 latency under a representative workload.
7. Complexity outcome — AI-time vs the proposal's 600–750-minute estimate.
8. Commits on `pos-v2`.
9. Any halt signals raised.
10. Recommended next action.

---

## What this brief is NOT

- Not a specification of module names, class hierarchies, file layout, or function signatures beyond the API surface and directory layout the proposal has sketched.
- Not a step-by-step execution plan.
- Not a graceful-degradation implementation. This build exposes hooks only; the component that calls them is a later Phase 2 brief.
- Not a commitment to designing adjacent primitives (observability aggregator, self-upgrade framework).

---

## inferences recorded in this brief (flagged so the builder can challenge)

Three items come from the primary persona's interpretation rather than the owner's verbatim words:

- *launchd is the primary supervision mechanism on macOS; systemd-user is the Linux parity target.* the owner is on macOS. If the builder finds a stdlib-only supervisor (no launchd/systemd dependency) that meets all acceptance criteria cleanly, halt and flag — the benefit would be platform-neutrality, the cost would be maintenance burden for a supervisor we'd otherwise get free from the OS.
- *Unix-domain-socket JSON-RPC is the IPC substrate.* Research-recommended, stdlib-only. If the builder finds a measurably better substrate that doesn't require additional dependencies, halt and flag.
- *`~/.pos/` is the default configuration directory.* Matches Unix convention for user-local state. If the builder finds a reason to prefer XDG base directory spec or similar, halt and flag — `~/.pos/` is the primary persona's default based on convention, not the owner's verbatim.
