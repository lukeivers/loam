# Research Plan — Hands-Off Lifecycle

**Status:** DRAFT — awaiting owner approval at G1.
**Authored by:** Eve. **Date:** 2026-04-21.
**Phase 5 opener.** First component authored under the new fourth research lens.

---

## 1. Why this component

pos-v2-rc-0.1.0 is the foundation-complete milestone — twelve sealed components, 824 tests passing, full rebuild-docs shipped. It is not the evaluation-ready milestone. The cutover experience that milestone produces today requires the owner to manually scaffold workspace config, launch the memory-system sidecar, start the orchestrator, and work around a stale README. That experience is a design failure against the goal of making pos v2 runnable by non-technical users.

This component fixes that. The outcome: opening a Claude Code session in a fresh pos-v2 workspace produces a running, healthy system on its own, and keeps it healthy through ongoing operation. The user does nothing they cannot do.

## 2. The fourth research lens — promoted here to first-class

> **Zero manual lifecycle management, ever.** Any setup that can be automated is automated. Any setup that must be user-visible is one confirmation, not a multi-step procedure. Any ongoing service-lifecycle concern (a sidecar crashing, the orchestrator hanging, a config going stale) is the harness's problem, not the user's — self-heal silently when possible, escalate loudly when not, degraded-mode that silently stays degraded is a failure of the lens.

This lens joins the three already in `FUTURE_IDEAS.md` Core Development Principles. Part of the deliverable: update that document to list four lenses, not three, and adjust Idea 1's enforcement programme to require a fourth research-plan question.

## 3. The memory-system constraint — load-bearing

The memory system is not a feature; it is the base layer the rebuild's entire value proposition rests on. The comprehensive, semantic, Graphiti-backed memory is mandatory. Losing it — even temporarily — is urgent-recovery territory, not graceful-degradation territory.

The lifecycle design must therefore honour three behaviours:

- **Normal mode.** Sidecar healthy; writes go to Graphiti; reads query Graphiti. The only mode anything is optimised for.
- **Degraded mode.** Sidecar unreachable; writes land in a filesystem staging area (durable, ordered, survives restart); reads answer from staging + last-known Graphiti state. The persona knows it is degraded and can tell the user if asked. Recovery is actively attempted throughout — this is an urgent state, not a stable one.
- **Reconcile on recovery.** When the sidecar returns, a drain worker replays the staging area into Graphiti in order; staging clears only on confirmed landing; on drain completion, normal mode resumes. In the common case the user never notices anything happened.

Supervisor disposition: bounded retries, then **loud escalation** to the user. If the sidecar cannot be recovered within the retry budget, pos v2 cannot hold its contract; the user must know plainly. Silent-fallback-and-hope is not a legitimate end state.

## 4. Scope of the component — what must land

### 4.1 Auto-launch on Claude Code session start

- When a Claude Code session opens in a pos-v2 workspace, a session-start hook brings the memory sidecar up if it is not already running.
- The orchestrator is either auto-started the same way, or is embedded into the session's lifecycle so starting the session starts the orchestrator.
- Both launches are silent on happy path; any failure surfaces immediately to the user with a named diagnostic and a suggested next action.
- Subsequent session opens detect already-running services and skip re-launch.

### 4.2 Continuous health supervision

- A supervisor probes the memory sidecar on a cadence (probe interval, timeout, failure thresholds all configurable).
- Probes cover: process liveness, HTTP responsiveness, response latency against a threshold, known-canary queries returning expected shapes.
- The orchestrator receives the same supervision from the same supervisor (or an analogous one — design choice).

### 4.3 Durable filesystem staging for memory writes during degraded mode

- A staging store (filesystem-backed, durable across process restarts, append-only with ordering preserved) receives memory writes while the sidecar is unreachable.
- The staging store has its own bounded size; overflow escalates loudly.
- Read path during degraded mode: query staging first (recent writes), fall back to last-known-snapshot of Graphiti state for historical reads.

### 4.4 Reconcile-on-recovery drain

- When the sidecar returns to healthy, a drain worker replays staging into Graphiti in strict order.
- Each staged write is removed from staging only on confirmed successful landing in Graphiti.
- Drain failures (e.g. the recovered sidecar rejects a write) surface as an explicit state; staging is not silently emptied.
- On drain completion, the supervisor marks memory as back to normal mode and the persona can reflect that.

### 4.5 Auto-scaffold workspace configuration

- On first-run detection (no `~/.pos/bootstrap.yaml` or equivalent markers), the session-start flow writes sensible defaults for every component's configuration: bootstrap manifest listing the foundational-adapter bundle, `safety/always_ask.yaml` with the framework-floor entries, `cost/ceilings.yaml` with reasonable starter caps, `reversibility/` registrations as appropriate, `self-correction/` config, etc.
- The user sees one confirmation sentence describing what was scaffolded. They proceed, not configure.

### 4.6 Loud-escalation protocol when self-heal fails

- The supervisor's escalation path uses the primary persona's one-on-one channel.
- The escalation message is plain language: what failed, what was attempted, what the user can do now, what state the system is in.
- Escalation is idempotent — a long-running unrecoverable state does not produce alert-flood; it produces one clear message plus a durable "pos v2 needs attention" surface until resolved.

### 4.7 Fresh README at the workspace root

- The root `README.md` on pos-v2 accurately describes the current state of the project: twelve sealed components, the `docs/rebuild/` reference tree, the operational model, what running a session looks like in the hands-off-lifecycle world this component ships.
- No reader's first orientation point should mislead.

## 5. Constraints the research must respect

- **No amendments to sealed components without surfacing.** This component will almost certainly require amendments to memory-system (staging + reconcile path), orchestrator (session-bound lifecycle), graceful-degradation (supervisor consumption) at minimum. Each amendment is surfaced as a halt-signal during research; the owner decides scope per amendment; the research does not improvise.
- **Memory is not optional.** No design path that makes Graphiti-backed memory a removable or optional layer is acceptable.
- **Degraded mode is urgent.** No design path that treats the filesystem-fallback as a stable operating mode is acceptable.
- **Self-heal is the default; silent-stay-degraded is forbidden.** Bounded retries then loud escalation.
- **Zero manual lifecycle management.** Every ongoing-operation concern the user would otherwise have to manage is the supervisor's problem.
- **Python 3.13, pos-v2 branch.** Permitted deps as per existing conventions.
- **Claude Code session-start hooks** are the entry point for auto-launch; if a needed hook type does not exist in Claude Code's current surface, halt and signal rather than invent a workaround that the user must install separately.
- **Halt on deviation.** Seven-gate discipline throughout.

## 6. Questions the research must answer

1. **Claude Code session-start hook mechanics.** What hook type fires reliably at session start? How does it invoke a long-running service launcher that outlives the hook itself? What are the known Claude Code hook patterns for background-service management?
2. **Memory sidecar launch and supervision.** Process-management primitive (`launchctl`? user-systemd? direct subprocess with a supervisor wrapper?). Probe protocol — which health endpoint, which canary query, which latency threshold. Failure-mode classification — what counts as sidecar-failing vs. transient-hiccup.
3. **Durable staging design.** Shape (JSONL? SQLite WAL? event log?), ordering guarantees, size caps, overflow behaviour, read-path integration with the persona's memory queries.
4. **Reconcile drain correctness.** Ordering, idempotence, conflict handling if Graphiti accepted writes via other paths during degraded mode, staging-cleanup semantics.
5. **Orchestrator lifecycle shape.** Session-bound (start/stop with the Claude Code session) vs. supervised-service (always running, session just attaches). Trade-offs.
6. **Config auto-scaffold contents.** The specific sensible-default content for each per-component config; what the single user confirmation sentence says.
7. **Loud-escalation protocol.** Message shape, idempotence mechanism, the "pos v2 needs attention" durable surface, integration with the primary-persona one-on-one channel.
8. **Sealed-component amendments required.** For each of memory-system, orchestrator, graceful-degradation, workspace-bootstrap — what changes are load-bearing for this component and how is each surfaced as a halt-signal in a separate sealed-component unseal cycle.
9. **README authorship.** What the fresh root README says; who its audience is; how it interacts with the `docs/rebuild/` tree.
10. **Fourth-lens capture.** Exact wording for `FUTURE_IDEAS.md`'s Core Development Principles section, and the research-plan question that enforces it at Idea 1 Step 3.

## 7. Deliverable — what the research document must contain

A markdown document at `components/hands-off-lifecycle/research.md` with:

1. **Survey of existing patterns** — process supervisors (launchd, systemd, foreman, pm2), durable-queue / outbox patterns in distributed systems, write-ahead-log reconciliation, Claude Code hook ecosystem and community patterns for background-service management.
2. **Recommended design shape** per each of the ten question groups — options considered, recommendation, rationale.
3. **Clause-by-clause scope coverage** — each of §4.1–§4.7 mapped to the recommended design.
4. **Sealed-component amendment inventory** — every amendment the design requires, named and surfaced as halt-signal candidates. The owner rules on each.
5. **Failure-mode catalogue** — every failure mode the supervisor must detect and its recovery disposition.
6. **Complexity estimate** — AI-time calibrated honestly. This component is substantial; likely comparable in scope to the full three-gate chain build (safety + reversibility + cost) combined, given it touches at least four sealed components and introduces a supervisor layer.
7. **Prototyping priorities** — questions only live prototype can answer.

## 8. Execution note

On owner's G1 approval, a research agent is dispatched against this plan. The research agent is read-only against the pos-v2 tree; any halt-signal surfaces during research rather than during build. Sealed-component amendments the research identifies become separate sealed-component cycles if the owner approves them.

---

## 9. Awaiting owner's approval

- Approve as written → research dispatch.
- Approve with changes → revise and resubmit.
- Reject → rework from whatever constraint broke.
