# Handoff Brief — Cost Governance

**For:** the general-purpose Agent dispatched to build the cost-governance component.
**From:** the primary persona, 2026-04-20 09:08 CDT.
**Status:** awaiting owner's review of this brief; not yet dispatched.

---

## 1. What you are building

The cost-governance primitive for pOS on the `pos-v2` branch of `the existing workspace root`. It enforces aggregate budget ceilings (money / tokens / `time_seconds`) across scope, session, and rolling-window dimensions via a sidecar `CostLedger` + activation-wrap pattern composed as the **innermost** wrap in the chain (cost registers first → reversibility wraps around it → safety wraps around that → orig_activate at the core).

The work is greenfield Python on `pos-v2`. It consumes sealed components — including the now-sealed safety layer and reversibility primitive — as read-only surfaces. It does not amend any of them.

## 2. Authoritative documents (read in this order)

1. **This brief** — gives you the objective, constraints, acceptance criteria in operational form.
2. **`docs/rebuild/components/cost-governance/proposal.md`** — the contract approved. Binding. Halt and signal rather than deviate.
3. **`docs/rebuild/components/cost-governance/research.md`** — design detail, SQL schema, sequence diagrams, prior-art survey. Reference only; the proposal is the contract.
4. **`docs/rebuild/spec/pos-v2-objectives-spec.md`** — spec v1.0 + v1.1 + v1.2 addenda.
5. **`docs/rebuild/STATE.md`** — governing rules for the rebuild.

**Precedents to emulate** (all four on `pos-v2`, all sealed):
- `objective-tracker/src/store.py` + `runtime.py` — sidecar table + pyee subscription pattern.
- `safety-layer/src/ipc_wiring.py` — IPC-handler wrap of `activate_scope` without amending the orchestrator.
- `reversibility-primitive/src/ipc_wiring.py` — second wrap composing with safety's; the four-wrap chain is your third.
- `observability-aggregator/src/retention.py` — retention-task pattern for the 30d/365d decaying retention.

Scope-of-work surfaces to consume (verified by research §0, use verbatim):
- `ScopeSpec.budget.time_seconds / tokens / money_cents` (each `Optional[int]`, `ge=0`).
- `BudgetDebited` / `BudgetRefunded` / `StateTransitioned` events via `ScopeRuntime.emitter.on("*", handler)`.
- `ScopeRuntime.per_prompt_costs()` — already delivers v1.1 R12; reference, do not re-implement.

## 3. The objective (single sentence)

Deliver cost governance such that a scope whose declared budget would push any applicable aggregate ceiling (session or any configured rolling window) past its cap cannot activate, a user-facing throttle notification fires at a configurable pre-ceiling threshold (default 80%), real-time spend totals are queryable per scope / session / rolling window with OTel surfacing, and the decaying-retention pattern (30d reservations, 365d session rollups, indefinite rolling rollups) is honoured — all without amending any sealed component.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** scope-of-work, orchestrator, graceful-degradation, primary-persona, objective-tracker, observability-aggregator, self-upgrade, safety-layer, reversibility-primitive, memory-system — all sealed on `pos-v2`. If you conclude an amendment is required, halt and signal with named component + surface + the sidecar/wrap alternative you tested first.
- **Wrap registration order is load-bearing.** Per ruling recorded #1: cost registers FIRST (innermost), then reversibility wraps, then safety wraps. Dispatch flows **safety → reversibility → cost → orig_activate**. The integration test is mandatory and mirrors `reversibility-primitive/tests/test_safety_wrap_composition.py`.
- **Deterministic enforcement.** Ceiling refusal is a Pydantic-validated raise from the wrap before `orig_activate` runs. No LLM inference inside the wrap or ledger.
- **Throttle warning ships in v1.0.** Per ruling recorded #2 and spec v1.0. Emit `pos.cost.ceiling_warning` span + one `OneOnOneChannel` dispatch when prospective reservation would push aggregate spend ≥ `warning_fraction` (default 0.8) of any ceiling. Fire once per crossing, not repeatedly per debit.
- **Decaying retention.** Per ruling recorded #3: 30d reservations after `reconciled_at`, **365 days** session rollups after `ended_at`, indefinite rolling rollups.
- **One-on-one channel only** for throttle notifications. Reuse `OneOnOneChannel` from `primary_persona.introduction`; inherit the `is_group=True` rejection.
- **Error-code range `-32060..-32069`.** No overlap with safety (`-32040..-32049`) or reversibility (`-32050..-32059`).
- **A1 correction held.** `trace.get_tracer("pos.cost_governance")` only; do not construct a `TracerProvider`.
- **Zero carryover from current pOS.**
- **Max-first.**
- **Halt on deviation.**

## 5. Acceptance (ODD — 28 criteria, in proposal §4)

C1: pass-through verification (scope-of-work enforces "at least one axis declared").
C2–C8: activation gate matrix — three ceilings (scope/session/rolling) × three axes (money/tokens/time), plus independence on `None`-axes and baseline pass case.
C9–C13: reservation lifecycle — insert on pass, in-place rollup updates on debit/refund, reconcile on terminal.
C14–C15: throttle / 80% warning — configurable, fires once at crossing.
C16: concurrent-activation serialisation via `IPCServer` async dispatch.
C17–C18: rolling-window rollup idempotence under clock skew and re-runs.
C19–C21: retention — 30d reservations, 365d session rollups, indefinite rolling.
C22: ceiling adjustment via IPC — audit-logged, applies to new activations only.
C23–C26: cross-cutting integration — no sealed-component mutation, aggregator-routed OTel, one-on-one channel, no legacy imports.
C27–C28: structural-impossibility defence — Pydantic + SQL `CHECK` on every amount field, config validation refuses invalid fractions and negative ceilings.

Each is an objective. Tests target the criterion directly. Negative cases re-extend as positive objectives — if you find one worth naming, add it as C29 and explain in the commit message.

## 6. Verify-against-code discipline

Before relying on any sealed-component surface, open the file on `pos-v2` and confirm the symbol exists with the shape you expect. Four surfaces to verify first — the research did this, but re-verify in case `pos-v2` has moved:

- **`ScopeSpec.budget` field names** — exactly `time_seconds` (NOT `seconds`), `tokens`, `money_cents`. All `Optional[int]` with `ge=0`. Per-axis `time_policy` / `tokens_policy` / `money_policy` exist as `BudgetExhaustionPolicy`.
- **`BudgetDebited` event shape** — `prompt_name`, `model`, `input_tokens`, `output_tokens`, `money_cents`, `call_id` on `scope-of-work/src/events.py`. `BudgetRefunded` reverses by `call_id`.
- **`ScopeRuntime.emitter`** — pyee emitter; `on("*", handler)` subscription pattern.
- **IPC `activate_scope` handler registered on `IPCServer`** — orchestrator's `_register_ipc_methods` runs first; workspace bootstrap wraps after.

If any proposal-level claim doesn't match the code, halt and signal with named file and symbol.

## 7. inferences recorded (proposal §8) — challenge any that feel wrong

Eight items in the proposal are the primary persona's extrapolation rather than the owner's direct words:

1. Default rolling windows ship as daily + hourly, money-only.
2. `warning_fraction` default 0.8.
3. Session boundary = orchestrator process lifecycle.
4. Ceiling-adjustment does NOT re-check active reservations.
5. Budget-extension over-commit emits `pos.cost.ceiling_post_hoc_overrun` as diagnostic only.
6. Reservations prune 30d after reconciliation.
7. Rolling-window rollups retained indefinitely.
8. Ceiling adjustment accepts absolute `new_value`, not delta.

Challenge any with a halt signal and proposed alternative. Not load-bearing unless the owner confirms.

## 8. Estimate

**30–40 AI-minutes wall-clock. Red line at 45.**

Anchor components: reversibility ~30 min, safety ~35 min. Cost governance is structurally between the two — simpler than safety (no kill engine), more surface than reversibility (three primary tables + one scheduled task).

**If the build exceeds 45 minutes, halt and signal.** The two specific failure classes to investigate on overrun: rolling-window interval-closure math under clock skew (§C17), or four-wrap composition subtlety in `ipc_wiring.py`.

## 9. What I need back

On completion:

1. **Paths to the commits on `pos-v2`.** Atomic per phase acceptable; single cohesive commit acceptable.
2. **Test results** — every C-criterion (C1–C28, plus any C29+ you added) mapped to a passing test. If any is unsatisfied, name it and explain.
3. **Sealed-component diff check** — `git diff --stat f657f8c..<your-head>` should show only `cost-governance/` changes. Any other delta is a halt-signal.
4. **primary-persona inferences you challenged** and the alternative you chose (or halted on).
5. **Any halt signals** — named component + surface + what you tried first.
6. **Actual wall-clock vs the 30–40 min estimate.**

Return summary: under 500 words. Code and tests carry the detail.

## 10. Failure modes I am watching for

- "Improving" the spec while building. Don't — file enhancement ideas in the commit message for a later component.
- Monkey-patching a sealed component. Halt and signal.
- Skipping structural enforcement and replacing it with a runtime nag. Pydantic `ge=0` + SQL `CHECK` are the enforcement.
- Registering the wraps in the wrong order. Cost innermost — registers first. An integration test must cover the call chain explicitly: safety kill → safety ask → safety danger-op → reversibility → cost.
- Emitting the throttle warning multiple times per debit. Fire once at the crossing, not per-event.
- Building an in-memory ceiling cache that forgets to re-read after `cost.adjust_ceiling`. The cache is a performance detail; correctness requires the adjustment to apply to subsequent activations.
- Letting the estimate slip past 45 minutes quietly. Halt at 45 and signal scope-creep for triage.

---

**End of brief.** the owner reviews; on the owner's green light, dispatch follows.
