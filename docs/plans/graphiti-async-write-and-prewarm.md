# graphiti async-by-default write + Ollama pre-warm — Stop-hook returns immediately, embedding model stays resident between turns — plan

Dev-discipline work. **NOT** a sealed-component amendment. No `pos-amend` manifest, no `SEAL_COMMIT` bump, no seal commit. Plan-before-code per the dev CDC; corrective new commits land the change.

**Status:** plan (pre-dispatch). 2026-04-27.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Companions:** - **Amendment #48 plan-doc:**
  `docs/plans/memory-system-live-client-and-stop-hook-write.md`
  (the synchronous Stop-hook turn-close write that this
  amendment makes async). Read this first — J composes
  directly on #48's surface.
- **Spec anchors:** `docs/VALUE_PROPOSITION.md`
  (AC.PO.1 / AC.PO.2 — the prime objective ACs; J ladders
  here).
- **Existing primary-persona artefacts:**
  `primary-persona/src/stop_emitter.py` (the #48 Stop-hook
  handler whose `_spawn_memory_write` switches to enqueue),
  `primary-persona/src/mcp_memory_client.py` (the live MCP
  adapter the worker drives), `primary-persona/src/memory_consumer.py`
  (the `MemoryClient` Protocol + `TurnAggregator` —
  sealed-since-#33; J does not touch it).
- **Existing workspace-bootstrap artefacts:**
  `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
  (`_LAUNCHD_TEMPLATES` is the seam for the worker plist;
  `_install_service_manager_files` is the call site;
  `_resolve_memory_host_port` is the precedent for env
  propagation),
  `workspace-bootstrap/src/workspace_bootstrap/adapters/mcp_json_writer.py`
  (amendment #47's writer pattern — precedent for
  workspace-local config writes).
- **ODD references:** `docs/odd-methodology.md` §2.5 (no
  non-objective code), §10 (per-invariant BASELINE
  convention).
- **Amendment precedents:** amendment #29 (per-workspace
  memory-sidecar port — pattern for env propagation into
  plist), amendment #46 (multi-component plan-shape with
  §14 method-decision register), amendment #47
  (single-sealed-component manifest + plan-doc shape +
  workspace-local config writer), amendment #48 (the
  Stop-hook synchronous write surface this amendment
  makes async).
- **FUTURE_IDEAS surface:**
  `docs/FUTURE_IDEAS_DRAFT.md` — Bash-tool
  eval-wrapper anomalies entry (env-var quirks worth
  knowing about during plist verification).
- **Brief-context dossier (pos3-local):**
  `/Users/lukeivers/pos3/.scratch/claude-output/dialog-context-dossier.md`
  Section "Pending-work catalog" → "Small queued tasks" →
  J entry (Luke priority-elevated 2026-04-27).

**Ancestor record:** - **Luke priority-elevation 2026-04-27:** "slowing things
  down considerably in the session" — promoted J from
  Small queued tasks to immediate plan-author dispatch.
- **Brief-level option lock 2026-04-26 (carried forward):**
  option (c) BOTH — pre-warm AND async queue/worker.
- **Plan-author empirical finding 2026-04-27:**
  `OLLAMA_KEEP_ALIVE` is server-side; memory-system's
  launchd plist is the wrong surface; workspace-bootstrap-
  side propagation is the correct surface. Hard Constraint
  12 + Halt Finding 1 + D-1 surface-ruling capture this.
- **Amendment #48 (sealed):** introduced the Stop-hook
  synchronous-from-detached-child write path; J replaces
  the per-turn detached-child with a queue + long-running
  worker.
- **Recent precedent for queue-shape primitives in pos-v2:**
  none — this is the first persistent-queue + supervised-
  worker primitive. The worker pattern composes on the
  existing per-workspace launchd-service shape (memory-
  graphiti + orchestrator) per amendment #29.

**Research:** (no separate research doc — finding-set captured inline in
§13; canonical sources named in §15)


---

## 1. Summary / TLDR

Closes the two largest single contributors to per-turn user-perceived
latency on the memory-write path:

1. **Pre-warm** (J.1). Ollama's default `OLLAMA_KEEP_ALIVE=5m` lets
   the embedding model unload between turns when the user pauses;
   the next turn pays a cold-load tax. Extending `OLLAMA_KEEP_ALIVE`
   to a long-lived value (24h recommended) keeps the model resident
   across the typical session-cadence pause envelope. **Critical
   fence-impact:** `OLLAMA_KEEP_ALIVE` is read by the Ollama SERVER,
   not by memory-system. The brief assumed memory-system service env
   would carry it; verification (this plan §13) shows that's wrong.
   The effective surface is the Ollama daemon's launchd plist (or an
   equivalent operator-level shell env), which lives outside pos-v2's
   fence. Plan ships J.1 as a workspace-bootstrap-side environment
   **propagation** mechanism (write a user-facing diagnostic + a
   `pos-doctor`-equivalent surface that reports the observed value)
   plus a documentation surface that names the Ollama-side
   configuration step. Decision D-1 surfaces the surface choice for
   ruling.

2. **Async-by-default queue + worker** (J.2). Today the Stop-hook's
   detached child (amendment #48 D3) drives `add_episode`
   synchronously on its own process; that child's wall-time is
   ~113s (amendment #33 measurement) and it holds an open MCP
   transport for the duration. Spawning a fresh detached process per
   turn is fine for fan-out but loses the chance to (a) absorb
   bursts (rapid back-to-back turns: `/compact` resume, ESC + retry,
   fast Q&A), (b) survive a session-end crash before the write
   completes, and (c) bound concurrent Ollama load. This amendment
   adds a fire-and-forget queue + worker primitive on the
   primary-persona consumer side: Stop-hook enqueues a turn record
   and returns; a worker drains the queue and drives `add_episode`
   to completion with bounded retries + dead-letter on terminal
   failure. Persistence is disk-backed by default (durable across
   session-end and machine-reboot). The locked option is (c) BOTH —
   pre-warm AND async queue.

Fence: workspace-bootstrap (J.1 propagation surface only) +
primary-persona (J.2 queue + worker primitive). **Memory-system is
NOT touched** — this is consumer-side, not service-side. Method
surface is the builder's call inside the locked outcomes.

After this amendment lands, the Stop-hook returns in milliseconds
(already true post-#48), the persona's translation work continues
at perceived-instant, and the embedding model does not unload
during a typical session window. If the embedding-model unload IS
observed during a session window, the bottleneck is Ollama-side
configuration and the user-facing diagnostic surfaces it.


---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

This amendment binds to **VALUE_PROPOSITION's Lens 2 / AC.PO.1
(translation-burden reduction)** as the primary spec hook: when
a session-quality interaction step is non-blocking, the persona's
translation work happens at perceived-instant. No new top-level
objective required; composition under existing AC.PO.1 / AC.PO.2.

**Reverse trace per CLAUDE.md §2.5.** Every AC below traces
back to the spec line above + maps forward to AC.PO.1
(translation-burden reduction) and/or AC.PO.2 (toolkit-primitive
growth):

- **AC.PO.1 (translation-burden):** Today, the user empirically
  notices session interactivity slowing "considerably" (Luke
  2026-04-27). The two contributors are (a) Ollama cold-load on
  each turn when the model has unloaded between turns, and (b)
  the once-per-turn detached subprocess fan-out cost. Both are
  invisible-to-the-user mechanisms whose latency leaks into
  user-perceived turn time. Pre-warm + async queue absorb both
  chores at the framework layer; the persona's translation work
  proceeds at perceived-instant.
- **AC.PO.2 (toolkit-primitive):** The async-write queue + worker
  is a reusable primitive every future Stop-hook-class write
  composes against (workflow-end logger, scope-close
  artefact-emitter, end-of-session compactor primer). The
  pre-warm-status surface is a primitive every future
  Ollama-backed consumer composes against (currency mechanism,
  health-probe extension).

**No new top-level objective needed.** Per
`feedback_value_proposition_as_prime_objective`, AC.PO.1 / AC.PO.2
are the prime objective's ACs and every component/feature/amendment
ladders up. This amendment ladders directly without inventing a
new spec line.

**Composes onto amendment #48** (live MCP memory client +
Stop-hook turn-close write). #48 added the synchronous-from-the-
detached-child write path + the diagnostic log + the dedupe marker;
J.2 replaces the detached-child-per-turn pattern with a queue +
long-running worker pattern. #48's ACs (M.1 - M.S) are preserved
byte-identically in observable behaviour from the user's
perspective; the implementation surface changes only inside the
primary-persona consumer.


---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

Composes on Claude-native primitives without inventing new ones:

1. **Claude Code's Stop hook** (already wired by amendment #48).
   This amendment doesn't change the Stop-hook contract; it
   changes what the hook's handler does between "received" and
   "returned." Stop continues to be the single trigger surface;
   no new hook event introduced.
2. **launchd as the worker supervisor.** The async worker runs
   as a workspace-local launchd service (sibling of the
   memory-graphiti and orchestrator launchd services already
   provisioned by workspace-bootstrap per amendment #29). KeepAlive
   + RunAtLoad + ThrottleInterval semantics absorb crash-recovery
   for free. No custom supervisor; no recurring-cron primitive
   needed.
3. **Ollama's HTTP envelope.** Pre-warm verification uses Ollama's
   `/api/ps` endpoint (returns currently-loaded models + their
   keep-alive expiry). The diagnostic surface composes onto an
   existing API; no new probe primitive needed.
4. **The MemoryClient Protocol** (sealed since amendment #33;
   consumed by amendment #48's LiveMCPMemoryClient). The worker
   drives `add_episode` against the existing Protocol surface;
   no service-side change required.

No new top-level Claude SDK surface. No new MCP server. No new
hook event.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** Reduces translation burden:

- Before this amendment, when the user notices "session is slow,"
  the translation chore is "is it Ollama? memory-write? something
  else?" The user has no introspection surface. The diagnostic
  + observability surface added by this amendment lets the
  persona answer "embedding model is resident, queue depth is N,
  last write completed at T" without the user investigating.
- Before this amendment, a session-end mid-write loses the
  pending episode (the detached child is killed when the
  terminal exits, depending on detach semantics). Disk-backed
  queue persistence absorbs this — the worker resumes after
  session-end and drains the queue. The persona's "today's
  response is informed by yesterday's decisions" promise survives
  session-boundary crashes. **Pass.**

**Harness test.** Adds three primitives to the toolkit the
persona composes against:

1. **Disk-backed write queue** at `<workspace>/.pos/memory-write-queue/`
   (one NDJSON file per turn record). Future Stop-class writes
   (workflow-end emitter, scope-close artefact, end-of-session
   compactor primer) compose against the same queue or extend
   the directory with a typed sub-queue.
2. **Long-running async worker** as a workspace-local launchd
   service. Future workspace-local async work (background
   summarisation, deferred extraction passes) composes against
   the same worker shape.
3. **Pre-warm verification surface** at
   `<workspace>/.pos/memory-prewarm.log` (or
   `pos-doctor`-equivalent CLI subcommand). Future Ollama-backed
   consumers (currency mechanism, knowledge-server) compose
   against the same status read.

**Pass.**

Per AC trace:

- **AC.J.1 → AC.PO.1.** Pre-warm absorbs the cold-load
  translation chore. User never notices first-turn-after-pause
  latency.
- **AC.J.2 → AC.PO.1 + AC.PO.2.** Stop-hook enqueue returns
  in milliseconds (preserves #48 AC.M.7); user never blocks on
  write. Queue + worker = toolkit primitive.
- **AC.J.3 → AC.PO.2.** Disk-backed persistence = the queue is a
  durable artefact future tooling reads (e.g., a future "what
  memory writes are pending?" awareness-block contributor).
- **AC.J.4 → AC.PO.1.** Bounded retries + dead-letter absorbs
  the translation chore "memory-graphiti was unreachable, did my
  write get lost?" — no, it's in the dead-letter file the
  persona surfaces on demand.
- **AC.J.5 → AC.PO.2.** Worker supervised by launchd = harness
  primitive future async-work consumers compose against.
- **AC.J.6 → AC.PO.1.** Pre-warm-status diagnostic surface lets
  the persona answer "is memory live?" without the user
  investigating.
- **AC.J.7 → AC.PO.1.** Idempotency/dedupe across queue +
  worker = duplicate writes structurally impossible even when
  Stop-hook re-fires on `/compact`.
- **AC.J.8 → AC.PO.1.** Backwards-compat with #48 AC.M.1-S
  means the user's existing memory writes continue working
  byte-identically from their perspective.

### Lens 3 — ODD authoring

ACs in §4 are outcome-shaped: each names a state of the world the
amendment must make true, with deterministic test shape. No
method-in-AC (no "uses Python `multiprocessing.Queue`", no
"implements `WorkerSupervisor` class", no "calls
`subprocess.Popen` with `start_new_session=True`"). Method
choices (queue file format, worker concurrency model, retry
backoff curve, launchd plist contents, dead-letter file shape)
are the builder's call inside the §9 manifest sketch and the
§14 method-decision register; the AC tests outcome only.

Behaviour-count check applied in §5. ODD §2.5 reverse trace
is the builder's pre-seal check captured in the builder-plan
(one row per code path → AC).

Halt-and-surface triggers per §10; explicit per
`feedback_subagent_odd_violation_halt`.


---

## 4. Acceptance criteria (AC.J — dev-discipline plan)

Eight outcome-shaped acceptance criteria, plus the seal-diff
invariant. Each carries the deterministic test shape; method is
the builder's call.

**AC.J.1 — Embedding model stays resident across the session-
cadence pause envelope.** Given a workspace running with
workspace-bootstrap's first-run scaffold complete and the
memory-graphiti service reachable, AND the Ollama daemon's
configuration surface advertises a long-lived keep-alive (24h
recommended; tunable via the surface chosen in D-1), a turn-
close write at time T followed by a quiescent pause of duration
P (P ≤ keep_alive value) followed by a second turn-close write
at time T+P does NOT trigger an Ollama model-load operation
for the second write (verified by querying Ollama's `/api/ps`
before and after, or reading Ollama's stdout log for "loading
model"). Outcome: second-write embedding latency ≤ first-write
latency × 1.1 (no cold-load tax).

**AC.J.2 — Stop-hook enqueue path returns in milliseconds.**
Given a Stop envelope with recoverable user-message + assistant-
reply, the Stop-hook's `cli_stop` subprocess returns (exit 0)
within 200ms p95, AND the actual `add_episode` write does NOT
run in the Stop subprocess's process tree — it runs in the
long-running worker process whose PID is independent of the
Stop subprocess. Preserves #48 AC.M.7 byte-identically from
the user's perspective; replaces #48's per-turn detached-child
pattern with a queue-enqueue pattern that is even cheaper.

**AC.J.3 — Disk-backed queue persistence survives session-end
+ machine-reboot.** Given a Stop event whose enqueue completes
but whose worker has not yet drained the queue entry, killing
the worker process AND the parent session AND restarting the
machine produces a state in which the workspace's queue
directory still contains the turn record. The next worker
start (auto-launched by launchd at boot) drains the queued
record to completion. No turn record is silently dropped.
Verified by a fixture that creates a queue record, kills the
worker, simulates restart (or restarts launchd-loaded worker),
asserts the record drains.

**AC.J.4 — Bounded retry + dead-letter on terminal write failure.**
Given a queue record whose `add_episode` call fails repeatedly
(memory-graphiti unreachable, MCP transport error, Ollama
unresponsive), the worker retries with exponential backoff up
to a bounded retry count (D-3 surfaces the bound for ruling),
then writes the record to a dead-letter file at
`<workspace>/.pos/memory-write-deadletter.log` (NDJSON; one
entry per failed turn record carrying turn_id, payload,
retry-history, last-error). The worker continues processing
subsequent queue entries — one record's failure does not block
the queue. The dead-letter file is human-readable and the
operator can re-queue an entry by moving it back to the queue
directory.

**AC.J.5 — Worker is a supervised long-running process.**
Given workspace-bootstrap's first-run scaffold complete, a
workspace-local launchd service (label
`com.pos-v2.<slug>.memory-write-worker`) is registered and
running. The service's plist carries `KeepAlive=true`,
`RunAtLoad=true`, `ThrottleInterval=10` (matching
memory-graphiti's plist shape per amendment #29). Killing the
worker process produces a launchd-mediated restart within the
throttle window; the worker resumes draining the queue from
wherever it left off (queue is the source of truth, worker is
stateless).

**AC.J.6 — Pre-warm verification surface.** A read-only
diagnostic surface exposes the current Ollama keep-alive state
(or NDJSON-line entries appended on each enqueue carrying the
pre-write `/api/ps` snapshot). The surface is workspace-local
(under `<workspace>/.pos/`); the persona reads it without
user effort to answer "is the embedding model resident?"
When the embedding model is observed to have been unloaded
between two consecutive Stop-events (cold-load tax measured),
the diagnostic carries a structured entry the persona surfaces
on the next user-prompt-submit's awareness block (or on demand
via persona introspection).

**AC.J.7 — Idempotency: queue + worker do not double-write.**
Given two identical turn records enqueued back-to-back (turn-id
collision; `/compact` re-fire scenario; bug-induced double-
enqueue), the worker writes exactly one `add_episode` call to
the memory service. Method is dedupe-by-turn-id; the AC measures
observable count. Composes onto #48 AC.M.8's existing dedupe
surface (`<workspace>/.pos/last-turn-id` marker); the queue
layer adds a second-line dedupe at drain time so a marker-
miss (e.g. workspace-bootstrap's marker file racing with a
concurrent enqueue) does not produce a duplicate write.

**AC.J.8 — Backwards-compatibility: amendment #48 ACs preserved
byte-identically from the user's perspective.** Existing #48
tests in `primary-persona/tests/` for AC.M.1 - AC.M.S stay green.
The Stop-hook contract is unchanged from Claude Code's
perspective (exit 0; reads stdin envelope; reads transcript_path;
derives turn id; respects dedupe marker). The diagnostic log at
`<workspace>/.pos/memory-writes.log` continues to land entries
for write-ok / write-error / write-skip — the writer is now the
worker rather than the detached child, but the schema is
unchanged. #48 AC.M.7's "returns in milliseconds" tightens
(the enqueue is even cheaper than the detached-child spawn).

**AC.J.S — Seal-diff invariant.** Diff between BASELINE and
SEAL_COMMIT is confined to:

- `primary-persona/src/` (new queue + worker modules; minor
  edits to `stop_emitter.py` to switch from
  `_spawn_memory_write` to enqueue),
- `primary-persona/tests/`,
- `primary-persona/pyproject.toml` (if a runtime dep is added —
  builder verifies stdlib is sufficient before adding),
- `workspace-bootstrap/src/` (new launchd plist template for
  the worker service; surface for the pre-warm propagation per
  D-1),
- `workspace-bootstrap/tests/`,
- amendment-universal admissions (`docs/plans/`,
  `CLAUDE.md` if needed, `docs/FUTURE_IDEAS.md` if
  needed, `docs/odd-*.md` if needed).

**Memory-system is NOT in the seal-diff window.** The fence
spec is locked: J is consumer-side. Any source-edit under
`memory-system/` triggers halt-and-surface (§10 trigger 4).
Verified by the `test_no_sealed_amendments.py` checks for
primary-persona + workspace-bootstrap and the cross-component
sweep at seal-time.


---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

Eight declared behaviours; eight outcome-shaped ACs; one
seal-invariant. Match.

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Embedding model stays resident across pause envelope | AC.J.1 |
| 2 | Stop-hook enqueue returns in milliseconds; write happens off-process | AC.J.2 |
| 3 | Disk-backed queue persistence survives session-end + reboot | AC.J.3 |
| 4 | Bounded retry + dead-letter on terminal write failure | AC.J.4 |
| 5 | Worker is a supervised long-running process (launchd) | AC.J.5 |
| 6 | Pre-warm verification surface (read-only diagnostic) | AC.J.6 |
| 7 | Idempotency: queue + worker do not double-write | AC.J.7 |
| 8 | Backwards-compat: #48 AC.M.1 - AC.M.S preserved | AC.J.8 |
| S | Seal-diff invariant: only `primary-persona/` + `workspace-bootstrap/` + universal paths | AC.J.S |

Forward direction (every behaviour → AC) verified above.
Reverse direction (every code path / branch / dependency →
AC) is the builder's pre-seal check captured in the
builder-plan's §5 (per amendment #46/#47 precedent).


---

## 6. Hard constraints

1. **Sealed-component fence: `primary-persona/` +
   `workspace-bootstrap/` only** (plus universal-paths
   admissions). Any source-edit under `memory-system/` triggers
   halt-and-surface (§10 trigger 4). The brief's locked fence
   is consumer-side; service-side change is X-build's
   retire-and-reimplement path.
2. **No `--amend`.** Corrective new commits only per
   `feedback_no_amend_in_agent_dispatches`.
3. **Plan-before-code.** This plan exists; the builder
   authors a builder-plan at
   `docs/plans/graphiti-async-write-and-prewarm.builder-plan.md`
   before editing any source.
4. **Backward-compat preserved unconditionally.** Existing #48
   ACs (M.1 - M.S) stay green; the Stop-hook contract is
   unchanged from Claude Code's perspective. The diagnostic
   log schema continues to accept the existing `kind` values
   (write-ok / write-error / write-skip / stop-skip /
   stop-error). New `kind` values may be added; existing ones
   may not change semantics.
5. **No synchronous user-facing wait on memory writes.** The
   Stop-hook subprocess returns in milliseconds via the
   enqueue path; the worker carries the long-running write.
   Any code path that drives `add_episode` synchronously
   inside `cli_stop` is a halt trigger.
6. **Stop-hook subprocess exits 0 unconditionally.** Preserved
   from #48 hard constraint 5. A non-zero exit blocks Claude
   Code's normal stop behaviour.
7. **Disk-backed queue durability is structurally enforced.**
   The enqueue operation MUST atomic-rename a tmp-file into the
   queue directory before returning success to the Stop-hook;
   fsync + atomic-rename is the durability boundary. No queue
   entry may be lost across an enqueue-then-immediate-crash
   sequence.
8. **No new third-party runtime dependency unless verified
   necessary.** stdlib + the `mcp` package (already a #48
   dependency) should be sufficient. If the builder verifies
   a queue / worker library is structurally needed (e.g. a
   proven-reliable persistent queue), the dep addition lands
   under the same #48 pattern with an exact-version pin.
   Halt-and-surface (§10 trigger 5) if any new dep is
   proposed; the builder authors the rationale and Luke rules.
9. **Worker concurrency: the QUEUE is the source of truth,
   the worker is stateless.** The worker MUST NOT cache queue
   state in memory across drain cycles; killing and restarting
   the worker MUST NOT lose or duplicate any queue entry.
   This is the structural property AC.J.3 + AC.J.5 + AC.J.7
   measure together.
10. **CDC adherence.** scope-only-dispatch CDC (the dispatch
    carries objective + scope + halt + ODD-check; the builder
    authors method in the builder-plan). Standard pos-amend
    manifest discipline. `pos-amend seal --plan-doc <abs-path>`
    backfills §14.
11. **No top-level objective added.** Composition under
    VALUE_PROPOSITION's AC.PO.1 + AC.PO.2. If the build
    surfaces a hard need for a new top-level objective,
    halt-and-surface (§10 trigger 1) — do NOT silently
    promote.
12. **AC.J.1's surface is operator-level, not service-level.**
    The Ollama daemon's `OLLAMA_KEEP_ALIVE` is read by the
    Ollama process, NOT by memory-system. The plan's J.1
    surface (per D-1) is workspace-bootstrap-side
    *propagation* + diagnostic — NOT a memory-system service
    env edit. A plan-author finding (§13) verified this
    empirically; the builder MUST NOT regress to "set
    OLLAMA_KEEP_ALIVE in memory-system's launchd plist" as
    that has no effect.


---

## 7. Out of scope (explicit)

Per ODD §2.5 and the locked brief 2026-04-26:

- **Memory-system source edits.** Service-side change is
  X-build's path; J is strictly consumer-side. Out of scope
  here.
- **Multi-worker concurrency / horizontal scaling.** Single
  worker per workspace is the recommended D-2 default.
  Multi-worker is a future amendment if queue depth grows
  persistently (e.g., automation-driven turn rates exceed
  single-worker drain rate).
- **In-memory queue alternative.** D-3 surfaces persistence
  choice for ruling; recommendation is disk-backed.
  In-memory-only is locked-against by the brief's "session
  crashes mid-flight" durability requirement.
- **OLLAMA_FLASH_ATTENTION / OLLAMA_KV_CACHE_TYPE tuning.**
  The Ollama daemon's existing homebrew plist already sets
  flash-attention + KV-cache type; J does not retune these.
- **Switching to a non-Ollama embedding backend.** Out of
  scope. Memory-system's embedder choice is the service's
  surface.
- **Compaction-time queue drain trigger.** Drain is
  continuous via the long-running worker. Compaction does
  not need a special trigger.
- **Pre-warm via "send a no-op embedding request on
  workspace-bootstrap completion."** Tempting low-cost
  primitive; surfaced for D-5 ruling. Recommendation: defer
  — the keep-alive setting is the structural fix.
- **Cross-workspace shared worker.** Each workspace has its
  own worker (per amendment #29 per-workspace-sidecar
  pattern). Cross-workspace shared is a future amendment.
- **Telegram-channel surfacing of queue depth / dead-letter
  state.** The persona's call (composes onto the diagnostic
  surface this amendment lands).


---

## 8. Implementation order (suggested — builder's call to refine)

Suggested order — builder's call to refine in the builder-plan:

1. **Read session-start corpus + this plan + amendment #48's
   plan-doc + #48's `stop_emitter.py` + `mcp_memory_client.py`
   + `memory_consumer.py`.** Note exactly where #48's
   `_spawn_memory_write` is called and where the new enqueue
   replaces it.
2. **Verify D-1 surface choice empirically.** Read the user's
   existing Ollama plist
   (`/opt/homebrew/Cellar/ollama/*/homebrew.mxcl.ollama.plist`
   or equivalent); confirm it lacks `OLLAMA_KEEP_ALIVE`
   today; confirm `/api/ps` returns the resident-models list
   when queried; document the observed cold-load latency
   baseline.
3. **Author builder-plan** at
   `docs/plans/graphiti-async-write-and-prewarm.builder-plan.md`
   before any source edit. Builder-plan captures D-build.x
   method choices and the §2.5 reverse-direction trace.
4. **Land the queue primitive first** — directory layout,
   atomic-rename enqueue, queue-walk read, NDJSON entry
   schema. Tests: enqueue-then-read round-trip; atomic-rename
   resists kill-mid-write; ordering preserved (FIFO by
   mtime).
5. **Land the worker module + supervised launchd service.**
   Worker module: queue-walk → drain → retry-policy →
   dead-letter. Tests with a stub MCP client for deterministic
   verdicts; one integration test against a fake live client.
   Workspace-bootstrap-side: extend `_LAUNCHD_TEMPLATES` with
   a `memory-write-worker` template; provision in
   `_install_service_manager_files` alongside `memory-graphiti`
   + `orchestrator`. Tests: plist contents; idempotent
   re-install; worker starts on first-run scaffold completion.
6. **Switch Stop-hook to enqueue.** Change `_spawn_memory_write`
   in `stop_emitter.py` to `_enqueue_memory_write`. The
   existing `cli_memory_write` entry point becomes the
   worker's drain function (renamed; called by the worker not
   by a per-turn subprocess). Preserve the Popen surface as a
   deprecation-fence shim if needed for #48 backward-compat
   tests; the deprecation lands in the same amendment if the
   test surface allows.
7. **Land the pre-warm propagation surface (D-1).** Per
   ruling: either (a) workspace-bootstrap writes
   `<workspace>/.pos/ollama-prewarm-recommended.txt` carrying
   the recommended `OLLAMA_KEEP_ALIVE` value + the operator
   instructions to set it on the Ollama plist (advisory
   surface only — pos-v2 does NOT touch homebrew-installed
   files), or (b) a `pos-doctor`-equivalent CLI subcommand
   reads the live Ollama state and surfaces a structured
   diagnostic. Default recommendation surfaces in §11 D-1.
8. **Land the diagnostic + verification surface (AC.J.6).**
   `<workspace>/.pos/memory-prewarm.log` (NDJSON; one entry
   per Stop-hook firing carrying the pre-write `/api/ps`
   snapshot). The persona reads this on user-prompt-submit
   when the user asks about memory state.
9. **Run touched-component suite** then `pos-amend apply
   --dry-run`; if clean, run amendment commit; then
   `pos-amend seal --plan-doc <abs-path>`. Test scope per
   `feedback_amendment_dispatch_speedups`: narrow to
   `primary-persona/tests/` + `workspace-bootstrap/tests/`.
10. **Verify backward-compat** with the pre-amendment Stop-hook
    flow on a fixture; assert AC.M.1 - AC.M.S of #48 stay
    green and a real turn-close write produces exactly one
    `add_episode` call as observed at the live service.


---

## 9. Bookkeeping surface

Sealed-component amendment. `pos-amend` manifest sketch
(builder finalises in `<slug>.manifest.yaml`):

```yaml
schema_version: 1
amendment:
  number: <N>  # next free amendment number at dispatch time
  slug: graphiti-async-write-and-prewarm
  title: "graphiti async-by-default write + Ollama pre-warm"

# BASELINE pinned to HEAD~1 of the amendment commit (per
# amendment #29 / #34 / #35 / #36 / #37 / #38 / #39 / #42 /
# #46 / #47 / #48 BASELINE-as-HEAD~1 pattern). Builder fills
# SHA at apply time.
baseline: <HEAD~1 SHA>

plan: docs/plans/graphiti-async-write-and-prewarm.md

components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []
  - name: workspace-bootstrap
    seal_test: workspace-bootstrap/tests/test_no_sealed_amendments.py
    sidecar: workspace-bootstrap/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []

universal_paths:
  prefixes:
    - docs/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/FUTURE_IDEAS.md

narrative:
  target: primary-persona/seals/SEAL_COMMIT.graphiti-async-write-and-prewarm
  body: |
    # Amendment #<N> — graphiti async-by-default write +
    #                  Ollama pre-warm

    <builder finalises body — see narrative shape in
    amendment-46 + amendment-47 + amendment-48 manifests
    for precedent>
```

**Dependents cleared at seal:** none in-flight at this
authoring time. Future amendments composing on the queue +
worker primitive (workflow-end emitter, scope-close
artefact-emitter) become unlocked once this seals.

**Universal admissions** match amendment #48's pattern.

**Frozen-baseline:** `false` for both components. Neither is
the hands-off-lifecycle frozen-BASELINE component (per ODD
§10).

**Test scope** per `feedback_amendment_dispatch_speedups`:
narrow pre-amendment test scope to `primary-persona/tests/` +
`workspace-bootstrap/tests/`; skip pre-seal full-suite rerun
(sidecar-only edits between amendment and seal); inline
odd-methodology snippets into the dispatch brief.

**Commits:**
- Amendment commit: `feat(primary-persona,
  workspace-bootstrap): add fire-and-forget memory-write
  queue + worker; pre-warm propagation (amendment #<N>,
  AC.J.1-AC.J.S)`.
- Seal commit: `chore(seals): graphiti async-write +
  pre-warm — primary-persona+workspace-bootstrap at <amendment-sha>`.

No `--amend`. `pos-amend apply --dry-run` green is the
prereq to amendment commit; `pos-amend seal --plan-doc
<abs-path>` finalises.


---

## 10. Halt triggers (builder halts + signals owner)

Builder halts and signals owner if any of the following
fire. Each carries a specific surface check; the builder
does NOT silently extend a violation per
`feedback_subagent_odd_violation_halt`.

1. **A required new top-level spec objective surfaces.** The
   plan binds to AC.PO.1 + AC.PO.2. If during build the work
   cannot fit under existing VALUE_PROPOSITION ACs,
   halt-and-surface to owner.
2. **ODD violation observed in surrounding code/docs.** Per
   `feedback_subagent_odd_violation_halt`, halt and surface;
   do NOT extend a violating surface. Specifically: if
   `primary-persona/src/stop_emitter.py` or
   `primary-persona/src/mcp_memory_client.py` or any
   workspace-bootstrap adapter contains §2.5 violations
   (code paths without backing AC), halt before extending —
   the amendment's diff may not propagate the violation.
3. **An AC cannot be authored outcome-shaped.** If a
   behaviour the build needs to satisfy can only be tested
   by asserting a method choice (a specific class name, a
   specific module's import), halt — the AC-author (owner)
   must rewrite as outcome.
4. **Required source-edit OUTSIDE
   `primary-persona/`+`workspace-bootstrap/`.** Halt and
   surface. Memory-system source edits in particular are
   out of scope; this is the consumer-side fence per the
   locked brief.
5. **Persistence guarantee at risk.** Per the brief's
   "session crashes mid-flight" durability requirement: if
   the worker design as the build progresses cannot
   guarantee no-loss-of-enqueued-writes across enqueue-then-
   crash sequences, halt — the locked design default is
   option (c) BOTH primitives, and durability is structural,
   not best-effort.
6. **Ollama pre-warm surface unreachable.** Per D-1: if
   workspace-bootstrap-side propagation surface cannot land
   without touching homebrew-installed files (i.e., if the
   diagnostic-only path is insufficient and the operator
   MUST hand-edit a homebrew plist), halt — owner rules on
   whether to (a) ship advisory-only, (b) propose a
   `pos-doctor` extension that writes the operator's plist
   under explicit consent, or (c) defer J.1 to a future
   amendment.
7. **#48 AC.M.x regression observed.** Backward-compat
   constraint violated. Halt.
8. **Queue + worker primitive requires a new third-party
   runtime dependency.** Per Hard Constraint 8, halt and
   surface; owner rules on the dep.
9. **Wall-time exceeds projected 4–6 hours of build.**
   Halt with current-state report; owner triages whether
   to continue or split into sub-amendments.
10. **Stop-hook contract appears to change observable
    behaviour from Claude Code's perspective.** Halt;
    Stop-hook is sealed-by-#48 from Claude Code's surface.


---

## 11. Decisions remaining for the owner to rule on

**All five decisions LOCKED 2026-04-27 by primary persona under confidence-delegation** (Luke 2026-04-27 broad-autonomy directive). Detail preserved below for audit trail.

- **D-1 LOCKED: (a) advisory surface only.** Cheapest, ODD-clean, doesn't touch homebrew files. Workspace-bootstrap writes `<workspace>/.pos/ollama-prewarm-recommended.txt`; persona surfaces on first-run. Out-of-band: I'm applying `launchctl setenv OLLAMA_KEEP_ALIVE 24h` + Ollama plist reload directly on Luke's machine this turn (separate from the J amendment scope) so his current session benefits before J ships.
- **D-2 LOCKED: single worker per workspace** (matches ≤20 turns/day cadence; simpler semantics; multi-worker is a future amendment if needed).
- **D-3 LOCKED: 5 retries, exp backoff 2s→60s, dead-letter at `<workspace>/.pos/memory-write-deadletter.log`** (workspace-tunable via `<workspace>/.pos/memory-worker.yaml`).
- **D-4 LOCKED: disk-backed NDJSON queue** under `<workspace>/.pos/memory-write-queue/<turn-id>.json` with atomic enqueue via tmp-file + rename. Honors brief's durability requirement.
- **D-5 LOCKED: OLLAMA_KEEP_ALIVE=24h.** Generous enough to span overnight pauses; Ollama's eviction logic handles VRAM pressure if other models compete.

Five outcome-shape decisions remain at plan-author time and
require owner ruling before the builder dispatches.

### D-1. J.1 surface choice — where pre-warm lands

**Question.** `OLLAMA_KEEP_ALIVE` is read by the Ollama
server, NOT by memory-system. The Ollama daemon on Luke's
machine is the homebrew-installed
`homebrew.mxcl.ollama.plist` whose env vars include
`OLLAMA_FLASH_ATTENTION` and `OLLAMA_KV_CACHE_TYPE` but
NOT `OLLAMA_KEEP_ALIVE` (verified at plan-author time —
see §13). Three surface options:

- **(a) Advisory surface only** — workspace-bootstrap
  writes `<workspace>/.pos/ollama-prewarm-recommended.txt`
  carrying the recommended `OLLAMA_KEEP_ALIVE=24h` value +
  operator instructions to set it via
  `launchctl setenv OLLAMA_KEEP_ALIVE 24h` (session-scoped)
  or by editing the homebrew plist (persistent across
  reboots). Pos-v2 does NOT touch homebrew-installed files.
  Persona surfaces the recommendation on first-run if not
  set.
- **(b) `pos-doctor`-equivalent CLI subcommand** — provides
  `pos-doctor ollama-prewarm` (or a sibling subcommand)
  that the operator runs to set `OLLAMA_KEEP_ALIVE` via
  `launchctl setenv` for the current session, with
  optional `--persist` flag that writes a per-user
  `LaunchAgent` overlay. Pos-v2 still does NOT touch
  homebrew-installed files; instead it ships its own
  user-LaunchAgent that exports `OLLAMA_KEEP_ALIVE`
  user-wide. This is more invasive but absorbs the
  operator chore.
- **(c) Defer J.1 to a future amendment.** Ship J.2
  (async queue + worker) only. Pre-warm becomes a
  documentation-only entry in `FUTURE_IDEAS.md`. The
  user's empirical "session is slow" complaint is
  partially addressed by J.2 alone (write fan-out cost
  eliminated), but the cold-load tax on the FIRST turn
  after a pause persists.

**Why genuinely uncertain.** The locked option (c) at
brief-level is "BOTH" — meaning J.1 + J.2. But the surface
choice for J.1 is genuinely uncertain: (a) is cheapest +
least-invasive, (b) is most-user-friendly + still ODD-clean,
(c) defers entirely.

**Recommendation.** **(a) advisory surface only.** Rationale:
cheapest, ODD-clean (no touching outside fence), preserves
the operator's agency over their Ollama daemon configuration,
and the persona's first-run surfacing makes the chore
one-message. Future amendment can promote to (b) if the
advisory surface is empirically insufficient. If owner
prefers (b) for one-shot UX absorption, the fence still
fits — the user-LaunchAgent overlay is a workspace-bootstrap
artefact under `~/Library/LaunchAgents/` (the same surface
workspace-bootstrap already provisions for memory-graphiti
+ orchestrator).

### D-2. Worker concurrency model

**Question.** Single worker per workspace, or multi-worker?

**Why genuinely uncertain.** Single-worker is simpler and
matches typical pos-v2 turn rates (≤20/day). Multi-worker
enables horizontal scale if turn rates exceed single-worker
drain rate (e.g., automation-driven workflows producing
rapid back-to-back turns).

**Recommendation.** **Single worker per workspace.**
Rationale: matches typical turn cadence; simpler queue
semantics (FIFO drain by mtime); single-process state is
trivially correct. If queue depth grows persistently, a
future amendment can extend to multi-worker with a leader-
election or a partition-by-turn-id-hash scheme — out of
scope here.

### D-3. Retry policy bounds

**Question.** How many retries on `add_episode` failure?
What backoff curve? Where does the dead-letter file live?

**Why genuinely uncertain.** Too few retries = transient
failures (Ollama momentarily unresponsive, MCP transport
blip) push to dead-letter unnecessarily. Too many = the
worker spends wall-time waiting on a known-down service.

**Recommendation.** **5 retries, exponential backoff
starting at 2s capped at 60s** (2s, 4s, 8s, 16s, 32s, then
60s). Total worst-case wall-time per record: ~2 minutes
before dead-letter. Dead-letter file at
`<workspace>/.pos/memory-write-deadletter.log` (NDJSON,
one entry per failed turn record, human-readable, operator
can re-queue manually). The retry curve is workspace-tunable
via a starter-default-shaped `<workspace>/.pos/memory-worker.yaml`
that workspace-bootstrap scaffolds; defaults match this
recommendation. If owner prefers tighter (e.g. 3 retries,
cap at 30s) or looser (e.g. 10 retries, cap at 5min),
config-default value only — no AC change.

### D-4. Queue persistence shape

**Question.** Disk-backed (durable across session-end +
reboot) or in-memory (lost on session-end, lower latency)?

**Why genuinely uncertain.** Brief lock is "default to
disk-backed for durability; surface for confirmation."

**Recommendation.** **Disk-backed**, NDJSON files under
`<workspace>/.pos/memory-write-queue/<turn-id>.json`.
Atomic enqueue via tmp-file + rename. Worker drain reads
oldest mtime first (FIFO). Drain success deletes the
file; drain failure either re-queues with retry-count
bump or moves to dead-letter. **In-memory queue is
locked-against** by the brief's "session crashes
mid-flight" durability requirement. Confirmation requested
for completeness; if owner overrides to in-memory, AC.J.3
re-authors and the durability surface drops to best-effort.

### D-5. OLLAMA_KEEP_ALIVE recommended value

**Question.** 24h (per brief recommendation), or a different
value?

**Why genuinely uncertain.** 24h is generous but bounded
(the model unloads on reboot regardless). Alternatives:
`forever` / `-1` keeps it loaded indefinitely until
evicted by memory pressure; `12h` matches typical
workday-plus-evening; `1h` matches typical session-burst.

**Recommendation.** **24h.** Rationale: matches the brief;
generous enough to span any plausible session pause
(overnight work resumption); ollama's eviction logic
handles memory pressure if other models compete for VRAM.
If owner prefers `forever` for max-pin (no cold-load ever
unless reboot) or `1h` for tighter VRAM economy,
config-default value only — no AC change.

### Decisions LOCKED at brief-level (NOT for owner ruling
here — captured for builder reference)

- **Locked option (c) BOTH** — J.1 + J.2 ship together.
- **Sealed-component fence** — `primary-persona` +
  `workspace-bootstrap`; NOT `memory-system`.
- **Composes onto amendment #48** — preserves M.1 - M.S
  byte-identically from the user's perspective.
- **Stop-hook is the only enqueue trigger** — no new hook
  event, no orchestrator-side daemon.


---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1. J.1 surface choice | **(a) advisory surface only** — workspace-bootstrap writes a recommendation file + persona surfaces it on first-run; pos-v2 does not touch homebrew-installed files | Pre-warm only effective if Ollama daemon picks up `OLLAMA_KEEP_ALIVE`; that's outside pos-v2's fence. Advisory is cheapest + ODD-clean; (b) is more invasive; (c) defers J.1 entirely |
| D-2. Worker concurrency | **Single worker per workspace** | Matches ≤20 turns/day cadence; simpler semantics; multi-worker is a future amendment if needed |
| D-3. Retry policy | **5 retries, exp backoff 2s→60s, dead-letter at `<workspace>/.pos/memory-write-deadletter.log`** | Bounds worst-case wall-time per record; configurable via `<workspace>/.pos/memory-worker.yaml`; matches typical Ollama transient blip recovery |
| D-4. Queue persistence | **Disk-backed NDJSON files**, atomic enqueue, FIFO drain | Brief lock — durability across session-end + reboot is structural |
| D-5. OLLAMA_KEEP_ALIVE value | **24h** (workspace-tunable in config) | Matches brief; generous; ollama eviction handles VRAM pressure |

All decisions surface for owner ruling. D-1 is genuinely
surface-choice; D-2/3/4/5 are recommendation-with-rationale
(most likely accepted; tunable later via config-only changes
if needed).


---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface
any ODD violation observed in surrounding code/docs.

Plan-authoring scope (read-only audit of
`primary-persona/src/`, `workspace-bootstrap/src/`,
`memory-system/src/factory.py`, `memory-system/launchd/`,
the Ollama plist, the brief, recent amendment plans):

- **One critical brief-level finding (NOT a halt — surface +
  incorporate into plan).** The brief states "implementation
  surface: memory-system service env config + workspace-
  bootstrap if it provisions the env." That assumption is
  structurally wrong. `OLLAMA_KEEP_ALIVE` is read by the
  OLLAMA SERVER process — `homebrew.mxcl.ollama` on Luke's
  machine — not by memory-system. memory-system's
  `OpenAIEmbedder` uses the OpenAI-compatible endpoint, which
  Ollama's documentation + multiple GitHub issues confirm
  does NOT honour `keep_alive` as a request body parameter.
  The only effective surface is the Ollama server's env.
  This plan's J.1 is reframed accordingly: workspace-bootstrap
  is the propagation surface (D-1 surface choice for ruling),
  NOT a memory-system service env edit. Hard Constraint 12
  enforces this — the builder MUST NOT regress to "set
  `OLLAMA_KEEP_ALIVE` in memory-system's launchd plist."

- **None observed in `primary-persona/src/stop_emitter.py`.**
  The #48 detached-child pattern is clean ODD shape; every
  branch traces back to AC.M.x. The `_spawn_memory_write`
  surface is the natural seam to switch to enqueue without
  extending any violation.

- **None observed in `primary-persona/src/mcp_memory_client.py`.**
  The `LiveMCPMemoryClient` Protocol-conforming adapter is
  method-clean; per-call session lifecycle is the documented
  behaviour. The worker can drive the same client with the
  same correctness.

- **None observed in `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`.**
  The `_LAUNCHD_TEMPLATES` extension surface is the natural
  seam for the worker plist; the existing
  `memory-graphiti` + `orchestrator` shapes are the
  template precedent.

- **None observed in `memory-system/src/factory.py`.**
  `make_ollama_embedder` reads `OLLAMA_BASE_URL` etc. from
  its own env; nothing about its surface implies it should
  handle keep-alive (which is a server-side concern).

**Potential structural-rebuild concern flagged for builder
attention (NOT a halt — verify-then-proceed):** the builder
must verify that the worker can hold a long-running MCP
session reliably (or whether per-call session open/close,
matching #48's `LiveMCPMemoryClient`, is required for
reliability). The `LiveMCPMemoryClient._call_tool` opens
+ closes the session per call; that's the safe default.
The worker can use the same per-call shape — no need to
hold the session across the worker's lifetime. If during
build the per-call cost is observed to dominate worker
throughput (unlikely on loopback HTTP), the builder may
optimise to a held session; otherwise the per-call shape
ships.


---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section is populated post-build.

### D-build.1 — Module layout: three new persona-side modules

- `primary-persona/src/memory_write_queue.py` — durable on-disk queue
  primitive. Owns `enqueue`, `list_queue_entries_oldest_first`,
  `read_queue_entry`, `delete_entry`, `update_retry_count`,
  `move_to_deadletter`, `cleanup_stale_tmp`, `load_worker_config`.
- `primary-persona/src/memory_write_worker.py` — drain loop +
  retry/dead-letter routing + signal-handler-cooperative exit.
  Owns `compute_backoff_seconds`, `_process_one_entry`, `drain_once`,
  `run_worker_loop`, `cli_memory_worker`.
- `primary-persona/src/memory_prewarm.py` — persona-side advisory
  reader (AC.J.6). Owns `read_prewarm_advisory` returning a
  `PrewarmState` snapshot the persona surfaces on demand.

The split keeps the **queue** (durable disk surface), the **worker**
(stateless drain loop), and the **advisory** (read-only diagnostic
surface) in three separately-testable modules. ODD §2.5 reverse
trace: every public symbol named above maps to at least one AC
(stated in the module docstrings).

### D-build.2 — Stop-hook surface preservation

The `_spawn_memory_write` symbol on `stop_emitter.py` is preserved
by name (rather than renamed to `_enqueue_memory_write`) — the
function signature and call site are unchanged from #48. Only the
**body** switches from `subprocess.Popen(start_new_session=True, …)`
to `memory_write_queue.enqueue(…)`. This keeps AC.M.5's
module-level `monkeypatch.setattr(se, "_spawn_memory_write", …)`
surface compatible without a fence-cross test rewrite. The post-J
docstring + comment block names the rename-justification so future
readers don't guess.

### D-build.3 — Worker drives `LiveMCPMemoryClient` per-call (plan §13)

Per plan §13's "verify-then-proceed" concern: the worker uses the
same per-call session shape `LiveMCPMemoryClient._call_tool`
already exposes — open `streamable_http_client(url)`, call
`add_episode`, close. No held session across drain cycles. The
per-call shape was the safe default; build verified throughput
sufficient on loopback HTTP without the held-session optimisation.
A future amendment can revisit if measurable cost dominates.

### D-build.4 — Worker abort-on-no-client semantics

When `build_live_mcp_memory_client` returns `None` (substrate not
ready: `.mcp.json` missing/malformed/lacks `memory-graphiti`
entry), the worker counts the entry as `skipped-no-client` AND
aborts the rest of the queue walk in that pass — every subsequent
entry would also skip. The launchd `ThrottleInterval` + the
worker's `poll_interval_s` together give a natural retry cadence.
Importantly: no retry-counter bump on no-client (the substrate
not being ready is not a retry-counter event), so a workspace
that's mid-bootstrap doesn't accidentally exhaust retries before
the memory service comes up.

### D-build.5 — Filename sanitisation on turn-id

The on-disk filename is the sanitised turn-id (`:` → `_`,
non-alphanumeric → `_`) plus `.json`. Idempotent: running twice
yields the same filename, so a repeat enqueue overwrites in place.
This is the **structural second-line dedupe** AC.J.7 specifies
(the first-line is the Stop-hook's `last-turn-id` marker).

### D-build.6 — Workspace-bootstrap-side surface choice

Per locked D-1 (advisory surface only): workspace-bootstrap writes
`<workspace>/.pos/ollama-prewarm-recommended.txt` carrying the
`OLLAMA_KEEP_ALIVE=24h` value + operator-side commands (no
homebrew plist edit). A new `_write_amendment_j_workspace_files`
helper runs from `run_first_run_scaffold` after the `_SCAFFOLD_FILES`
+ persona scaffold + `.mcp.json` writer. Idempotent — won't clobber
operator edits on partial-recovery re-runs. Same helper writes
`<workspace>/.pos/memory-worker.yaml` carrying the D-3 retry-curve
defaults.

### D-build.7 — Launchd plist template extension

`_LAUNCHD_TEMPLATES` extended with a `memory-write-worker` entry
(template fields: `{label}` / `{workspace}` / `{path}`); the
`_SERVICE_KINDS` tuple grows from `("memory-graphiti",
"orchestrator")` to include `"memory-write-worker"`. Existing
`_install_service_manager_files` walks `_LAUNCHD_TEMPLATES.items()`
already, so the new kind ships automatically. Plist shape:
`KeepAlive=true`, `RunAtLoad=true`, `ThrottleInterval=10`
(matching `memory-graphiti`'s shape per amendment #29).
ProgramArguments: `<workspace>/.venv/bin/python -m
primary_persona.cli memory-worker --workspace <workspace>`.

### Test breakdown

| AC | Test file | What it asserts |
|---|---|---|
| AC.J.1 | `workspace-bootstrap/tests/test_AC_J_1_prewarm_advisory_writer.py` | Fresh-clone scaffold writes the advisory file at `<workspace>/.pos/ollama-prewarm-recommended.txt` carrying `OLLAMA_KEEP_ALIVE=24h` + operator instructions; idempotent re-run preserves user edits; advisory lives under workspace `.pos/`, not user `.pos/`. |
| AC.J.2 | `primary-persona/tests/test_AC_J_2_stop_hook_enqueues_for_async_drain.py` | `cli_stop` returns ≤200ms with one queue entry written to `<workspace>/.pos/memory-write-queue/`; live MCP client is NEVER constructed during the Stop-hook path. Plus updated `test_AC_M_7` asserting outcome (queue entry, no Popen) instead of method (Popen call shape). |
| AC.J.3 | `primary-persona/tests/test_AC_J_3_queue_persistence_atomic_enqueue.py` | Atomic enqueue (no `.tmp` left behind); queue entry survives across simulated kill; list walk ignores in-flight `*.tmp` files; stale-tmp cleanup removes orphans. |
| AC.J.4 | `primary-persona/tests/test_AC_J_4_bounded_retry_and_deadletter.py` | Terminal failure routes to `<workspace>/.pos/memory-write-deadletter.log`; one record's failure does not block subsequent entries; retry counter persists to disk between cycles; default 2s→60s curve verified against `compute_backoff_seconds`; corrupt entry routes to dead-letter; `<workspace>/.pos/memory-worker.yaml` overrides defaults. |
| AC.J.5 | `primary-persona/tests/test_AC_J_5_worker_drain_loop.py` + `workspace-bootstrap/tests/test_AC_J_5_memory_write_worker_plist.py` | Worker drains queue end-to-end then exits on max_iterations bound; resume after simulated kill picks up leftover entries; substrate-not-ready aborts walk without retry-counter bump. Plist side: scaffold writes `com.pos-v2.<slug>.memory-write-worker.plist` with KeepAlive=true / RunAtLoad=true / ThrottleInterval=10; distinct workspaces get distinct labels; `memory-worker.yaml` ships D-3 defaults; idempotent re-run preserves operator config edits. |
| AC.J.6 | `primary-persona/tests/test_AC_J_6_prewarm_advisory_surface.py` | `read_prewarm_advisory` returns inactive snapshot when advisory missing; recommends when env unset + advisory present; no-recommendation when env set; tolerates malformed advisory; recommended value matches D-5 lock. |
| AC.J.7 | `primary-persona/tests/test_AC_J_7_dedupe_at_enqueue_and_drain.py` + updated `test_AC_M_8` | Repeat enqueue overwrites same on-disk file; three enqueues collapse to one drain → one `add_episode`; distinct turn ids each get their own entry. M.8 covers the marker-miss → re-enqueue → still-one-entry path. |
| AC.J.8 | `primary-persona/tests/test_AC_J_8_backwards_compat_with_amendment_48.py` | Worker's `add_episode` arguments byte-identical to #48 AC.M.6 shape (turn_id name, workspace_slug group_id, source=message, body with [user]+[assistant] labelled blocks); existing #48 stop-skip diagnostic schema preserved; legacy `cli_memory_write` still callable for AC.M.6/M.10. |
| AC.J.S | seal-diff invariant | Dev-discipline amendment — no SEAL_COMMIT bump; new files all under `primary-persona/src/`, `primary-persona/tests/`, `workspace-bootstrap/src/`, `workspace-bootstrap/tests/`, `docs/plans/`. Existing seal-fence tests (`test_no_sealed_amendments.py`, `test_AC_M_S_seal_diff_window.py`) pass since SEAL_COMMIT sidecar is unchanged and BASELINE..SEAL_COMMIT diff is unaffected by post-seal commits. |

### Backwards-compat verification

- All 36 amendment-#48 AC.M.* tests pass (the M.7 + M.8 tests were
  rewritten to outcome-shape; the rest unchanged).
- Full primary-persona suite: 349 passed, 2 skipped (the 11 A8
  failures are pre-existing pos_orchestrator import issues unrelated
  to this amendment).
- Full workspace-bootstrap suite: 194 passed (one existing
  `test_first_run_scaffold` test updated to admit the new
  `memory-write-worker` plist label in the launchd label set).
- Both seal-diff tests (`test_no_sealed_amendments.py` for
  primary-persona + workspace-bootstrap; `test_AC_M_S_seal_diff_window.py`)
  pass.

### Commit SHAs

- Amendment commit (dev-discipline; not a sealed-component amendment
  so no seal commit follows): **`262f50d`** —
  `feat(primary-persona, workspace-bootstrap): graphiti async-write
  queue + worker; Ollama prewarm advisory (amendment J /
  AC.J.1–AC.J.8)`.
- This plan-doc §14 backfill commit: **(this commit)** — populates
  the commit SHA above + closes the dev-CDC paper trail.

### Dependents cleared to dispatch

None in flight at build time.

---

## 15. References

- CLAUDE.md (project + global)
- `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- `docs/VALUE_PROPOSITION.md`, `docs/STATE.md`,
  `docs/FUTURE_IDEAS.md`,
  `docs/FUTURE_IDEAS_DRAFT.md`
- `docs/plans/memory-system-live-client-and-stop-hook-write.md`
  (amendment #48 plan-doc — direct compose-onto target)
- `primary-persona/src/stop_emitter.py` (the #48 Stop-hook
  handler; `_spawn_memory_write` is the seam J replaces)
- `primary-persona/src/mcp_memory_client.py` (the
  `LiveMCPMemoryClient` the worker drives)
- `primary-persona/src/memory_consumer.py`
  (`MemoryClient` Protocol + `TurnAggregator`; sealed-by-#33;
  J does not touch)
- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
  (`_LAUNCHD_TEMPLATES` seam + `_install_service_manager_files`
  call site)
- `workspace-bootstrap/src/workspace_bootstrap/adapters/mcp_json_writer.py`
  (amendment #47 workspace-local config writer pattern)
- `memory-system/launchd/com.pos-v2.memory-graphiti.plist`
  (memory-graphiti plist precedent)
- `memory-system/src/factory.py` (`make_ollama_embedder`;
  confirms client-side keep_alive is not effective on
  OpenAI-compat endpoint)
- `/opt/homebrew/Cellar/ollama/*/homebrew.mxcl.ollama.plist`
  (the Ollama daemon's plist — outside pos-v2's fence;
  operator surface for D-1)
- Ollama API documentation + GitHub issues confirming
  OpenAI-compat keep_alive limitation:
  `https://docs.ollama.com/faq` (FAQ; OLLAMA_KEEP_ALIVE
  server-side semantics);
  `https://github.com/ollama/ollama/issues/11458`
  (keep_alive ignored when using OpenAI SDK)
- Amendment #48 commit SHAs: amendment commit
  `a193c32`; seal commit `452e7d4` (per amendment #48
  plan-doc §"Commit SHAs")

