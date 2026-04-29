# Proposal — Hands-Off Lifecycle

**Status:** DRAFT — awaiting owner's G2 approval.
**Authored by:** Eve. **Date:** 2026-04-21.
**Research baseline:** `research.md` at this component's directory.

---

## 1. Objective

Opening a Claude Code session in a fresh pos-v2 workspace produces a running, healthy system on its own, and keeps it healthy through ongoing operation. The user does nothing they cannot do — no `pip install`, no sidecar launch, no YAML scaffolding, no orchestrator start command. Every ongoing lifecycle concern (sidecar health, orchestrator state, config drift, platform failure) is the harness's problem; the user sees one confirmation sentence on first run and loud escalation only when self-heal cannot recover.

## 2. Owner rulings (locked inputs)

All rulings received 2026-04-21 across two approval turns.

### 2.1 Scope framing

- **One component with four sub-amendments, sequenced carefully.** The four sealed-component amendments land as sub-cycles within this component's build rather than as five separate component cycles.
- **All four sealed-component amendments approved** in principle. Each amendment's specific surface becomes part of this component's build scope; each amendment's seal is part of this component's seal.

### 2.2 The seven questions

| Q | Ruling |
|---|---|
| Q1 — Amendment 4 shape | **New `first_run_scaffold` phase** before `before_orchestrator_start` in workspace-bootstrap. Not a per-adapter flag. Phases are architectural; flags accumulate coupling. |
| Q2 — Supervisor location | **Inside orchestrator (B.1).** launchd / systemd-user is already the outer supervision layer; in-process supervisor handles continuous probing and coordinated drain. |
| Q3 — Scaffold boldness | **Install autonomously** — launchd/systemd-user files written and `launchctl bootstrap` / `systemctl --user start` invoked without consent prompt. The fourth lens requires it; installation is reversible; session-open is functional consent. |
| Q4 — Platform unsupported | **Halt.** Refuse to run on platforms without launchd/systemd-user with a named diagnostic. Subprocess-degrade fallback violates the silent-stay-degraded prohibition. |
| Q5 — Tier-1 escalation cap | **Exceed the cap, but deduplicate per escalation class.** One notification per open escalation class; a class change produces a second; recovery produces the short "resolved" message. Memory-sidecar unrecoverable is the class of emergency the cap should not block. |
| Q6 — Staging overflow | **Error to caller.** `StagingOverflow` surfaces to the primary persona or the scope that tried to write; loud-escalation protocol covers the underlying cause. Orchestrator does not halt. |
| Q7 — First-run confirmation sentence | **Accept the research's proposed wording.** *"pos v2 first-run scaffold complete: twelve foundational components configured at defaults (safety/always-ask, cost ceilings, reversibility, self-correction, memory, degradation), memory sidecar and orchestrator launched as user services, staging store initialised. `~/.pos/` is your config dir — edit any file to adjust. Proceeding."* |

---

## 3. Design shape (summary — research is the detail)

Four mutually-dependent streams of work, delivered in one coherent build.

### 3.1 The session-start hook path

Claude Code's `SessionStart` hook (type: `command`, synchronous, FD-safe) invokes a session-start helper. The helper is non-blocking: it asks `launchctl`/`systemctl --user` to bring services up if they are not already running; it reports success or named failure via the hook's stdout-as-context mechanism; it returns quickly. The helper never launches child processes itself — doing so hits the Claude Code v2.1.87 FD-inheritance bug (research §0, GitHub issue #43123).

### 3.2 The supervisor state machine

Living inside the orchestrator process per Q2 ruling. Continuously probes the memory sidecar (liveness, HTTP responsiveness, latency, canary query); maintains a state machine across `normal`, `degraded`, `recovering`, `escalated`; coordinates the memory-drain worker on recovery; opens and closes escalations idempotently per class.

### 3.3 The durable staging store

SQLite-WAL-backed, keyed on client-generated UUIDs for idempotence; receives memory writes during `degraded` and `recovering` states; `StagingOverflow` surfaces to caller per Q6 ruling. Read path during degraded mode answers from staging + last-known Graphiti snapshot where available.

### 3.4 The reconcile-on-recovery drain

Forwards staged entries to the sidecar in strict FIFO order on transition into `normal`; each entry clears from staging only on confirmed landing; drain failures surface as an explicit state; staging is never silently emptied.

### 3.5 The first-run scaffold

A new `first_run_scaffold` phase in workspace-bootstrap runs before `before_orchestrator_start`. On detected first run (no `~/.pos/bootstrap.yaml` and no `~/.pos/` directory), it writes the nine per-component YAML defaults the research §Q6 inventories, installs the two service-manager files (memory-graphiti + orchestrator), invokes `launchctl bootstrap` / `systemctl --user start`, and emits the one confirmation sentence per Q7.

### 3.6 The loud-escalation protocol

Uses the primary-persona one-on-one channel. Escalations are idempotent per class via the `~/.pos/supervisor-escalation.json` state record; a durable `~/.pos/attention.md` mirrors the current unresolved state for any session to surface.

### 3.7 The fresh root README

Replaces the prototyping-phase placeholder with an accurate description of current pos-v2 state (twelve sealed components, `docs/rebuild/` reference tree, operational model, what a session looks like under hands-off-lifecycle).

---

## 4. Sealed-component amendments (the four approved sub-cycles)

Each amendment is part of this component's build. Each is individually sealed as the sub-cycle completes; the overall component seal depends on all four.

### 4.1 Amendment 1 — memory-system

New modules for staging and drain; degraded-mode branches on the existing MemoryAPI ingest/search surfaces; new Linux systemd-user service file to complement the existing macOS launchd file. Existing Graphiti-backed core behaviour unchanged; the amendment only adds the degraded-mode path and the service-lifecycle hook points.

### 4.2 Amendment 2 — orchestrator

New supervisor module wired into `_startup()`; new helper script `bin/pos-session-start` (or equivalent) that the Claude Code hook invokes. Existing orchestrator heartbeat and event-loop plumbing preserved; the supervisor is additive, not replacing.

### 4.3 Amendment 3 — graceful-degradation

New `memory_sidecar` failure mode in the FSM; new subscription in the detection layer to consume supervisor signals. Closes the memory-detection blind spot already logged in BACKLOG. Complementary to the existing ClaudeClient-adapter-based detection, not replacing.

### 4.4 Amendment 4 — workspace-bootstrap

New `first_run_scaffold` phase in the phase model, placed before `before_orchestrator_start`. New `first_run_scaffold` adapter that performs the nine-YAML + two-service-manager-file + `launchctl`/`systemctl` actions. Most architecturally delicate of the four because it extends the phase model itself; the design adds a single named phase, does not otherwise alter the phase ordering or the adapter interface.

---

## 5. Acceptance criteria (ODD — 21 objectives)

Each an observable outcome, test-shaped, deterministic. Structural refusal preferred where available.

### 5.1 First-run (H1–H5)

- **H1.** On a workspace with no `~/.pos/` directory, the first `SessionStart` hook invocation runs the first-run scaffold; on its return, `~/.pos/bootstrap.yaml` + eight per-component YAML files + two service-manager files exist on disk; both services are reported `running` by `launchctl list` / `systemctl --user status` respectively.
- **H2.** The first-run confirmation sentence is emitted to the Claude Code session once and only once; subsequent session opens do not re-emit (detected by presence of `~/.pos/`).
- **H3.** First-run scaffold running on a platform without launchd and without systemd-user halts with a named diagnostic matching `platform-unsupported:<platform>`.
- **H4.** If `~/.pos/` exists but `~/.pos/bootstrap.yaml` does not (partial prior state), the scaffold does not overwrite — it halts with `partial-scaffold-detected` and surfaces a diagnostic.
- **H5.** The confirmation sentence exactly matches the Q7 approved wording.

### 5.2 Supervisor state machine (H6–H10)

- **H6.** Memory sidecar healthy on probe → supervisor reports `normal`; sidecar unreachable on probe → `degraded`; recovery confirmed → `recovering` while drain runs, then `normal`; bounded retries exceeded without recovery → `escalated`.
- **H7.** Probe cadence and timeout are driven by `~/.pos/memory.yaml` config (`poll_interval_s`, `startup_timeout_s`) and `~/.pos/memory-staging.yaml` (`latency_threshold_ms`). Changing those values without restart takes effect on next probe cycle.
- **H8.** Supervisor emits OTel spans for each state transition, each probe, each escalation open/close, each drain start/end — via the sealed observability-aggregator's tracer-get pattern (no `TracerProvider` construction).
- **H9.** Orchestrator process crash → launchd/systemd-user restarts orchestrator → new orchestrator process's supervisor resumes from the persisted state (reads `~/.pos/supervisor-escalation.json` on bootstrap).
- **H10.** Supervisor is unit-testable without a live memory sidecar (fake-probe injection at construction).

### 5.3 Staging + drain (H11–H15)

- **H11.** Writes during `degraded`/`recovering` state land in `~/.pos/memory-staging.sqlite` in strict FIFO order with client-generated UUIDs preserved.
- **H12.** On transition to `normal`, the drain worker forwards staged entries to the sidecar in FIFO order; each entry clears from staging only after `add_episode` returns successfully; idempotence is preserved through client UUID on the sidecar side.
- **H13.** `StagingOverflow` raises to the caller when staging size exceeds `hard_cap`; the orchestrator does not halt.
- **H14.** Drain failure (sidecar rejects a staged entry after recovery) transitions supervisor to `escalated` rather than silently dropping the entry.
- **H15.** Read path during `degraded`/`recovering` answers queries from staging + last-known-Graphiti snapshot (where available); the persona can report its degraded state if asked.

### 5.4 Loud escalation (H16–H18)

- **H16.** Supervisor opens an escalation on transition to `escalated`; notification dispatches once via the primary-persona one-on-one channel; notification does not repeat while the escalation stays the same class.
- **H17.** A class change (`unreachable` → `corrupt`) produces a second notification; recovery produces a short resolved-and-drained message; `~/.pos/attention.md` reflects current unresolved state for any session to surface.
- **H18.** Tier-1 cap is exceeded for genuine memory-sidecar emergencies (per ruling Q5); deduplication ensures one escalation per class per opening, not three-per-day alert flood.

### 5.5 Cross-cutting (H19–H21)

- **H19.** `git diff --stat <baseline>..<seal>` shows amendments to exactly the four named sealed components + new `hands-off-lifecycle/` (or equivalent new-component surface). No other sealed component touched.
- **H20.** All sealed-component regression suites pass post-build: safety-layer, reversibility-primitive, cost-governance, self-correction, objective-tracker, scope-of-work, primary-persona, session-resilient-orchestrator, self-upgrade, observability-aggregator, workspace-bootstrap (amended), graceful-degradation (amended), memory-system (amended), orchestrator (amended).
- **H21.** Root `README.md` replaced with the fresh content described in §3.7.

---

## 6. Constraints

- **Python 3.13; pos-v2 branch.** Permitted runtime deps as established.
- **Four sealed-component amendments scoped and approved.** Each amendment is individually sealed with its own SEAL_COMMIT sidecar as the sub-cycle completes. The overall component's seal depends on all four.
- **No other sealed-component amendments.** If the build surfaces a fifth amendment case, halt and signal; the fifth is a new cycle.
- **Memory is mandatory.** No design path that makes Graphiti-backed memory removable or optional.
- **Silent-stay-degraded is forbidden.** Bounded retries then loud escalation; the fourth lens requires it.
- **Zero manual lifecycle management.** Every ongoing-operation concern the user would otherwise have to manage is the supervisor's problem.
- **Claude Code hook primitives only.** The auto-launch mechanic uses `SessionStart` with `type: command`; if the FD-inheritance bug's workaround (delegate to launchctl/systemctl) proves insufficient in practice, halt and signal.
- **A1 correction held.** All OTel via `trace.get_tracer("loam.hands_off_lifecycle")` (or equivalent namespace). No `TracerProvider` construction.
- **Error-code range `-32090..-32099` reserved** to this component. No overlap with the five already-allocated ranges.
- **Seal-test pattern mandatory.** `SEAL_COMMIT` sidecar-file per component; new pattern for the multi-amendment case documented in the build.
- **Halt on deviation.**

---

## 7. File layout and phase shape

Builder's call on both. The component spans multiple sealed-component directories plus a new top-level component directory; cohesion within each sub-amendment is the per-amendment builder's judgement. No suggested file layout prescribed here.

Phase shape recommendation only: the four amendments are ordered by dependency — workspace-bootstrap's new phase lands first (its absence would force the first-run scaffold to be hacked elsewhere), memory-system's staging + drain land second, orchestrator's supervisor lands third (consumes the memory-system surfaces), graceful-degradation's failure-mode integration lands fourth (subscribes to supervisor signals). Each amendment sealed individually before the next begins.

---

## 8. Build estimate

**155–250 AI-minutes wall-clock. Red line at 180 unless progressing clearly.** Honest calibration from the research. This component is substantial — four sealed-component amendments + a new supervisor layer + staging + drain + first-run scaffold + Claude Code hook + fresh README.

**Halt triggers at build time:**

- Past 180 minutes without a sealed sub-amendment landed, halt and report partial progress.
- Any fifth amendment case discovered (i.e., a component not among the four approved requires amendment), halt and surface — do not improvise a fifth.
- Any test regression on one of the unamended sealed components (safety, reversibility, cost, self-correction, observability, scope-of-work, primary-persona, session-resilient-orchestrator, self-upgrade), halt.

---

## 9. Eve's inferences — flagged for the builder to challenge

1. **Each amendment gets its own SEAL_COMMIT sidecar** — four new sidecars across four sealed-component directories. Alternative: one SEAL_COMMIT at the hands-off-lifecycle root covering the composite seal. Eve's lean is per-amendment sidecars to preserve the sealing-ritual discipline; challenge if composite is cleaner in practice.
2. **Error-code range `-32090..-32099`** reserved to hands-off-lifecycle. Parallel to other frameworks' ranges. Challenge if a different range serves better.
3. **Amendment ordering (workspace-bootstrap → memory-system → orchestrator → graceful-degradation)** is a dependency-led recommendation; the builder may reorder if the dependency graph proves different under closer reading.
4. **The new `first_run_scaffold` phase placement** before `before_orchestrator_start` is inferred from workspace-bootstrap's existing three-phase model. If the phase model has accepted patterns for where to place a pre-phase, follow those; if this is the first pre-phase ever added, the design choice is a fresh call the builder makes.
5. **`~/.pos/attention.md`** as the durable unresolved-state surface is the research's choice. Challenge if a different surface (daily note, status bar entry, etc.) serves better.
6. **Platform-halt diagnostic wording** — `platform-unsupported:<platform>` — is a placeholder; the builder authors the actual diagnostic after reviewing Claude Code's hook-failure error-surfacing conventions.
7. **OTel span namespace** `loam.hands_off_lifecycle.*` inferred for consistency with `loam.safety.*`, `loam.reversibility.*`, etc. Challenge if a different namespace is cleaner (e.g., `loam.supervisor.*` if the supervisor is the recognisable surface).
8. **First-run detection heuristic** (absence of `~/.pos/` AND absence of `~/.pos/bootstrap.yaml`) is from research Q6. Challenge if a more robust heuristic is required (e.g., a dedicated `~/.pos/.scaffold-version` marker).

---

## 10. Approval ask (G2)

Approve this proposal to open the handoff-brief drafting stage. Specifically:

- Locked rulings in §2 as faithful to your approvals.
- The 21 ODD acceptance criteria in §5 (H1–H21).
- The constraints in §6.
- The 155–250 AI-min estimate with 180-min red line.
- Eve's inferences in §9 as listed (approve as written, or adjust).

On G2 approval, Eve drafts the brief and surfaces for your G3 review before dispatch.
