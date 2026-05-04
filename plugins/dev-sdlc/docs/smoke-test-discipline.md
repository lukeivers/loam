# Smoke-test discipline — the 6-dimension coverage spec

**Audience:** AI assistants and human builders authoring smoke tests for any
loam component, plugin, or dependency-bearing artefact. Canonical reference
for what "smoke test coverage" means at the methodology level. Normative:
when this document and a builder's instinct disagree, this document wins.

**Companions:** `odd-methodology.md` (the authoring discipline this layers
on top of) and `duration-estimation-rubric.md` (wall-clock cost of running
these dimensions).

**Provenance.** Authored 2026-05-04 after the M-FBM operational-failure
diagnosis (`workspace/.scratch/claude-output/m-fbm-operational-failure-diagnosis-2026-05-04.md`
in pos3) showed the FBE.6/6b/6c/6d smoke pattern — pos-v2's existing
reach-for shape — exercises one of six dimensions. Canonical incident:
M-FBM worker dead ~3 days, queue backlog 174 items, retrieval surfacing
only stale probe markers, every test green throughout.

---

## 1. What a smoke test is supposed to do

A smoke test answers one question: *does this component work right now in
the environment that matters?* Not a unit test (isolated code paths
against synthetic state), not an integration test (wired-up against
fixture state), not a load test (behaviour under stress). It is a
coarse-grained liveness signal — green justifies trusting the component
for the next operating window; red halts that window with a named
failure.

The failure mode this discipline corrects is **structural-AC-only smoke
coverage** — smoke tests verifying the named ACs are implemented but not
verifying the running system is healthy. The M-FBM smoke wrote a turn,
retrieved it, asserted content, returned green daily while the worker
was dead, the queue 174-deep, retrieval surfacing stale probes. Suite
passed. Production broken. The discipline below names the gap.

---

## 2. The six dimensions

Every component's smoke coverage is graded on six dimensions. All six =
operationally trusted. Fewer = ships with a named coverage debt. Only
dimension 1 — the current default across pos-v2 — is structurally
under-tested per ODD §2.5: operational-health behaviours declared by
the component's existence without acceptance criteria backing them.

### 2.1 Dimension 1 — Cold-state functional

**What it tests.** From a clean fixture, a single representative
operation produces the expected output and side-effects.

**Failure mode caught.** Code that does not run at all — import errors,
configuration parse failures, missing dependencies, broken primary
paths.

**Smoke pattern shape.** Run on every commit and release-candidate
build. Fixture freshly initialised (empty database, no prior state, no
warm caches). Single operation executes end-to-end. Assert observable
output; assert side-effect artefacts (files, rows, log lines) exist;
timeout band 5–60 seconds depending on operation cost.

**Anti-pattern.** Asserting only that a function returns the right
shape, not that the side-effect landed. `write_episode()` returning
`{ok: true}` is not the same as the episode existing on disk
afterward. The verdict-shape test passes; the mutation silently
failed. Mirror of `odd-methodology.md` §8.2.14.

This is the dimension every existing pos-v2 smoke covers. Necessary,
not sufficient.

### 2.2 Dimension 2 — Steady-state durability

**What it tests.** Sustained operation over N turns / M minutes leaves
the system in a healthy steady state. Queue depths bounded. Log volumes
bounded. Memory growth bounded. No leaked file handles, no orphan child
processes, no unbounded retry loops.

**Failure mode caught.** Components that work cold but degrade under
load — slow leaks, queue producers without matching consumers, log
volumes that fill the disk, non-terminating retry storms. The M-FBM
queue backlog (174 items over three days) is the canonical example:
dimension 1 was green throughout because cold-fixture writes still
landed; real session activity wasn't draining.

**Smoke pattern shape.** Run on every release-candidate and on a
periodic schedule (daily for live workspaces, hourly for production
plugins). Fixture is the live system or long-lived staging. Drive N
operations over M minutes (band: ≥10 over ≥5 min for cheap components,
≥100 over ≥30 min for queue-bearing). Assert end-state queue depth ≤
threshold; log lines within ±2× cold baseline; RSS growth ≤ threshold;
no orphaned children.

**Anti-pattern.** Running N operations and asserting only the Nth
worked, ignoring queue depth and log volume between them. The system
degrades while operations succeed individually. Dimension-1-with-
extra-iterations, not dimension 2.

### 2.3 Dimension 3 — Restart resilience

**What it tests.** Killing the running process — `SIGTERM`, `SIGKILL`,
unhandled exception, OOM kill — results in the supervisor (`launchd`,
`systemd`, Docker restart policy, Kubernetes liveness) restarting it
within a bounded time window, and the restarted process recovers.

**Failure mode caught.** `KeepAlive` misconfigured. Plist points at a
stale fixture path. Supervisor not loaded at all (plist on disk but
`launchctl bootstrap` never run). Restart succeeds but the process
can't recover prior state because state was in-memory. M-FBM has
elements of this: the worker exited and was never restarted because
the plist was never bootstrapped into the system domain.

**Smoke pattern shape.** Run on every release-candidate touching a
long-running process and on every supervisor-config change. Fixture is
staging with supervisor loaded. `kill -TERM <pid>`; assert supervisor
restarts within Y seconds (band: 1–30 sec); assert new PID differs;
drive a representative operation and assert success.

**Anti-pattern.** Verifying the plist file's contents are correct
(structural check) without verifying `launchctl list` shows it loaded
(operational check). The plist parses; the supervisor doesn't see it.
The M-FBM failure verbatim.

### 2.4 Dimension 4 — Reboot resilience

**What it tests.** A full host reboot (or `launchctl bootout` +
`launchctl bootstrap`) brings the supervisor back, the supervisor
brings the component back, and any state accumulated during downtime
is drained or reconciled.

**Failure mode caught.** Plist not registered for boot-time load
(loaded by hand once, never persisted). Drain pipeline can't recover
from a queue accumulated during downtime. State surviving only in
memory, lost across reboots without graceful-degradation fallback.
State files in volatile temp directories the OS clears on reboot.

**Smoke pattern shape.** Run on every release-candidate touching
boot-time configuration and on a periodic schedule (weekly). Fixture
is a staging host. Trigger reboot or supervisor-bootout cycle. Wait Y
seconds (band: 30 sec to 5 min). Assert process running. Assert
downtime backlog drained within Z seconds (band: 1–60 min). Assert
representative operation succeeds.

**Anti-pattern.** Skipping the reboot and testing "manually restart the
worker, observe it recovers." That is dimension 3. A reboot exercises
boot-time `launchctl` paths — `RunAtLoad`, `KeepAlive`, persistent vs.
session domain — that dimension 3 does not reach. Components passing
dimension 3 can fail dimension 4 silently because the supervisor was
loaded only in the developer's interactive session.

### 2.5 Dimension 5 — Cross-session continuity

**What it tests.** State produced by session A is retrievable and
operationally meaningful in session B — where session B is a fresh
process, a fresh `claude` session, a fresh login shell, or a fresh
container.

**Failure mode caught.** Per-session state silos. In-memory caches that
don't flush. Per-session directories the next session doesn't read.
Async writes (LLM extraction, batched writes, delayed indexing) where
session A ends before the write lands and session B races ahead of it.
The 2026-05-01 owner ruling — "the actual ship-test for memory is
cross-session continuity" — is the operationalisation of this
dimension for M-FBM; the principle generalises.

**Smoke pattern shape.** Run on every release-candidate and on a
periodic schedule. Fixture is two distinct session contexts (two
separate `claude` invocations, two processes, two container runs). In
A: produce a uniquely-tagged piece of state (e.g., marker
`kestrel-9341`) via the production path. End A cleanly. Start B. Drive
a query whose correct answer requires retrieving A's state. Assert the
marker surfaces. Rotate markers per run so a shared-cache leak doesn't
masquerade as success.

**Anti-pattern.** Running both halves in the same process and asserting
the second sees the first. That is dimension 1. Async writes are the
trap — within-session retrieval often races the writer and the test
passes through a code path production doesn't take.

### 2.6 Dimension 6 — Operational telemetry floor

**What it tests.** The component emits a heartbeat, drain-event, or
health signal at a known cadence — such that the *absence* of the
signal for longer than a threshold is itself a smoke FAIL, without
any positive failure indicator.

**Failure mode caught.** Silent worker death. Silent queue stall.
Silent supervisor unload. Failures where a component goes quiet
rather than red. Without a floor, every other dimension catches a
failure only when its scheduled run fires; with a floor, an absent
heartbeat is detectable in seconds-to-minutes. The M-FBM worker logged
5 lines in 3 days; a 30-second heartbeat would have produced ~8,640
lines and >2 min of silence would have been the failure.

**Smoke pattern shape.** Run as a continuous monitor, not a
point-in-time test. Component emits a heartbeat at cadence C (band:
10 sec for hot paths, 60 sec for queue workers, 5 min for low-activity
supervisors). Monitor reads the stream (log tail, metrics endpoint,
observability surface) and FAILs if no heartbeat in N×C seconds (band:
3×C to 5×C). Heartbeat content carries PID, queue depth, last-drain
timestamp, build SHA — so a present-but-stuck heartbeat still surfaces
as anomaly via timestamp drift.

**Anti-pattern.** Treating heartbeats as logging-for-debugging and
turning them off in production to reduce volume. The heartbeat IS the
smoke test; suppressing it suppresses the test. Sample structured
fields if volume is the concern. Second anti-pattern: emitting from a
watchdog thread separate from the work thread — the worker can
deadlock without the heartbeat noticing. Instrument from the work
loop itself.

---

## 3. Existing-component coverage map

pos-v2 framework components graded on the six dimensions. Almost every
component is at 1/6 today; the table is the inventory the next amendment
cycle works against. Source of truth: `docs/rebuild/STATE.md`.

| Component | D1 cold | D2 steady | D3 restart | D4 reboot | D5 cross-session | D6 telemetry |
|---|---|---|---|---|---|---|
| memory-system | yes | partial | gap | gap | partial | gap |
| scope-of-work | yes | gap | n/a | n/a | gap | gap |
| primary-persona | yes | gap | n/a | n/a | gap | gap |
| objective-tracker | yes | gap | n/a | n/a | gap | gap |
| orchestrator | yes | gap | gap | gap | gap | gap |
| safety-layer | yes | gap | n/a | n/a | gap | gap |
| reversibility-primitive | yes | gap | n/a | n/a | gap | gap |
| cost-governance | yes | gap | n/a | n/a | gap | gap |
| self-correction | yes | gap | n/a | n/a | gap | gap |
| observability-aggregator | yes | partial | gap | gap | gap | partial |
| self-upgrade | yes | gap | n/a | n/a | gap | gap |
| dormancy | yes | gap | gap | gap | gap | gap |
| workspace-bootstrap | yes | n/a | n/a | n/a | n/a | n/a |
| workspace-sync | yes | gap | n/a | n/a | gap | gap |
| telegram-interface | yes | gap | gap | gap | partial | gap |
| hands-off-lifecycle | yes | gap | gap | gap | gap | gap |
| loam-init | yes | n/a | n/a | n/a | n/a | n/a |

`yes` = covered. `partial` = some coverage, gap named in BACKLOG.
`gap` = no coverage; coverage debt. `n/a` = dimension does not apply
(a one-shot bootstrap script has no steady-state). Long-lived processes
(memory-system worker, orchestrator daemon, telegram-interface bot) need
all six; one-shot CLIs (workspace-bootstrap, loam-init) need 1, 5, and
arguably 6 only.

The gradings above are best-effort initial, not audit-grade. Each
component owner re-grades against its own test inventory as the
discipline lands; the table is corrected by amendment.

---

## 4. Connection to ODD §2.5

ODD §2.5 — "every line of code, every branch, every test, every
dependency must map to a named acceptance criterion backing a named
objective" — is the rule this discipline extends. The connection runs
both directions.

**Forward.** A long-lived process *declares* a steady-state behaviour
by existing. A queue worker declares "queue depth stays bounded under
sustained load" the moment it ships. A supervised daemon declares
"I survive my own death" by being supervised. A cross-session
retriever declares "state survives the process boundary" by being a
retriever. These declarations are objective-shaped, but historically
have not been backed by named ACs. The pos-v2 cold-state-only smoke
pattern is the consequence: structural ACs (`AC.<COMP>.*`) present;
operational-health ACs (`AC.<COMP>-OPS.*`) absent.

**Reverse.** A suite running only dimension 1 covers only the
structural family. The operational-health behaviours the component
declares by existing are uncovered — the diff contains code (the
worker loop, the supervisor plist, the cross-session write path)
operating without any AC verifying it works. By §2.5 the
reverse-direction check fails. The methodology answer is re-extension
(per `odd-methodology.md` §4): add the operational-health AC family.

The structural mechanism is **per-component AC families**:

- `AC.<COMP>.*` — structural ACs (API, schema, behaviour contract).
  Smoke covered by dimension 1.
- `AC.<COMP>-OPS.*` — operational-health ACs (steady state, restart,
  reboot, cross-session, telemetry floor). Smoke covered by dimensions
  2–6.

A component is ODD-§2.5-clean when both families exist *and* are
covered. An empty `-OPS.*` family means operational claims made by
existence without criteria backing them — the structural symptom of
the gap this document closes.

The fix is not retroactive across all pos-v2 components in a single
amendment. It is the next-amendment posture for every long-running
component as it comes up for revision, with an explicit BACKLOG entry
in `component.md` naming the operational-AC family it needs.

---

## 5. Where this fits

The smoke-test methodology layer in dev-sdlc's docs corpus.
Companions:

- `odd-methodology.md` — the ODD authoring discipline this layers on;
  the reverse-direction check is the structural rule that surfaces
  the smoke-coverage gap.
- `duration-estimation-rubric.md` — wall-clock for smoke runs.
  Dimensions 2 and 4 are expensive (sustained-load runs, full reboot
  cycles); the rubric's category table is where their cost lives.
- `cdcs/` — the dev-mode CDC catalogue. A future CDC may codify this
  as a structural check on amendment briefs (every brief for a
  long-running component names which dimensions it covers).

The smoke-test contract: every long-running component graded on six
dimensions; coverage debts named; an absent operational-AC family is
itself an ODD §2.5 defect.

---

## 6. Quick reference card

**Authoring:**

1. Long-running process? All six dimensions. One-shot CLI / library?
   Dimensions 1, 5 (state crosses runs), 6 (output consumed
   asynchronously).
2. Each applicable dimension gets an AC in `AC.<COMP>-OPS.*` with a
   deterministic check.
3. Author the smoke per §2's shape; cross-check the anti-pattern.
4. Dimensions that don't apply: mark `n/a` with one-sentence
   rationale in `component.md`.

**Reviewing:**

1. Both `AC.<COMP>.*` and `AC.<COMP>-OPS.*` families exist.
2. Each operational-AC has a smoke test.
3. Long-running components: dimensions 2–6 each have an AC, or a
   named BACKLOG debt.
4. Every smoke test points at a dimension + AC. No backing = no test.

**Recognising the M-FBM failure pattern:**

1. Tests pass; production wrong → structural-AC-only coverage.
2. Long-running component, no telemetry floor → dimension 6 gap.
3. Plist on disk no one verifies is loaded → dimension 3 or 4 gap.
   `launchctl list` is the operational fact.
4. Cross-session feature tested within a single session → dimension 5
   gap. Async writes hide silently.
