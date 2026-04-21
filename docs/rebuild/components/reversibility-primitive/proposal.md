# Proposal — Reversibility Primitive

**Component:** Reversibility Primitive — promotes `ScopeSpec.reversibility_class` from a passive declaration to an active structural contract with compensation-path registration, rollback invocation with idempotence, and path-choice telemetry.
**Status:** DRAFT — awaiting owner's approval before brief authoring.

**Branch:** `pos-v2`. **Language:** Python 3.13.
**Consumes (no amendment):** scope-of-work, safety-layer, orchestrator, observability-aggregator, primary-persona-loader.

---

## 1. Objective

Deliver the reversibility primitive such that:

- A scope declared `compensatable` or `irreversible` cannot activate without a registered compensation-path binding (or, for `irreversible`, an active safety-layer dangerous-op approval). The refusal is deterministic.
- A registered compensation path is invokable via rollback with read access to the scope's committed state (events + projection).
- `compensatable` and `fully_reversible` are distinct: `compensatable` requires a binding; `fully_reversible` does not.
- When the workspace asks the primitive to rank alternative scope specs, the default preference is `fully_reversible > compensatable > irreversible`, and the choice is recorded in OTel as `pos.reversibility.path_chosen` with alternatives, class, reason, and a `downrank_warning` flag when a less-reversible option was chosen over a more-reversible alternative.

The design shape and acceptance evidence are in `research.md`; this proposal encodes the decisions the owner has ruled on and states the hard contract the builder works against.

---

## 2. the owner's rulings (locked inputs)

| # | Question | Ruling |
|---|----------|--------|
| 1 | Wrap registration order on the shared `IPCServer` | **Reversibility first → safety second → orig_activate.** Reversibility's structural refusal runs before safety's owner-approval gates. |
| 2 | Rollback invoked during an active dangerous-op gate | **Refuse**, with error code `-32052 REVERSIBILITY_NOT_ACTIVATED`. A gated scope hasn't activated; no committed state to unwind. |
| 3 | Default `budget_seconds` on compensation handlers | **`None`** — no framework-imposed timeout. Per-workspace opt-in if a ceiling is wanted. |
| 4 | Reuse of safety's `structural_hash(spec)` | **Import** from `safety_layer.events`. Single source of truth. Builder verifies no circular dependency at wiring time. |

---

## 3. Design shape (summary — detail in `research.md`)

### 3.1 Composition

A new package `reversibility-primitive/` (Python, on `pos-v2`) exposes `ReversibilityController` — the composed runtime. The controller hosts:

- **`CompensationPathBinding`** — Pydantic-validated record (`scope_id`, `handle`, `description`, `budget_seconds?`, `idempotency_key`, `registered_at`, `registered_by`). Persisted in a sidecar SQLite table owned by the primitive. Frozen + `extra="forbid"` + `model_validator` rejecting empty handles.
- **Handler registry** — workspace calls `register_handler(handle, fn)` at startup. `fn` is an async callable with signature `(RollbackContext) -> RollbackResult`.
- **`RollbackContext`** — frozen dataclass carrying `scope_id`, `scope_spec`, `events` tuple, `projection`, `idempotency_key`, `invocation_id`. Built at rollback invocation via existing scope-of-work read surfaces.
- **`RollbackResult`** — Pydantic model with `outcome: Literal["succeeded","failed","degraded"]`, `narrative`, `compensated_at`, `recoverable`.
- **Activation-gate wrap** — IPC-handler wrap of `activate_scope`, registered on the shared `IPCServer` **before** safety's wrap so the call chain becomes `reversibility → safety → orig_activate`. Class dispatch: `fully_reversible` passes; `compensatable` requires a binding; `irreversible` requires a binding OR an active safety dangerous-op approval (peek into safety's store).
- **Rollback runtime** — four-state FSM (`requested → in_progress → {succeeded|failed|degraded}`) persisted in a `rollback_invocation` table with `(scope_id, idempotency_key)` uniqueness constraint. Second invocation with same key returns cached result without re-running the handler.
- **Cascade trigger** — pyee subscription to scope-of-work's emitter (`ScopeRuntime.subscribe_all`) invokes rollback on child-failure cascade when a binding exists for the failed child.
- **`rank_alternatives(alternatives)`** — pure function returning a `RankedAlternatives` object. Emits `pos.reversibility.path_chosen` span with attributes in research §6.1. The primitive does not second-guess whether two specs are genuinely alternatives — the caller declares that.
- **SQLite store** at `~/.pos/reversibility/reversibility.sqlite`. Schema in research §2.6. WAL + `synchronous=FULL` + `foreign_keys=ON` per pos-v2 standard.
- **CLI** — `pos reversibility bind`, `pos reversibility handlers`, `pos rollback scope <id>`, `pos rollback status <id>`.
- **Notification** — `OneOnOneChannel` reuse for rollback-failure Tier-1 surfacing; group-channel rejection inherited.
- **Observability** — spans enumerated in research §6.1 and §2.6, emitted via the observability aggregator's registered provider.

### 3.2 Composition with safety

Reversibility's activation wrap registers **first** per ruling #1. Safety's wrap registers **second**. Because `IPCServer.register` overwrites the handler dict entry and the new handler captures the prior one as `orig_activate`, the call chain becomes: reversibility → safety → orchestrator's true `activate_scope`.

Cross-component read dependency: the reversibility wrap consults `safety_layer.store.SafetyStore.find_active_approval(spec_hash)` using `safety_layer.events.structural_hash(spec)` for the `irreversible + no-binding + approved` case. This is a one-way read — safety does not consume anything from reversibility. If safety is not wired into the workspace bootstrap, reversibility's wrap treats the absence as "no approval exists" and applies the stricter refusal (fail-closed).

### 3.3 Refusal boundary (error codes)

| Refusal | Code | Raised by |
|---------|------|-----------|
| `compensatable`/`irreversible` scope has no compensation binding (and no safety approval for irreversible) | `-32050 REVERSIBILITY_MISSING_COMPENSATION` | Reversibility wrap |
| Binding references a handle not in the registry | `-32051 REVERSIBILITY_UNREGISTERED_HANDLE` | Reversibility runtime at rollback invocation |
| Rollback invoked against a scope that has not activated | `-32052 REVERSIBILITY_NOT_ACTIVATED` | Rollback IPC |

Codes `-32050..-32059` are reserved to reversibility; `-32040..-32043` remain safety's. No overlap.

---

## 4. Acceptance criteria (ODD — 18 objectives)

Each criterion is authored as an objective, not a behaviour. Tests target the criterion directly.

### 4.1 Compensation-path contract (research §2.1, §4)

- **R1.** `CompensationPathBinding` refuses empty `handle` or empty `idempotency_key` at construction (Pydantic validation).
- **R2.** `reversibility.register_compensation` IPC method accepts a well-formed payload, writes the binding row, emits `pos.reversibility.binding_registered`, and returns `{ok: True, binding_id}`.
- **R3.** `pos reversibility bind <scope_id> --handle <name>` CLI reaches the same IPC path and produces the same side effects as R2.
- **R4.** A binding registered against a `scope_id` that does not yet exist is accepted (activation is where enforcement happens, not registration).
- **R5.** Registering a second binding for the same `scope_id` replaces the prior binding (last-writer-wins) and emits `pos.reversibility.binding_replaced` with a `prior_handle` attribute for audit.

### 4.2 Activation-gate enforcement (research §2.7, §8)

- **R6.** A `fully_reversible` scope activates without regard to binding presence. Binding present produces no refusal and emits `pos.reversibility.binding_redundant` for audit; binding absent is the normal case.
- **R7.** A `compensatable` scope with no binding → wrap raises `-32050 REVERSIBILITY_MISSING_COMPENSATION`; orchestrator `activate_scope` does not run; scope stays `proposed`.
- **R8.** A `compensatable` scope with a registered binding → wrap passes; safety's wrap runs; orchestrator activates on safety pass.
- **R9.** An `irreversible` scope with a binding → wrap passes; safety's dangerous-op gate still independently fires on the irreversible class (binding does not substitute for owner approval); on both passes, orchestrator activates.
- **R10.** An `irreversible` scope with no binding and no active safety dangerous-op approval → wrap raises `-32050`; scope stays `proposed`.
- **R11.** An `irreversible` scope with no binding but an active safety dangerous-op approval (peek-resolved via `structural_hash`) → reversibility passes; safety may still gate on other conditions.
- **R12.** When safety is not wired at all (resolver absent), reversibility treats the peek as "no approval" and applies the stricter rule (fail-closed matches safety's own fail-closed posture).

### 4.3 Rollback invocation and FSM (research §2.2, §5)

- **R13.** `reversibility.rollback_scope(scope_id, reason)` IPC writes a `rollback_invocation` row in `requested` state, transitions to `in_progress`, invokes the handler with a `RollbackContext` carrying the full event log and projection, and records the `RollbackResult` outcome + narrative on the row.
- **R14.** Rollback is idempotent by `(scope_id, idempotency_key)`. A second call with the same key returns the prior row's outcome without re-invoking the handler and emits `pos.reversibility.rollback_idempotent_hit`.
- **R15.** Handler `RollbackResult(outcome="succeeded")` transitions the invocation to `succeeded`, drives the scope to `cancelled` via `ScopeRuntime.cancel(scope_id, reason="rollback_invoked")`, and emits `pos.reversibility.rollback_succeeded`.
- **R16.** Handler failure (returns `failed`, raises, or exceeds `budget_seconds` when set) transitions to `failed`, records narrative, emits `pos.reversibility.rollback_failed`, and surfaces a Tier-1 notification via `OneOnOneChannel` (no group-channel escape).
- **R17.** Rollback invoked against a scope that has not activated yet → IPC returns `-32052 REVERSIBILITY_NOT_ACTIVATED`. (Locks ruling #2.)
- **R18.** Parent-cascade rollback: when a child scope transitions to `failed` (via pyee `subscribe_all`) and that child has a registered compensation binding, the runtime invokes rollback automatically with a generated `idempotency_key` keyed to the cascade event.

### 4.4 Path-choice ranking and telemetry (research §2.4, §6)

- **R19.** `rank_alternatives([spec_i, spec_r])` where `spec_r.reversibility_class = fully_reversible` and `spec_i.reversibility_class = irreversible` returns `spec_r` as chosen. Emits `pos.reversibility.path_chosen` with `chosen_class=fully_reversible`, `alternatives_count=2`, `alternative_classes=["irreversible","fully_reversible"]`, `chosen_index=1`, `reason="default_preference"`, `downrank_warning=false`.
- **R20.** Caller-supplied preference override (`preference=irreversible`) picks the irreversible alternative and emits the span with `override=true` and `downrank_warning=true`.

### 4.5 Cross-cutting integration (research §2.5, §8)

- **R21.** `git diff --stat 45a15b9 <reversibility-commit>` shows only `reversibility-primitive/` and workspace-bootstrap wiring changes. Zero deltas to any sealed component.
- **R22.** All OTel emissions flow through the observability aggregator's registered `TracerProvider`. The primitive does not construct its own.
- **R23.** All user-facing notifications use `OneOnOneChannel` from `primary_persona.introduction`. No group-channel paths.
- **R24.** Zero imports from current-gen Ruby pOS rules-file machinery.

### 4.6 Structural-impossibility defence-in-depth

- **R25.** Ruling #3 enforced: a binding with `budget_seconds` explicitly set to `0` is refused by Pydantic (`ge=1`); `None` is accepted. No framework-default timeout is applied when the field is `None`.
- **R26.** Ruling #4 enforced: the reversibility module imports `structural_hash` from `safety_layer.events` rather than duplicating it; a test asserts the identity (`reversibility.get_spec_hash is safety_layer.events.structural_hash` or an equivalent reference check).

---

## 5. Constraints

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** If the builder concludes an amendment is required, halt and signal with named component + surface + the sidecar/wrap alternative considered.
- **Deterministic enforcement.** The activation-gate refusal is structural — Pydantic-validated raise from the wrap before `orig_activate` runs. No LLM inference inside the wrap.
- **Wrap registration order is load-bearing.** Reversibility first → safety second → orchestrator `orig_activate`. Documented in workspace bootstrap; covered by an integration test.
- **Fail-closed on safety-resolver absence.** If safety's store resolver is not injected, reversibility applies the stricter refusal rule for irreversible-no-binding.
- **One-on-one channel only** for rollback-failure notifications.
- **Max-first.** No LLM inference inside the primitive.
- **Zero carryover from current pOS.**
- **Halt on deviation.**

---

## 6. Suggested file layout

```
reversibility-primitive/
  src/
    spec.py              # CompensationPathBinding, RollbackResult, RollbackContext, typed events
    store.py             # SQLite schema + upsert/query
    controller.py        # ReversibilityController composed runtime
    activation_gate.py   # activation wrap + class dispatch
    rollback.py          # RollbackRuntime (invocation, idempotence, timeout, cascade subscribe)
    path_choice.py       # rank_alternatives pure function
    ipc_wiring.py        # IPC registration + activate_scope wrap
    cli.py               # pos reversibility / pos rollback commands
    observability.py     # span emitters
    notification.py      # one-on-one rollback failure dispatch
  tests/
    test_binding_registration.py            # R1–R5
    test_activation_wrap_gates.py           # R6–R12 (matrix over class × binding × safety-approval)
    test_rollback_lifecycle.py              # R13, R15
    test_rollback_idempotence.py            # R14
    test_rollback_failure_notification.py   # R16
    test_rollback_preactivation_refusal.py  # R17
    test_cascade_on_child_failure.py        # R18
    test_path_choice_default.py             # R19
    test_path_choice_override_downrank.py   # R20
    test_safety_wrap_composition.py         # wrap ordering + error code disambiguation
    test_no_sealed_amendments.py            # R21
    test_observability_routing.py           # R22
    test_one_on_one_channel_only.py         # R23
    test_no_legacy_imports.py               # R24
    test_structural_defence.py              # R25, R26
```

File cohesion is the builder's call to refine. Test list is the minimum set; additional tests welcomed, none removed.

---

## 7. Build phases and estimate

**Calibrated AI-time estimate: 30–40 minutes wall-clock. Red line at 45.**

Anchor: safety layer ~35 min; graceful-degradation ~20 min. Reversibility is structurally close to safety (same IPC-wrap pattern, same SQLite+OTel+notification scaffold, same Pydantic-validated contract pattern). Fewer moving parts than safety (no kill engine, no YAML floor list) offset by the rollback FSM + pyee cascade subscription.

If the build exceeds 45 minutes, halt and signal. The failure class to investigate: wrap-ordering subtlety in `ipc_wiring.py` or projection-surface uncertainty (see §8 inference #2).

Suggested phase shape (builder's call):

1. Pydantic schemas + loader (`spec.py`, structural validators) — R1.
2. Store (`store.py`) with schema migrations.
3. Handler registry + `ReversibilityController` skeleton — R4, R5.
4. `rank_alternatives` + path-choice telemetry — R19, R20.
5. Rollback runtime + FSM + idempotence — R13, R14, R15, R16, R17.
6. Cascade trigger (pyee subscription) — R18.
7. Activation gate wrap + class dispatch — R6–R12.
8. IPC-wiring composition with safety's wrap — wrap ordering + error code test.
9. CLI.
10. Observability routing — R22.
11. Notification — R16, R23.
12. Cross-cutting tests — R21, R24, R25, R26.

Atomic commits per phase acceptable; single cohesive commit acceptable.

---

## 8. inferences recorded — flagged for the builder to challenge

These items are not direct quotes from the owner and represent the primary persona's reading of the research + rulings. Challenge any of them with a halt signal and a proposed alternative:

1. **"Last-writer-wins on duplicate binding registration" (R5).** The research proposed replacement with a `binding_replaced` span. the primary persona carried it forward. The alternative is refuse-on-duplicate. If you think the primitive should refuse rather than replace, halt.
2. **Public projection accessor on `ScopeRuntime`.** Research §11.4 flagged the exact symbol as uncertain (`_public` vs `get_projection`). Verify against `pos-v2` code. If neither matches, halt and signal with the stable surface you'd use.
3. **Cascade trigger on `ParentClosePolicy=TERMINATE`.** Research §2.2 recommended this scope filter for the pyee subscription. If the policy is not on scope-of-work's public projection or if a cleaner filter presents itself, halt.
4. **`rank_alternatives` emits a span for every call, including one-element lists.** inference recorded: emitting the span on a one-element call is noise; suggest the primitive skip telemetry when `alternatives_count == 1`. The research didn't specify. If you disagree (e.g. "always emit for audit"), halt.
5. **`binding_redundant` audit span on `fully_reversible + binding`.** Research proposed emitting this. If it's noise rather than signal, halt and suggest dropping.
6. **`idempotency_key` generated per cascade event rather than exposed for caller control.** R18 says "generated keyed to the cascade event." The alternative is "exposed in the subscribe filter for caller-supplied keys." If caller-supplied is cleaner, halt.
7. **Error-code range `-32050..-32059` reserved to reversibility.** the primary persona chose this range to stay adjacent to safety's `-32040..-32043` without collision. If the builder sees a better range (e.g. the JSON-RPC reserved space rules prefer something different), halt.
8. **No framework-authored YAML catalogue of common compensations.** Research §2.7 mentioned YAML as optional workspace convenience. the primary persona did not include a framework-shipped YAML. If the builder thinks shipping a default catalogue reduces workspace-authoring friction, halt.

---

## 9. Approval ask

sign-off on this proposal moves the component to `proposal_approved` and opens handoff-brief drafting. On brief review, the background agent is dispatched.

Specifically requesting approval of:

- The locked rulings in §2 as faithful to the conversation.
- The acceptance criteria in §4 (R1–R26) as the complete ODD objective set.
- The constraints in §5 (wrap ordering, fail-closed, no amendments, no carryover).
- The 30–40 min estimate with 45-min red line.
- the primary persona's flagged inferences in §8 (approve as written, or adjust and re-land).

Approve as-is, approve with changes, or reject.
