# Handoff Brief — Reversibility Primitive

**For:** the general-purpose Agent dispatched to build the reversibility primitive.
**From:** the primary persona, 2026-04-19 17:56 CDT.
**Status:** awaiting owner's review of this brief; not yet dispatched.

---

## 1. What you are building

The reversibility primitive for pOS on the `pos-v2` branch of `the existing workspace root`. It promotes `ScopeSpec.reversibility_class` from a passive declaration to an active structural contract — a compensation-path binding sidecar, an activation wrap that refuses unbound `compensatable`/`irreversible` scopes, a rollback runtime with idempotence and FSM, and path-choice telemetry.

The work is greenfield Python on `pos-v2`. It consumes sealed components — including the just-sealed safety layer — as read-only surfaces. It does not amend any of them.

## 2. Authoritative documents (read in this order)

1. **This brief** — gives you the objective, constraints, and acceptance criteria in operational form.
2. **`docs/rebuild/components/reversibility-primitive/proposal.md`** — the contract the owner has approved. Binding. Halt and signal rather than deviate.
3. **`docs/rebuild/components/reversibility-primitive/research.md`** — design detail, prior art, sequence diagrams, storage schema. Reference only; the proposal is the contract.
4. **`docs/rebuild/spec/loam-objectives-spec.md`** — spec v1.0 + addenda.
5. **`docs/rebuild/STATE.md`** — governing rules for the rebuild.

**Precedents to emulate** (both on `pos-v2`, both sealed):
- `objective-tracker/src/store.py` + `objective-tracker/src/runtime.py` — sidecar binding table pattern (`scope_objective_binding`) and pyee subscription pattern (`_bind_scope_success_listener`).
- `safety-layer/src/ipc_wiring.py` — IPC-handler wrap of `activate_scope` without amending the orchestrator.
- `safety-layer/src/events.py` — `structural_hash(spec)` helper; you will **import** this per ruling #4, not duplicate it.

## 3. The objective (single sentence)

Deliver the reversibility primitive such that a `compensatable` or `irreversible` scope cannot activate without a registered compensation-path binding (or, for `irreversible`, an active safety dangerous-op approval), a registered compensation path can be invoked via rollback with read access to the scope's committed state, and alternatives ranked by reversibility class emit telemetry that surfaces when a less-reversible path was chosen over a more-reversible one — all without amending any sealed component.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** scope-of-work, orchestrator, graceful-degradation, primary-persona, objective-tracker, observability-aggregator, self-upgrade, safety-layer, memory-system are all sealed on `pos-v2`. If you conclude an amendment is required — halt and signal with named component + named surface + the sidecar/wrap alternative you tested before concluding it fails. Amendment is last resort, not first question.
- **Wrap registration order is load-bearing.** Per ruling recorded #1: reversibility first → safety second → orchestrator `orig_activate`. The call chain becomes `reversibility → safety → orig_activate` because each wrap captures the prior handler as its `orig_activate`. Document this in the workspace bootstrap wiring and cover it with an integration test.
- **Fail-closed on safety-resolver absence.** If safety's `SafetyStore.find_active_approval` resolver is not injected into the reversibility wrap, apply the stricter rule (refuse `irreversible` without binding regardless of approval state). Matches safety's own fail-closed posture.
- **Deterministic enforcement.** The activation-gate refusal is a Pydantic-validated raise from the wrap before `orig_activate` runs. No LLM inference inside the wrap.
- **Reuse safety's `structural_hash`.** Per ruling recorded #4: `from safety_layer.events import structural_hash`. Single source of truth. If the import creates a circular dependency at wiring time, halt and signal with the dependency graph.
- **One-on-one channel only** for rollback-failure notifications. Reuse `OneOnOneChannel` from `primary_persona.introduction`; inherit the `is_group=True` rejection.
- **Error-code range `-32050..-32059` reserved to reversibility.** No overlap with safety's `-32040..-32043`.
- **Zero carryover from current pOS.** No imports from, references to, or patterns copied out of current-gen Ruby.
- **Max-first.** No LLM inference inside the primitive.
- **Halt on deviation.**

## 5. Acceptance (ODD — 26 criteria, in proposal §4)

R1–R5: compensation-path contract + registration surfaces.
R6–R12: activation-gate enforcement — three-class × binding-presence × safety-approval matrix.
R13–R18: rollback lifecycle, idempotence, pre-activation refusal, pyee cascade trigger.
R19–R20: path-choice ranking and telemetry (including `downrank_warning`).
R21–R24: cross-cutting integration — no sealed-component mutation, aggregator-routed OTel, one-on-one channel, no legacy imports.
R25–R26: structural-impossibility defence-in-depth — `budget_seconds` Pydantic validation; `structural_hash` identity to safety's.

Each criterion is an objective. Tests are authored against the criterion directly. Negative cases re-extend as positive objectives — if you find one worth naming, add it as R27 and explain its rationale in the commit message.

## 6. Verify-against-code discipline

Before relying on any sealed-component surface, open the file on `pos-v2` and confirm the symbol exists with the shape you expect. Four surfaces to verify first because the research flagged them as the highest-uncertainty spots:

- **`ScopeRuntime` public projection accessor.** Research §11.4 noted `_public(proj)` is private; the stable accessor is likely `get_projection(scope_id)` or similar. Confirm the name and use the public one when building `RollbackContext`.
- **`ScopeRuntime.subscribe_all(callback)`** — the pyee emitter surface objective-tracker uses. Verify it exists and accepts a callback with the `StateTransitioned(to=failed)` event shape you'll filter on.
- **`ScopeRuntime.cancel(scope_id, reason)`** — you'll call this on successful rollback to drive the scope to `cancelled`.
- **`ParentClosePolicy` enum and its `TERMINATE` value** — the filter for the cascade trigger subscription. inference recorded in proposal §8 #3; verify the policy is on the public projection or accessible via a public accessor.

If any proposal-level claim about a sealed surface doesn't match, halt and signal with the named file and symbol.

## 7. inferences recorded (proposal §8) — challenge any that feel wrong

Eight items in the proposal are the primary persona's extrapolation rather than the owner's direct words:

1. Last-writer-wins on duplicate binding registration (R5).
2. Public projection accessor name uncertainty.
3. Cascade trigger on `ParentClosePolicy=TERMINATE` filter.
4. `rank_alternatives` emits a span on one-element lists (possibly noise).
5. `binding_redundant` audit span on `fully_reversible + binding`.
6. Cascade-generated `idempotency_key` vs caller-supplied.
7. Error-code range choice `-32050..-32059`.
8. No framework-shipped YAML compensation catalogue.

Challenge any with a halt signal and proposed alternative. Not load-bearing unless the owner confirms.

## 8. Estimate

**30–40 AI-minutes wall-clock. Red line at 45.**

Anchor components: safety layer (~35 min), graceful-degradation (~20 min). Reversibility is structurally close to safety (same IPC-wrap + SQLite + OTel + notification scaffold; same Pydantic contract pattern). Fewer moving parts than safety (no kill engine, no YAML floor list) offset by rollback FSM + pyee cascade.

**If the build exceeds 45 minutes, halt and signal.** Failure class to investigate: wrap-ordering subtlety in `ipc_wiring.py` (two wraps composing on one `IPCServer`) or projection-surface uncertainty. Do not extend silently.

## 9. What I need back

On completion:

1. **Paths to the commits on `pos-v2`.** Atomic commits per phase acceptable; single cohesive commit acceptable.
2. **Test results** — every R-criterion (R1–R26, plus any R27+ you added) mapped to a passing test. If any R-criterion is unsatisfied, name it and explain.
3. **Sealed-component diff check** — `git diff --stat 45a15b9..<your-head>` should show only `reversibility-primitive/` and workspace-bootstrap changes. Any delta to a sealed component is a halt-signal condition.
4. **primary-persona inferences you challenged** and the alternative you chose (or halted on).
5. **Any halt signals** — named component + surface + what you tried first.
6. **Actual wall-clock vs the 30–40 min estimate.**

Return summary: under 500 words. Code and tests carry the detail.

## 10. Failure modes I am watching for

- "Improving" the spec while building. Don't — deliver what the proposal specifies; file enhancement ideas in the commit message for a later component.
- Monkey-patching a sealed component. Halt and signal instead.
- Skipping structural enforcement and replacing it with a runtime nag. The activation wrap raising `ApplicationError` before `orig_activate` runs is the enforcement.
- Registering the wraps in the wrong order. Reversibility first → safety second. An integration test must cover the call chain explicitly.
- Building LLM inference into the gate or rollback runtime. Deterministic; persona rendering is outside.
- Letting the estimate slip past 45 minutes quietly. Halt at 45 and signal scope-creep or wiring subtlety for triage.
- Circular import between `reversibility_primitive.events` and `safety_layer.events`. If you find one at wiring time, halt — the proposal's `import` directive is contingent on the import being clean.

---

**End of brief.** the owner reviews; on the owner's green light, dispatch follows.
