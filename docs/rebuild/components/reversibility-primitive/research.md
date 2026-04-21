# Research — Reversibility Primitive

**Component:** Reversibility Primitive — promotes `ScopeSpec.reversibility_class` from a passive declaration to an active structural contract with compensation paths, rollback records, and telemetry for reversible-vs-irreversible path choice.

**Status:** research draft, ready for proposal.
**Authored by:** general-purpose research agent, 2026-04-19.
**Branch:** `pos-v2`.
**Consumes (no amendment):** scope-of-work, safety-layer, orchestrator, observability-aggregator, primary-persona-loader (for the one-on-one channel on user-facing rollback surfaces).

---

## 0. Factual confirmations and corrections (read first)

The research plan's factual claims against `pos-v2` were verified by direct inspection. One confirmation, one clarification, no amendment cases.

1. **`ReversibilityClass` enum with three values is present** — `pos-v2/scope-of-work/src/spec.py` lines 50-53 confirm `fully_reversible | compensatable | irreversible` exactly as the plan describes. `ScopeSpec.reversibility_class` is a required field (no default, line 293). Plan's assertion verified.

2. **`ReversibilityTrigger` already exists on scope-of-work** — `spec.py` lines 243-253 expose a `ReversibilityTrigger` discriminated-union member whose `match_class` defaults to `irreversible`. The comment in the sealed code explicitly anticipates the safety layer seeding this trigger. The reversibility primitive can re-use the same trigger as a consumer for path-choice or escalation telemetry — no new trigger kind needed and no ScopeSpec amendment.

3. **Safety layer reads `reversibility_class` as a gate input** — verified at `safety-layer/src/dangerous_op.py` line 76-77: `if spec.reversibility_class == ReversibilityClass.irreversible: reasons.append("irreversible")`. The irreversible class currently causes the dangerous-op gate to fire. The reversibility-primitive refusal must compose **cleanly** with this — see §8.

4. **Sidecar precedent is mature on `pos-v2`** — verified two independent precedents:
   - `objective-tracker/src/store.py` lines 55-61 defines `scope_objective_binding` SQL sidecar with its own append API (`bind_scope` in `runtime.py:466`).
   - `safety-layer/src/events.py` `structural_hash(spec)` helper uses `spec.model_dump_json()` rather than amending ScopeSpec with a `structural_hash()` method.
   - `safety-layer/src/ipc_wiring.py` wraps the shared `IPCServer`'s `activate_scope` handler by capturing `orig_activate = server._handlers.get("activate_scope")`, registering a new handler, and forwarding within.

**Conclusion:** No factual corrections; no amendments required; the sidecar/wrap pattern is directly applicable.

---

## 1. Survey of existing patterns

### 1.1 Database transactions and compensation

- **2PC (two-phase commit)** — preparer/committer protocol. Holds locks until commit or abort. Not applicable to pOS: external actions (email, DNS, API calls to foreign systems) cannot "prepare without committing" — once the email's been sent, the action is committed from the outside world's perspective.
- **Saga pattern** (Garcia-Molina 1987, re-popularised by microservices) — a long-running transaction decomposed into a sequence of local transactions, each paired with a compensating transaction that semantically undoes it. Orchestrated sagas use a central coordinator; choreographed sagas use event-driven peer coordination. **This is the closest prior art** for pOS's "compensation path" concept: the compensation is explicit, declarative, and invoked on failure. Key lesson: compensations are *semantic* undos, not byte-level rollbacks — they restore system-observable state, not physical history.
- **3PC (three-phase commit)** — adds a pre-commit step to reduce blocking. Still inapplicable (same external-action problem).
- **Database CHECKPOINT + ROLLBACK** — journal-driven. The scope-of-work event log already records every scope transition — a "reversible via event log alone" scope could theoretically be replayed backward, but physical-world consequences don't rewind. This is where `fully_reversible` vs `compensatable` differ.

### 1.2 Undo/redo systems

- **Command pattern** (Gang of Four) — every action is a `Command` object with `execute()` and `undo()`. Commands stack; undo pops. pOS's compensation path is a specific case: the `undo()` method of a command class, registered by string handle.
- **Memento pattern** — store snapshot of state before action; restore snapshot on undo. The scope-of-work projection + event log already enables this — given an event-id, replay to that point produces the prior projection. But memento-style undo fails for external actions (you cannot re-shred a sent email by restoring a pre-send memento).
- **CRDT operational transforms** — commutative-replica data types allow concurrent edits to converge; inversion is structural. Not applicable: pOS does not model collaborative text, it models imperative actions.

**Lesson:** pOS needs *command-pattern-with-registration*, not memento: the compensation is a first-class callable registered at scope authoring, not a "restore this state" instruction.

### 1.3 SOA / service-oriented compensation

- **AWS Step Functions "compensation"** — each state in the state machine can declare a catch/retry/compensate branch. Compensation is a parallel state machine that runs when forward progress fails.
- **Temporal workflows** — "compensations" are explicit Activity calls, typically registered in a `defer`-style block so that workflow failure triggers them in reverse order. The registration happens at code-authoring time, not at spec time; compensations are Turing-complete.
- **Camunda BPMN** — compensation events model "what to do if this step has to be undone", attached to specific tasks.

**Lesson:** compensation in SOA is *invoked*, not *automatic*. A compensation is a callable the system invokes when the trigger fires; pOS must define both the registration surface and the invocation trigger.

### 1.4 Functional-programming effect handlers

- **Algebraic effects** (Eff, Koka, OCaml 5) — effects are declared in the type signature; handlers provide concrete implementations including reversal logic. Clean separation of "effect declaration" from "effect handling". The `irreversible` class in pOS is analogous to declaring an un-pure effect.
- **Monadic transactions** (STM in Haskell) — pure computations compose trivially; irreversibility appears at the I/O boundary. pOS inherits this: scope internals may be pure, but the scope-of-work transitions (activate, debit budget, emit events) are effectful.

**Lesson:** treat the reversibility class as an effect declaration. A scope declaring `irreversible` is declaring "I perform a non-reversible effect" — the system's response is to refuse activation unless a compensation handler is registered.

### 1.5 Version control: git revert vs git reset

- **`git revert <commit>`** — creates a new commit that inverts the target commit's changes. History is preserved; the revert is itself auditable. **This is the `compensatable` pattern:** the original action is not erased; a forward action undoes its effect.
- **`git reset --hard <commit>`** — rewrites history to the named commit; the previous commits are unreachable. **This is the `fully_reversible` pattern:** the action is erased from history.
- **`git push --force`** — irreversible on published branches (other repos may have already pulled). **This is the `irreversible` pattern.** Git does not forbid `--force`; it requires an explicit flag. This is the exact model pOS should adopt: irreversible actions require an explicit approval (the equivalent of the flag), not a refusal to exist.

**Lesson:** pOS should not forbid `irreversible`-classified scopes. It should refuse to activate them silently. Either (a) the safety layer's dangerous-op gate approves (the owner acknowledged the irreversibility) or (b) the reversibility primitive confirms a compensation path is registered (the system has a semantic-undo plan). Both are structurally enforced; neither requires LLM judgment at runtime.

---

## 2. Recommended design shape

One section per question group from the plan.

### 2.1 Compensation path — the contract (Q1-5)

**Recommended shape:** `CompensationPathBinding` is a Pydantic record persisted in the reversibility primitive's sidecar table keyed on `scope_id`. The compensation path itself is a **registered callable handle** — the same pattern scope-of-work already uses for `Observer.callback_handle`.

**Pydantic record:**

```python
class CompensationPathBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_id: str = Field(min_length=1)
    handle: str = Field(min_length=1)  # registered callable key
    description: str = ""               # human-readable; surfaced in rollback UI
    budget_seconds: int | None = Field(default=None, ge=1)  # optional rollback time cap
    idempotency_key: str = Field(min_length=1)  # stable id for dedupe on re-invocation
    registered_at: str                  # ISO-8601 UTC
    registered_by: str = "user"         # "user" | persona handle

    @model_validator(mode="after")
    def _non_empty_handle(self) -> "CompensationPathBinding":
        if not self.handle.strip():
            raise ValueError("handle must be non-empty")
        return self
```

**Q1 — what is a compensation path concretely?** A registered callable. The workspace calls `ReversibilityController.register_handler(handle: str, fn: Callable[[RollbackContext], Awaitable[RollbackResult]])` at startup (same shape as `ScopeRuntime.register_callback`). The binding references the handle by string; the runtime resolves it at rollback time.

Rejected alternatives:
- *Full scope spec that activates on rollback* — tempting but heavier than needed; creates a recursion hazard (rollback scope's own rollback). Also, compensation-as-scope couples rollback lifecycle to the scope-of-work state machine, which is the wrong granularity — a compensation is a single atomic semantic-undo, not a multi-stage workflow.
- *Declarative YAML of actions to undo* — not Turing-complete. Real compensations need to read committed state (scope events) and make decisions. YAML-only rules out the harder cases.

The handle pattern covers the easy case (declarative compensation via a registered handler that reads a YAML config) and the hard case (complex compensation reading arbitrary state). **Adopt: handle-only, workspace extends via custom registrations if they want YAML.**

**Q2 — where is the compensation path declared?** In the sidecar, **not** on `ScopeSpec`. Two registration surfaces, both producing the same sidecar row:

1. **IPC method `reversibility.register_compensation`** — used at scope authoring time (typically from the workspace's scope-authoring layer). Payload: `{scope_id, handle, description, budget_seconds?, idempotency_key}`. Returns `{ok: True, binding_id}`.
2. **CLI `pos reversibility bind <scope_id> --handle <name>`** — for manual/recovery use. Same fields as IPC.

No change to ScopeSpec. The scope author declares `reversibility_class` at spec construction (existing contract); the workspace registers the compensation path separately. Authoring order is workspace-visible: the workspace must call `register_compensation` *before* activating any `compensatable` or `irreversible` scope, or the activation wrap refuses.

**Q3 — what happens at activation of `irreversible` without a compensation path?** The reversibility-primitive **activation wrap** refuses with error code `-32050 REVERSIBILITY_MISSING_COMPENSATION`. This is distinct from safety's dangerous-op block:

- Safety's `irreversible` path (existing `DangerousOpGate`) fires because *any* irreversible scope needs owner approval. It blocks with `-32041 DANGEROUS_OP_GATE_BLOCKED` until an approved ask-gate decision exists.
- Reversibility's path checks "is there a compensation path *registered*?" It blocks with `-32050 REVERSIBILITY_MISSING_COMPENSATION` when the class is `compensatable` or `irreversible` AND no binding exists.

Gate ordering: reversibility-primitive wrap runs **before** safety's wrap. Rationale: missing-compensation is a structural contract failure — the scope was declared incorrectly by the authoring layer. Safety's dangerous-op is an owner-approval gate. If the contract is broken, there's nothing for the owner to approve. See §8 for the full ordering diagram.

**Q4 — how does compensation reference committed state?** Via a `RollbackContext` passed to the handler:

```python
@dataclass(frozen=True)
class RollbackContext:
    scope_id: str
    scope_spec: ScopeSpec                 # read-only
    events: tuple[ScopeEvent, ...]        # full event log for the scope
    projection: ScopeProjection           # public projection at rollback time
    idempotency_key: str
    invocation_id: str                    # UUID, stable across retries
```

The context is built by the reversibility runtime at rollback invocation time by reading the scope-of-work projection and event stream via existing public surfaces (`ScopeRuntime.store.events_for(scope_id)`, `ScopeRuntime._public(...)`). No new scope-of-work surfaces.

**Q5 — what if compensation itself fails?** The handler returns a `RollbackResult`:

```python
class RollbackResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["succeeded", "failed", "degraded"]
    narrative: str = ""            # what the handler did; surfaced in audit
    compensated_at: str            # ISO-8601 UTC
    recoverable: bool = False      # may be retried
```

On `failed`, the primitive writes a `rollback_failed` event to its own log and surfaces a Tier-1 notification to the one-on-one channel. The primary persona's introduction-channel rule applies (no group-channel rollback prompts). If `recoverable=True`, a retry is permitted via explicit IPC call; if `False`, human intervention is required. No automatic retry loop — exponential-backoff retry of a failed compensation could compound the damage.

### 2.2 Rollback invocation (Q6-9)

**Q6 — what triggers rollback?** Four defined triggers, three implemented at foundation-level, one deferred to self-correction:

| Trigger | Implementer | Mechanism |
|---------|-------------|-----------|
| Scope calls `rollback()` during own runtime | Reversibility primitive | IPC `reversibility.rollback_scope {scope_id, reason}` |
| Parent cascade on child failure | Scope-of-work + reversibility | Subscribe to pyee emitter; on `StateTransitioned(to=failed)` of a child whose `ParentClosePolicy=TERMINATE` and which has a registered compensation path, invoke rollback |
| User issues `pos rollback scope <id>` | Reversibility CLI | Same IPC as scope-initiated |
| Self-correction loop detects error | Deferred to self-correction component | Out of scope for the reversibility primitive; exposed as the same IPC method |

The pyee subscription in the cascade case is a **consumer** of scope-of-work's emitter (`ScopeRuntime.subscribe_all`) — same pattern objective-tracker uses for `scope_success` auto-evaluation (`objective-tracker/src/runtime.py:659 _bind_scope_success_listener`). No amendment to scope-of-work.

**Q7 — is rollback idempotent?** Yes, by construction. The `idempotency_key` on `CompensationPathBinding` is the dedupe key. The reversibility store has a `rollback_invocations` table keyed on `(scope_id, idempotency_key)`. A second `rollback_scope` call with the same key returns the prior result (no re-invocation). A different key for the same scope is rejected — a scope has one registered binding; to rollback twice, the workspace must register two bindings (which is legitimate for multi-stage undo scenarios but rare).

**Q8 — rollback state machine and terminal states.** The scope-of-work state machine is sealed. The reversibility primitive **does not** add a new scope state. Instead, rollback is recorded as an **event**: the scope moves to `cancelled` via existing `ScopeRuntime.cancel(scope_id, reason="rollback_invoked")` and the reversibility store writes a parallel `RollbackInvoked` event in its own log.

The reversibility store's rollback lifecycle is its own small state machine, independent of scope-of-work:

```
requested → in_progress → {succeeded | failed | degraded}
```

Represented as a typed event stream:

```python
class RollbackRequested(BaseModel): ...
class RollbackInProgress(BaseModel): ...
class RollbackSucceeded(BaseModel): ...
class RollbackFailed(BaseModel): ...
class RollbackDegraded(BaseModel): ...
```

All frozen Pydantic models with `extra="forbid"`, persisted as JSON in SQLite (same pattern as safety and objective-tracker). The scope-of-work view sees only a `cancelled` scope with a `reason` field; the reversibility view sees the full invocation lifecycle.

**Q9 — rollback budget / time limit.** Optional per-binding `budget_seconds`. When set, the runtime wraps the handler in `asyncio.wait_for(fn(ctx), timeout=budget_seconds)`. On timeout, the invocation records `failed` with `narrative="timeout"`. Default: no timeout — a compensation is semantic; it runs as long as it needs. The optional cap is for workspaces that prefer a bounded time envelope.

### 2.3 `compensatable` vs `fully_reversible` distinction (Q10-12)

**Q10 — concrete difference in declaration.** Sealed `ReversibilityClass` has three values. The reversibility primitive imposes **structural constraints on the sidecar binding**, not on the ScopeSpec itself:

| `reversibility_class` | Binding required? | Rollback invocation source |
|-----------------------|-------------------|----------------------------|
| `fully_reversible` | **Optional.** Binding permitted but redundant (the event log is sufficient). | Event-log replay reconstructs state; if a binding is registered, it is preferred. |
| `compensatable` | **Required.** Binding must be registered *before* activation. | Handler invocation. |
| `irreversible` | **One of:** binding registered OR safety-layer dangerous-op approval. | If binding exists, same as `compensatable`; if no binding and dangerous-op-approved, rollback is best-effort (records "acknowledged irreversible, no compensation possible" event). |

The `irreversible` row is the interesting one: it captures the owner's "two refusal shapes" (research plan §99) cleanly. An irreversible scope without a compensation path is acceptable *only* with explicit dangerous-op approval — matching git's `--force` pattern (§1.5).

**Q11 — should the primitive enforce the distinction?** Yes, at the activation wrap. Pseudocode:

```python
async def reversibility_check_gates(spec, scope_id, store):
    binding = store.get_binding(scope_id)
    cls = spec.reversibility_class

    if cls == ReversibilityClass.fully_reversible:
        return  # pass

    if cls == ReversibilityClass.compensatable:
        if binding is None:
            raise ApplicationError(REVERSIBILITY_MISSING_COMPENSATION,
                f"compensatable scope {scope_id} has no compensation path registered")
        return

    # irreversible: binding OR dangerous-op approval
    # Note: dangerous-op approval is checked by safety's wrap AFTER this one.
    # Here we only refuse if there's no binding AND no approval. We can
    # peek at safety's store via an injected resolver — see §8 for ordering.
    if binding is None and not safety_has_active_approval(spec):
        raise ApplicationError(REVERSIBILITY_MISSING_COMPENSATION,
            f"irreversible scope {scope_id} requires compensation path OR dangerous-op approval")
```

The `fully_reversible + binding` case is not an error — it is permitted but logged as `binding_redundant=true` in telemetry so the workspace can audit over-declared compensations.

**Q12 — preference ordering.** Three classes, three ranks, preference high-to-low: `fully_reversible > compensatable > irreversible`. The path-choice chooser (§2.4) records each alternative's class and prefers the highest rank by default. **Rationale:** `fully_reversible` has structurally less risk than `compensatable` (undo-via-log is cheaper and more reliable than semantic compensation); both are less risky than `irreversible`. Workspace may override the ranking with an explicit preference flag on the chooser call.

### 2.4 Path-choice preference and telemetry (Q13-16)

**Q13 — where does path choice happen?** Three candidates, **all valid at different layers**:

- **Scope authoring (LLM-surface):** the LLM authoring a scope chooses which of several candidate implementations to propose. This is a workspace-layer concern (the LLM is the one making the choice) — the primitive provides the *telemetry hooks* and the *recommendation surface* but does not make the choice itself.
- **Planning (multi-scope plans):** when a plan has alternative subplans with different reversibility classes, the planner chooses. Again workspace-layer.
- **Dispatch (orchestrator routing):** if multiple implementations of the same scope exist, the dispatcher picks one. The primitive provides the ordering function.

**Recommended:** the reversibility primitive exposes **one** function — `rank_alternatives(alternatives: Sequence[ScopeSpec]) -> RankedAlternatives` — that workspace callers at any layer use. The function is pure (deterministic, no side effects except an OTel span emission). The caller *invokes* the ranking; the primitive does not intercept any scope flow. This matches the "max-first" constraint — no LLM inference inside the primitive.

**Q14 — "same declared outcome" operationally.** Out of scope for the primitive. The caller is responsible for declaring that two `ScopeSpec`s are alternatives. Concretely, the chooser takes a sequence and declares "these are alternatives for a single objective" — the primitive does not second-guess this claim. The workspace-layer (or LLM author) makes the equivalence judgment. The primitive's single deterministic job is ranking by `reversibility_class`.

**Q15 — telemetry signal.** One OTel span: `pos.reversibility.path_chosen`, attributes:

| Attribute | Type | Notes |
|-----------|------|-------|
| `pos.reversibility.chosen_class` | string | `fully_reversible \| compensatable \| irreversible` |
| `pos.reversibility.alternatives_count` | int | total count including chosen |
| `pos.reversibility.alternative_classes` | string[] | all classes present in the alternatives list |
| `pos.reversibility.chosen_index` | int | index of chosen in the input sequence |
| `pos.reversibility.reason` | string | caller-supplied rationale ("default_preference" if none) |
| `pos.reversibility.override` | bool | true if caller's preference differed from default |

Additionally, when a `compensatable` or `irreversible` alternative exists and a more-reversible alternative was rejected, the span carries `pos.reversibility.downrank_warning = true`. This is the telemetry signal the observability aggregator surfaces as "the system chose a less-reversible path despite having a reversible option".

**Q16 — how does the system know alternatives exist?** It doesn't autonomously. The primitive does not maintain an alternative-registry (that would be a lifetime of architecture the acceptance criteria don't need). The workspace-layer (scope authoring, planner, or dispatcher) calls `rank_alternatives` with a constructed sequence. If no caller ever constructs a sequence, no path-choice telemetry fires — which is accurate, because no choice was presented. Future workspaces may build registry-backed choice surfaces on top; the primitive is the ranking primitive, not the alternative-discovery primitive.

### 2.5 Integration with sealed components (Q17-21)

**Q17 — scope-of-work.** Read-only consumer. Uses:
- `ScopeSpec.reversibility_class` (read attribute)
- `ScopeRuntime.store.events_for(scope_id)` (read events for `RollbackContext`)
- `ScopeRuntime.subscribe_all(callback)` (subscribe for cascade-on-failure trigger)
- `ScopeRuntime.cancel(scope_id, reason)` (drive the scope to cancelled when rollback invoked)
- `ScopeRuntime._public(proj)` — actually `ScopeRuntime.get_projection(scope_id)` (TBD — confirm public projection API in proposal; §11 prototype item)

**No amendment.** Sidecar binding in reversibility-primitive's own SQLite.

**Q18 — safety layer.** Verified gate composition. Two different refusal shapes, distinct error codes:
- `REVERSIBILITY_MISSING_COMPENSATION (-32050)` — contract failure, raised by reversibility's wrap, not user-approvable
- `DANGEROUS_OP_GATE_BLOCKED (-32041)` — owner-approval gate, raised by safety's wrap

Does safety need to read compensation-path presence? **No.** The gate ordering (§8) runs reversibility first, safety second. If reversibility passes an irreversible scope (because a binding exists), safety still independently fires its dangerous-op gate — the owner still has to acknowledge the irreversibility. A binding does *not* substitute for dangerous-op approval. This is deliberate: a system-authored compensation is not a user acknowledgment of risk.

**Q19 — orchestrator.** No amendment. The reversibility primitive wraps `activate_scope` on the shared `IPCServer` exactly like safety does. The safety-layer ipc_wiring pattern at `pos-v2/safety-layer/src/ipc_wiring.py:143-161` is copied: capture `orig_activate = server._handlers.get("activate_scope")`, register the reversibility wrap, forward. The reversibility wrap is registered **before** safety's wrap (workspace bootstrap orders the two) so that reversibility checks run first. Alternatively, both wraps are composed in a single workspace-bootstrap step that wires them in a chain.

The one question the prototype must answer (§11): when two wraps both target `activate_scope`, the second `register()` call *replaces* the first (since `_handlers` is a dict). The bootstrap must wire them as a chain: `wrap_reversibility(wrap_safety(orig_activate))`. This is straightforward but must be explicit in the proposal.

**Q20 — observability aggregator.** Standard emission. All spans emit via the aggregator's registered tracer provider (A1 correction from v1.1). Span namespace: `pos.reversibility.*`. See §6 for the full schema.

**Q21 — memory system.** No write dependency. Compensation-path registration and rollback events live in the reversibility primitive's own SQLite log — same pattern as safety's `ask_decisions` and `kill_events` tables. The memory system (Graphiti) is not a prerequisite for the reversibility primitive. If a workspace later wants "explain why rollback X happened" as a Graphiti query, that's a post-hoc indexer over the reversibility log, not a primitive dependency.

### 2.6 State and storage (Q22-23)

**Q22 — does the primitive own its own SQLite?** Yes, at `~/.pos/reversibility/reversibility.sqlite` (same pattern as safety, degradation, observability). Tables:

```sql
CREATE TABLE IF NOT EXISTS compensation_binding (
    scope_id         TEXT PRIMARY KEY,
    handle           TEXT NOT NULL,
    description      TEXT NOT NULL DEFAULT '',
    budget_seconds   INTEGER,
    idempotency_key  TEXT NOT NULL UNIQUE,
    registered_at    TEXT NOT NULL,
    registered_by    TEXT NOT NULL DEFAULT 'user'
);
CREATE INDEX IF NOT EXISTS idx_comp_binding_handle ON compensation_binding(handle);

CREATE TABLE IF NOT EXISTS rollback_invocation (
    invocation_id    TEXT PRIMARY KEY,
    scope_id         TEXT NOT NULL,
    idempotency_key  TEXT NOT NULL,
    state            TEXT NOT NULL,      -- requested|in_progress|succeeded|failed|degraded
    outcome          TEXT,                -- null until terminal
    narrative        TEXT NOT NULL DEFAULT '',
    recoverable      INTEGER NOT NULL DEFAULT 0,
    requested_at     TEXT NOT NULL,
    completed_at     TEXT,
    UNIQUE(scope_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_rb_scope ON rollback_invocation(scope_id);
CREATE INDEX IF NOT EXISTS idx_rb_state ON rollback_invocation(state);

CREATE TABLE IF NOT EXISTS reversibility_events (
    event_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_id         TEXT NOT NULL,
    kind             TEXT NOT NULL,
    payload          TEXT NOT NULL,     -- JSON
    created_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rev_events_scope ON reversibility_events(scope_id);
CREATE INDEX IF NOT EXISTS idx_rev_events_kind  ON reversibility_events(kind);
```

PRAGMAs match the pos-v2 standard: WAL, `synchronous=FULL`, `foreign_keys=ON`. Schema initialisation runs via `executescript(_SCHEMA)` on store construction (same pattern as objective-tracker).

**Q23 — OTel emissions.** Every state change emits a span:

- `pos.reversibility.binding_registered`
- `pos.reversibility.binding_redundant` (fully_reversible + binding declared)
- `pos.reversibility.path_chosen` (§2.4)
- `pos.reversibility.activation_blocked` (reversibility-primitive refusal)
- `pos.reversibility.rollback_requested`
- `pos.reversibility.rollback_in_progress`
- `pos.reversibility.rollback_succeeded`
- `pos.reversibility.rollback_failed`
- `pos.reversibility.rollback_degraded`
- `pos.reversibility.rollback_idempotent_hit` (second call with same idempotency_key)

All carry `pos.scope.id` attribute; rollback spans additionally carry `pos.reversibility.invocation_id` and `pos.reversibility.handle`.

### 2.7 Deterministic enforcement — sidecar/wrap confirmed (Q24-26)

**Q24 — does sidecar/wrap fully deliver the acceptance criterion?** Yes. The activation wrap reads `ScopeSpec.reversibility_class` (sealed surface, read-only) and consults the sidecar `compensation_binding` table. If `compensatable` + no binding → refuse. If `irreversible` + no binding + no dangerous-op approval → refuse. If `fully_reversible` → pass. This implements "irreversible cannot activate without a compensation path" **structurally** — the refusal is a Pydantic-validated raise from the wrap before `orig_activate` runs.

Composition with safety's wrap (confirmed by reading `safety-layer/src/ipc_wiring.py:143-161`):

```
IPC activate_scope call
    ↓
reversibility-primitive wrap (checks binding presence per class)
    ↓ (raise REVERSIBILITY_MISSING_COMPENSATION on failure)
safety-layer wrap (system-kill check, ask gate, dangerous-op gate)
    ↓ (raise IPC_SYSTEM_KILL_ACTIVE / IPC_ASK_GATE_PENDING / IPC_DANGEROUS_OP_GATE_BLOCKED on failure)
orchestrator orig_activate
```

Error codes are disambiguated by IPC numeric range: `-32040..-32043` (safety); `-32050..-32059` (reversibility — reserved). The two wraps never raise overlapping codes. A client can distinguish the refusal source by `error.code` alone. No ambiguity, no short-circuit surprises.

**Short-circuit semantics:** both wraps raise `ApplicationError` on block. The standard `ApplicationError` propagation (unhandled) stops request processing and returns the error to the IPC client. The orchestrator's `orig_activate` never runs. No partial state — the scope remains in `proposed` state.

**Q25 — Pydantic shape and registration surface.** Declared in §2.1 (`CompensationPathBinding`). Registration surfaces:

- **IPC:** `reversibility.register_compensation` — primary surface used by the scope-authoring layer. Returns structured success/failure. The method validates input via Pydantic at construction — an empty handle or malformed payload is rejected with `-32602 INVALID_PARAMS`.
- **CLI:** `pos reversibility bind <scope_id> --handle <name> [--description ...] [--budget-seconds N] [--idempotency-key K]` — reaches the same IPC method. For manual registration / recovery / debugging.
- **YAML** (optional convenience): `reversibility.register_from_yaml path/to/compensations.yaml` — bulk registration. Parses into a list of `CompensationPathBinding`s; per-row failures are reported without affecting other rows. Recommended for workspace-authored compensation catalogues.

All three surfaces share one code path: parse → Pydantic-validate → insert into `compensation_binding` table → emit `pos.reversibility.binding_registered` span.

**Rejection of non-existent scope binding:** the sidecar cannot validate that `scope_id` actually refers to an existing scope (the scope may not exist yet at registration time — authoring layers legitimately register the binding and then create the scope). The primitive records the binding regardless; the **activation wrap** is what refuses, and at that point the scope exists. This matches constraint recorded "structurally refuse invalid declarations" without over-coupling: the binding is valid if its schema is valid; the gate enforces at activation.

**Q26 — is there any case sidecar/wrap cannot deliver?** None identified. The only hypothetical amendment case would be "the scope runtime needs to know at event-authoring time whether a binding exists," which would require a callback from scope-of-work to reversibility — a dependency reversal. But the acceptance criteria don't demand this; they demand activation-time enforcement, which the wrap covers. **No halt-and-signal. Amendment is not required.**

### 2.8 Testing discipline (Q26-27; plan numbering has a duplicate 26)

**Compensation-path tests without irreversible side effects** — `tests/` structure:

```
reversibility-primitive/tests/
├── conftest.py                          # in-memory store + fake IPCServer + fake scope runtime
├── fakes.py                             # FakeCompensationHandler with recorded invocations
├── test_binding_registration.py         # Pydantic refusal on empty handle, workspace-IPC flow
├── test_activation_wrap_gates.py        # three-class × binding-presence matrix
├── test_rollback_idempotence.py         # double-invocation returns cached result
├── test_rollback_state_machine.py       # requested → in_progress → succeeded/failed/degraded
├── test_rollback_context_access.py      # RollbackContext carries full event log
├── test_path_choice_ranking.py          # ranking produces expected order; preference override
├── test_path_choice_telemetry.py        # OTel span emitted with correct attributes
├── test_safety_wrap_composition.py      # wraps stack correctly; error codes distinct
├── test_cascade_on_child_failure.py     # pyee subscription triggers rollback
└── test_rollback_budget_timeout.py      # asyncio.wait_for timeout produces failed invocation
```

The `FakeCompensationHandler` is a sync-instantiated async callable with a `calls: list[RollbackContext]` recording every invocation. Tests assert invocation count, invocation order (in multi-scope rollback scenarios), and that the context carries the expected events. No network, no real external actions, no real email/DNS/etc — the compensation concept is the registered callable's *contract*, not its side effects.

**ODD pattern for path-choice tests.** The test constructs two `ScopeSpec`s with identical goals and different `reversibility_class` values, calls `rank_alternatives([spec_a, spec_b])`, and asserts (a) the reversible one is ranked first, (b) an OTel span with the expected attributes was emitted (using a memory `SpanExporter` injected via the aggregator's test fixture).

```python
def test_reversible_preferred_over_irreversible(path_chooser, otel_memory_exporter):
    spec_r = make_spec(goal="send update", class_=ReversibilityClass.fully_reversible)
    spec_i = make_spec(goal="send update", class_=ReversibilityClass.irreversible)
    ranked = path_chooser.rank_alternatives([spec_i, spec_r])
    assert ranked.chosen is spec_r
    span = otel_memory_exporter.finished_spans[-1]
    assert span.name == "pos.reversibility.path_chosen"
    assert span.attributes["pos.reversibility.chosen_class"] == "fully_reversible"
```

---

## 3. Clause-by-clause spec coverage

Mapping the acceptance criteria (v1.0 Reversibility §149-150, implicit from the v1.0 Core-primitives behaviours) to the design.

| Acceptance criterion | Covered by |
|---|---|
| Reversibility class declared on every scope | Existing `ScopeSpec.reversibility_class` required field (verified §0); no primitive work needed. |
| Reversible preferred when choice exists | `rank_alternatives` function + `pos.reversibility.path_chosen` span (§2.4). Default ordering `fully > compensatable > irreversible`. |
| Irreversible escalated | Safety-layer dangerous-op gate (existing; §2.5). Reversibility primitive composes by running its own gate first. |
| Given a reversible vs irreversible pair, system selects reversible | `rank_alternatives` pairwise test (§2.8). |
| Irreversible cannot activate without compensation path OR dangerous-op approval | Reversibility activation wrap + sidecar binding + existing safety wrap (§2.1, §2.7, §8). |
| Compensation path is invokable with access to committed state | `RollbackContext` pattern (§2.1 Q4). |
| Path-choice telemetry records alternative and reason | `pos.reversibility.path_chosen` span (§2.4). |

All criteria traceable to a design artifact; no gaps.

---

## 4. Compensation-path contract specification

### 4.1 Pydantic shape

See §2.1 for `CompensationPathBinding`. Reproduced below for reference:

```python
class CompensationPathBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_id: str = Field(min_length=1)
    handle: str = Field(min_length=1)
    description: str = ""
    budget_seconds: int | None = Field(default=None, ge=1)
    idempotency_key: str = Field(min_length=1)
    registered_at: str
    registered_by: str = "user"
```

### 4.2 Handler registration

`ReversibilityController.register_handler(handle: str, fn: Callable[[RollbackContext], Awaitable[RollbackResult]])` — workspace calls at startup. A handle may be overwritten by a later registration (last-writer-wins); this is explicit, emits `pos.reversibility.handler_replaced` span. Attempting to activate a scope whose binding references an unregistered handle at activation time is a separate error class: `-32051 REVERSIBILITY_UNREGISTERED_HANDLE`.

### 4.3 State access pattern

`RollbackContext` carries the full event log and the public projection. The handler is handed a read-only snapshot at rollback invocation; it is **not** passed a reference to the live `ScopeRuntime`. This prevents handlers from mutating scope state during rollback — rollback is observed state-in, compensation-out.

If a handler needs to mutate state (e.g. create a follow-up scope for corrective action), it does so via the workspace's standard scope-authoring surface (via IPC call to the orchestrator from inside the handler). This is outside the primitive's concern.

---

## 5. Rollback state-machine

```
                    ┌─────────────┐
                    │  requested  │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ in_progress │
                    └──────┬──────┘
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
         ┌───────────┐  ┌────────┐  ┌──────────┐
         │ succeeded │  │ failed │  │ degraded │
         └───────────┘  └────────┘  └──────────┘
                    (all terminal)
```

**Transitions:**

- `requested → in_progress`: the runtime dequeues the invocation and begins executing the handler.
- `in_progress → succeeded`: handler returned `RollbackResult(outcome="succeeded", ...)`.
- `in_progress → failed`: handler returned `RollbackResult(outcome="failed", ...)` OR raised an exception OR timed out (when `budget_seconds` set). Failed invocations that set `recoverable=True` may be re-invoked manually via a new IPC call with a **new idempotency_key** (the old key's state is frozen terminal).
- `in_progress → degraded`: handler returned `RollbackResult(outcome="degraded", ...)` — partial compensation. Recorded for audit; scope already moved to cancelled; one-on-one notification sent to the user noting partial success.

**Idempotence:** a second `rollback_scope` call for a `(scope_id, idempotency_key)` already present returns the current row without re-invoking the handler. The read is a single SQLite SELECT; the span emitted is `pos.reversibility.rollback_idempotent_hit`.

**Terminal states carry the reason:** `RollbackResult.narrative` is the handler-authored prose surfaced in the one-on-one notification and in `pos rollback status <scope_id>` CLI output.

---

## 6. Path-choice telemetry specification

### 6.1 Span schema

Name: `pos.reversibility.path_chosen`

| Attribute | Type | Required | Example |
|-----------|------|----------|---------|
| `pos.reversibility.chosen_class` | string enum | yes | `fully_reversible` |
| `pos.reversibility.alternatives_count` | int | yes | 2 |
| `pos.reversibility.alternative_classes` | string[] | yes | `["irreversible","fully_reversible"]` |
| `pos.reversibility.chosen_index` | int | yes | 1 |
| `pos.reversibility.reason` | string | yes | `default_preference` |
| `pos.reversibility.override` | bool | no | `false` |
| `pos.reversibility.downrank_warning` | bool | no | `false` |

`downrank_warning=true` fires when the caller explicitly chose a less-reversible option despite a more-reversible alternative being present. This is the signal downstream consumers (observability aggregator) use to surface the anti-pattern.

### 6.2 Workflow integration points

- **Scope authoring:** workspace-level scope author calls `rank_alternatives(candidates)` before calling `propose_scope`; chosen spec proceeds to scope proposal. Span fires at call site.
- **Planning:** multi-scope planners call `rank_alternatives` once per decision point. Span fires per decision.
- **Dispatch:** if the orchestrator is given multiple implementation candidates for a scope, the dispatcher calls `rank_alternatives`. Span fires per dispatch decision.

No workflow amendment is required anywhere — all three are workspace-layer patterns consuming the primitive's ranking function.

---

## 7. Integration sequence diagrams

### 7.1 Compensation-path registration

```
Workspace (scope-author)          ReversibilityController      SafetyStore             OTel
     │                                    │                         │                   │
     │── register_compensation ───────────▶                         │                   │
     │  (scope_id, handle,                 │                         │                   │
     │   idempotency_key)                  │                         │                   │
     │                                    │── Pydantic validate ────▶                   │
     │                                    │── INSERT binding row ──▶                    │
     │                                    │                         │── SELECT check ──▶│
     │                                    │                         │                   │
     │                                    │───── emit span ──────────────────────────────▶
     │                                    │   pos.reversibility.binding_registered      │
     │◀─ {ok: True, binding_id} ──────────                                                 │
```

### 7.2 Rollback-on-failure (child cascade via pyee)

```
ScopeRuntime (child scope)        ReversibilityRuntime          HandlerRegistry     CompensationStore
     │                                    │                           │                    │
     │─ emit StateTransitioned(failed) ──▶│ (pyee subscribe_all)      │                    │
     │                                    │                           │                    │
     │                                    │─ get_binding(child_id) ────────────────────────▶
     │                                    │◀── CompensationPathBinding ─────────────────────│
     │                                    │                           │                    │
     │                                    │─ resolve(handle) ────────▶│                    │
     │                                    │◀── callable ──────────────│                    │
     │                                    │                           │                    │
     │                                    │─ build RollbackContext ───                     │
     │                                    │      (events, projection) │                    │
     │                                    │                           │                    │
     │                                    │─ INSERT rollback_invocation(requested) ────────▶
     │                                    │─ UPDATE state=in_progress ─────────────────────▶
     │                                    │                                                │
     │                                    │── invoke handler(ctx) ────▶                   │
     │                                    │◀── RollbackResult ────────│                    │
     │                                    │                                                │
     │                                    │─ UPDATE state=succeeded ──────────────────────▶
     │                                    │                                                │
     │                                    │─ ScopeRuntime.cancel(reason="rollback") ──▶   │
     │                                    │─ emit span rollback_succeeded ────────────▶   │
```

### 7.3 Path choice at scope authoring

```
Workspace author (LLM output)     ReversibilityController      OTel
     │                                    │                        │
     │─ rank_alternatives([spec_a, spec_b, spec_c]) ──▶             │
     │   with preference=None               │                        │
     │                                    │                        │
     │                                    │─ sort by class rank ──  │
     │                                    │  (reversible > comp     │
     │                                    │   > irreversible)       │
     │                                    │                        │
     │                                    │─ emit path_chosen span ▶│
     │◀─ RankedAlternatives(chosen=spec_b, alternatives=[...]) ───   │
```

---

## 8. Relationship to safety layer

### 8.1 Refusal boundary

| Refusal | Component | Code | Shape |
|---------|-----------|------|-------|
| Scope-spec contract violated (missing binding for compensatable/irreversible) | Reversibility primitive | `-32050 REVERSIBILITY_MISSING_COMPENSATION` | Structural — pre-authoring caller must fix the contract |
| Handle referenced by binding is not registered | Reversibility primitive | `-32051 REVERSIBILITY_UNREGISTERED_HANDLE` | Structural — workspace bootstrap must register the handler |
| System kill active | Safety layer | `-32042 SYSTEM_KILL_ACTIVE` | Operational — user clears the kill |
| Ask gate pending | Safety layer | `-32040 ASK_GATE_PENDING` | Owner-approval pending |
| Dangerous-op gate blocked | Safety layer | `-32041 DANGEROUS_OP_GATE_BLOCKED` | Owner-approval pending |

Each refusal is structurally distinct. `reversibility_class=irreversible` triggers both reversibility and safety gates, but they ask different questions: reversibility asks "does this irreversible scope have a compensation plan?"; safety asks "has the owner acknowledged the irreversibility of this specific spec?" Both must pass for activation. Either alone is insufficient.

### 8.2 Gate ordering

```
IPC activate_scope(scope_id)
    │
    ▼
┌───────────────────────────────────────────┐
│ Reversibility primitive wrap              │
│   1. load binding for scope_id            │
│   2. class dispatch:                      │
│      - fully_reversible → pass            │
│      - compensatable + binding → pass     │
│      - compensatable + no binding → RAISE │
│      - irreversible + binding → pass      │
│      - irreversible + no binding + no     │
│        safety approval → RAISE            │
│      - irreversible + no binding + safety │
│        approval (peek) → pass             │
└───────────────┬───────────────────────────┘
                │ (pass)
                ▼
┌───────────────────────────────────────────┐
│ Safety layer wrap                         │
│   1. refuse_if_system_killed              │
│   2. ask-gate check                       │
│   3. dangerous-op gate check              │
│      (reversibility_class=irreversible    │
│       is one of the fires)                │
└───────────────┬───────────────────────────┘
                │ (pass)
                ▼
        orchestrator orig_activate_scope
```

**Ordering rationale:**
- Reversibility first: if the contract is malformed (missing binding), nothing else matters. Refusing early avoids emitting safety-layer audit records for a scope that was never validly activatable. The refusal is purely structural; no user interaction.
- Safety second: the owner-approval gates are the last line before the orchestrator. They answer "should this approved-shape scope actually run right now?"

### 8.3 The irreversible + no-binding + safety-approved case

This is the cross-component peek. The reversibility wrap consults safety's store via an injected resolver (analogous to how safety's own wrap takes a `spec_resolver`). Proposal-level question: does this create a dependency cycle? **No** — reversibility depends on safety's **store** for a read-only query (`find_active_approval(spec_hash)`); safety does not depend on reversibility at all. The store query is identical to the one safety's own gate uses.

If workspace bootstrap has not wired safety, the reversibility wrap treats the absence of a resolver as "no approval exists" and applies the stricter rule (refuse without binding). This is fail-closed — the same posture safety itself takes on channel-unavailable.

### 8.4 What the safety layer does NOT need to learn

The safety layer does not need to know about compensation paths at all. Its dangerous-op gate continues to operate on `reversibility_class` alone. The reversibility primitive is a consumer, not a provider, of safety — it reads safety's approval state but does not push anything back. **No amendment to safety.**

---

## 9. Dependency map

**Consumed by:**
- **Cost governance** (deferred component) — will read rollback budget consumption; future read-only consumer.
- **Self-correction loop** (deferred component) — will invoke `rollback_scope` as part of automated error recovery; future IPC consumer.
- **Observability aggregator** — already registered; consumes `pos.reversibility.*` spans.

**Depends on (read-only, no amendment):**
- **Scope-of-work** — `ScopeSpec`, `ScopeRuntime.store.events_for`, `ScopeRuntime.subscribe_all`, `ScopeRuntime.cancel`, public projection surface, `ReversibilityClass` enum.
- **Safety layer** — `SafetyStore.find_active_approval` for the cross-component peek (§8.3). The `structural_hash(spec)` helper is also consumed for the spec-hash lookup.
- **Orchestrator** — shared `IPCServer` (`pos_orchestrator.ipc.IPCServer`), `pos_orchestrator.ipc.ApplicationError` class.
- **Observability aggregator** — registered tracer provider for span emission (A1 correction from v1.1).
- **Primary-persona-loader** — `OneOnOneChannel` for rollback-failure notifications (Tier 1, one-on-one only, no group channels).

---

## 10. Complexity estimate

**Calibrated AI-minutes for build:** 30–40 minutes wall-clock.

**Anchoring:**
- Safety layer came in at ~35 min wall-clock (8 src files, 10+ test files, ask-list Pydantic schema, three-level kill machinery, IPC wiring, CLI surface).
- Graceful-degradation came in at ~20 min wall-clock (simpler FSM, single-adapter wrap).
- Reversibility is **structurally similar to safety** — same IPC-wrap pattern, same SQLite+OTel+notification scaffold, same Pydantic-validated contract. Fewer moving parts than safety (two code-paths: gate and rollback; no kill-engine equivalent; no YAML floor list). But slightly more state modelling (rollback state machine with idempotence).

**Estimated file layout:**
```
reversibility-primitive/src/
├── __init__.py
├── spec.py            # CompensationPathBinding, RollbackResult, RollbackContext, events
├── store.py           # SQLite schema + upsert/query
├── controller.py      # ReversibilityController composed runtime
├── activation_gate.py # activation wrap + class dispatch
├── rollback.py        # RollbackRuntime: invocation + idempotence + timeout
├── path_choice.py     # rank_alternatives pure function
├── ipc_wiring.py      # IPC registration + activate_scope wrap
├── cli.py             # pos reversibility commands
├── observability.py   # span emitters
└── notification.py    # one-on-one rollback failure dispatch
```

**Estimated test count:** 10-12 test modules (per §2.8), similar density to safety.

**Wall-clock risk factors that might push toward 45+ min:**
- The reversibility ↔ safety wrap composition subtlety (§2.7) may require a small integration test suite that both teams' fixtures interact cleanly — prototype item, see §11.
- The pyee-driven child-cascade subscription requires careful test setup; similar to objective-tracker's `_bind_scope_success_listener` but with a different emission filter.

**Recommendation to the owner:** anchor 35 min wall-clock; flag 45 as the red line at which the builder halts and reports rather than silently overrun. Push back on the research plan's upper bound only if the integration-test composition (reversibility wrap + safety wrap in a single IPC server) doesn't slot cleanly into one of the existing conftest patterns.

---

## 11. Prototyping priorities

Questions only a prototype can answer.

1. **Two-wrap composition on one `IPCServer`.** The sealed safety wrap pattern captures `orig_activate = server._handlers.get("activate_scope")` at registration time. If reversibility registers first and safety registers second, safety's `orig_activate` will be *reversibility's* wrapped handler (correct chaining). If safety registers first and reversibility registers second, reversibility's `orig_activate` will be safety's handler (also correct — but different ordering, and reversibility runs **last**). **The workspace bootstrap order is load-bearing.** The prototype must establish a canonical registration order (recommend: reversibility first → safety second, which gives the ordering diagrammed in §8.2, because the last-registered runs first in the call chain). A 3-line integration test confirms.

2. **Compensation path invoked after orchestrator restart.** If rollback is triggered by a child-failure cascade but the orchestrator restarts before the pyee handler fires, the rollback may be lost. Recovery approach: the `rollback_invocation` table has a `requested` state with no `in_progress` transition — on startup, the runtime scans for orphaned `requested` rows and re-invokes. Prototype must confirm this scan completes within the session-resilient orchestrator's startup budget and that idempotency_key dedupe protects against double-invocation.

3. **Rollback during an active dangerous-op gate.** Sequence: scope is in `proposed`, dangerous-op gate is awaiting user approval, user issues `pos rollback scope <id>`. What does reversibility do? Candidate: refuse — cannot rollback a scope that has not activated. Alternative: accept — the user is withdrawing the request. Prototype the case and pick. (Tentative recommendation: refuse with `-32052 REVERSIBILITY_NOT_ACTIVATED`; user cancels via safety's `pos kill scope` surface instead.)

4. **Public projection API on ScopeRuntime.** §2.5 Q17 referenced `ScopeRuntime._public(proj)` — the leading underscore suggests this is private. Prototype must confirm the stable public projection accessor and use it. If the public surface is only `ScopeRuntime.get_projection(scope_id)` or similar, the `RollbackContext` builder uses that; the research plan's one factual uncertainty.

5. **Cross-store spec-hash consistency.** Safety's `structural_hash(spec)` is the canonical hash. Reversibility uses it for the irreversible + safety-approval peek (§8.3). Prototype: import `from safety_layer.events import structural_hash` directly vs reimplement in reversibility's own events module. Recommendation: import from safety (single source of truth). If the import creates a circular dependency risk, the prototype will flag it.

---

## Summary

The sidecar/activation-wrap pattern delivers every acceptance criterion cleanly. Factual claims in the research plan held on verification. No amendments to any sealed component are required. The reversibility primitive is a new package at `reversibility-primitive/` on `pos-v2`, structurally analogous to safety, consuming scope-of-work + safety-layer + orchestrator + observability-aggregator as read-only surfaces.

Remaining uncertainty is concentrated in the wrap composition prototype (§11.1) and the public projection surface (§11.4). Both are low-risk — if either surprises, the fix is localised to this component's wiring module.

Build estimate: 35 min wall-clock anchored to safety layer. Risk of 45 min if the dual-wrap integration test reveals unexpected ordering subtlety; halt-and-signal at that line rather than silent overrun.
