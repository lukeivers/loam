# Dormancy — Architecture

**Component:** `dormancy` (loam Phase 2; formerly graceful-degradation pre-M1f rename).
**Ships on `pos-v2` branch at `<workspace>/loam/framework/dormancy/`.**
**Authored against:** `../../docs/rebuild/components/dormancy/{brief,proposal,research}.md`.

---

## Purpose

Detect Claude-upstream failure modes, apply one of four declared
response policies via the sealed orchestrator's hooks, notify the user
via the primary-persona layer's one-on-one channel surface when a
compound-OR blast-radius threshold is crossed, and resume cleanly once
the upstream returns. State is event-sourced in its own SQLite; no
sealed component is amended.

---

## Component map

```
                            ┌─────────────────────────────┐
                            │  Workspace-supplied invoke  │
                            │  (AsyncAnthropic or shim)   │
                            └──────────────┬──────────────┘
                                           │
 pOS LLM callers                           │ Claude API
 (primary-persona authoring,               │
  monitor stuck-reason, pipeline           ▼
  and degradation's own                ┌───────────────┐
  narrative / probe / judge) ───────►  │ ClaudeClient  │   D1
                                       │   (adapter)   │
                                       └───────┬───────┘
                                               │ on_event(AdapterEvent)
                                               ▼
 ┌───────────────────────────────────────────────────────────┐
 │                    DegradationComponent                   │
 │                                                           │
 │  ┌──────────────────────┐    ┌──────────────────────┐     │
 │  │ DegradationDetector  │───►│ 6 × ModeFSM (D2)     │     │
 │  │   (D3 rubrics)       │    │  closed/open/        │     │
 │  │ ├── passive (adapter)│    │  half_open/gated     │     │
 │  │ └── scope-event      │    └─────────┬────────────┘     │
 │  │     subscription     │              │ transition       │
 │  │     (pyee fallback)  │              ▼                  │
 │  └──────────────────────┘    ┌──────────────────────┐     │
 │                              │ PolicyDispatcher     │     │
 │                              │   (D4: P1/P2/P3/P4)  │     │
 │                              └──────────┬───────────┘     │
 │                                         │                  │
 │                              ┌──────────┴──────────┐      │
 │                              ▼                     ▼      │
 │                      pause_activation()     rt.pause/fail │
 │                      (orchestrator hook)    (scope-runtime│
 │                                              public API)  │
 │                                                           │
 │  ┌──────────────────┐   ┌──────────────────────┐          │
 │  │ ThresholdEvaluator│  │ DegradationNotifier  │          │
 │  │ (D5 compound OR)  ├─►│  (D5; one-on-one    │          │
 │  └──────────────────┘   │   OneOnOneChannel)  │          │
 │                         └──────────────────────┘          │
 │                                                           │
 │  ┌──────────────────┐   ┌──────────────────────┐          │
 │  │ NarrativeRenderer │  │ DegradationStore     │          │
 │  │ (D6; Claude or    │  │ (D8 SQLite @         │          │
 │  │  template)        │  │  ~/.loam/            │          │
 │  └──────────────────┘   │   dormancy.sqlite)│          │
 │                         └──────────────────────┘          │
 │                                                           │
 │  OTel emission (D9, A1-safe)                              │
 │  loam.dormancy.{detection_event | fsm_transition |      │
 │  episode_started | episode_resolved | policy_decision |   │
 │  probe_call | notification_dispatched}                    │
 └───────────────────────────────────────────────────────────┘
```

---

## Data flow — representative episode (Down)

```
  t=0        Claude API available. Calls succeed.
  t=10       Claude network drops. Adapter classifies
             APIConnectionError → DegradationSignal.connection_error.
             Detector routes signal into Down FSM. Failures count=1.
  t=12,15    Two more connection failures. Down FSM.should_trip()=True.
             Transition: closed → open. Component._enter_open():
               - episode_id minted
               - PolicyDispatcher.apply(Down, episode_id):
                   • orchestrator.pause_activation(reason)
                   • rt.pause(scope_id) for each LLM-dep active scope
               - store.create_episode(...)
               - active_episodes[Down] = ActiveEpisode(...)
  t=12       Not yet above notification thresholds (10s, 3 scopes).
  t=300+     comp.tick() every time-slice evaluates thresholds.
             elapsed >= 300s → ThresholdTrigger.time. Notification
             rendered (Claude-authored for Rate-limited; template for
             Down — Claude is the failure source here). Tier 2. One
             notification per episode (dedup).
  t=3600     Claude recovers. tick() notices dwell expired (30s ago).
             FSM.open → FSM.half_open. _enter_half_open() probes via
             ClaudeClient.probe(). Probe succeeds.
             Probe result fed into the Down FSM directly. FSM.half_open
             → FSM.closed. _enter_closed() triggers auto_resume (since
             Down is in auto_resume_modes and elapsed < 30min gate).
               - rt.resume(scope_id) for each previously-paused scope
               - orchestrator.resume_activation()
               - store.resolve_episode(episode_id, "auto")
               - resume notification rendered and sent (Tier 2)
```

---

## Relationship map

### Upstream dependencies (consumed, unamended)

- **Orchestrator** (sealed) — `pause_activation(reason)` /
  `resume_activation()` only. Reads the pause state for reconciliation
  on startup.
- **Scope-of-work** (sealed) — `ScopeRuntime.list(states=...)`,
  `.pause(scope_id, reason)`, `.resume(scope_id)`, `.fail(scope_id,
  reason)`, `.get(scope_id)`, `.subscribe_all(callback)`,
  `.per_prompt_costs()`. No amendment.
- **Primary-persona layer** (sealed) — `OneOnOneChannel` type reused
  verbatim; `DegradationChannel` is a nominal subclass. The
  `is_group=False` invariant enforced at construction is reused (v1.2
  R15).
- **Objective tracker** (sealed) — not directly consumed.
- **Memory system** (sealed) — see the "Memory-system detection blind
  spot" note below.

### Downstream dependencies (future)

- **Observability aggregator** — subscribes to the OTel
  `loam.dormancy.*` span namespace. Not required.
- **Self-upgrade framework** — the own SQLite will participate in the
  upgrade-fidelity story via `snapshot_probe()` (v1.1 R1).

---

## Memory-system detection blind spot (documented)

The brief's D1 acceptance states every pOS LLM call routes through the
adapter. Memory-system uses Graphiti's `AnthropicClient` internally
(see `memory-system/src/factory.py:21`). Routing that through this
adapter would require a memory-system amendment, which the brief
prohibits.

**Mitigation:** the degradation component subscribes to scope-of-work's
pyee emitter via `ScopeRuntime.subscribe_all()`. When memory-system's
ingest pipeline fails due to Claude-upstream issues, it surfaces as a
scope `fail` event with a `reason` string naming the underlying cause
(timeout, 429, 401, etc.). The detector's `record_scope_fail()` method
heuristically maps those reasons to DegradationSignals and feeds the
detector via a synthesized AdapterEvent.

This is not as tight as direct adapter routing. The cost: one-call
misses are invisible; degradation detects only when a scope outright
fails. Given memory-system is bulk extraction (one failure typically
fails the whole ingest scope), the supplementary path is adequate for
this release. A future memory-system amendment could tighten it.

**Flagged for Eve's review at seal time.** Not silent deviation — this
is the documented trade-off.

---

## API reference (one-page)

### Module imports

```python
from loam.dormancy import (
    # adapter
    ClaudeClient, ClaudeCallable, LLMResult, ProbeResult,
    # errors + signals
    DegradationSignal, ClaudeAPIError, APIConnectionError, APITimeoutError,
    RateLimitError, OverloadedError, AuthenticationError, BadRequestError,
    InternalServerError, GarbageResponseError, classify_exception,
    # FSM
    FSMState, DegradationMode, ModeFSM,
    # policy
    Policy, PolicyDispatcher,
    # notification
    DegradationChannel, DegradationNotifier,
    NotificationTier, DegradationNotification,
    # config + composition
    DegradationConfig, load_config, DegradationComponent,
)
```

### Core composition

```python
cfg = load_config("~/.loam/dormancy-config.yaml")  # or defaults
comp = DegradationComponent.build(
    cfg=cfg,
    orchestrator=my_orchestrator,          # pause_activation/resume_activation
    scope_runtime=my_scope_runtime,        # scope_of_work.ScopeRuntime
    notifier=DegradationNotifier(channels=[terminal_channel]),
    client=ClaudeClient(invoke=workspace_invoker),
    clock=time.monotonic,                  # injectable for tests
)
# At process startup, after discovering orchestrator's pause state:
plan = await comp.reconcile_on_startup(orchestrator_paused=...)
# Periodically (e.g. from the orchestrator's heartbeat loop):
await comp.tick()
# On incoming scope event (if subscribing):
rt.subscribe_all(comp.on_scope_event)
```

### Key types

| Symbol | Shape |
|---|---|
| `ClaudeClient.call(*, prompt_name, text, model=None)` | returns `LLMResult` |
| `ClaudeClient.probe(timeout=5.0)` | returns `ProbeResult` |
| `DegradationMode` | enum: `down`, `overloaded`, `rate_limited`, `garbage`, `auth_broken`, `latency_sustained` |
| `FSMState` | enum: `closed`, `open`, `half_open`, `gated` |
| `Policy` | enum: `pause_all` (P1), `pause_llm_only` (P2), `fall_through_to_fail` (P3), `request_user_decision` (P4) |
| `NotificationTier` | enum: `tier_1` (audible), `tier_2` (silent) |
| `DegradationNotification` | payload: episode_id, tier, threshold_triggered, text, kind |

### Config surface

```yaml
# ~/.loam/dormancy-config.yaml — workspace override
modes:
  down:
    trip_threshold: {failures: 3, window_seconds: 60}
    half_open_dwell_seconds: 30
    probe_success_requirement: 1
    default_policy: pause_all
  overloaded:
    trip_threshold: {failures: 2, window_seconds: 30}
    half_open_dwell_seconds: 15
    probe_success_requirement: 1
    default_policy: pause_all
  rate_limited:
    trip_threshold: {failures: 1, window_seconds: 1}
    half_open_dwell_seconds: null  # uses retry-after header
    probe_success_requirement: 1
    default_policy: pause_llm_only
  garbage:
    trip_threshold: {failures: 3, window_calls: 10}
    half_open_dwell_seconds: 60
    probe_success_requirement: 2
    default_policy: pause_llm_only
    judge_budget_per_hour: 5
  auth_broken:
    trip_threshold: {failures: 1, window_seconds: 1}
    default_policy: request_user_decision
  latency_sustained:
    trip_threshold: {p95_seconds: 30, window_calls: 20}
    action: emit_signal_only

notification:
  thresholds:
    time_seconds: 300
    paused_scope_count: 3
    auth_broken_immediate: true
  default_tier: 2
  auth_broken_tier: 1
  dedup_per_episode: true

resume:
  auto_resume_modes: [down, overloaded, rate_limited, garbage]
  user_confirm_after_seconds: 1800  # 30-min dwell gate

narrative:
  model: claude-haiku-4-5
  timeout_seconds: 2.0
  fallback_template: "[pOS — claude upstream degraded]\n..."
  recovery_template: "[pOS] Claude upstream recovered. ..."

state:
  sqlite_path: ~/.loam/dormancy.sqlite
```

### Per-scope policy override

Workspaces declare `degradation_policy=<name>` as a constraint on
`ScopeSpec.constraints` to override the mode's default policy for a
specific scope:

```python
ScopeSpec(
    goal="critical task",
    constraints=("degradation_policy=fall_through_to_fail",),
    ...
)
```

A scope is detected as **deterministic** (not paused by P2/P4) if it
declares `deterministic_only=true` in constraints, or if its budget
carries no tokens/money caps.

### OTel span namespace

- `loam.dormancy.claude_call` — per adapter call; carries
  `loam.prompt.type`, `loam.model`, `loam.call_id`, and the embedded
  `loam.dormancy.detection_event` as an event on the span
- `loam.dormancy.fsm_transition` — per state transition
- `loam.dormancy.episode_started` / `.episode_resolved`
- `loam.dormancy.policy_decision`
- `loam.dormancy.probe_call`
- `loam.dormancy.notification_dispatched`

---

## Verification summary (D10)

### One-hour-outage simulation (`test_d10_one_hour_outage.py`)

Time-compressed with an injectable clock; full outage + recovery runs
in milliseconds. All eight invariants pass:

| # | Invariant | Result |
|---|---|---|
| I1 | Scope event log consistency | PASS |
| I2 | No half-ingested memory records | PASS |
| I3 | No orphan OTel spans | PASS |
| I4 | No lost bind_scope events | PASS |
| I5 | Orchestrator pause/resume balanced | PASS (1 pause, 1 resume) |
| I6 | Episode log balanced | PASS (1 started, 1 resolved) |
| I7 | Deterministic scopes not paused under P1 | PASS (0 det scopes paused) |
| I8 | LLM-dependent scopes resumed after recovery | PASS (3 paused → 3 resumed) |

### Garbage false-positive rate (`test_d10_garbage_false_positive.py`)

20 known-good Claude responses across memory-extraction, prose,
structured JSON, code, short acknowledgments, clarifying questions,
technical explanations, and probe-style outputs. Result:

```
GARBAGE FALSE-POSITIVE RATE: 0/20 = 0.00%
```

This is the deterministic-tier result (no LLM-judge). With the
research's 3-of-10 threshold and the regex markers scoped narrowly,
the detector does not flag plausible Claude outputs. Well below the
research-recommended acceptable ceiling of 15%.

A companion true-positive check on 5 known-bad responses (empty,
whitespace-only, three refusal phrasings) catches all 5 — sanity-check
on the other direction.

---

## File index

```
framework/dormancy/
├── pyproject.toml                     # editable install
├── pytest.ini
├── requirements.txt
├── src/
│   ├── __init__.py                    # public surface
│   ├── adapter.py                     # D1
│   ├── component.py                   # D4+D5+D6+D7 composition
│   ├── config.py                      # YAML-backed DegradationConfig
│   ├── detection.py                   # D3 detector + GarbagePipeline
│   ├── errors.py                      # SDK-optional exception taxonomy
│   ├── fsm.py                         # D2 six ModeFSMs
│   ├── notification.py                # D5 threshold + D6 narrative
│   ├── observability.py               # D9 OTel helpers
│   ├── policy.py                      # D4 four-policy dispatcher
│   └── state.py                       # D8 SQLite + reconciliation
├── tests/
│   ├── fakes.py                       # FakeClock, FakeOrchestrator, etc.
│   ├── test_d1_adapter.py
│   ├── test_d2_fsms.py
│   ├── test_d3_detection.py
│   ├── test_d4_policy.py
│   ├── test_d5_notification.py
│   ├── test_d6_narrative.py
│   ├── test_d7_resume.py
│   ├── test_d8_state.py
│   ├── test_d9_observability.py
│   ├── test_d10_one_hour_outage.py
│   └── test_d10_garbage_false_positive.py
└── docs/
    └── architecture.md                # this file
```
