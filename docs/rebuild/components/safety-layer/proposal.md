# Proposal — Safety Layer

**Component:** Safety Layer — deterministic-layer enforcement of kill switches (scope / session / system), the always-ask list, and dangerous-operation gates for irreversible-blast-radius actions.
**Status:** DRAFT — awaiting owner's approval before brief authoring.

**Branch:** `pos-v2`. **Language:** Python 3.13.
**Consumes (no amendment):** scope-of-work, orchestrator, graceful-degradation (pattern only), primary-persona, observability-aggregator.

---

## 1. Objective

Deliver the safety layer as specified in spec v1.0 "Foundational layer — Safety and constraint layer":

> Kill switches at scope-of-work, session, and system level. Categorical "always ask the user" list — short, explicit, testable. Dangerous-operation gates for irreversible-blast-radius actions.
>
> Acceptance:
> - Each kill switch (scope, session, system) is independently testable and stops work within a bounded time.
> - The "always ask" list exists as a testable artifact and is enforced at the deterministic layer.
> - A sample irreversible-blast-radius action is blocked at the gate in a test run.

The design shape and acceptance evidence come from `research.md`; this proposal encodes the decisions the owner has ruled on and states the hard contract the builder works against.

---

## 2. the owner's rulings (locked inputs)

| # | Question | Ruling |
|---|----------|--------|
| 1 | Dangerous-op money threshold | **Tunable with floor.** Framework-configurable default; per-workspace override accepted; minimum floor 1 cent (i.e. any non-zero money budget), default $10 (1000 cents). |
| 2 | System-kill orchestrator behaviour | **Clean exit.** Orchestrator exits 0 via `request_stop`. Next bootstrap refuses to activate until `pos safety clear-system-kill` is run. |
| 3 | Tier-D close-associate category | **Workspace additions only.** Framework floor does not carry a close-associate entry; each workspace's primary persona adds the allowlisted category with per-category policy. |
| 4 | Ask-list timeout granularity | **Freeform duration string.** Schema accepts `Nm`, `Nh`, `Nd` (minutes/hours/days). Schema-enforced **minimum of 15 minutes**. YAML examples default to hour units (e.g. `4h`) to set the right habit. |
| 5 | Ask-gate when `OneOnOneChannel` is unreachable | **Fail-closed.** Gate stays BLOCKED; scope stays `proposed`; next session startup surfaces pending asks. No queue-and-fire, no auto-approve on channel loss. |

---

## 3. Design shape (summary — detail in `research.md`)

### 3.1 Composition

A new package `safety-layer/` (Python, on `pos-v2`) exposes `SafetyController` — the composed runtime. The controller hosts:

- **KillEngine** — three-level kill dispatcher with a single internal code path (`issue_kill(level, reason, source)`) reached by CLI, persona phrase, or IPC call. Uses sealed surfaces: `ScopeRuntime.cancel`, `Orchestrator.pause_activation`, `Orchestrator.request_stop`.
- **AlwaysAskList** — Pydantic-validated YAML at `<workspace>/.pos/safety/always_ask.yaml`. Framework-fixed floor via `FrameworkFloorCategory` enum; workspace additions via open string set; `model_validator` refuses any load that drops a floor category.
- **DangerousOpGate** — stricter gate composed on top of the ask gate. Reads `ScopeSpec.reversibility_class`, `action_class` from `ScopeSpec.constraints`, and `ScopeSpec.budget.money_cents` against the tunable threshold.
- **SafetyStore** — SQLite at `~/.pos/safety/safety.sqlite`. Tables: `ask_decisions`, `kill_events`, `system_kill_state`.
- **Notification** — sends asks and gate-fires via `OneOnOneChannel` from `primary_persona.introduction` (inherits the `is_group=True` rejection; no group-channel escape).
- **CLI** — `pos kill {scope|session|system}`, `pos safety resume-session`, `pos safety clear-system-kill`, `pos safety status`.
- **Observability** — emits `pos.safety.*` spans via the aggregator's registered provider.

### 3.2 Integration — IPC-wrapping pattern

The workspace bootstrap wraps the IPC handler for `activate_scope`: the handler calls `SafetyController.check_gates(spec)` before forwarding to `orchestrator.activate_scope(...)`. The orchestrator object is untouched; the wrap is consumption of the sealed `IPCServer.register` surface. **This is the only composition path that does not amend a sealed component** — any alternative that reaches inside the orchestrator is a halt-signal condition.

Kill IPC methods (`kill_scope`, `kill_session`, `kill_system`, `ask_gate_decide`, `safety_status`) register on the same `IPCServer`.

### 3.3 Kill-switch surfaces and time budgets

| Level | Surfaces | Two-step confirm? | p95 time budget |
|-------|----------|-------------------|-----------------|
| Scope | CLI `pos kill scope <id>`; persona phrase ("halt scope X"); IPC `kill_scope` | No | 500ms |
| Session | CLI `pos kill session`; persona phrase ("halt session"); IPC `kill_session` | No | 2s |
| System | CLI `pos kill system --yes-really`; persona phrase (LLM-mediated confirm); IPC `kill_system` with nonce | Yes (mandatory) | 5s |

Scope-kill is terminal and non-reversible by design (cancelled is terminal in scope-of-work). Session-kill is reversible via `resume-session`. System-kill requires explicit `clear-system-kill` to allow the next orchestrator start to activate anything.

### 3.4 Framework-floor ask categories (shipped default)

Seven entries mapped from spec v1.0 Prime Rule 6 high-stakes-irreversible set:
`commit_external_funds`, `send_communication_as_user_to_third_party`, `strategy_pivot_or_mission_change`, `personal_life_judgment_call`, `destroy_user_data_beyond_workspace`, `publish_to_public_surface_user_does_not_control`, `modify_production_systems_serving_real_users`.

A `dangerous_op_subset` (framework-fixed, workspace cannot extend) marks which floor categories additionally trigger the stricter dangerous-op gate.

---

## 4. Acceptance criteria

Each criterion is an ODD objective — tests are authored against it directly, not against behaviours in aggregate. Negative cases that the research surfaced are re-extended as positive objectives here.

### 4.1 Kill-switch acceptance (spec clause a)

- **A1.** Scope kill issued against an active scope transitions the scope and its TERMINATE-policy children to `cancelled` within 500ms p95. Emits `pos.safety.scope_kill` span with level + reason + source. Writes a `kill_events` row.
- **A2.** Session kill calls `pause_activation("safety:session_kill")`, cancels every active scope, writes `kill_events`, emits OTel, within 2s p95.
- **A3.** System kill requires the two-step confirm (CLI `--yes-really`, IPC nonce token, persona LLM-mediated confirm). On commit: pause + cancel all scopes + write `system_kill_state` row + call `request_stop`. Within 5s p95.
- **A4.** Next orchestrator bootstrap reads `system_kill_state` and refuses to activate any scope until `clear-system-kill` is run and records a `system_kill_cleared` row.
- **A5.** A wedged scope (stubbed slow LLM adapter, 10s awaitable) does not exceed the p95 budget at levels A1–A3 for the **issuance** of the kill; the kill initiates within budget even if the wedged task has not yet returned. (Documents the "bounded-time-to-initiate vs bounded-time-to-liveness" distinction surfaced in research §11.)

### 4.2 Always-ask list acceptance (spec clause b)

- **A6.** Loading a `always_ask.yaml` that omits any framework-floor category raises a Pydantic validation error at load time. Scope activation refuses on a safety-controller initialisation failure (fail-closed).
- **A7.** A scope whose `constraints` declare `action_class=commit_external_funds` and has no matching approval in `ask_decisions` → `check_ask_gate` returns BLOCK; `activate_scope` IPC returns `-32040 ask_gate_pending`; the scope stays `proposed`.
- **A8.** User replying "approve" via the `ask_gate_decide` IPC writes a row to `ask_decisions` with `expires_at = now + timeout`. A subsequent `activate_scope` for the same spec hash passes the gate.
- **A9.** Timeout is a schema-validated duration string (`Nm|Nh|Nd`) with a 15-minute minimum. `5m` or `0h` entries fail load; `15m`, `4h`, `2d` accepted.
- **A10.** When no reachable `OneOnOneChannel` exists at gate-fire time, the gate returns BLOCK and no notification is queued. The scope stays `proposed`; `pos safety status` surfaces it. (Locks ruling #5.)

### 4.3 Dangerous-op gate acceptance (spec clause c)

- **A11.** A scope with `reversibility_class=irreversible` and `action_class=send_communication_as_user_to_third_party` triggers the dangerous-op gate; gate returns BLOCK with four-option response set rendered in the notification.
- **A12.** A scope claiming `reversibility_class=fully_reversible` but with `budget.money_cents >= threshold` (default 1000) triggers the gate under clause 3 of the research's decision procedure.
- **A13.** The threshold is read from `safety.yaml` config with the framework-default 1000 cents and a minimum floor of 1 cent. Workspace may tune above the floor.
- **A14.** Gate BLOCK ⇒ `activate_scope` returns `-32041 dangerous_op_gate_blocked`; scope stays `proposed`. Approved-one-time decisions bind to `ScopeSpec.structural_hash()` and do not extend across spec mutations.

### 4.4 Integration acceptance (cross-cutting)

- **A15.** IPC-wrapping gate composition does not mutate the orchestrator object. A clean reconstruction of the orchestrator without the safety wrapper produces identical behaviour to pre-safety-layer `pos-v2`.
- **A16.** OTel emission flows through the observability aggregator's registered provider. The safety layer does not construct its own `TracerProvider`.
- **A17.** `OneOnOneChannel` with `is_group=True` is refused at channel construction. No group-channel escape paths in the safety layer's code.
- **A18.** Zero imports from `current pOS` rules-file machinery. Zero references to legacy Ruby safety constructs.

### 4.5 Structural-impossibility acceptance (defence-in-depth)

- **A19.** A hand-crafted `always_ask.yaml` with `framework_floor: []` is refused at load. A workspace that attempts to monkey-patch `FrameworkFloorCategory` at runtime does not change the gate's behaviour because the gate reads the validated model, not the enum directly. (Tests the clause-(g)-style structural check, not the runtime guard.)

---

## 5. Constraints

- **Python 3.13; `pos-v2` branch.** Permitted runtime dependencies: stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. Test-only: pytest, pytest-asyncio.
- **No amendments to sealed components.** If the builder concludes an amendment is required, halt and signal — do not proceed. Signal format: named component + named surface + the alternative considered before halting.
- **Deterministic-layer enforcement.** Always-ask list and dangerous-op gate are structural checks (Pydantic-validated schema, pure-function match). No LLM inference inside either gate. The only LLM surface is the primary persona rendering the ask to the user, which happens outside the gate.
- **One-on-one notification channel only.** Reuses `OneOnOneChannel` from `primary_persona.introduction`. No group channels, ever.
- **Fail-closed on notification loss.** (Locks ruling #5.)
- **Safety always wins.** Collision with graceful-degradation resolves to safety's action; degradation records "superseded by safety" on its own episode.
- **No carryover from current pOS.** Rules-file machinery is not referenced.
- **Max-first.** LLM inference inside the safety layer itself is unexpected and must be justified explicitly if introduced.
- **Halt-on-deviation.** Deviating from this proposal without explicit approval is forbidden; halt and signal.

---

## 6. File structure (expected)

```
safety-layer/
  src/
    controller.py        # SafetyController — composed runtime
    kill.py              # KillEngine — three-level dispatcher
    ask_list.py          # AlwaysAskList Pydantic schema + loader
    dangerous_op.py      # DangerousOpGate decision procedure
    store.py             # SQLite store
    events.py            # SafetyEvent Pydantic models
    action_class.py      # FrameworkFloorCategory enum
    notification.py      # Safety notifications via OneOnOneChannel
    cli.py               # `pos kill`, `pos safety ...` commands
    observability.py     # OTel emission
    config.py            # safety.yaml loader with threshold defaults
  tests/
    test_kill_scope.py
    test_kill_session.py
    test_kill_system.py
    test_ask_gate_floor.py
    test_ask_gate_workspace_additions.py
    test_ask_gate_timeout_granularity.py   # ruling #4
    test_ask_gate_fail_closed.py           # ruling #5
    test_dangerous_op_gate.py
    test_dangerous_op_threshold_tunable.py # ruling #1
    test_system_kill_clean_exit.py         # ruling #2
    test_structural_enforcement.py
    test_timing_bounded.py
    test_safety_beats_degradation.py
    test_no_sealed_amendments.py           # A15
```

File layout is the builder's judgement to adjust where internal cohesion argues for it. The `tests/` list is the minimum set mapped to the acceptance criteria; additional tests welcomed, none removed.

---

## 7. Build phases and estimate

**Calibrated AI-time estimate: 25–35 minutes wall-clock.** Anchored to self-upgrade (~25 min) and graceful-degradation (~20 min). The safety layer has less surface area than either (no FSMs, no conflict detection, no JSONL tailer). If the build exceeds 40 minutes, the failure class to investigate is **scope creep**, not undersized estimate — halt and signal rather than extend.

Suggested phase shape (builder's call to refine):

1. Pydantic schemas (`action_class.py`, `events.py`, `ask_list.py`, `config.py`) and loader with structural validators — A6, A9, A19.
2. Store (`store.py`) and its schema migrations.
3. KillEngine (`kill.py`) with three-level dispatcher — A1, A2, A3, A4, A5.
4. Gates (`dangerous_op.py`) and their composition — A7, A8, A10, A11, A12, A13, A14.
5. Notification (`notification.py`) and LLM-rendered ask templates.
6. IPC registration + activation wrapping (in workspace bootstrap) — A15.
7. CLI (`cli.py`).
8. Observability (`observability.py`) — A16.
9. Tests for every A-criterion above.

One atomic commit per phase is acceptable; a single commit for the whole build is also acceptable if cohesion argues for it.

---

## 8. inferences recorded — flagged for the builder to challenge

These items are not direct quotes from the owner and represent the primary persona's reading. The builder may challenge any of them with a halt signal and a proposed alternative:

- **Floor threshold of 1 cent on ruling #1.** feedback recorded "tunable with floor." I inferred a minimum floor of 1 cent to prevent a workspace dialing the threshold to zero (which would turn every money-budgeted scope into a dangerous-op). If the intent was "tunable without floor" or "tunable with a floor the user specifies," challenge and halt.
- **15-minute minimum on ruling #4.** feedback recorded "option 3 sounds good." Option 3 in the conversation specified a 15-minute floor. If the builder believes a different floor (e.g. 5 minutes or 30 minutes) serves the acceptance better, challenge.
- **`clear-system-kill` as the gesture name.** the primary persona's label. The builder may name the command otherwise (`pos safety reset-system`, `pos safety unkill`) if idiomatic Python-CLI conventions argue against "clear."
- **Seven framework-floor categories as the shipping default.** The research proposed seven mapped from Prime Rule 6. I have not asked the owner to ratify each individually. If any entry feels out of place (e.g. `strategy_pivot_or_mission_change` as an action class rather than a governance event), challenge.
- **Session-kill cancels every active scope (not just the current session's).** The orchestrator is single-process; there is one activation surface. I'm treating "session" as "everything currently running under this orchestrator instance." If "session" was intended at a finer granularity (e.g. the user's active conversation vs background scopes), challenge.
- **Persona-phrase regex set.** Five scope-kill phrases and three session-kill phrases enumerated in research §4. The builder's actual persona-phrase discipline may want a different set.
- **`ScopeSpec.structural_hash()` exists as a scope-of-work surface.** The research plan referenced it; if it doesn't exist on `pos-v2`, the builder halts and signals (this is one of the repeated "verify-against-code" failure modes I'm watching for).
- **Two-step IPC nonce for system-kill.** Research proposed a `kill_system_request` / `kill_system(nonce)` two-call pattern. If a cleaner pattern exists in the orchestrator's IPC surface (e.g. a confirm-token parameter on a single call), the builder may substitute.

---

## 9. Approval ask

sign-off on this proposal moves the component to `proposal_approved` and opens handoff-brief drafting. On brief review, the background agent is dispatched.

Specifically requesting approval of:

- The locked rulings in §2 as faithful to the conversation.
- The acceptance criteria in §4 as the complete ODD objective set.
- The constraints in §5 (no amendments, fail-closed, safety-wins, no carryover).
- The 25–35 min AI-time estimate.
- the primary persona's flagged inferences in §8 (approve as written, or adjust and re-land).

Approve as-is, approve with changes, or reject.
