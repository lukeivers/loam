# Research — Hands-Off Lifecycle

**Status:** DRAFT — produced against the G1-approved research plan at `research-plan.md`.
**Authored by:** research agent on Eve's behalf.
**Date:** 2026-04-19.
**Phase:** Phase 5 opener; first component authored under the new fourth research lens.

This document responds to the ten question groups and seven deliverable sections in the research plan. It is deliberately long: the component touches four sealed components, introduces a supervisor layer, and depends on the exact shape of Claude Code's session-start hook surface today. Skimming the section headings will give the structure; detailed recommendations live under each.

---

## 0. Framing read — what this component has to do, compactly

The cutover experience at pos-v2-rc-0.1.0 requires the user to (a) scaffold `~/.pos/bootstrap.yaml` by hand, (b) install and load a memory-sidecar plist, (c) install and load an orchestrator plist, (d) remember that the root README does not describe the current state, and (e) know what to do if any of the above fails mid-operation. That is four manual steps and one orientation trap before the first conversational turn.

The target experience is: the user opens a Claude Code session in a pos-v2 workspace. The session comes up. The system is running. If it was the first session, a single confirmation sentence reports what was scaffolded. Nothing else. Ongoing operation is the harness's problem; the user notices only if something fails badly enough that it needs founder-authority intervention.

The memory system is the base layer. Filesystem-staging exists to keep the urgent-recovery window short, not to be a stable fallback. Self-heal with bounded retries, then loud escalation — silent-stay-degraded is forbidden.

---

## 1. Survey of existing patterns

### 1.1 Process supervisors (macOS-primary, Linux-secondary)

**launchd** is the macOS-native surface. The sealed memory-system and orchestrator components already ship launchd plists — `memory-system/launchd/com.pos-v2.memory-graphiti.plist` and `orchestrator/ops/launchd/com.pos.orchestrator.plist.tmpl`. Both use `KeepAlive=true` with `ThrottleInterval` to cap rapid-crash loops. `RunAtLoad=true` starts them at user login; `bootstrap`/`bootout` is the current (non-deprecated) install/uninstall verb pair.

**systemd-user** is the Linux equivalent. The orchestrator ships a parallel `.service.tmpl` under `orchestrator/ops/systemd/`. Memory-system does not (yet) — an inventory gap worth noting.

**supervisord** (third-party Python supervisor) is cross-platform and config-driven but is not the native supervisor on either target platform; adopting it would add a dependency that duplicates what launchd/systemd already do.

**direct subprocess with a Python supervisor wrapper** is the third option, used by the existing `workspace-bootstrap/src/workspace_bootstrap/adapters/memory_system.py` — the bootstrap adapter `Popen`s the sidecar and polls `/health`. This works for a test workspace that wants the sidecar only for the lifetime of the bootstrap run; it does not give auto-start-at-login.

**Observation about the rebuild's current posture.** Memory-system and orchestrator each carry their own service-manager config, but there is no single artefact that installs all required services at first run in a consistent way. That is precisely the gap this component closes.

### 1.2 Durable-queue / outbox patterns

The transactional outbox pattern is the reference design for "a write has to land in two places and I cannot distributed-transaction them." The writing service commits the business write and the outbox entry atomically; a separate worker reads the outbox and forwards to the downstream system; on confirmed forward, the outbox entry is deleted (or marked forwarded).

Three candidate durable substrates for the staging store:

- **JSONL append-only file.** Simplest; `fsync` after each line gives durability; ordering is line order. Disadvantages: rewriting to drop forwarded entries means rewriting the file or carrying a "forwarded_at" column. No concurrent-reader story.
- **SQLite with WAL mode.** `INSERT` for staging, `DELETE` after confirmed landing. WAL gives concurrent readers; `fsync` via WAL-checkpoint gives durability. Schema is trivial (`id`, `created_at`, `payload`, `forward_attempts`, `last_error`). Recovery semantics are well-understood — WAL replay on open. pos-v2 already uses SQLite for orchestrator local state (`orchestrator/src/local_state.py`) and for graceful-degradation's episodes (`~/.pos/degradation.sqlite`); this is the established substrate.
- **Per-entry file in a spool directory.** Simple filesystem semantics; each file is one write; `fsync` + atomic `rename` for durability; delete on confirmed landing. Ordering is lexicographic on filename. Less popular but eliminates a single-file bottleneck and lets shell tools inspect the queue.

### 1.3 Write-ahead-log reconciliation

WAL reconciliation in the database sense (Postgres, SQLite) provides crash consistency for a single store. What pos needs is *cross-system* reconciliation: staged writes persist on disk; the Graphiti/Kuzu store is the downstream. The pattern is closer to the outbox pattern above than to database WAL — the relevant constraints are:

- **Ordering.** Replay must preserve the order writes were staged in. Graphiti episodes carry temporal semantics (`valid_at`, `reference_time`); out-of-order replay could produce an inconsistent temporal view. Strict FIFO drain.
- **Idempotence.** A drain attempt may fail mid-write; restart must not duplicate. Option A: the staged entry carries a client-generated UUID and Graphiti deduplicates on it. Option B: the drain worker uses transactional semantics — `INSERT` to staging, attempt Graphiti write, `DELETE` from staging only on confirmed success; a crash between write and delete means the next attempt re-writes the same episode (which Graphiti may accept or may deduplicate on UUID). Graphiti's `add_episode` appears to generate UUIDs at the Graphiti side; a client-side UUID passed in explicitly would be the cleanest contract. Needs confirmation during prototyping.
- **Conflict handling.** If the sidecar was reachable from a parallel path during degraded mode — e.g., a long-running background task that kept its own connection to the healthy sidecar — the replay could produce duplicates. For pos-v2 this is unlikely (there is only one writer path), but the design should not assume so.

### 1.4 Claude Code hook ecosystem — the critical input

The hook surface most directly relevant is `SessionStart`. Official documentation confirms the following, as of April 2026:

- `SessionStart` fires on session start, resume (`--resume`), after `/clear`, and after compaction. Input JSON carries a `source` field (`startup` / `resume` / `clear` / `compact`) and a `hook_event_name` of `SessionStart`. Stdout from the hook is special: it is added to Claude's context (unlike most hook events, where stdout goes to debug log).
- Only `type: "command"` hooks are supported for SessionStart — no HTTP or prompt-type hooks.
- Configuration lives in `.claude/settings.json` under `hooks.SessionStart`.
- `async: true` launches the hook in the background and lets Claude continue immediately. `asyncRewake: true` launches in background and, on the background process's exit code 2, wakes Claude with the stderr/stdout as a system reminder. Timeout applies even to async hooks.
- Hook output injected as context is capped at 10,000 characters; overage is saved to a file and replaced with a pointer.

**Known failure mode, directly relevant to this component.** After Claude Code v2.1.87 (January 2026), a `SessionStart` hook that spawns a background process inheriting the parent's stdin/stdout/stderr file descriptors causes Code mode to hang indefinitely — claude-code waits for the subprocess to release the pipes it uses for stream-json communication with Claude Desktop. Issue #43123 is the canonical reference. The official workaround is not to use `async: true` alone but to fully detach the child process from inherited FDs: `nohup <command> </dev/null >/dev/null 2>&1 &`. `async: true` is insufficient on its own because it still inherits the parent's FDs.

**Consequence for this component.** The SessionStart hook must not itself *be* the long-lived process. It must *trigger* a fully-detached launch of the services and return quickly. The recommended shape is: SessionStart hook runs a small synchronous script that (a) checks whether the services are already up, (b) if not, invokes a detached `launchctl bootstrap` (macOS) or `systemctl --user start` (Linux) — which is itself non-blocking and FD-safe — and (c) reports status as additionalContext. The detached service-manager becomes the process supervisor; the hook has no long-lived child.

This is **not a workaround-requiring-user-install**: `launchctl` and `systemctl --user` exist on every macOS/Linux system pos-v2 targets. The hook payload is small, synchronous, and exits promptly.

**Other hook events worth noting:**

- `SessionEnd` — fires on session termination. Useful for logging "session closed" to the observability aggregator. Cannot block termination.
- `UserPromptSubmit` — fires on every user prompt. Its stdout is also added to context. Could be used for a lightweight per-turn health check, but the sealed graceful-degradation component already performs passive detection via the `ClaudeClient` adapter, so this is unneeded for this component.
- `PreCompact` — fires before compaction. Not relevant here; memory's own compaction survival is the orchestrator's concern.

### 1.5 Community patterns for background-service management via hooks

The `claude-mem` / `claude-claude-mem` community patterns, and the disler `claude-code-hooks-mastery` repo, show the prevailing approach: SessionStart hooks load static context (git status, TODOs, sprint priorities) rather than launching services. There is not yet a widely-adopted pattern for SessionStart-triggered service launch, precisely because issue #43123 made the naive approach fatal. This component, if it lands cleanly, would become one of the first reference implementations of the "SessionStart triggers detached service-manager, returns quickly" pattern.

---

## 2. Recommended design shape — per question group

### Q1 — Claude Code session-start hook mechanics

**Recommendation.** Use a `SessionStart` hook of type `command`, running a small script (`bin/pos-session-start`) synchronously with `async: false`. The script:

1. Probes the memory sidecar and the orchestrator on their canonical ports / socket.
2. If either is not healthy:
   - Invokes `launchctl bootstrap gui/<uid> ~/Library/LaunchAgents/com.pos-v2.<label>.plist` (macOS) or `systemctl --user start pos-v2-<label>.service` (Linux). These are non-blocking: they *ask* the service manager to launch; they do not fork the process.
   - Waits up to a bounded time (e.g. 15 seconds, configurable) for the health probe to pass, using a polling loop.
3. Writes a short status to stdout (which becomes `additionalContext` to Claude via the plain-stdout path, or is returned as JSON with `hookSpecificOutput.additionalContext`).
4. Exits 0 on success, non-zero on failure.

**Rationale.**

- `SessionStart` is the correct hook event — it fires on session start, resume, and after compaction. On resume/compact the services are almost certainly already up, so the probe branch succeeds instantly and the hook exits in milliseconds.
- The synchronous short-script pattern avoids issue #43123 entirely — no background child process inherits FDs from Claude Code. The service manager (launchd/systemd) is the thing actually supervising the long-lived process.
- The hook itself contains no supervision logic — it delegates to the platform-native supervisor. This is correct separation: the hook is a trigger, not a supervisor.

**Halt signal.** If the user is on a platform where neither launchd nor systemd-user is available (niche — e.g., some Windows/WSL configurations, or containerised environments without a user service manager), the hook halts with a named diagnostic pointing to `docs/platforms.md` for the supported-platform matrix. Per the research-plan's constraint, we do *not* invent a workaround that the user must install separately.

**Status field use.** On `source: "startup"`, the hook runs the full probe-and-launch sequence. On `source: "resume"` or `source: "compact"`, the hook assumes services should already be running and runs a faster probe-only sequence; if the probe fails, that is a supervisor-escalation-worthy signal, not a cold-start signal.

### Q2 — Memory sidecar launch and supervision

**Launch primitive.** launchd on macOS, systemd-user on Linux. Plist/service-file already exists for the memory-system sidecar (macOS only). The `hands-off-lifecycle` component needs to:

- Author and ship the missing Linux systemd-user service file for memory-system (amendment candidate — see §4).
- Install both memory-system and orchestrator service files as part of the first-run scaffold (see §4.5 below), without requiring the user to run `cp` and `launchctl bootstrap` by hand.

**Supervision in steady state.** The launchd/systemd manager handles restart-on-crash (`KeepAlive=true` + `ThrottleInterval`). The pos-v2 supervisor layer — which is this component's core new runtime piece — handles *semantic* supervision: probe-based health, latency tracking, canary queries, and the escalation state machine. It does not restart processes itself; if the sidecar needs a kick, the supervisor asks the service manager (`launchctl kickstart`/`systemctl --user restart`).

**Probe protocol.**

- **Liveness probe.** `GET /health` on `http://127.0.0.1:<port>`. Success: 200 within a configurable timeout (default 2 seconds).
- **Latency threshold.** Rolling P95 on probe round-trip time. Exceeds configurable threshold (default 500 ms) for N consecutive probes (default 3) → "degraded-latency" signal.
- **Canary query.** A fixed known-shape query against a fixed known-entity UUID, run at a lower frequency (default every 5 probes). Compares the response shape to a stored expected shape. Mismatch (missing fields, wrong types, empty results when results are expected) → "degraded-correctness" signal.
- **Probe cadence.** Default 30 seconds between probes; aggressive during half-open recovery; configurable.

**Failure-mode classification.**

| Signal | Interpretation | Supervisor action |
|--------|---------------|-------------------|
| HTTP connection refused | Process not listening (crashed or not yet up) | Count; after N consecutive, escalate to "sidecar-down" |
| HTTP 5xx | Process up but broken | Count; escalate to "sidecar-error" |
| HTTP timeout | Process stuck / slow | Count; escalate to "sidecar-hang" |
| Latency over threshold N probes | Probably loaded / gc'ing / disk-slow | Degraded-latency signal (advisory) |
| Canary-query shape mismatch | DB state or code broken | Escalate to "sidecar-corrupt" — hard signal |
| Process PID exited | Service manager will restart per KeepAlive | Count restarts; excess → "restart-storm" |

**Transient vs. sidecar-failing.** A transient hiccup is ≤ 2 consecutive failed probes within 60 seconds; beyond that, classify as sidecar-failing. Thresholds are configurable.

**Orchestrator supervision is the same shape** — the probe targets differ (Unix-domain-socket JSON-RPC `ping` instead of HTTP `/health`), but the state machine is identical. Single supervisor implementation, two targets, one config per target. See §3 below for the shape.

### Q3 — Durable staging design

**Recommendation: SQLite with WAL mode, one DB per-workspace at `~/.pos/memory-staging.sqlite`.**

**Schema:**

```sql
CREATE TABLE staged_writes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,  -- order-preserving
  created_at TEXT NOT NULL,              -- ISO 8601 UTC
  episode_uuid TEXT NOT NULL,            -- client-generated; survives retry
  payload_json TEXT NOT NULL,            -- the IngestRequest body as JSON
  forward_attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  last_attempt_at TEXT
);
CREATE INDEX idx_created_at ON staged_writes(created_at);
```

**Why SQLite-WAL over JSONL or per-entry files.**

- pos-v2 already uses SQLite in two sealed components (`orchestrator/src/local_state.py`, graceful-degradation's `~/.pos/degradation.sqlite`). Adopting the same substrate reduces operational surface.
- `DELETE FROM staged_writes WHERE id = ?` on confirmed landing is trivial and transactional; JSONL would require rewriting the file or carrying a "forwarded_at" column that is read-expensive.
- WAL-mode gives a single writer, many readers; the drain worker, the write path, and any diagnostic read path coexist cleanly.
- Schema evolution is well-understood.

**Ordering guarantees.** `id INTEGER PRIMARY KEY AUTOINCREMENT` gives monotonic insert order. Drain worker reads `ORDER BY id ASC LIMIT 100` and forwards in that order.

**Size caps.** Two caps:

- **Soft cap** (default 10,000 entries). Emits an OTel warning span; supervisor records the signal.
- **Hard cap** (default 50,000 entries). Supervisor escalates loudly (Tier 1) — the degraded mode has lasted too long and staging is filling; user intervention needed.

Both cap values are configurable in `~/.pos/memory-staging.yaml`.

**Overflow behaviour.** At hard cap, subsequent `ingest()` calls raise `StagingOverflow`, which propagates up to the memory API caller. Memory callers who cannot fail — e.g., session-critical captures — must handle this by surfacing to the user. **The staging store does not silently drop writes.** Dropping = data loss; the whole point of staging is durability.

**Read-path integration.** The existing memory `MemoryAPI.search()` queries Graphiti directly. In degraded mode, the `MemoryAPI` must additionally consult staging for recent-write coverage. Concretely: the MemoryAPI gains a `degraded_mode_read_fallback` path that, when the sidecar is unreachable or the supervisor has flagged it down, queries `staged_writes` for entries in the requested group/scope AND the last-successful-Graphiti-snapshot for historical facts. The fallback is transparent to the persona — the persona asks `search(query, ...)` and gets merged results, with a `degraded: true` flag in the response. The persona can then choose whether to tell the user.

This read path is an amendment to memory-system (see §4).

### Q4 — Reconcile drain correctness

**Drain worker.** Runs inside the orchestrator process (co-located with the supervisor — see §Q5 for the supervisor-hosting decision). Activated by the supervisor when the memory sidecar transitions from `down` or `degraded` back to `healthy`.

**Drain sequence.**

1. Supervisor emits `pos.supervisor.memory.mode=recovering`.
2. Drain worker reads up to 100 entries from `staged_writes ORDER BY id ASC`.
3. For each entry, in order:
   a. Call `sidecar.ingest(payload_json, episode_uuid=...)`.
   b. On success: `DELETE FROM staged_writes WHERE id = ?`.
   c. On failure: increment `forward_attempts`, write `last_error`, `last_attempt_at`. If `forward_attempts >= 3`, move to a poison-pill table (see below) and continue.
4. When `staged_writes` is empty (or only poison-pills remain), supervisor emits `pos.supervisor.memory.mode=healthy` and the drain worker stops.
5. If the sidecar goes down again mid-drain, drain pauses; staging continues to accept new writes in staging-order; drain resumes from the next pending entry when the sidecar comes back.

**Idempotence via client-generated `episode_uuid`.** Every `ingest()` call (in normal mode or degraded) generates a `uuid4()` at the client and passes it to the sidecar. In normal mode, the sidecar stores the write and returns the same UUID. In degraded mode, the UUID is written into staging. On drain replay, the same UUID is sent — if Graphiti already accepted it (e.g., through a parallel path), Graphiti's dedup logic applies (or if not present, we accept the duplicate; Graphiti upserts on UUID appear to be safe, but needs prototyping confirmation). This avoids the "same write succeeded server-side, client crashed before deleting staging, retry duplicates" problem.

**Prototyping-only uncertainty.** Whether Graphiti's `add_episode` accepts a client-supplied UUID with idempotent semantics is not verified from the source here. The prototyping priorities in §7 name this as the first thing to verify.

**Poison-pill handling.** An entry that has failed 3 times with the same classified error moves to `staged_writes_poison`. The supervisor logs this and does not retry automatically. On the poison table reaching its own soft cap (default 10), the supervisor escalates Tier 1 — repeated rejection from the recovered sidecar implies the data itself is bad or the schema has diverged.

**Staging-cleanup semantics.** Staging is never silently emptied. Cleanup happens only through: (a) confirmed successful forward (the common path), or (b) explicit user action via `pos staging clear-poison` (no auto-cleanup of poison). The research-plan constraint — "drain failures surface as an explicit state; staging is not silently emptied" — rules out any background cleanup of failed entries.

### Q5 — Orchestrator lifecycle shape

**Options considered:**

- **A. Session-bound.** Orchestrator starts when the first Claude Code session opens, stops when the last session closes.
- **B. Supervised-service.** Orchestrator is always running (launchd/systemd), Claude Code sessions attach to it as IPC clients.
- **C. Hybrid.** Supervised-service by default; session can optionally start/stop on demand.

**Recommendation: B — supervised-service.**

**Rationale.**

- The orchestrator already hosts the primary-persona's `BackgroundWorkMonitor` (primary-persona layer, sealed). Work that the user dispatched earlier and expects to be running *between* sessions must be running between sessions. Session-bound would kill these. This is the "persistent work" property in `VALUE_PROPOSITION.md` and is non-negotiable.
- The existing orchestrator launchd plist (`orchestrator/ops/launchd/com.pos.orchestrator.plist.tmpl`) already assumes this shape: `RunAtLoad=true` + `KeepAlive=true` means "start at login, always keep running."
- The session-start hook's job is therefore to *probe* the orchestrator, not to *start* it — but on first run (or after `launchctl bootout` etc.) the hook must be able to kick the orchestrator via `launchctl bootstrap` to get it up.
- Both probe-and-start can coexist: on session start, probe; if down, bootstrap; then probe again; if still down, escalate.

**Where does the supervisor layer live?** Two sub-options:

- **B.1 Supervisor is part of the orchestrator process** (same event loop as the background-work monitor). Co-location simplifies state sharing and OTel spans.
- **B.2 Supervisor is its own process**, launched by launchd alongside the orchestrator and memory sidecar.

**Recommendation: B.1 — supervisor inside the orchestrator.** Rationale:

- The supervisor talks to the memory sidecar (HTTP) and to the orchestrator (itself). Making the supervisor part of the orchestrator means the "orchestrator-health" probe is literally the orchestrator checking itself — which, for the launchd-managed orchestrator, is what we already get from `KeepAlive=true`. The in-process self-check is about *semantic* health (can it dispatch? is the monitor running?) not *process* health. No separate supervisor-process needed for this.
- Memory-sidecar probing from inside the orchestrator requires only an HTTP client — trivial.
- The orchestrator's existing OTel emission layer is the natural home for supervisor spans.

B.1 makes orchestrator amendment load-bearing — see §4.

**Orchestrator amendment consequence.** The sealed orchestrator today does not have a supervisor module. Adding one is an amendment to the orchestrator component. The amendment is tightly scoped: a new `orchestrator/src/supervisor.py` module, wired into `_startup()` alongside the heartbeat task. This is named as an amendment-candidate in §4.

### Q6 — Config auto-scaffold contents

**First-run detection.** No `~/.pos/bootstrap.yaml` exists AND no `~/.pos/` directory exists → first run. (If `~/.pos/` exists but `bootstrap.yaml` doesn't, that is a *partial* scaffold — surface it, don't overwrite.)

**Scaffold contents.** The scaffold writes:

1. **`~/.pos/bootstrap.yaml`** — the twelve-adapter bundle listing the sealed Phase 1–4 foundational components, with `enabled: true` defaults on all foundational ones and `launch: true` on memory-system (so the sidecar launches when bootstrap runs). Layout matches the existing `workspace-bootstrap/docs/` examples.
2. **`~/.pos/memory.yaml`** — `launch: true`, `host: 127.0.0.1`, `port: 8765`, `health_path: /health`, `startup_timeout_s: 30`, `poll_interval_s: 0.5`. These match the current adapter defaults.
3. **`~/.pos/memory-staging.yaml`** — (new) soft_cap: 10000, hard_cap: 50000, db_path: `~/.pos/memory-staging.sqlite`, drain_batch_size: 100, probe_interval_s: 30, latency_threshold_ms: 500.
4. **`~/.pos/safety/always_ask.yaml`** — the framework-floor always-ask entries per safety-layer sealed spec. Starter contents: the documented framework-floor list (external payments, irreversible deletions of user data, etc. — copied from the safety-layer docs).
5. **`~/.pos/cost/ceilings.yaml`** — starter daily and monthly caps that match the cost-governance sealed documented starter values. Advisory by default, with a note that they are starter caps the user may want to raise or lower.
6. **`~/.pos/reversibility.yaml`** — empty registrations (the user adds per-tool reversibility classes over time; the framework defaults cover the sealed primitives).
7. **`~/.pos/self-correction.yaml`** — starter config with default enabled.
8. **`~/.pos/degradation-config.yaml`** — starter config with the Tier-2-default + Tier-1-for-auth-broken defaults the sealed graceful-degradation component uses.
9. **Service-manager files** — `~/Library/LaunchAgents/com.pos-v2.memory-graphiti.plist` and `~/Library/LaunchAgents/com.pos.orchestrator.plist` (macOS), or the equivalent `~/.config/systemd/user/*.service` files on Linux, templated with absolute paths resolved to the current workspace.
10. **Service-manager bootstrap** — `launchctl bootstrap gui/<uid> ~/Library/LaunchAgents/com.pos-v2.memory-graphiti.plist` and the orchestrator equivalent, so the services are installed and started in one shot.

**What the single confirmation sentence says.**

> "pos v2 first-run scaffold complete: twelve foundational components configured at defaults (safety/always-ask, cost ceilings, reversibility, self-correction, memory, degradation), memory sidecar and orchestrator launched as user services, staging store initialised. `~/.pos/` is your config dir — edit any file to adjust. Proceeding."

The sentence is one line in chat. Detail is available on request ("what was scaffolded?" → full list).

**Not scaffolded.**

- The user's personal persona (`personas/`). That is a workspace-level artefact and is either pre-existing or the user's own onboarding choice.
- Any business-logic config. Plugins and domain adapters are explicit add-ons.
- Anything requiring founder-authority inputs (spending caps above starter levels, external channel registrations, etc.).

### Q7 — Loud-escalation protocol

**Escalation channel.** The primary-persona one-on-one channel. In the default workspace, this is the Telegram channel registered in `config/stack.yml` under `channels.primary.telegram`. For non-Telegram workspaces, the channel is whatever the user has registered as primary per the channel-agnostic interaction objective (v1.1 spec revision #13).

**Message shape (plain language).**

> pOS v2 needs attention.
>
> **What failed:** memory sidecar unreachable for 15 minutes despite 3 restart attempts.
> **What was tried:** launchd auto-restart (3 attempts, throttle 30s). Last probe error: connection refused.
> **Current state:** memory writes staged (1,247 entries pending). Normal operation paused.
> **What you can do now:** (1) check `~/.pos/memory-staging.sqlite` is present and writable, (2) run `pos memory doctor` for a diagnostic dump, (3) check the sidecar log at `memory-system/data/graphiti-service.err.log`.
>
> Updates will not repeat until the state clears or changes class.

**Idempotence mechanism.** The supervisor maintains an escalation-state record in `~/.pos/supervisor-escalation.json`:

```json
{
  "current": {
    "id": "uuid-...",
    "class": "memory.sidecar.unreachable",
    "opened_at": "2026-04-19T10:15:00Z",
    "notifications_sent": 1,
    "last_notified_at": "2026-04-19T10:15:00Z"
  }
}
```

An escalation stays "current" as long as the classified failure mode stays the same. The supervisor sends a notification the *first* time the escalation opens and does not re-notify while it remains in the same class. It emits a *second* notification if the class changes (e.g., `unreachable` → `corrupt`). On recovery, it emits a short "recovered: memory sidecar healthy; 1,247 staged writes drained; normal operation resumed" message. Repeated notifications for the same escalation are an anti-pattern.

**The "pos v2 needs attention" durable surface.** A file at `~/.pos/attention.md` containing the current escalation text, written at notification time and cleared on recovery. The user can `cat` it any time to see current state. It is also referenced from the session-start hook's additionalContext when present — on session start, if an escalation is open, Claude knows about it from turn one.

**Integration with the sealed notification tier system.** Loud escalations go out as Tier 1 per `.claude/rules/communication-routing.md`. The per-day Tier 1 cap is a hard limit; if pos v2 is generating Tier 1 escalations daily, that is its own misconfiguration signal (degradation is too frequent → investigate root cause) and the supervisor emits an OTel span naming it so the alignment-review process picks it up.

### Q8 — Sealed-component amendments required

See §4 for the full inventory. Briefly: **four amendments** are load-bearing:

1. **memory-system:** staging + reconcile path + degraded-mode read-fallback; linux systemd-user service file.
2. **orchestrator:** supervisor module; session-start-hook helper script.
3. **graceful-degradation:** supervisor consumption — the supervisor's memory signals flow into graceful-degradation's existing detection pipeline (not a replacement; a complement).
4. **workspace-bootstrap:** first-run scaffold wiring — a new `first_run` phase or a new `first_run_adapter` type that runs before any `before_orchestrator_start` adapters when the scaffold markers are absent.

### Q9 — README authorship

**Audience.** A user who just cloned the pos-v2 repo and wants to know what to do next. Not a contributor, not a framework archaeologist. The bar: after reading, they know (a) what pos-v2 is, (b) what running a session looks like, (c) where to find more detail.

**Proposed structure** (short — target 80 lines):

```
# pOS v2 — personal OS, Claude-native

pos-v2 is a Claude-only personal operating system: a long-running background
process (the orchestrator) plus a semantic memory store, a three-gate safety
chain, and a primary persona that translates your natural-language intent
into AI-effective execution.

## Status

Foundation-complete: twelve sealed components, 824 tests passing.
See `docs/rebuild/STATE.md` for the full component status table.

## What running a session looks like

1. Open a Claude Code session in this workspace.
2. First run: a single sentence reports what was scaffolded. Proceed.
3. Normal runs: your primary persona greets you with what needs attention.
4. Close the session. Background work continues.

## Layout

  docs/rebuild/      — research, proposals, briefs for each sealed component
  memory-system/     — semantic memory sidecar (FastAPI + Graphiti + Kuzu)
  orchestrator/     — long-lived asyncio process, Unix-socket JSON-RPC surface
  workspace-bootstrap/ — composition engine; twelve-adapter bundle
  safety-layer/ reversibility-primitive/ cost-governance/ self-correction/
                     — the three-gate chain + self-correction loop
  graceful-degradation/ objective-tracker/ scope-of-work/ primary-persona/
                     — runtime policy + primitives
  observability-aggregator/ self-upgrade/
                     — infrastructure

## Implementation

Python 3.13. See `docs/rebuild/STATE.md` rules 6-9 for language/test/file
conventions.

## License, contributions, etc.
[standard boilerplate]
```

**Interaction with `docs/rebuild/`.** The root README is the entry point; `docs/rebuild/` is the reference tree. The README points at STATE.md for status and names component directories; readers wanting implementation detail follow the links. No content duplication.

### Q10 — Fourth-lens capture

**Exact wording for `FUTURE_IDEAS.md` Core Development Principles — four lenses.**

Insert as Lens 4 after the existing Lens 3 — ODD authoring:

````markdown
### Lens 4 — Hands-off lifecycle

> **Zero manual lifecycle management, ever.** Every feature must assume the user performs no setup beyond opening a Claude Code session, and no ongoing service-management beyond responding when the system tells them something is wrong. Any setup that can be automated is automated; any setup that must be user-visible is one confirmation, not a multi-step procedure. Any ongoing service-lifecycle concern (a sidecar crashing, the orchestrator hanging, a config going stale) is the harness's problem, not the user's — self-heal silently when possible, escalate loudly when not. Degraded mode that silently stays degraded is a failure of the lens, not a satisfaction.

The required research question: **"What would a user who has never configured a server have to do to turn this feature on? Can we eliminate it?"**

A feature that answers "install a plist" or "edit a YAML file" is asking the user to do translation work the harness should do for them. Features that fail the hands-off-lifecycle test turn non-tech users away and turn tech users into system administrators — both modes are failure.
````

**Research-plan Step 3 addition.**

The Idea 1 enforcement programme's Step 3 currently requires four questions. After this landing, it should require five — the fourth lens gets its own mandatory research-plan section. The wording to insert:

> - **Hands-off lifecycle:** what would a user have to do to turn this feature on, and can we eliminate it? What ongoing lifecycle concerns does this introduce, and who owns them?

The research-plan validator (when it lands — the validator itself is not built yet per Idea 1) refuses to mark a plan reviewable until this section is present and non-empty.

---

## 3. Clause-by-clause scope coverage (§4.1–§4.7 mapped to design)

### §4.1 — Auto-launch on Claude Code session start

- **Hook**: `SessionStart` of type `command` in `.claude/settings.json`, invoking `bin/pos-session-start`.
- **Script responsibility**: probe → (if needed) `launchctl bootstrap`/`systemctl --user start` → probe again → exit.
- **Silent on happy path**: the script writes only a minimal `additionalContext` ("pos v2 ready") when everything passes.
- **Failure surfaces immediately**: non-zero exit with stderr = named diagnostic; Claude Code treats this as a hook error and surfaces it to the user.
- **Idempotent re-open**: probe short-circuits when services are up; script exit time < 500ms typical.

### §4.2 — Continuous health supervision

- **Supervisor** runs inside the orchestrator process (co-located with BackgroundWorkMonitor).
- **Probe targets**: memory sidecar HTTP, orchestrator's own IPC socket (self-probe).
- **Probe cadence, timeouts, thresholds**: all in `~/.pos/supervisor.yaml`, with starter defaults.
- **Signal classification**: per table in Q2.

### §4.3 — Durable filesystem staging for memory writes during degraded mode

- **Substrate**: SQLite WAL at `~/.pos/memory-staging.sqlite`.
- **Shape**: per Q3 schema.
- **Bounded size**: soft cap 10k entries, hard cap 50k entries (configurable).
- **Overflow**: `StagingOverflow` raised; never silent drop.
- **Read-path integration**: MemoryAPI consults staging in degraded mode; transparent to the persona.

### §4.4 — Reconcile-on-recovery drain

- **Drain worker** runs inside the orchestrator process.
- **Activation**: supervisor transitions memory mode back to healthy.
- **Strict FIFO** via `id ASC`.
- **Confirmed-landing delete**: entries removed from staging only on successful Graphiti forward.
- **Poison-pill handling**: per Q4.
- **No silent empties**: per research-plan constraint.

### §4.5 — Auto-scaffold workspace configuration

- **First-run detection**: absence of `~/.pos/bootstrap.yaml` + absence of `~/.pos/` dir.
- **Scaffold contents**: per Q6 full list.
- **Single confirmation sentence**: per Q6 wording.
- **Service-manager install**: scripted; no manual `cp` or `launchctl` needed.

### §4.6 — Loud-escalation protocol when self-heal fails

- **Message shape**: per Q7 template — what failed / what was tried / current state / what the user can do.
- **Idempotence**: `~/.pos/supervisor-escalation.json` tracks the current escalation class; one notification per class; second notification only on class change; recovery notification always.
- **Durable surface**: `~/.pos/attention.md` mirrors the current escalation text.
- **Channel integration**: Tier 1 via the sealed notification tier system.

### §4.7 — Fresh README at workspace root

- **New README content**: per Q9 outline.
- **Interaction with `docs/rebuild/`**: README points in, does not duplicate.
- **Accuracy**: reflects actual sealed-components state, not the prototyping-phase content.

---

## 4. Sealed-component amendment inventory

The research-plan is explicit that amendments are halt-signals to surface, not to improvise around. Each amendment below is named with (a) the named surface changing, (b) a one-sentence rationale for why it is load-bearing. The owner rules per amendment; each becomes its own unseal cycle if approved.

### Amendment 1 — memory-system: staging + reconcile path + degraded-mode read-fallback

**Named surfaces changing.**

- `memory-system/src/memory.py` — `MemoryAPI.ingest()` gains a "try sidecar, on fail write-to-staging" branch. `MemoryAPI.search()` gains a degraded-mode fallback path that queries staging + last-known-Graphiti snapshot.
- `memory-system/src/staging.py` — **new module.** SQLite-WAL-backed staging store; `stage_write(payload)`, `list_pending(limit)`, `forward(id, result)`, `size()`, overflow handling.
- `memory-system/src/drain.py` — **new module.** Drain worker; called by the supervisor; reads staging, forwards to sidecar, confirms, deletes.
- `memory-system/src/ephemerality.py`, `memory-system/src/retention.py` — no change expected; staging records the post-ephemerality payload.
- `memory-system/src/observability.py` — add spans for stage/drain events.
- `memory-system/tests/` — new tests covering degraded-mode ingest, degraded-mode search, reconcile, overflow, poison-pill, idempotent replay.

**Why load-bearing.** The research plan's §3 requires degraded-mode behaviour where writes land in a filesystem staging area, reads answer from staging + last-known-Graphiti state, and reconcile runs on recovery. Without the MemoryAPI branch for staging, the memory system either drops writes (violates memory-is-base-layer) or blocks the caller (violates zero-manual-lifecycle — user has to manually re-submit after the sidecar comes back). This amendment is the only way to satisfy the research plan's memory-system constraint without weakening the base-layer-mandatory rule.

**Also in this amendment.** Ship `memory-system/systemd/com.pos-v2.memory-graphiti.service` — the Linux systemd-user equivalent of the existing launchd plist. The research plan does not name Linux explicitly, but the orchestrator already ships both; memory-system should match for scaffold parity.

### Amendment 2 — orchestrator: supervisor module + session-start helper

**Named surfaces changing.**

- `orchestrator/src/supervisor.py` — **new module.** `Supervisor` class with probe loop, state machine (healthy / degraded-latency / degraded-correctness / down / recovering), signal emission (pyee or direct OTel), and memory-drain coordination.
- `orchestrator/src/orchestrator.py` — `_startup()` instantiates `Supervisor` alongside the heartbeat task; `_shutdown()` stops it.
- `orchestrator/config.py` — new config block for supervisor probe cadence, timeouts, thresholds.
- `orchestrator/scripts/pos-session-start` — **new script.** Session-start helper invoked by the Claude Code hook. Probes, launches if needed via `launchctl`/`systemctl --user`, reports.
- `orchestrator/tests/` — new tests covering supervisor state machine, probe classification, drain activation, supervisor-off-of-hooks.

**Why load-bearing.** The research plan's §4.2 requires a supervisor that probes memory sidecar and orchestrator. The sealed orchestrator does not host one — it has a heartbeat loop but no external-process probing, no state machine, no drain coordination. Adding the supervisor inside the orchestrator (per §Q5 recommendation B.1) is the simplest shape; the alternative (separate supervisor process) multiplies the lifecycle surface without clear benefit.

### Amendment 3 — graceful-degradation: supervisor-signal consumption

**Named surfaces changing.**

- `graceful-degradation/src/detection.py` — gains an input path for supervisor-emitted signals (pyee subscription or direct method call). These complement, not replace, the existing `ClaudeClient`-adapter-based detection. The memory-blind-spot noted in graceful-degradation's architecture.md becomes partially un-blinded: the supervisor's memory-sidecar probe gives graceful-degradation a direct signal about memory degradation that the existing pyee-on-scope-fail heuristic does not.
- `graceful-degradation/src/fsm.py` — new `memory_sidecar` mode (alongside the existing six failure modes) with its own policy default.
- `graceful-degradation/tests/` — new tests covering the supervisor-driven signal path.

**Why load-bearing.** Graceful-degradation currently treats memory as a blind spot (documented in its architecture.md and logged to the rebuild's BACKLOG.md). This component introduces a supervisor that directly observes memory health; feeding those signals into graceful-degradation closes the blind spot. Without this amendment, two separate detection layers emit separate signals about the same thing, and user notifications could duplicate.

**Note on minimal-amendment framing.** This is a small amendment in LOC — mostly a new subscription point and a new mode enum entry. The logic in graceful-degradation is unchanged in structure.

### Amendment 4 — workspace-bootstrap: first-run scaffold wiring

**Named surfaces changing.**

- `workspace-bootstrap/src/workspace_bootstrap/main.py` — new phase `first_run_scaffold` (or equivalent) that runs before `before_orchestrator_start` when scaffold markers are absent. OR: the existing adapter system gains a `run_on_first_run_only` flag.
- `workspace-bootstrap/src/workspace_bootstrap/adapters/` — new adapter `first_run_scaffold.py` that writes the `~/.pos/` config files, installs the service-manager files, and invokes `launchctl bootstrap`/`systemctl --user daemon-reload`.
- `workspace-bootstrap/src/workspace_bootstrap/spec.py` — if going the new-phase route, add the phase to `PHASE_ORDER` and to the phase enum.
- `workspace-bootstrap/tests/` — new tests covering first-run behaviour, idempotent re-run on non-first runs, partial-scaffold detection.

**Why load-bearing.** The sealed workspace-bootstrap assumes `~/.pos/bootstrap.yaml` and the surrounding config already exist. The research plan's §4.5 requires first-run auto-scaffold — which means bootstrap has to do something *before* the normal bootstrap flow on first run. The existing three-phase model (`before_orchestrator_start` / `wrap_activate_scope` / `after_orchestrator_ready`) does not have a pre-phase. The amendment is either (a) a fourth phase before the existing three, or (b) a first-run-only adapter type. Either way, sealed code changes.

**Surface-area impact.** This amendment is the most architecturally load-bearing of the four; workspace-bootstrap's phase model was carefully scoped at seal time. The amendment is defensible because the scope it enables (zero-manual first run) is precisely the value proposition this component delivers. The halt-signal must be surfaced and discussed, not improvised around.

### Summary amendment table

| # | Component | Surface | Depth | Rationale |
|---|-----------|---------|-------|-----------|
| 1 | memory-system | new staging + drain modules; MemoryAPI degraded-mode branches | Medium-large | Base-layer requirement for degraded-mode behaviour; no alternative that preserves the memory-is-mandatory rule |
| 2 | orchestrator | new supervisor module; session-start helper | Medium | Host for the supervisor layer; existing heartbeat-only loop is insufficient |
| 3 | graceful-degradation | supervisor-signal consumption path; new failure mode | Small | Closes the documented memory detection blind spot; complementary, not replacing, existing detection |
| 4 | workspace-bootstrap | first-run phase or first-run-only adapter | Medium | Zero-manual first-run scaffold cannot land without a pre-bootstrap hook point |

Each amendment is a candidate for its own unseal cycle. The owner rules per amendment.

---

## 5. Failure-mode catalogue

The supervisor must detect and respond to the following classes. Disposition column names the recovery behaviour.

| Class | Detection signal | Transient threshold | Sidecar-failing threshold | Recovery disposition |
|-------|------------------|---------------------|---------------------------|----------------------|
| Memory process not listening | HTTP connection refused | 2 consecutive failed probes in 60s | 3 consecutive | launchd restart (automatic); supervisor waits up to 60s; if not up, open escalation |
| Memory process hanging | HTTP timeout at probe | 2 consecutive | 3 consecutive | `launchctl kickstart -k` (force restart); wait up to 60s; if not up, open escalation |
| Memory process 5xx | HTTP 500-599 response | 3 consecutive | 5 consecutive | `launchctl kickstart -k`; wait; escalate |
| Memory latency degraded | Rolling P95 > threshold | N consecutive elevated probes | Sustained ≥15min | Advisory signal (no restart); escalate only at sustained duration |
| Memory correctness degraded | Canary-query shape mismatch | First occurrence | Same | Hard signal; immediate escalation (suggests DB corruption or code divergence) |
| Memory restart storm | launchd restart count ≥ N in 10min | N=3 | N=5 | Open escalation immediately; do not kick again; user intervention needed |
| Orchestrator self-check fail | IPC ping timeout from inside its own process | 3 consecutive | 5 consecutive | Emit crash span; exit nonzero; launchd restarts; supervisor resumes on restart |
| Orchestrator restart storm | launchd restart count for orchestrator ≥ N in 10min | N=3 | N=5 | Escalate; user intervention needed |
| Staging overflow (soft) | staging size > soft_cap | immediate | same | Advisory; begin aggressive recovery probing |
| Staging overflow (hard) | staging size > hard_cap | immediate | same | Reject new writes; escalate Tier 1 |
| Drain poison-pill accumulation | poison table size > 10 | immediate | same | Escalate Tier 1; halt drain until resolved |
| Reconcile drift detected | Post-drain sanity check finds Graphiti has fewer episodes than staging had entries | immediate | same | Escalate; do not clear poison; user intervention needed |
| Config file corrupted | YAML parse fail at session start | immediate | same | Hook exits with named diagnostic; points at the corrupted file |
| Service-manager unavailable | `launchctl`/`systemctl` binary missing | immediate | same | Hook exits with named diagnostic; platform-unsupported halt-signal |

Each row above maps to an OTel span name (`pos.supervisor.<class>.<state>`); graceful-degradation subscribes via Amendment 3.

---

## 6. Complexity estimate

Per `.claude/rules/task-orchestration.md` rule 15: `estimated_minutes` is AI-agent execution time, not human-engineer time. Complex cross-cutting feature anchor: 20–45 minutes.

**This component is substantial.** It introduces a supervisor layer, amends four sealed components, writes 10+ new files, modifies 10+ existing files, adds ~40 new tests, and integrates with a Claude Code hook event whose correct usage requires careful attention to the v2.1.87 FD-inheritance issue. It is comparable in scope to the full three-gate chain build (safety + reversibility + cost) combined, as the research plan anticipated.

**Band estimate:**

| Phase | AI-minute estimate | Notes |
|-------|-------------------|-------|
| 0. Environment setup, venv, test baselines | 5–10 | Standard |
| 1. Amendment 1 (memory-system staging + drain + read-fallback) | 45–75 | New modules, MemoryAPI branching, tests; UUID-idempotence verification against Graphiti is the main uncertainty |
| 2. Amendment 2 (orchestrator supervisor + session-start helper) | 35–55 | New module, startup wiring, probe loop, state machine, hook script |
| 3. Amendment 3 (graceful-degradation supervisor signal consumption) | 15–25 | Small in structure; mostly new mode + subscription |
| 4. Amendment 4 (workspace-bootstrap first-run scaffold) | 30–45 | New phase (or new adapter type) is the most architecturally delicate piece |
| 5. Component integration + first-run acceptance test | 15–25 | End-to-end: nuke `~/.pos/`, open session, verify scaffold + supervision + recovery |
| 6. Docs bundle (per spec v1.1 R4) | 10–15 | Architecture, prose-explanation, escalation runbook |
| **Total** | **155–250 AI-minutes** | **Calibrate toward the upper band** |

**Red-line recommendation.** Halt and resume at 180 minutes unless progressing clearly; the total reflects four sealed-component amendments, not a single-component build. If any amendment surfaces owner-ruling-required decisions mid-build, halt immediately per the research plan's discipline.

**Comparison.** Orchestrator build was estimated 600–750 AI-minutes; this component's estimate is lower because much of the plumbing (process supervision via launchd, SQLite-based local state, OTel emission) exists in the sealed components and is being reused, not re-built. The net-new surface (supervisor state machine, staging, drain, first-run scaffold) is where the time goes.

---

## 7. Prototyping priorities — questions only live prototype can answer

Per research-plan §7.7, these are the questions where reasoning from docs gets us most of the way but cannot give a confident final answer.

1. **Graphiti `add_episode` idempotence with client-supplied UUID.** Does passing an explicit UUID into `add_episode` give dedup on re-submit, or does Graphiti store the duplicate? If duplicate: the drain worker needs a different idempotence strategy (server-side dedup via a custom episode field; or pre-drain duplicate check; or accept-and-cleanup). A 10-line prototype answers this definitively — write the same episode twice with the same UUID and query.

2. **Claude Code SessionStart hook behaviour on resume / compact.** Documentation describes the `source` field but does not specify exact ordering with respect to other session-restoration work. Is the hook stdout injected *before* or *after* the session's own memory restoration? Does it fire on every compaction event, including auto-compaction during a long session? A live prototype opens a session, forces compaction, observes ordering.

3. **`launchctl bootstrap` latency from a synchronous hook.** The session-start hook runs a `launchctl bootstrap` and then polls. Empirical question: typical cold-launch latency on the owner's machine for memory-sidecar (Graphiti + Kuzu init is ~3–10s per the existing adapter docstring) and orchestrator. If the p95 latency is near the 15s budget, the budget must rise or the hook must return async-capable and let the services come up in the background.

4. **SQLite-WAL throughput under write bursts.** Typical pos-v2 write volume is modest (research estimates 3,000 memory events/year per existing cost baseline). But a cold-reconnect after a long outage could produce a burst: all the scoped writes that accumulated during degraded mode get drained. A prototype measures drain throughput and confirms the 100-entry-per-batch default is sensible.

5. **`launchctl kickstart -k` behaviour when launchd is in a restart-storm throttle.** If the supervisor asks launchd to kick a sidecar that launchd has already throttled for rapid crashes, does the kickstart bypass the throttle or wait for it? This affects the escalation timing — if kickstart waits, the supervisor must too; if it bypasses, the supervisor can try more aggressively. Empirical.

6. **`~/.pos/attention.md` visibility in the session-start hook context.** The design has the hook inject escalation text into `additionalContext` when `attention.md` is non-empty. The 10,000-char cap on hook context means a very long escalation list would be truncated. Prototyping confirms the cap and the overflow-to-file behaviour works as documented (in practice escalations are short, but verifying the limit lets us set a hard cap on the supervisor's message length).

7. **macOS vs. Linux service-manager parity.** Both launchd and systemd-user exist on the target platforms, but the exact invocation syntax differs. A small test on both confirms the session-start helper and first-run scaffold work identically, and the error messages on failure are useful.

---

## 8. Open questions requiring owner ruling

1. **Amendment 4's exact shape.** New phase in workspace-bootstrap vs. new adapter type with `run_on_first_run_only` flag. New phase is cleaner architecturally; flag is less invasive. Owner preference?

2. **Supervisor location.** Recommendation is B.1 (inside orchestrator). Is the owner comfortable with orchestrator growing in scope, or would B.2 (separate supervisor process) be preferred for lifecycle isolation?

3. **Scaffold boldness.** §Q6 scaffold includes installing launchd/systemd service files and running `launchctl bootstrap`. These are irreversible in a weak sense (reversed by `launchctl bootout`) but they are modifications to the user's machine-level service registry. Is this in the tier-C autonomous bucket for pos-v2's own components, or should the first-run sentence include a one-line consent prompt before it runs?

4. **Platform-unsupported halt behaviour.** If the session-start hook runs on a platform without launchd/systemd-user (e.g., a container without a user service manager), does the hook halt (refusing to continue) or degrade to a subprocess-supervisor Python-managed fallback? The research plan's constraint favours halt; confirming explicitly.

5. **Tier-1 escalation cap interaction.** If memory-sidecar keeps failing and the supervisor keeps escalating, we could exceed the 3-per-day Tier-1 cap. Is that acceptable (genuine emergencies should escalate), or should the supervisor demote to Tier 2 after the first Tier 1?

6. **Staging-overflow behaviour.** `StagingOverflow` raises to the caller. In the common case, the caller is the primary persona or a background scope; either can surface it. Is there ever a memory write so important that staging overflow should halt the whole orchestrator until resolved? (Probably not, but confirming.)

7. **First-run confirmation sentence.** Owner happy with the proposed wording, or prefers different phrasing?

---

## 9. The four-lens check (retrospective, per FUTURE_IDEAS.md)

Per Idea 1 Step 3, every future feature research plan is supposed to answer the four lenses. This research plan predates the enforcement programme, but answering them here is the model for future plans.

- **Claude-leverage.** Leans heavily on Claude Code's `SessionStart` hook as the integration point. Extends the hook's additionalContext mechanism for session-startup signalling. Does not re-implement session supervision (Claude Code already knows when a session starts); composes on top.

- **Primary-persona test.** The user's natural-language intent is "I want pos v2 to work." The persona should not have to translate that into "install a plist, edit a YAML, `launchctl bootstrap`." This component moves the translation burden entirely into the harness. A feature that lands this reduces translation burden massively — pass.

- **Harness test.** The supervisor, staging, drain, and first-run scaffold are new tools the harness can invoke. The primary persona gains: "the memory system is running and healthy" as a queryable state; "all pos v2 services are up" as a precondition any dispatch can check; "supervisor says degraded" as a signal to adjust its own behaviour. Adds to the persona's toolkit — pass.

- **ODD authoring.** This is a research document; the proposal and brief phases will produce ODD-shaped acceptance criteria. Structural-refusal candidates: the hook refuses to continue on platform-unsupported (structural); the staging store refuses silent-drops (structural); the supervisor refuses silent-stay-degraded (structural). All three of those are structural enforcement rather than advisory.

- **Hands-off lifecycle** (the lens this very component installs). The component satisfies its own lens: every manual step is eliminated or reduced to one confirmation; every ongoing lifecycle concern is owned by the supervisor; loud escalation covers the "cannot self-heal" case. Pass — by construction.

---

## 10. Summary

**Build shape.**

- Session-start Claude Code hook (type `command`, synchronous, FD-safe) invokes `bin/pos-session-start`.
- Helper script probes memory sidecar and orchestrator; if down, asks launchd/systemd-user to bring them up; reports.
- Supervisor module (inside orchestrator process) continuously probes both services, maintains a state machine, coordinates the memory-drain worker on recovery, and opens/closes escalations.
- SQLite-WAL staging store at `~/.pos/memory-staging.sqlite` receives memory writes during degraded mode; drain worker forwards to sidecar in strict FIFO order on recovery, using client-generated UUIDs for idempotence.
- First-run scaffold writes `~/.pos/*.yaml`, installs service-manager files, invokes `launchctl bootstrap`/`systemctl --user start`. Single confirmation sentence reports completion.
- Loud escalation via the primary-persona one-on-one channel uses the sealed notification tier system; escalations are idempotent per class; a durable `~/.pos/attention.md` mirrors current state.
- Fresh root README replaces the prototyping-phase placeholder.

**Four sealed-component amendments surfaced as halt-signals** for owner ruling (memory-system, orchestrator, graceful-degradation, workspace-bootstrap).

**Build cost: 155–250 AI-minutes, calibrated to the upper band.**

**Three halt signals during research:**

1. Claude Code v2.1.87 SessionStart + background-process FD-inheritance bug — mitigated in the recommended design by never launching a background child from the hook; delegating to `launchctl`/`systemctl --user` instead. Not a blocker for this component, but worth surfacing: the naive design (hook launches services directly) does not work on current Claude Code.
2. Each of the four amendments is itself a halt signal — the owner rules per amendment before any unseal cycle begins.
3. The seven open questions in §8 require owner ruling before the proposal can lock.

The component, if it lands, produces the evaluation-ready milestone the research plan names: a user opens a Claude Code session in a fresh pos-v2 workspace, gets a running healthy system on its own, and is not asked to do anything they cannot do.

---

*End of research document. See `research-plan.md` for the authoritative input this was produced against; see the four amendment proposals (to be authored) for the unseal cycles this research has named as load-bearing.*
