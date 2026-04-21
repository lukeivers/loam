# Research — Safety Layer

**Component:** Safety Layer — deterministic-layer enforcement of kill switches (scope / session / system), the "always ask" list, and dangerous-operation gates for irreversible-blast-radius actions.

**Status:** research draft, ready for proposal.
**Authored by:** general-purpose research agent, 2026-04-19.
**Branch:** `pos-v2`.
**Consumes (no amendment):** scope-of-work, orchestrator, graceful-degradation, primary-persona, observability-aggregator.

---

## 0. Factual corrections to the research plan (read first)

Two assertions in the research plan that the agent must surface before the proposal stage:

1. **`halt-cascade` is NOT a public surface on scope-of-work.** The research plan says scope-of-work's public surface "includes `cancel(scope_id)`, `halt-cascade`, reversibility_class field." Inspection of `pos-v2/scope-of-work/src/runtime.py` shows only `cancel(scope_id, reason)` is exposed; cascade behaviour is built *into* `cancel` via `_cascade_to_children` and is governed by each child's `ParentClosePolicy` (default `TERMINATE`). There is no separate `halt-cascade` or `halt_cascade` symbol anywhere in the scope-of-work package (grep confirmed). The design below treats `cancel` as the scope-level kill surface and relies on the TERMINATE default to cascade. This is not a halt signal — it is a correction to the surface description. No amendment needed.

2. **`SIGTERM handling` is on the orchestrator process, not a public safety surface.** The orchestrator installs `SIGTERM/SIGINT` handlers in `_install_signal_handlers()` that set `_stop_event` and drive graceful shutdown (`orchestrator.py:282-296`). There is a test hook `request_stop()` that triggers the same event. These are process-lifecycle concerns, not a user-facing kill surface — but they are the mechanism a system-level kill uses to terminate the orchestrator.

No component amendments required as a result of these corrections.

---

## 1. Survey of existing patterns

### 1.1 OS-level kill switches

- **SIGTERM / SIGINT / SIGKILL** — classical process termination. SIGTERM is catchable and allows graceful shutdown; SIGKILL bypasses userspace and is uninterruptible. Ctrl-C delivers SIGINT to the foreground process group. The orchestrator already installs SIGTERM+SIGINT handlers; SIGKILL is the OS's "big red button" for a stuck process.
- **Ctrl-C in a terminal** — the canonical "stop what you're doing" gesture. Non-technical users know this one; they do not know `pkill -9`.
- **macOS "Force Quit" (Cmd-Opt-Esc)** — system-level panic button with graphical affordance.
- **Physical emergency stops** (industrial, automotive) — unmissable colour, position, shape; single action commits; reset requires deliberate action.

Lesson for pOS: the *system-level* kill must be reachable from a state where the user has lost confidence in the running software. A CLI subcommand nobody remembers at 3am is the wrong surface for system-kill. Multiple redundant surfaces (CLI + conversation + signal) are appropriate because the user's mental state during a kill is the worst-case for discovery.

### 1.2 Approval-gate patterns

- **sudo** — elevates one command; prompts for password; timeout invalidates the grant. Clear scope (the command), clear audit (syslog), clear reversal (exit).
- **OAuth scopes** — each permission is named, auditable, and independently revocable. The app declares; the user grants or refuses; grants are revocable post-hoc.
- **Deploy-gate approvals** (GitHub, Vercel, Fly): a human must click "approve" before a promotion happens. Approval attributes to the individual and is recorded.
- **iOS "Allow" / "Don't Allow" dialogs** — first-use blocking; subsequent runs silent; revocable in settings.

Lesson for pOS: approval gates need (a) a specific, named action ("commit $47 on Claude API tokens for next 30m"), (b) a short timeout, (c) an audit record of who approved and when, (d) a revocation path. The "always ask" list and dangerous-op gate both fit this pattern.

### 1.3 Deterministic pre-check patterns in AI agents

- **Constitutional AI** (Anthropic) — a rubric the model self-evaluates against before acting. This is advisory at the model layer; pOS rejects this pattern for safety because an LLM can reason around it.
- **Tool-use permission models** (Claude Code `settings.json` permissions, OpenAI Assistants "required approval" on tools) — the *host* decides whether a tool call proceeds, independent of the model. The model's intent does not grant permission; only the host does. This matches pOS's "deterministic-layer enforcement" requirement exactly.
- **Claude's built-in refusal patterns** — the model declines some classes of action. Useful but unaudited by the host; pOS cannot rely on this as the primary gate because the model is not a pOS-controlled surface.
- **Pydantic-at-the-boundary** — the pattern self-upgrade's clause (g) uses: `Resolution` enum has no `skipped` value, so YAML parsing structurally cannot produce a skipped resolution. This is the template the safety layer adopts for the always-ask list and the dangerous-op gate.

Lesson for pOS: the always-ask list must be a Pydantic-validated schema that an LLM's "reasoning" cannot route around — the *structural impossibility* pattern from clause (g). An LLM can say any words; a Pydantic validator can refuse to construct any object whose `action_class` matches an entry on the ask list without a matching `user_decision` that a structural check confirms was authored by the user (not the LLM).

---

## 2. Recommended design shape

### 2.1 Three kill switches — surface and propagation

**Surface per level** (recommended):

| Level  | User surface                                                                                                   | Propagates to                                                                 |
|--------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Scope  | `pos kill scope <id>` CLI; primary-persona phrase ("halt scope X"); IPC method `kill_scope`                    | `ScopeRuntime.cancel(scope_id)` → TERMINATE cascade to children               |
| Session| `pos kill session` CLI; primary-persona phrase ("stop everything", "halt session"); IPC method `kill_session`  | `Orchestrator.pause_activation("safety:session_kill")` + cancel each active scope |
| System | `pos kill system --yes-really` CLI (two-step); SIGTERM to orchestrator; IPC method `kill_system` (double-ack)  | pause_activation + cancel all scopes + write terminal `system_killed` event + `Orchestrator.request_stop()` |

The three surfaces share a single internal dispatcher, `SafetyController.issue_kill(level, reason, source)`. Consolidation is deliberate: all three channels must reach the same code path so that the audit record and observability shape are identical regardless of entry point.

**Why all three surfaces for every level:**

- CLI is reliable and scriptable; the user knows the command exists because onboarding taught them. Non-tech users at 3am won't remember arguments, so each command is short and the help text is bold.
- Primary-persona conversation is the fastest path for the user currently in-session. The persona listens for a small set of phrases ("stop", "halt", "emergency stop", "kill session", "kill system") and on match, calls the same IPC method. This is a convenience surface — if it fails (model down), the CLI is unaffected.
- IPC method exists so the kill is testable without shelling out and so a workspace-local GUI (future) can invoke it.

**Bounded-time commitment** (recommended targets):

| Level  | Time budget        | Measurement                                                                                   |
|--------|--------------------|-----------------------------------------------------------------------------------------------|
| Scope  | ≤ 500ms p95        | From `issue_kill` call to `ScopeState.cancelled` on the target scope + its children            |
| Session| ≤ 2s p95           | From `issue_kill` call to all non-terminal scopes in `cancelled` state + `paused_reason` set   |
| System | ≤ 5s p95           | From `issue_kill` call to orchestrator `_stop_event.set()` returning + terminal event written  |

These are runtime targets, not hard guarantees — a wedged LLM call holds a Python task until its awaitable returns. The safety layer's job is to *initiate* halt within the budget; whether the sub-task drops the CPU is a separate liveness question (the "prototyping priorities" section below surfaces this).

**Measurement methodology:** a test fixture constructs a runtime with N active scopes, calls `issue_kill(level)`, then polls the projection every 10ms until all target states match. The test records the wall-clock from issue to satisfied.

**State preservation on kill:**

- Scope-level kill: scope transitions to `cancelled`; the event log preserves every event emitted before the cancel. Scope cannot be resumed (cancelled is terminal); user rebuilds from a new scope if desired. Budget refunds are NOT automatic — the refund semantic is workspace policy, not a safety-layer concern.
- Session-level kill: all active scopes go to `cancelled`; `pause_activation` prevents new activations until `resume_activation` or orchestrator restart. State is preserved; the session can resume (see reversibility below).
- System-level kill: same as session-level for the scope state, then the orchestrator process exits via `request_stop`. Next orchestrator start reads the terminal `system_killed` event and refuses to auto-resume until the user runs `pos safety clear-system-kill` (explicit gesture — see anti-accidental-kill below).

**Kill reversibility:**

- Scope kill: *not* reversible — `cancelled` is terminal in scope-of-work's state machine. Intentional: a cancelled scope was cancelled for a reason; silently reviving it would lose the audit record. User starts a new scope.
- Session kill: reversible via `pos safety resume-session`. Calls `orchestrator.resume_activation()`. Because cancelled scopes are terminal, resume lets *new* scopes activate again but does not un-cancel.
- System kill: reversible only by an explicit `pos safety clear-system-kill` followed by an orchestrator restart. The clear-system-kill command writes a `system_kill_cleared` event with the user's reason; the orchestrator's bootstrap checks this before activating anything else.

### 2.2 Always-ask list — the testable artifact

**Concretely, it is:**

- A Pydantic-validated YAML file at `<workspace>/.pos/safety/always_ask.yaml`.
- Framework-fixed *floor* — a short list of categories the framework hard-codes and a workspace cannot remove.
- Workspace-tunable *additions* — the workspace may add categories above the floor.
- Structurally enforced via a Pydantic `ActionClass` enum (floor) + open string set (workspace additions) + a runtime check that every queued action is matched against the union.

**Floor categories** (framework-fixed, shipping default):

```yaml
# Framework floor — shipped in pOS core, not workspace-removable.
framework_floor:
  - commit_external_funds
  - send_communication_as_user_to_third_party
  - strategy_pivot_or_mission_change
  - personal_life_judgment_call
  - destroy_user_data_beyond_workspace
  - publish_to_public_surface_user_does_not_control
  - modify_production_systems_serving_real_users

# Workspace additions — tunable; listed here for example.
workspace_additions: []
```

These are the seven categories from spec v1.0 Prime Rule 6 (high-stakes irreversible actions) mapped onto verbs. The taxonomy intentionally mirrors the Tier A / Tier B gates from `prior-pOS .claude/rules/security.md` so the workspace and framework are not expressing the same concept in two incompatible vocabularies.

**Deterministic-layer enforcement — where the gate sits:**

Before any scope activation that declares an `action_class` matching the ask list, the orchestrator's `activate_scope` path calls `SafetyController.check_ask_gate(scope_spec)`. The check:

1. Reads the scope's declared action classes from `ScopeSpec.constraints` (workspaces encode them as constraint strings of the form `action_class=<value>` — same pattern graceful-degradation uses for per-scope policy overrides; no scope-of-work amendment).
2. Matches against the merged always-ask list.
3. If any match, consults the ask-resolution store (SQLite at `~/.pos/safety/safety.sqlite`, table `ask_decisions`) for an existing unexpired approval.
4. If no unexpired approval exists, **returns a `GateRefusal`** that the orchestrator propagates as an IPC error (`-32040 ask_gate_pending`). The scope stays `proposed`; no scope activation happens.
5. Simultaneously, the controller dispatches a structured ask to the primary-persona one-on-one channel (reuses `OneOnOneChannel` from `primary_persona.introduction`; same group-channel rejection).
6. The user's response (via Telegram reply, CLI, or persona) writes a row into `ask_decisions` with `scope_id`, `decision`, `timestamp`, `expires_at`, `reasoning`.
7. A later `activate_scope` call rechecks the store and proceeds if the decision is `approved` and not expired.

**Why this placement (not `scope_runtime.start`):** the check must happen before the orchestrator binds the scope to its objective (binding is the expensive part — creates events, acquires OTel spans). Placing it in `activate_scope` before `bind_scope` also means the refusal is visible at the IPC layer so a workspace-local GUI sees it cleanly.

**Response protocol:**

- Default timeout: 4 hours (matches the Tier-1 notification criterion in `communication-routing.md` — "time-sensitive decisions under 4 hours"). Configurable per-category.
- Timeout behaviour: the request is marked `expired` in `ask_decisions`; the scope stays `proposed`; no auto-approve, no auto-refuse. The user sees on next session startup: "N scopes waiting on safety approval."
- Approval can be one-time (binds to `scope_id`) or category-wide for a bounded window (e.g. "approve commit_external_funds for the next 30 minutes"). Category-wide approvals still write per-scope decisions for audit; the shortcut is a UI sugar.

**LLM use inside the gate — none.** The match between scope spec's `action_class` and the ask list is pure string comparison. No LLM inference. The only LLM surface is the primary persona *rendering* the ask prompt for the user, and that happens outside the gate.

### 2.3 Dangerous-operation gate — blast-radius enforcement

**Operational definition:** an action is *dangerous* when any of the following hold:

1. The enclosing scope's `reversibility_class` is `irreversible`.
2. The scope's `action_class` (from constraints) matches a framework-fixed dangerous-op set — a subset of the always-ask list focused on actions that cannot be retracted (`commit_external_funds`, `send_communication_as_user_to_third_party`, `publish_to_public_surface_user_does_not_control`, `destroy_user_data_beyond_workspace`).
3. The scope's budget ceiling for money exceeds a framework-configurable threshold (default $10 — also tunable per workspace).

Clauses 1+2 alone cover the "seven behaviours" from spec v1.0 Prime Rule 6. Clause 3 is added because a scope that *claims* `fully_reversible` but has a $1000 money budget is lying; the blast-radius check refuses that lie.

**Relationship to the always-ask list:** the dangerous-op gate is a *stricter* gate composed on top of the ask gate. Every dangerous-op action is also an ask-list action; not every ask-list action is dangerous. The gate stacks:

```
activate_scope
  → SafetyController.check_ask_gate(spec)       (always-ask list)
  → SafetyController.check_dangerous_op(spec)    (stricter — irreversibility check)
  → bind_scope → scope_runtime.start
```

**Where the gate sits:** same place as the ask gate — pre-activation, inside `Orchestrator.activate_scope`. Both gates are pure functions of the scope spec + decision store state, which means they are testable without a real scope runtime and cheap enough to run on every dispatch.

**Is the gate integrated with `reversibility_class`?** Yes, via clause 1 above. The scope-of-work primitive declares the class at construction; the safety layer reads it on activation. This is consumption-only.

**"Sunk LLM spend before the gate fires" question:** in the recommended placement, the gate fires *before* any bind, so no tokens are spent on the work itself. The tokens spent *composing* the scope spec are separate (workspace authors scopes via LLM calls upstream). The safety layer does not need a refund semantic because it does not cause refundable work.

**User-facing message on gate fire:**

```
[Safety gate — dangerous operation]
Scope: {scope_id}
Goal: {spec.goal}
Classification: irreversible (reversibility_class) + {action_classes}
Budget committed if approved: {money_cents_display} + {tokens_display} + {time_display}

Approve once        → one-shot approval, this scope only
Approve + allowlist → add {category} to workspace allowlist for {duration}
Refuse              → scope cancels immediately; audit record written
Refuse + denylist   → add {category} to workspace denylist; scope cancels

Reply with: approve / approve-allowlist / refuse / refuse-denylist
```

Rendered text lives in a template module (no LLM); the primary persona adapts tone via its own session behaviour when it relays the message.

### 2.4 Architecture shape

**Internal structure:**

```
safety-layer/
  src/
    controller.py        # SafetyController — the composed runtime
    kill.py              # KillEngine — three-level kill issuance
    ask_list.py          # AlwaysAskList — Pydantic-validated YAML + runtime check
    dangerous_op.py      # DangerousOpGate — stricter gate composed on top
    store.py             # SQLite at ~/.pos/safety/safety.sqlite
    events.py            # SafetyEvent Pydantic models (Pydantic enum over action types)
    action_class.py      # ActionClass enum (framework floor) + string-extensible
    notification.py      # SafetyNotification via OneOnOneChannel (sibling of degradation)
    cli.py               # `pos safety ...` commands
    observability.py     # OTel emission
  tests/
    test_kill_scope.py
    test_kill_session.py
    test_kill_system.py
    test_ask_gate_floor.py
    test_ask_gate_workspace_additions.py
    test_dangerous_op_gate.py
    test_structural_enforcement.py   # the "LLM cannot reason around the enum" test
    test_timing_bounded.py
```

**Composition at the orchestrator layer:** the orchestrator bootstrap constructs `SafetyController(scope_runtime, objective_tracker, channels, store_path, config)` once, and registers a pre-activation hook that runs `controller.check_gates(spec)` inside `activate_scope`. This is new bootstrap wiring — the orchestrator's `activate_scope` signature does not change; the safety layer hooks in by monkeypatching the method? **No.** Monkeypatching a sealed component is forbidden in spirit even if not in letter.

Instead: the safety layer exposes `SafetyController.gate(scope_spec) -> GateOutcome`. The workspace bootstrap, which already constructs the orchestrator, wires the gate by **calling it before IPC method registration** — the safety layer registers its own IPC methods (`kill_scope`, `kill_session`, `kill_system`, `ask_gate_decide`, `safety_status`) on the same `IPCServer`, and those methods close over the shared `SafetyController`. For the *activation-path gate*, the workspace bootstrap wraps the orchestrator's `activate_scope` call at the IPC handler layer — the orchestrator object itself is untouched; the IPC handler reads `method == "activate_scope"`, calls `controller.check_gates(params)` first, then forwards to `orchestrator.activate_scope(...)` on pass. Wrapping at the IPC layer is consumption of the sealed IPC surface (`register()`), not amendment of the orchestrator.

**This is the critical design decision.** An alternative is to amend the orchestrator to expose a pre-activation hook point. That would be an amendment to a sealed component — forbidden. The IPC-wrapping pattern is the only path that composes the gate without amending any sealed surface.

---

## 3. Clause-by-clause spec coverage

Every v1.0 Safety acceptance criterion, mapped to the piece of the design that delivers it:

| Spec clause                                                                                  | Design piece                                                            |
|----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| (a) Each kill switch (scope/session/system) independently testable                           | `kill.py` exposes three separate methods; `test_kill_*.py` per level    |
| (a) Each kill stops work within a bounded time                                               | Targets in §2.1; `test_timing_bounded.py` measures per level             |
| (b) "Always ask" list exists as a testable artifact                                          | `ask_list.py` loads `<workspace>/.pos/safety/always_ask.yaml` + `ActionClass` enum; `test_ask_gate_floor.py` |
| (b) Enforced at the deterministic layer                                                      | Pydantic validation on load; pure-function match at `check_ask_gate`; `test_structural_enforcement.py` |
| (c) Sample irreversible-blast-radius action blocked at gate in a test                        | `test_dangerous_op_gate.py` — constructs irreversible scope, activates, asserts gate refused |

v1.1 R11 (OTel emission) — `observability.py` emits `pos.safety.*` spans; the aggregator ingests via its in-process SpanExporter (no aggregator change needed — it already subscribes via `register_otel_provider`).

v1.2 R15 (one-on-one channel only) — `notification.py` uses `OneOnOneChannel` verbatim from `primary_persona.introduction`; the `is_group=True` rejection at `__post_init__` is inherited; a `DangerousOpChannel` subclass inherits the guard (same pattern as `DegradationChannel`). No group-channel escape hatch anywhere.

---

## 4. Kill-switch invocation surface specification

**Scope kill:**

- CLI: `pos kill scope <scope_id> [--reason "text"]` — one-step commit. Scope kills are frequent and localised; two-step confirm would cause kill fatigue.
- Persona phrase: "halt scope X" / "kill scope X" / "stop scope X" — persona maps via regex → IPC `kill_scope`.
- IPC: `kill_scope(scope_id, reason)` over Unix socket.

**Session kill:**

- CLI: `pos kill session [--reason "text"]` — one-step commit *within the active session*. Session kills are rarer than scope kills but the user is still in the session context and knows the blast radius.
- Persona phrase: "halt session" / "stop everything" / "emergency stop" — persona matches and calls IPC.
- IPC: `kill_session(reason)`.

**System kill:**

- CLI: `pos kill system --yes-really --reason "text"` — two-step commit via the `--yes-really` flag. A stray `pos kill system` refuses and prints a message naming the flag required. This is the anti-accidental-fire discipline for the highest-blast-radius level.
- Persona phrase: "kill system" / "shut down pos" — persona does NOT relay directly. Instead, it sends a confirm prompt back to the user: "This will stop every scope, pause all activation, and exit the orchestrator process. Reply 'yes kill system' to confirm." This is deliberate two-step, LLM-mediated, matching the CLI's `--yes-really`.
- IPC: `kill_system(reason, confirm_token)` where `confirm_token` must equal a short-lived nonce the server issued on a prior `kill_system_request` call. No single IPC call can initiate and commit a system kill.

**Discoverability:**

- The `pos` CLI's top-level `--help` lists `kill` as a first-class verb (not buried under `pos safety kill`).
- Onboarding explicitly demonstrates scope-kill and session-kill on a synthetic scope; system-kill is named in docs but not demonstrated (demonstration would require orchestrator restart mid-onboarding).
- The primary persona, on any session's startup briefing, prints a one-line reminder in its first N sessions of calibration: "You can say 'halt scope', 'halt session', or 'kill system' at any time."

**Anti-accidental-fire:**

- Scope kill: no confirm, one-step. Wrong cancellations are recoverable (start a new scope).
- Session kill: no confirm, one-step. Wrong cancellations are recoverable (resume activation + start new scopes).
- System kill: two-step mandatory (`--yes-really` flag on CLI; nonce token on IPC; LLM-mediated confirm prompt on persona phrase). The orchestrator *refuses* to auto-restart after a system kill — user must explicitly clear.

---

## 5. Always-ask list — format + default contents

**YAML schema:**

```yaml
# ~/.pos/safety/always_ask.yaml  (workspace-local)
version: 1

framework_floor:
  # Shipped fixed — workspace cannot override or remove.
  # These map to the seven Tier A/B categories in security.md rule 6.
  - action_class: commit_external_funds
    default_timeout_hours: 4
    description: "Committing the user's money or spending Claude API tokens above budget"

  - action_class: send_communication_as_user_to_third_party
    default_timeout_hours: 4
    description: "Sending email, message, or comment that could be read as the user's voice"

  - action_class: strategy_pivot_or_mission_change
    default_timeout_hours: 24
    description: "Changing the workspace's stated direction or abandoning a project"

  - action_class: personal_life_judgment_call
    default_timeout_hours: 24
    description: "Decisions affecting the user's relationships, health, or personal standing"

  - action_class: destroy_user_data_beyond_workspace
    default_timeout_hours: 4
    description: "Deleting files outside ~/<workspace> or dropping databases"

  - action_class: publish_to_public_surface_user_does_not_control
    default_timeout_hours: 4
    description: "Posting to social media, public git, app stores, or public blog"

  - action_class: modify_production_systems_serving_real_users
    default_timeout_hours: 4
    description: "Deployments, DNS changes, infra modifications that affect real users"

workspace_additions:
  # Tunable by the workspace — authored or extended by primary persona with user approval.
  # Example entries:
  # - action_class: send_telegram_to_allowlisted_close_associate
  #   default_timeout_hours: 1
  #   description: "Close-associate messages are Tier D; still gated per v1.2 R15 policy."

dangerous_op_subset:
  # Which framework_floor categories trigger the dangerous-op gate's stricter check.
  # This is a framework-fixed subset; workspace cannot add to it.
  - commit_external_funds
  - send_communication_as_user_to_third_party
  - publish_to_public_surface_user_does_not_control
  - destroy_user_data_beyond_workspace
  - modify_production_systems_serving_real_users
```

**Pydantic shape** (`ask_list.py`):

```python
class FrameworkFloorCategory(str, Enum):
    commit_external_funds = "commit_external_funds"
    send_communication_as_user_to_third_party = "send_communication_as_user_to_third_party"
    strategy_pivot_or_mission_change = "strategy_pivot_or_mission_change"
    personal_life_judgment_call = "personal_life_judgment_call"
    destroy_user_data_beyond_workspace = "destroy_user_data_beyond_workspace"
    publish_to_public_surface_user_does_not_control = "publish_to_public_surface_user_does_not_control"
    modify_production_systems_serving_real_users = "modify_production_systems_serving_real_users"

class AskListEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    action_class: str
    default_timeout_hours: int = Field(ge=1)
    description: str = Field(min_length=1)

class AlwaysAskList(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal[1]
    framework_floor: tuple[AskListEntry, ...]
    workspace_additions: tuple[AskListEntry, ...]
    dangerous_op_subset: tuple[FrameworkFloorCategory, ...]

    @model_validator(mode="after")
    def _floor_cannot_shrink(self) -> "AlwaysAskList":
        floor_classes = {e.action_class for e in self.framework_floor}
        required = {c.value for c in FrameworkFloorCategory}
        missing = required - floor_classes
        if missing:
            raise ValueError(
                f"AlwaysAskList framework_floor missing required categories: {missing}. "
                "The floor cannot be reduced below the framework-fixed set."
            )
        return self
```

**Structural enforcement logic:** the validator refuses any YAML that drops a floor category. A workspace cannot "remove" a category by commenting it out — the loader rejects the file and no activation proceeds (fail-closed). This is the clause-(g) pattern applied to ask-list integrity: structural impossibility, not runtime nagging.

---

## 6. Dangerous-operation gate — specification

**Signals read:**

1. `ScopeSpec.reversibility_class` — from scope-of-work spec (direct field read).
2. `ScopeSpec.constraints` — workspace-encoded `action_class=<value>` entries (same mechanism graceful-degradation uses for `degradation_policy`).
3. `ScopeSpec.budget.money_cents` — compared against framework-configurable threshold.

**Decision procedure** (`dangerous_op.py::check`):

```python
def check(spec: ScopeSpec, ask_list: AlwaysAskList, threshold_cents: int) -> GateOutcome:
    classes = _extract_action_classes(spec.constraints)
    is_irreversible = spec.reversibility_class == ReversibilityClass.irreversible
    has_dangerous_class = any(c in ask_list.dangerous_op_subset_values() for c in classes)
    exceeds_money = (spec.budget.money_cents or 0) >= threshold_cents

    if not (is_irreversible or has_dangerous_class or exceeds_money):
        return GateOutcome.PASS

    # gate fires; look up existing approval
    decision = store.find_approval_for(
        scope_spec_hash=spec.structural_hash(),
        not_expired=True,
    )
    if decision is None or decision.state != "approved":
        return GateOutcome.BLOCK
    return GateOutcome.PASS
```

**Placement:** inside `SafetyController.check_gates`, called by the IPC-wrapping layer *before* `orchestrator.activate_scope` is invoked. Gate fires on the scope spec; LLM has not yet been called for the work.

**Output of a blocked gate:** a JSON-RPC error `-32041 dangerous_op_gate_blocked` with `data` carrying the gate's classification + the ask sent to the user.

---

## 7. Integration sequence diagrams

### 7.1 User-initiated scope kill

```
user           pos-cli      safety-ctrl    scope-runtime   objective-tracker
 |               |               |               |               |
 |  "pos kill scope s-42"        |               |               |
 |-------------->|               |               |               |
 |               |  IPC kill_scope("s-42")       |               |
 |               |-------------->|               |               |
 |               |               | cancel("s-42")|               |
 |               |               |-------------->|               |
 |               |               |               | _cascade_to_children
 |               |               |               |<------------->|
 |               |               |               |  (TERMINATE)  |
 |               |               |<-- ok ---------               |
 |               |               | append_event(safety_kill_issued, level="scope")
 |               |               | emit OTel pos.safety.scope_kill
 |               |<-- ok ---------               |               |
 |  "scope cancelled"            |               |               |
 |<--------------|               |               |               |
```

### 7.2 User-initiated session kill

```
user         pos-cli      safety-ctrl    orchestrator   scope-runtime
 |             |               |               |               |
 |  "pos kill session"         |               |               |
 |------------>|               |               |               |
 |             |  IPC kill_session             |               |
 |             |-------------->|               |               |
 |             |               | pause_activation("safety:session_kill")
 |             |               |-------------->|               |
 |             |               |               |               |
 |             |               | list(active scopes)           |
 |             |               |<------------->|               |
 |             |               | for each: cancel(sid)         |
 |             |               |------------------------->----->|
 |             |               | append_event(safety_kill_issued, level="session")
 |             |               | emit OTel pos.safety.session_kill
 |             |<-- ok --------|               |               |
 |  ...        |               |               |               |
```

### 7.3 Always-ask gate firing

```
workspace-caller      ipc-wrap       safety-ctrl      ask-store      primary-persona     user
 |                     |               |                |                  |               |
 |  activate_scope(spec)                |                |                  |               |
 |-------------------->|               |                |                  |               |
 |                     | check_gates(spec)              |                  |               |
 |                     |-------------->|                |                  |               |
 |                     |               | extract action_classes            |               |
 |                     |               | match ask list                    |               |
 |                     |               | find_approval(hash)               |               |
 |                     |               |--------------->|                  |               |
 |                     |               |<-- none -------|                  |               |
 |                     |               | dispatch ask via OneOnOneChannel  |               |
 |                     |               |------------------------------->----               |
 |                     |               |                |                  | send(text)    |
 |                     |               |                |                  |---------------|
 |                     |<-- BLOCK -----|                |                  |               |
 |                     |                                |                  |  reply        |
 |<-- -32040 --+       |                                |                  |<--------------|
              ...       |                                |                  |               |
                       | (later) IPC ask_gate_decide(scope_id, "approve")  |               |
                       |<----------------------------------------------------               |
                       | record_decision                |                  |               |
                       | (user retries activate_scope)  |                  |               |
```

### 7.4 Dangerous-op gate firing

Identical to 7.3 until the check; the user-facing message carries the extra blast-radius classification and the four-option response set.

---

## 8. Relationship to graceful-degradation

**Recommendation: the two share the `OneOnOneChannel` abstraction and the `pause_activation` consumer pattern, but they are semantically distinct and MUST keep separate identities.**

- Safety is user-initiated (the user triggers; the system obeys).
- Degradation is Claude-initiated (Claude misbehaves; the system pauses).

Sharing infrastructure below is explicit and bounded:

| Shared                                               | Separate                                                        |
|------------------------------------------------------|------------------------------------------------------------------|
| `OneOnOneChannel` type (via `primary_persona`)        | `SafetyController` vs `DegradationComponent` — no shared state   |
| `pause_activation` / `resume_activation` hook pattern | Reason strings: `"safety:session_kill"` vs `"degradation:down"`  |
| OTel emission via aggregator's SpanExporter           | Separate tracer names: `pos.safety_layer` vs `pos.graceful_degradation` |
| SQLite per component                                  | `~/.pos/safety/safety.sqlite` vs `~/.pos/degradation/*`          |

Collisions between the two (e.g. degradation paused activation for "down" and then user issues system kill) resolve by principle: **safety always wins**. A system kill during a degradation pause succeeds (session kill + orchestrator stop); the degradation episode records "superseded by system_kill" on its own episode row. The reason strings are distinct so the audit trail is unambiguous.

---

## 9. Dependency map

**Consumed by:**

- **Self-correction loop** (future Phase 3) — uses the ask-list to ensure correction-authoring that crosses Tier A/B fires the gate.
- **Reversibility primitive** (future) — reads the safety layer's dangerous-op classification when upgrading a `fully_reversible` scope to `compensatable` or `irreversible`.
- **Cost ceiling enforcement** (future) — the money-cents threshold in dangerous-op gate §2.3 clause 3 is the hand-off point.

**Depends on (consumption, no amendment):**

| Sealed component          | Surface used                                              |
|---------------------------|-----------------------------------------------------------|
| scope-of-work              | `ScopeRuntime.cancel`, `ScopeRuntime.list`, `ScopeRuntime.get`, `ScopeSpec.reversibility_class`, `ScopeSpec.budget`, `ScopeSpec.constraints`, `ReversibilityClass` enum |
| orchestrator              | `Orchestrator.pause_activation`, `Orchestrator.resume_activation`, `Orchestrator.request_stop`, `IPCServer.register`, `ApplicationError` |
| graceful-degradation      | (none — pattern parallel, not consumer of the component)  |
| primary-persona           | `OneOnOneChannel` type, `ChannelKind` enum                |
| objective-tracker          | (none)                                                    |
| observability-aggregator  | OTel via `register_otel_provider` (already global)        |
| self-upgrade              | (none)                                                    |
| memory-system             | (none — audit lives in safety's own SQLite)               |

**No amendments required.** All access is through sealed public surfaces.

---

## 10. Complexity estimate

**AI-time estimate for the build: 25–35 AI-minutes.**

Anchored to observed completions on `pos-v2`:

- self-upgrade: full build ~25 min wall-clock (the owner's anchor).
- graceful-degradation: ~20 min wall-clock (the owner's anchor).
- The safety layer is structurally simpler than either: no FSMs, no conflict detection/rollback, no JSONL tailer. The work is (a) a Pydantic-validated YAML loader, (b) a three-level kill dispatcher that calls existing surfaces, (c) an IPC-wrapping gate composition, (d) a SQLite decision store, (e) the usual OTel + tests.

**I am pushing back on the research plan's "400–550 AI-min → 40–55 min calibrated wall-clock" band.** That band is larger than both anchor components above, and the safety layer has less surface area than either. The 25–35 min range I am proposing is below the plan's low end — a deliberate signal that this component is simpler than it sounds, not a stretch estimate.

If the build actually takes 40+ minutes, the failure class to investigate is "I wrote more surface than the spec required" (scope creep), not "the component was larger than estimated."

---

## 11. Prototyping priorities

Five questions only a prototype can answer with confidence:

1. **System-kill bounded-time under a wedged LLM call.** If the orchestrator has a scope whose current task is awaiting a long Claude API call, how long does `request_stop` take to return? Needs a prototype with a stubbed slow-adapter and a measured `issue_kill(system)`.

2. **IPC-wrapping gate latency.** The per-activation gate adds IPC-local overhead on every `activate_scope`. Measure p95 added latency; if > 50ms, the wrapping pattern needs to move into a more tightly-coupled structure (likely the bootstrap's orchestrator-factory closure).

3. **Primary-persona phrase recognition.** The persona "halt scope X" pattern is easy to state but depends on the persona's prompt discipline. Needs a test fixture that runs several real persona interactions and measures false-positive + false-negative rates on the phrase set.

4. **Ask-list expiry-under-session-gap semantics.** If the user is approved for a category at T=0, session dies at T=1h, new session at T=5h — should the approval still apply? Default proposed: yes if within the category's timeout; prototype measures whether that feels right to the user in practice.

5. **Deterministic match against a workspace-authored action_class.** The `action_class=<value>` constraint-string pattern needs to be readable by the gate without a per-workspace schema. A prototype with three distinct workspaces (minimal, complex, adversarial) confirms the scan is robust.

---

## Open questions surfacing from this research

Questions the proposal stage will need to resolve — flagged now so the owner can rule before implementation:

1. **Should the dangerous-op gate's money threshold be fixed (e.g. $10) or per-workspace-tunable with a framework floor (minimum $1, maximum open)?** Recommendation: tunable with floor. Needs ruling recorded.

2. **On system-kill, does the orchestrator exit (exit 0) or remain alive in a terminal `killed` state awaiting `clear-system-kill`?** Recommendation: exit cleanly; startup checks the terminal event and refuses to activate until cleared. Alternative: remain alive but refuse every activation. The exit path is simpler and more OS-conventional.

3. **Close-associates Tier-D category** — should `send_telegram_to_allowlisted_close_associate` be in the framework floor or the workspace additions? Current v1.0 security.md rule 6 lists it as an explicit close-associate exception. Recommendation: workspace additions (framework doesn't know the allowlist); the framework's `send_communication_as_user_to_third_party` category covers the broader case.

4. **Timeout granularity.** `default_timeout_hours: int` — is hour granularity sufficient, or should the schema accept minutes? Recommendation: int-hours is sufficient for the ask-list (timeouts are rough); minutes are overkill and invite bikeshedding.

5. **What happens when primary persona is unloaded (pre-R14 authoring) and an ask gate fires?** The gate needs a channel to dispatch to. Recommendation: fail-closed — if no `OneOnOneChannel` is reachable, the gate stays BLOCKED and the scope stays `proposed`; safety status surfaces the pending ask. This matches degradation's queue-and-fire pattern.

---

**End of research.** Proposal stage can proceed on the basis of this document.
