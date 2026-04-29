# OSS v0.1.0 publish — M5 — wire dormancy constructor + bind orchestrator pause/resume + connect MemorySupervisor outage events — sub-plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` (master plan §5 M5 row + §6 sequencing rule #3).
**Programme predecessor:** M4.wire-dispatch (sealed `1719e14` 2026-04-29; §14 backfill `bf56763`). M4 itself composed on M3.wire-clis (sealed `95f1ab2`) + M2.partition (sealed `4cda805`) + M1.rename series (M1g seal `f6c22fd`).

**Authority documents:**
- Master plan §5 M5 row + §6 sequencing rule #3 (M3/M4/M5 are independent in scope; serial in tree).
- Programme AC: AC.OSS.2 (D-2) — `docs/rebuild/plans/oss-v0-1-0-publish.md` §3.
- Feature-usage audit D-2 — `DormancyComponent.build(...)` is invoked only by tests; bootstrap adapter is declaration-only; orchestrator pause/resume hooks are declared but unbound.
  Path: `.scratch/claude-output/feature-usage-audit.md` §D-2 (line 402).
- VALUE_PROPOSITION (prime objective hook): `docs/rebuild/VALUE_PROPOSITION.md` — primary-persona test (translation-burden absorption) + harness test (toolkit-primitive growth). M5 wires the dormancy runtime so memory-sidecar outages produce real observable degradation episodes in production.
- Existing dormancy component (DO NOT MODIFY): `framework/dormancy/src/loam/dormancy/component.py` — `DegradationComponent.build(...)` already constructs detector + dispatcher + notifier + threshold internally. Sealed.
- Existing dormancy adapter (DECLARATION-ONLY today): `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/dormancy.py` — `contribute()` returns None.
- Existing orchestrator pause/resume hooks (DECLARED, ALREADY-WIRED to dispatcher): `framework/orchestrator/src/loam/orchestrator/orchestrator.py:564,574` — `pause_activation(reason)` + `resume_activation()` are sync no-arg-or-string hooks. The `PolicyDispatcher` (`framework/dormancy/src/loam/dormancy/policy.py:166,245`) already calls them; no orchestrator change needed.
- Existing MemorySupervisor (DEFINED, NOT-CONSTRUCTED-IN-PRODUCTION): `framework/orchestrator/src/loam/orchestrator/supervisor.py:191`. Exposes `on_recovering` (Awaitable, no-arg) + `on_normal` (Awaitable, no-arg) + `on_transition` (Awaitable, takes `SupervisorTransition`). No production caller instantiates it today.
- Existing supervisor-signal surface in dormancy: `framework/dormancy/src/loam/dormancy/detection.py:299` — `record_supervisor_signal(signal=memory_sidecar_down|memory_sidecar_recovered)`. Already authored, sealed; consumed by the `memory_sidecar` mode FSM.

---

## 1. Summary / TLDR

**M5 promotes the dormancy bootstrap adapter from declaration-only
(returns None) to a real constructor that builds `DegradationComponent`
in production, AND constructs the orchestrator's `MemorySupervisor`
(today defined-but-not-instantiated), AND wires the supervisor's
state-transition callbacks into the dormancy detector's
`record_supervisor_signal` surface.** This is the AC.OSS.2 (D-2) closure
per the feature-usage audit + master plan §5 M5 row.

The audit found three coupled gaps:

1. **`DormancyContribution.contribute()` returns None** —
   `DegradationComponent.build(...)` is invoked exclusively by tests.
2. **Orchestrator's `pause_activation` / `resume_activation` hooks are
   declared but unbound** — already wired into dormancy's
   `PolicyDispatcher` (which calls them on policy application + release),
   but the dispatcher is never constructed in production because the
   component never is. So in practice, the hooks are unbound.
3. **MemorySupervisor outage events are never detected** —
   `MemorySupervisor` is defined in `orchestrator/supervisor.py` but
   has zero production callers; the `memory_sidecar` FSM in dormancy
   would receive `memory_sidecar_down`/`memory_sidecar_recovered` if a
   supervisor were running, but there is no supervisor.

M5 closes the chain by adding a real adapter body + production
supervisor instantiation + a bridge that translates supervisor
transitions to dormancy signals. Post-M5, when a workspace boots and
the memory sidecar fails, the bridge fires `memory_sidecar_down` into
dormancy's detector, the FSM trips, the dispatcher applies a policy,
the orchestrator's `pause_activation` is called, and a notification
is dispatched to the persona's one-on-one channel — the full pipeline
runs end-to-end.

**Critical architectural findings (§11 details; non-blocking; design
accommodations recorded in §10):**

- **Finding #1 — Adapter phase ordering.** Today
  `DormancyContribution.metadata.phase = before_orchestrator_start`
  with no `after=` declaration, but the adapter body needs
  `host.orchestrator` + `host.scope_runtime` populated by
  `primary_persona`'s adapter (which itself runs in
  `before_orchestrator_start`). Resolution: declare
  `after=("primary_persona",)` so the dormancy adapter runs after
  primary-persona within the same phase. Verified at plan-authoring:
  `host.orchestrator` is populated by primary-persona at line 71 of
  `adapters/primary_persona.py`; the framework's intra-phase
  topo-sort honours `after=` declarations.
- **Finding #2 — MemorySupervisor has no `on_degraded` callback,
  only `on_recovering` + `on_normal` + `on_transition`.** The
  asymmetric callback surface means "memory down" is detected via
  the `on_transition` callback (filter `to_state == degraded`),
  while "memory recovered" can use either `on_normal` (final
  recovery) OR `on_recovering` (first-good-probe). Resolution:
  M5's bridge subscribes via `on_transition` to fire
  `memory_sidecar_down` on `→ degraded` AND on `→ escalated` (both
  represent ongoing outage; escalated is "still unreachable past the
  retry limit"); fires `memory_sidecar_recovered` on `→ normal` (the
  full-recovery transition). The bridge does NOT use the
  `on_recovering` / `on_normal` callable shorthands — using
  `on_transition` is uniformly stateful and captures every relevant
  edge with a single subscription. Per plan §10 D-build.M5.4.
- **Finding #3 — MemorySupervisor needs a probe function.** The
  supervisor's constructor takes a required `probe: ProbeFn`
  (`Callable[[], Awaitable[ProbeResult]]`). Production needs an
  HTTP-probe against the sidecar's `/health` endpoint; the
  memory-system adapter already validates the URL at boot
  (`host.memory_sidecar_url`). Resolution: M5 authors a tiny probe
  function in the dormancy adapter that hits
  `host.memory_sidecar_url` and returns a `ProbeResult` per the
  supervisor's existing protocol. Per plan §10 D-build.M5.5.
- **Finding #4 — `host.memory_sidecar_url` may be None when
  `launch: False`.** Many test workspaces skip the sidecar (per the
  memory_system adapter's `launch` config flag). When the URL is
  None, the supervisor cannot probe. Resolution: M5's adapter
  short-circuits supervisor construction when
  `host.memory_sidecar_url is None`; the `DegradationComponent` is
  still constructed (the Claude-API adapter detection path stays
  active), but the memory-sidecar mode's input signal stays dormant
  (just like the rest of dormancy's modes when they have no
  triggers). Per plan §10 D-build.M5.6.
- **Finding #5 — Notifier needs at least one one-on-one channel
  registered on `host.channel_registry`.** `DegradationNotifier`
  rejects group channels at construction; needs ≥1
  `OneOnOneChannel`. Today the channel registry is populated by
  `telegram_interface` adapter (which runs in
  `after_orchestrator_ready` — strictly LATER than the dormancy
  adapter's `before_orchestrator_start` phase). Resolution: M5's
  adapter pulls channels from `host.channel_registry` at construction
  time, accepting an empty list (per the existing
  `DegradationNotifier`'s queue-when-no-active-channel behaviour —
  notifications are queued in-memory and flushed when a channel
  registers). Builder-side note: since dormancy's adapter runs
  BEFORE telegram_interface's, the notifier's channels list will be
  empty at construction; this is the intended behaviour per
  `DegradationNotifier.send` (queue + emit `queued_no_channel`
  span). Per plan §10 D-build.M5.7.
- **Finding #6 — No HC#4 byte-content sample paths impacted by M5
  diff.** Verified at plan-authoring: M5's diff is (a) ~80-120 LOC
  in `dormancy.py` adapter (full constructor body), (b) ~40-60 LOC
  NEW supervisor-bridge module (lives under
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/`
  alongside `dormancy.py`, OR inline in `dormancy.py`), (c) 4-5 NEW
  test files, (d) no edits to dormancy/ or orchestrator/ source.
  No HC#4 sample paths under any of the 3 fenced components are
  touched. Per plan §10 D-build.M5.8.

**Halt-and-surface findings encountered at plan-authoring (full list
in §11):** none block dispatch; six observations recorded for builder
awareness (§11 maps each to a §10 design decision).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Prime objective:** VALUE_PROPOSITION's two tests (harness-test +
primary-persona-test). Per `feedback_value_proposition_as_prime_objective`,
every component / feature / amendment / AC ladders up.

**Programme objective:** AC.OSS.2 — wired-feature-density: "Every
sealed component in the public set is wired and exercised by primary
persona's normal operation."

**M5-specific scope:** AC.OSS.2 (D-2) — `DormancyContribution` is
declaration-only; orchestrator pause/resume hooks are unbound;
`MemorySupervisor` is defined-but-not-constructed; memory outage
events never reach `DegradationComponent`. M5 wires all four surfaces.

**Lens 1 — Claude-leverage-first:** **pass.** No new Claude primitives
required; M5 composes on existing surfaces (workspace-bootstrap's
contribution model, orchestrator's already-declared hooks, dormancy's
already-authored detector signal). The leverage point M5 unlocks is
*observability of memory-sidecar outages by the persona* — the
`DegradationNotifier` routes alerts through the persona's one-on-one
channel (Telegram or terminal-stub). When memory goes down, the
persona learns about it through the notification surface; that surface
itself is a Claude-Code-shaped capability.

**Lens 2 — Harness + primary-persona test:**

- *Primary-persona test:* **pass.** Pre-M5, when the memory sidecar
  fails (e.g. process dies, port unbound, or Graphiti+Kuzu OOM),
  there is no observable signal — the persona keeps issuing memory
  writes that silently drop, and the user sees no notification.
  Post-M5, the supervisor probes detect the failure, dormancy's
  `memory_sidecar` mode trips, the policy dispatcher pauses
  LLM-dependent active scopes, the persona is notified, and the user
  is informed via the one-on-one channel. Translation burden between
  "memory broke" and "user knows + active work paused" drops from
  "user discovers stale memory hours later" to "structural
  side-effect of supervisor probe loop."
- *Harness test:* **pass.** M5 lights up four toolkit primitives
  that already existed but were dormant: (1) DormancyComponent's
  detection / FSM / policy / notification pipeline, (2) the
  orchestrator's pause/resume hooks, (3) MemorySupervisor's probe
  loop, (4) DormancyDetector's `record_supervisor_signal` input
  surface. None of these are NEW capabilities — they are existing
  capabilities the harness gains the ability to USE.

**Lens 3 — ODD authoring:** ODD §2.5 enforced — every changed line
maps to an explicit AC under AC.OSS-M5.1..AC.OSS-M5.7. Hook + adapter
+ bridge + tests are the entire diff; no "while we're here" edits.

---

## 3. Three-lens analysis

(Condensed — see §2 for the per-lens answers.)

### Lens 1 — Claude-leverage-first

The contribution-model pattern (workspace-bootstrap's adapter phase
ordering) is itself a Claude-Code-shaped extension surface. M5
promotes a declaration-only adapter to a real one — the same pattern
M4 used for the PreToolUse hook. No new Claude primitive needed.

### Lens 2 — Harness + primary-persona value

Per §2 above: dormancy's full pipeline goes from dormant to live.
Memory-sidecar outage detection becomes a structural side-effect of
the running supervisor probe loop, not a manually-invoked check.

### Lens 3 — ODD authoring

Every line in the M5 diff maps to one of the seven ACs (M5.1..M5.7).
ODD §2.5 enforced. No defensive `if` branches without a backing AC.

---

## 4. Acceptance criteria — AC.OSS-M5.*

### AC.OSS-M5.1 — DormancyContribution constructs DegradationComponent in production

`framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/dormancy.py`
gains a real `contribute(host)` body that:

  1. Loads dormancy config via
     `loam.dormancy.config.load_config(host.config_dir / "dormancy-config.yaml")`
     (returns defaults when the file is absent — per the existing
     loader's behaviour).
  2. Constructs a `DegradationNotifier` from
     `[ch for ch in host.channel_registry.values() if not ch.is_group]`
     (empty list is acceptable per Finding #5 — notifications queue
     in-memory until a channel registers).
  3. Calls `DegradationComponent.build(cfg=..., orchestrator=host.orchestrator,
     scope_runtime=host.scope_runtime, notifier=...)` and stores the
     result on `host.dormancy`.
  4. Subscribes `comp.on_scope_event` to `host.scope_runtime.subscribe_all(...)`
     (per `framework/dormancy/docs/architecture.md` §"Core composition"
     line 211 — the architecture doc names this exact subscription).
  5. Calls `await comp.reconcile_on_startup(orchestrator_paused=host.orchestrator.is_paused)`
     to handle restart edge cases (per architecture.md line 207).
  6. Phase: `before_orchestrator_start` with `after=("primary_persona",)`
     so `host.orchestrator` is populated.

**Verification:** a unit test runs the dormancy adapter against a
synthesised `BootstrapHost` populated with the orchestrator + scope
runtime stubs; asserts `host.dormancy` is a `DegradationComponent`
instance after `contribute()` returns.

**Test:** `framework/workspace-bootstrap/tests/test_AC_OSS_M5_1_dormancy_adapter_constructs_component.py` (new).

### AC.OSS-M5.2 — Orchestrator pause/resume hooks are bound via DormancyComponent's PolicyDispatcher

After AC.OSS-M5.1 fires, the constructed `DegradationComponent`'s
`PolicyDispatcher` holds a reference to `host.orchestrator` as its
`OrchestratorHooks` implementation (per existing dormancy/policy.py
shape — the PolicyDispatcher takes `orchestrator: OrchestratorHooks`
in its constructor). When a mode FSM trips, the dispatcher calls
`orchestrator.pause_activation(reason)`; when the episode resolves,
it calls `orchestrator.resume_activation()`.

This binding is **already wired in dormancy source** — the gap was
that the dispatcher was never constructed in production. AC.OSS-M5.1
closes that gap; AC.OSS-M5.2 verifies the pause/resume contract is
exercised through the wired path.

**Verification:** an integration test (a) constructs the bootstrap
host + runs the dormancy adapter, (b) directly invokes
`comp.dispatcher.apply(mode=DegradationMode.memory_sidecar,
episode_id="test", signal="test")`, (c) asserts
`host.orchestrator.is_paused == True` and the orchestrator's
`local_state` has a `pause_activation` event. Then calls
`comp.dispatcher.release(...)` and asserts `is_paused == False`.

**Test:** `framework/workspace-bootstrap/tests/test_AC_OSS_M5_2_orchestrator_pause_resume_responds_to_dormancy.py` (new).

### AC.OSS-M5.3 — MemorySupervisor instantiated in production with HTTP probe against sidecar

M5 authors a `MemorySupervisor` instance inside the dormancy adapter
(or in a small new module under `adapters/` for cohesion). The
supervisor:

  1. Constructs only when `host.memory_sidecar_url is not None` (per
     Finding #4 — when memory_system adapter's `launch: False` skips
     the sidecar, no supervisor needed).
  2. Receives a probe callable that issues an HTTP GET against
     `host.memory_sidecar_url` (the existing health endpoint) and
     returns a `ProbeResult` per supervisor's protocol. Probe
     implementation reuses `urllib.request.urlopen(url, timeout=2.0)`
     mirroring the memory_system adapter's existing probe pattern
     (lines 90-91 of `adapters/memory_system.py`).
  3. Receives an `on_transition` callback that bridges supervisor
     state transitions to dormancy detector signals (per AC.OSS-M5.4).
  4. Started via `await supervisor.start()` (registers the
     background probe task per the supervisor's `start()` contract).
  5. Registered as a shutdown hook on the host (per
     `host.register_shutdown("memory_supervisor", ...)`) so the
     probe loop is stopped cleanly at process teardown.

**Verification:** a unit test stubs `host.memory_sidecar_url` to a
fake URL, mocks the probe function (no real HTTP), runs the adapter,
asserts (a) `host.memory_supervisor` is a `MemorySupervisor`, (b)
the supervisor's state is `normal` initially, (c) the shutdown hook
is registered.

**Test:** `framework/workspace-bootstrap/tests/test_AC_OSS_M5_3_memory_supervisor_instantiated.py` (new).

### AC.OSS-M5.4 — Supervisor outage transitions reach DormancyComponent's detector

M5 authors a small bridge function (~15-25 LOC) — call it
`_supervisor_to_dormancy_bridge(comp)` — that returns an
`async def on_transition(t: SupervisorTransition)` callable wired into
`MemorySupervisor.__init__(on_transition=...)`. Bridge contract:

  - `t.to_state == SupervisorState.degraded` → `await
    comp.detector.record_supervisor_signal(signal=DegradationSignal.memory_sidecar_down)`.
  - `t.to_state == SupervisorState.escalated` →
    `record_supervisor_signal(memory_sidecar_down)` (idempotent if
    the FSM is already open per existing fsm.py semantics).
  - `t.to_state == SupervisorState.normal` →
    `record_supervisor_signal(memory_sidecar_recovered)`.
  - `t.to_state == SupervisorState.recovering` → no-op (the dormancy
    FSM transitions through half_open via dwell/probe; the
    "recovering" intermediate state is supervisor-internal and
    doesn't translate to a dormancy signal directly).

**Verification:** a unit test (a) constructs the bridge against a
real `DegradationComponent`, (b) feeds synthetic
`SupervisorTransition` events for each `to_state` value, (c) asserts
the dormancy detector's `memory_sidecar` FSM is in the expected state
after each transition (open after degraded; closed after normal;
unchanged after recovering).

**Test:** `framework/workspace-bootstrap/tests/test_AC_OSS_M5_4_supervisor_bridge_translates_transitions.py` (new).

### AC.OSS-M5.5 — End-to-end: memory outage triggers full pipeline

An end-to-end test that exercises the wiring chain in a single async
flow:

  1. Construct host + run all relevant adapters (observability +
     primary-persona + memory-sidecar-stub-via-monkeypatch + dormancy).
  2. Manually invoke a synthetic supervisor probe-failure (call
     `supervisor.tick()` with a probe stub returning `ok=False`,
     `error_class="refused"`).
  3. After enough ticks to cross the supervisor's
     `transient_threshold` (default 2) → assert supervisor state is
     `degraded`.
  4. Assert dormancy's `memory_sidecar` FSM has trippped (state
     `open`).
  5. Assert at least one episode is active in `comp.active_episodes[memory_sidecar]`.
  6. Assert `host.orchestrator.is_paused == True` (the
     PolicyDispatcher applied `memory_sidecar`'s default policy via
     `orchestrator.pause_activation`).
  7. Then feed a probe-success → cross the recovery threshold →
     assert supervisor state is `normal` → assert dormancy's
     `memory_sidecar` FSM is back to `closed` (after dwell + probe
     attribution, OR via the supervisor-recovered signal short-path
     per detection.py:324).
  8. Assert `host.orchestrator.is_paused == False`.

**Verification:** the test above. Heavy-but-not-prohibitive; uses
synthetic probes (no real HTTP, no real memory sidecar). Per
dispatch constraint test scope is narrow but this E2E test is
necessary to verify "production-path-vs-test-path" separation per
plan-authoring §11 finding #1 mitigation.

**Test:** `framework/workspace-bootstrap/tests/test_AC_OSS_M5_5_end_to_end_memory_outage_triggers_pipeline.py` (new).

### AC.OSS-M5.6 — Adapter short-circuits cleanly when memory sidecar absent

When `host.memory_sidecar_url is None` (sidecar not launched per
`memory_system` adapter's `launch: False` config — the common test/
no-graphiti workspace pattern):

  - `DegradationComponent` IS constructed (the Claude-API detection
    path stays active).
  - `MemorySupervisor` is NOT constructed (no probe target).
  - `host.memory_supervisor` is `None`.
  - No shutdown hook for the absent supervisor.

**Verification:** a unit test stubs `host.memory_sidecar_url = None`,
runs the adapter, asserts (a) `host.dormancy` is a
`DegradationComponent`, (b) `host.memory_supervisor` is None, (c)
no shutdown hook named `memory_supervisor` registered.

**Test:** `framework/workspace-bootstrap/tests/test_AC_OSS_M5_6_supervisor_skipped_when_no_sidecar.py` (new).

### AC.OSS-M5.7 — Notifier composes against pre-empty channel_registry; queues until channels register

When the dormancy adapter runs (phase `before_orchestrator_start`,
after=`primary_persona`), `host.channel_registry` may be empty —
the `telegram_interface` adapter (which populates it) runs later in
`after_orchestrator_ready`. The dormancy adapter must construct a
notifier with whatever channels are present (potentially empty) and
rely on `DegradationNotifier`'s existing queue-on-no-active-channel
behaviour.

**Verification:** a unit test (a) runs the adapter against a host
with empty `channel_registry`, (b) triggers a synthetic
notification via `comp._maybe_fire_notification(...)`, (c) asserts
the notifier's `_pending_queue` has the notification queued (per
`DegradationNotifier.send` line 119), (d) asserts no exception
raised.

**Test:** `framework/workspace-bootstrap/tests/test_AC_OSS_M5_7_notifier_queues_when_no_channel.py` (new).

### AC.OSS-M5.S — Sealed-component fence

The 3 sealed components in the M5 fence:

  - `framework/workspace-bootstrap/` — the adapter body lands here.
  - `framework/dormancy/` — sidecar bump only (no source diff; the
    adapter consumes existing public API).
  - `framework/orchestrator/` — sidecar bump only (no source diff;
    the supervisor's existing public surface is consumed).

Each component bumps its `tests/SEAL_COMMIT` sidecar at seal time.
The seal-diff fence is enforced via `tests/test_no_sealed_amendments.py`
in each component (workspace-bootstrap + orchestrator) and via
`test_cross_cutting.py`-style frozen-baseline for any HOL-derived
fence (dormancy uses the standard `test_no_sealed_amendments.py`).

**Verification:** seal-diff tests pass post-build for all three
components.

---

## 5. Out-of-scope (explicit)

- **DormancyComponent's internal logic.** Already authored, sealed.
  M5 consumes the existing `build(...)` API; no source change.
- **MemorySupervisor's internals.** Already authored (FSM + escalation
  + notifier + persistence); sealed via orchestrator's seal-diff.
  M5 instantiates it; no source change.
- **Orchestrator's pause/resume mechanism.** Already authored. M5
  consumes via the dispatcher's existing `OrchestratorHooks`
  protocol; no source change.
- **Notifier channel registration changes.** Per Finding #5 — the
  empty-channel-list case is explicitly handled by existing
  `DegradationNotifier` behaviour. No change to notification.py.
- **Notification flush hook.** When the telegram_interface adapter
  later registers a channel, the dormancy notifier's
  `flush_queue()` would need to be called. Adding a "queue flush on
  channel registration" hook is a reasonable future amendment but
  out of M5 scope (the notifier still works — alerts are queued, and
  the supervisor's escalation path still emits to its own
  notification surface).
- **Period tick scheduling.** `DegradationComponent.tick()` should
  be invoked periodically to advance dwelled FSMs. The orchestrator's
  heartbeat task (`framework/orchestrator/src/loam/orchestrator/orchestrator.py:200`)
  is the natural integration point, but adding a `comp.tick()` call
  to the heartbeat loop touches orchestrator source — out of M5
  scope. Halt-trigger if the test exercise reveals tick is required
  for AC.OSS-M5.5 to pass; mitigation in §11 finding #7.
- **M6 / Dev-SDLC plugin / etc.** Per master plan §6 sequencing —
  M5 is critical-path predecessor to M6; M6 is the next milestone.

---

## 6. Method-shape decisions deferred to builder

Per ODD §4 / `feedback_agent_prompts_scope_only`, the plan-doc carries
outcome-shape ACs; method-shape (file layout, exact test names beyond
the AC-mapped ones, exact LOC deltas) is the builder's call.

What's intentionally not specified:

- Whether the supervisor-bridge function lives inline in
  `dormancy.py` or in a new sibling module under `adapters/`.
  Recommendation in §10 D-build.M5.4 (inline; adds <30 LOC).
- Exact `SupervisorConfig` overrides for production. Recommendation
  in §10 D-build.M5.5 (defaults; the supervisor's defaults match
  research §Q2).
- Whether to invoke `comp.reconcile_on_startup` synchronously inside
  `contribute()` (which is async) vs deferring. Recommendation in
  §10 D-build.M5.3 (synchronous await within contribute).

---

## 7. Test scope (per dispatch constraint)

Test scope is **narrow**: 7 new test files exercising the wired
path. No full-suite rerun pre-seal per
`feedback_amendment_dispatch_speedups`.

Per-test ownership:

- 7 in workspace-bootstrap/tests/ (the structural-fence component;
  all tests cover the adapter's behaviour against a synthesised
  host).

No new tests in dormancy/ or orchestrator/ — those components have
existing tests (`test_d*`, `test_supervisor.py`) that cover their
internal logic. M5's tests cover the **wiring layer** (adapter +
bridge), not re-validate sealed internals.

---

## 8. Risks (M5-specific)

1. **Phase-ordering dependency on primary_persona.** The dormancy
   adapter must run after primary_persona within
   `before_orchestrator_start`. The framework's intra-phase
   topo-sort honours `after=` declarations — verified at plan-
   authoring. If a future amendment moves primary_persona to a
   different phase, M5's adapter breaks. Mitigation: the dependency
   is declared explicitly in metadata; topo-sort fails closed with
   a clear error if the dependency is unresolvable.
2. **Supervisor probe-loop background task lifecycle.** The
   supervisor's `start()` registers an `asyncio.create_task` for
   the probe loop. The adapter must register a shutdown hook to
   call `await supervisor.stop()` at process teardown. If the hook
   is missed, the probe loop continues until the event loop closes.
   Mitigation: AC.OSS-M5.3 mandates the shutdown hook; test asserts
   it's registered.
3. **Notifier's empty-channel-list case may surprise.** Future
   readers of the adapter source might expect notifier construction
   to fail without channels. Mitigation: inline comment in the
   adapter explaining the queue-until-channel-registers contract;
   AC.OSS-M5.7 test makes the expected behaviour test-visible.
4. **Reconcile-on-startup may have edge cases against a fresh host.**
   `comp.reconcile_on_startup` is designed for restart scenarios
   where the orchestrator's pause state may not match the dormancy
   store's unresolved-episodes table. On a fresh boot, both are
   empty and the call is a no-op. Mitigation: AC.OSS-M5.1's test
   asserts `contribute()` runs cleanly; the reconcile call is
   defensive.
5. **Potential conflict between Claude-API-degradation modes and
   memory-sidecar mode.** Both can fire policies that pause active
   scopes. The existing dispatcher handles this per-mode (each FSM
   tracks its own episode); two simultaneous modes mean two episodes
   in `active_episodes`. The existing dormancy logic handles this
   correctly — verified at plan-authoring (per
   `comp.active_episodes` keying by `DegradationMode`). Not an M5
   risk; documented for awareness.

---

## 9. Halt-and-surface conditions

Per dispatch + `feedback_subagent_odd_violation_halt`:

1. **Bootstrap adapter has structural concerns that resist promotion.**
   Specifically: if the adapter's host-attribute access requires
   not-yet-implemented host surfaces. Verified at plan-authoring:
   `host.orchestrator`, `host.scope_runtime`,
   `host.memory_sidecar_url`, `host.channel_registry` all exist
   today. If the builder finds an unmet host surface, halt and
   surface.
2. **Orchestrator's pause/resume hook signature doesn't cleanly
   accept policy_dispatch's surface.** Verified at plan-authoring:
   `pause_activation(reason: str)` + `resume_activation()` match
   the `OrchestratorHooks` Protocol exactly. If the builder finds
   a signature mismatch (e.g. orchestrator changed its hook surface
   in an unfreezed amendment), halt and surface.
3. **MemorySupervisor's outage event surface doesn't match
   DormancyComponent's expected input shape.** Per Finding #2 —
   asymmetric callbacks (`on_recovering` + `on_normal`, no
   `on_degraded`); resolution in M5.4 uses the unified
   `on_transition` callback. If the builder finds an `on_transition`
   signature mismatch (the SupervisorTransition shape changes), halt
   and surface.
4. **HC#4 byte-content invariant breach beyond ODD §4 in-band.** Per
   Finding #6 — no HC#4 sample paths are touched by M5's adapter
   diff. If the builder finds an HC#4 retire-and-rebaseline is
   required (e.g. the diff impacts a sample path that wasn't
   visible at plan-time), halt and surface; do NOT silently
   rebaseline without owner ruling.
5. **ODD §2.5 violations.** Per `feedback_subagent_odd_violation_halt` —
   the builder must halt if any code path in the M5 diff (or in
   surrounding code touched incidentally) doesn't ladder up to a
   named AC. The seven AC.OSS-M5.* cover the planned diff; if the
   builder finds a defensive branch without backing AC, halt.
6. **Frozen-baseline / per-invariant-BASELINE concerns.** If any of
   the 3 fenced components' seal-test BASELINEs are pinned and the
   M5 build requires advancing them, halt and surface (the BASELINE
   advance must be explicit; the per-component manifest's
   `frozen_baseline: false|true` field declares whether advance is
   permitted).
7. **Test fragility from real MemorySupervisor instances.** If the
   builder finds that AC.OSS-M5.5's E2E test requires real-time
   sleeps or wall-clock awaits to exercise the supervisor's probe
   loop, halt and surface — the supervisor's `tick()` is
   directly callable and admits clock injection (verified at plan-
   authoring per `framework/orchestrator/src/loam/orchestrator/supervisor.py:209,218`).
   Mitigation: tests use direct `tick()` calls + injected clock;
   no `asyncio.sleep`-based waits.

---

## 10. Decisions (recommendations locked; recorded for §14 register)

**None requiring owner ruling.** The plan resolves every design
decision via dispatch authority (master plan §5 + dispatch
constraints) + plan-side recommendations.

### D-build.M5.1 — Adapter phase + ordering

**Decision:** `phase=before_orchestrator_start, after=("primary_persona",)`.

**Why this shape:** primary_persona populates `host.orchestrator`
+ `host.scope_runtime` within `before_orchestrator_start`; dormancy
needs both. Same phase, post-primary_persona ordering is the minimal
declaration. Alternative `after_orchestrator_ready` would work but
delays the supervisor probe loop start unnecessarily.

### D-build.M5.2 — Supervisor construction location

**Decision:** inside `dormancy.py` adapter's `contribute()` body
(NOT a new module).

**Why this shape:** the supervisor + bridge are tightly coupled to
the dormancy component's lifecycle (start when component built; stop
when component shut down). Inline keeps the wiring co-located + the
adapter file stays under ~150 LOC. A separate module would be
premature abstraction. Builder may split if the file exceeds 200
LOC at build time.

### D-build.M5.3 — Sync vs async `contribute()`

**Decision:** `async def contribute(self, host)` (the framework's
contribution model awaits coroutines per `spec.py` line 30).

**Why this shape:** the supervisor's `start()` is async; the
component's `reconcile_on_startup` is async; both need to be
awaited. The framework already handles async `contribute()` (per
primary_persona's adapter line 42).

### D-build.M5.4 — Bridge function — `on_transition` vs `on_recovering`+`on_normal`

**Decision:** subscribe via `on_transition(SupervisorTransition)`;
filter on `t.to_state` to determine which dormancy signal to fire.

**Why this shape:** uniform stateful subscription captures every
relevant edge with one callback. `on_recovering` + `on_normal`
shorthands are convenience callables, but using only those two
misses the `degraded` and `escalated` transitions (no
`on_degraded` exists). Per Finding #2.

Bridge mapping:

```
to_state == degraded   → memory_sidecar_down
to_state == escalated  → memory_sidecar_down  (idempotent)
to_state == recovering → no-op  (intermediate state)
to_state == normal     → memory_sidecar_recovered
```

### D-build.M5.5 — Probe function shape + supervisor config

**Decision:** stdlib `urllib.request.urlopen(url, timeout=2.0)`;
returns `ProbeResult(ok=resp.status == 200, latency_ms=...)`. Use
`SupervisorConfig` defaults (no override).

**Why this shape:** mirrors the existing memory_system adapter's
probe pattern (lines 90-91); zero new dependencies. Defaults are
research-§Q2-aligned per `SupervisorConfig` docstring.

### D-build.M5.6 — Sidecar absent → supervisor skip

**Decision:** when `host.memory_sidecar_url is None`, construct
`DegradationComponent` but skip `MemorySupervisor`. Set
`host.memory_supervisor = None`.

**Why this shape:** test workspaces with `launch: False` shouldn't
fail-closed on missing sidecar; the Claude-API detection path stays
active. AC.OSS-M5.6 covers this.

### D-build.M5.7 — Notifier with empty channel list

**Decision:** construct `DegradationNotifier(channels=[])`; rely on
existing queue-on-no-active-channel behaviour. Add inline comment
explaining the contract.

**Why this shape:** dormancy adapter runs BEFORE telegram_interface
adapter (different phases — `before_orchestrator_start` vs
`after_orchestrator_ready`). Channel registry is empty at
construction. The notifier's existing queue behaviour is correct;
no new code required.

### D-build.M5.8 — Sealed-component fence membership

**Decision:** the 3 components — `workspace-bootstrap`, `dormancy`,
`orchestrator`. workspace-bootstrap carries the diff; the other two
bump sidecars only.

**Why this shape:** per dispatch authority + master plan §5 M5 row.
Fence width is dictated by the seal-diff scope; dormancy and
orchestrator carry no source change but their seal-test BASELINEs
must advance to admit the workspace-bootstrap-side wiring.

Alternative considered: 1-component fence (workspace-bootstrap
only). Rejected — dormancy and orchestrator are *consumed* by the
M5 diff; sealing only the consumer allows the producer's seal-diff
test to drift. Three-component fence keeps all consumed surfaces
under explicit baseline-advance rule.

### D-build.M5.9 — HC#4 retire-and-rebaseline

**Decision:** NO RETIRE-AND-REBASELINE.

**Why this shape:** per Finding #6 — the M5 diff is contained in
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/dormancy.py`
+ tests; no HC#4 sample paths are impacted. The HC#4 invariant
should remain GREEN through M5.

---

## 11. Halt-and-surface findings encountered during plan authoring

### Finding #1 — Production-path-vs-test-path separation

**Surface:** the audit's recommendation D-2.a names "wire the
constructor" — but the constructor (`DegradationComponent.build`) IS
already callable; it's just not called in production. The actual gap
is "no production code path calls the constructor." This sounds
trivial but conflates two things: (a) adapter-side wiring (M5 lands
this), (b) verification-that-the-wired-path-is-ACTUALLY-exercised-in-
production (not test-only).

**Resolution:** AC.OSS-M5.5's E2E test exercises the full wired path
through synthesised supervisor probe failures — this is closer to a
production code path than the existing `test_d*` tests (which call
`build` directly with mocked dependencies). The E2E test still uses
synthetic probes (no real sidecar), but it instantiates the *real*
adapters and bridges that production runs. Per the M4 lesson recorded
in `feedback_verify_post_amendment_state`: verify the actual wired
shape, not the test-fixture shape.

### Finding #2 — Asymmetric MemorySupervisor callback surface

**Surface:** `MemorySupervisor` exposes `on_recovering` (no-arg
async) + `on_normal` (no-arg async) + `on_transition(SupervisorTransition)`.
There is no explicit `on_degraded` callback. The supervisor's state
machine (per supervisor.py lines 323-396) transitions are:

  - `normal → degraded` (transient_threshold reached)
  - `degraded → escalated` (escalation_retry_limit reached)
  - `degraded → recovering` (first good probe)
  - `escalated → recovering` (first good probe)
  - `recovering → normal` (recovery_success_threshold reached)
  - `recovering → degraded` (recovery aborted)

To detect "memory down" using only `on_recovering` + `on_normal` is
impossible (those fire on the recovery side).

**Resolution:** D-build.M5.4 + AC.OSS-M5.4 — bridge subscribes via
`on_transition` and filters by `to_state`. Uniform; captures every
relevant edge.

### Finding #3 — MemorySupervisor has no production caller today

**Surface:** verified at plan-authoring:

```
$ grep -rn "MemorySupervisor(" framework/ 2>/dev/null
framework/orchestrator/tests/test_s4_teardown_observability.py:60
framework/orchestrator/tests/test_supervisor.py:77,403
```

Test-only callers. M5 lands the first production caller — inside the
dormancy adapter.

**Resolution:** AC.OSS-M5.3 explicitly authors the production
construction. Recorded for §14.

### Finding #4 — `host.memory_sidecar_url` may be None

**Surface:** the memory_system adapter at line 92 sets
`host.memory_sidecar_url = url` only on health-probe success; if
`launch: False` skips the sidecar entirely, `memory_sidecar_url`
stays None.

**Resolution:** D-build.M5.6 + AC.OSS-M5.6 — short-circuit
supervisor construction when URL is None. DegradationComponent still
constructed (Claude-API detection path stays active).

### Finding #5 — Notifier needs channels; channel registry empty at adapter-run time

**Surface:** `DegradationNotifier`'s `__init__` accepts a `channels`
sequence; it does not require non-empty (per notification.py line
93). When all channels are empty (no active ones), `send()` queues
the notification per existing behaviour (line 119-127). No
construction-time error.

**Resolution:** D-build.M5.7 + AC.OSS-M5.7 — pass the (potentially
empty) `host.channel_registry.values()` filtered to non-group
channels; notifier handles the queue case.

### Finding #6 — No HC#4 byte-content sample paths impacted by M5 diff

**Surface:** the M5 diff is contained in `framework/workspace-bootstrap/`
(adapter + tests). HC#4 sample paths historically include
graceful-degradation sample test fixtures (per feature-usage audit
line 56) and primary-persona dispatch wrapper byte-content. Neither
is touched.

**Resolution:** D-build.M5.9 — NO RETIRE-AND-REBASELINE. HC#4
expected GREEN through M5.

### Finding #7 — `DegradationComponent.tick()` not invoked by the adapter

**Surface:** the component's `tick()` method advances dwelled FSMs
(half_open transitions). Without periodic ticks, the
`memory_sidecar` mode would trip on supervisor-down but never
auto-recover even after a `memory_sidecar_recovered` signal — the
recovery path requires the FSM to be in `half_open` state. However,
per detection.py:324-327, the `record_supervisor_signal(memory_sidecar_recovered)`
calls `fsm.record_success` directly, which can transition from any
state (including `open`) per the FSM's accepted transitions.

**Resolution:** verified at plan-authoring — the supervisor-recovery
short-path bypasses the dwell + half_open + probe flow. AC.OSS-M5.5's
test exercises this. No periodic tick required for the
`memory_sidecar` mode specifically. Other modes (Claude-API down,
overloaded, etc.) DO need ticks for dwell-based recovery; that's a
separate dormant-tick-loop issue not in M5 scope (per §5).

### Finding #8 — `host.memory_supervisor` is a NEW host attribute

**Surface:** `BootstrapHost` (host.py) declares attributes for
`orchestrator`, `scope_runtime`, `dormancy`, etc. There is no
existing `memory_supervisor` attribute.

**Resolution:** the host's open-attribute-surface convention (per
host.py line 65) admits new attributes from contributions. M5
assigns `host.memory_supervisor = supervisor`. Optional but cleaner
to add a typed declaration (`self.memory_supervisor: Any = None`)
in `BootstrapHost.__init__` — but this would expand the
workspace-bootstrap fence. Decision: skip the typed declaration; rely
on the open-attribute convention. Builder records actual choice in
§14.

---

## 12. Method-decision register (placeholder)

(See §14 for the post-build narratives + commit SHAs.)

---

## 13. Test breakdown (post-build)

Seven new test files, total ~350-450 LOC across all seven:

1. **`test_AC_OSS_M5_1_dormancy_adapter_constructs_component.py`** —
   adapter runs against synthesised host; asserts `host.dormancy` is
   a `DegradationComponent` instance.
2. **`test_AC_OSS_M5_2_orchestrator_pause_resume_responds_to_dormancy.py`** —
   integration test: dispatcher.apply triggers `pause_activation`;
   dispatcher.release triggers `resume_activation`.
3. **`test_AC_OSS_M5_3_memory_supervisor_instantiated.py`** — adapter
   constructs `MemorySupervisor` with stub probe; asserts shutdown
   hook registered.
4. **`test_AC_OSS_M5_4_supervisor_bridge_translates_transitions.py`** —
   bridge function maps each `SupervisorTransition.to_state` to the
   correct dormancy signal.
5. **`test_AC_OSS_M5_5_end_to_end_memory_outage_triggers_pipeline.py`** —
   E2E synthetic-probe flow: failure → degraded supervisor → trip
   memory_sidecar mode → pause activation → recovery → resume.
6. **`test_AC_OSS_M5_6_supervisor_skipped_when_no_sidecar.py`** —
   `host.memory_sidecar_url = None` short-circuit; supervisor not
   constructed; component still constructed.
7. **`test_AC_OSS_M5_7_notifier_queues_when_no_channel.py`** —
   notifier constructed with empty channel list; notifications queue
   in-memory; no exception raised.

**No tests in dormancy/ or orchestrator/.** Their internal logic
remains under existing test coverage; M5 tests cover the wiring
layer specifically.

### Cross-tree verification

The adapter imports `loam.dormancy.config.load_config`, `loam.dormancy.component.DegradationComponent`, `loam.dormancy.notification.DegradationNotifier`, `loam.orchestrator.supervisor.MemorySupervisor`, `loam.orchestrator.supervisor.ProbeResult`, `loam.orchestrator.supervisor.SupervisorState`, `loam.orchestrator.supervisor.SupervisorTransition`, `loam.dormancy.errors.DegradationSignal`. All are public exports verified at plan-authoring.

### Backwards-compat verification

- Existing dormancy-source tests pass (build + detection paths
  unchanged).
- Existing orchestrator-source tests pass (supervisor + pause/resume
  hooks unchanged).
- Existing workspace-bootstrap adapter tests pass (other adapters
  unaffected).
- Existing memory_system adapter unchanged (M5 reads but does not
  modify it).

### HC#4 byte-content sample status

NO RETIRE-AND-REBASELINE per §10 D-build.M5.9 + Finding #6.

### Dependents cleared to dispatch (post-M5)

- M6 (dev-sdlc-plugin) — M5 is its critical-path predecessor per
  master plan §6; M6 cleared post-M5.
- M7, M8, M9 — not gated on M5.

---

## 14. Method-decision register (post-build)

(SHA register populated by `loam amend seal --plan-doc` SHA-backfill;
method-decision narratives populated by builder during build.)

### D-build.M5.1 — Adapter phase + ordering

(Populated at build time. Recommendation per §10 D-build.M5.1:
`before_orchestrator_start, after=("primary_persona",)`.)

### D-build.M5.2 — Supervisor construction location

(Populated at build time. Recommendation per §10 D-build.M5.2:
inline in dormancy.py adapter; split if file exceeds 200 LOC.)

### D-build.M5.3 — Sync vs async `contribute()`

(Populated at build time. Recommendation per §10 D-build.M5.3: async.)

### D-build.M5.4 — Bridge subscription model

(Populated at build time. Recommendation per §10 D-build.M5.4:
`on_transition` filtered by `to_state`.)

### D-build.M5.5 — Probe function shape

(Populated at build time. Recommendation per §10 D-build.M5.5:
stdlib urlopen; SupervisorConfig defaults.)

### D-build.M5.6 — Sidecar-absent short-circuit

(Populated at build time. Recommendation per §10 D-build.M5.6: skip
supervisor when URL is None; component still built.)

### D-build.M5.7 — Notifier empty-channel-list

(Populated at build time. Recommendation per §10 D-build.M5.7:
construct with empty list; rely on queue behaviour.)

### D-build.M5.8 — Sealed-component fence

(Populated at build time. Recommendation per §10 D-build.M5.8: 3
components — workspace-bootstrap + dormancy + orchestrator.)

### D-build.M5.9 — HC#4 retire-and-rebaseline

(Populated at build time. Recommendation per §10 D-build.M5.9: NO.)

### Commit SHAs

(post-build per amendment)

- M5 sub-plan + manifest commit: `<TBD>`
- M5 feature commit(s): `<TBD>`
- M5 apply commit: `<TBD>`
- M5 corrective commit(s) (if any): `<TBD>`
- M5 seal commit: `<TBD>`
- M5 §14 backfill commit: `<TBD>`

---

## 15. Backwards-compat verification (post-build)

To be filled by builder post-build.

- All pre-existing tests pass post-amendment (touched-component
  pytest pass; full-repo skipped pre-seal per
  `feedback_amendment_dispatch_speedups`).
- Per-component seal-diff tests pass for all 3 fenced components.
- HC#4 invariant remains GREEN (no rebaseline).
- No new third-party deps (HC#3 analogue).

---

## 16. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause:

1. **Findings #1–#8 in §11** above. None block dispatch; each maps to
   a §10 design decision or §9 halt condition. Recorded for builder
   awareness + §14 method-decision register.
2. **No audit/invariant conflict found.** D-2.a's "wire the
   constructor" recommendation composes cleanly with sealed-component
   invariants. The dormancy adapter is not sealed (it's
   declaration-only — explicitly designed for promotion); the
   orchestrator's pause/resume hooks are public; the supervisor's
   constructor + callbacks are public.
3. **No methodology breach found.** Every AC is outcome-shape;
   method-shape is the builder's call.
4. **No surrounding-code ODD violations found.** The audit's ODD
   §2.5 check (audit line 347) found no code-without-AC surfaces
   under any of the 3 components in the M5 fence.

**Halt summary.** None. Plan is authorised to proceed pending owner
sign-off.

---

*End of plan.*
