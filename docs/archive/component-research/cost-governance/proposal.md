# Proposal — Cost Governance

**Component:** Cost Governance — enforces aggregate budget ceilings (money / tokens / time_seconds) across scope, session, and rolling-window dimensions via a sidecar `CostLedger` + activation-wrap pattern composed as the innermost wrap in the chain.
**Status:** DRAFT — awaiting owner's approval before brief authoring.

**Branch:** `pos-v2`. **Language:** Python 3.13.
**Consumes (no amendment):** scope-of-work, safety-layer, reversibility-primitive, orchestrator, observability-aggregator.

---

## 1. Objective

Deliver cost governance such that:

- A scope whose declared budget plus already-reserved and committed spend would exceed any applicable ceiling (scope's own, session aggregate, or any configured rolling-window aggregate) cannot activate. Deterministic refusal.
- Real-time spend totals are queryable per scope, per session, and per rolling window — via IPC and via OTel emission.
- A pre-ceiling notification fires at a declared threshold (spec's "throttling") so the user is warned before the hard cap.
- Refusal is structurally distinguishable from safety and reversibility refusals (error-code range `-32060..-32069`).
- The decaying-retention pattern applies: per-scope reservations prune 30 days after reconciliation; session rollups retained 365 days; rolling-window rollups retained indefinitely (low volume, audit record).
- The component ships without amending any sealed component — sidecar + activation wrap layered as the innermost wrap in the four-wrap chain.

The design shape and acceptance evidence are in `research.md`; this proposal encodes the owner's three rulings and states the hard contract the builder works against.

---

## 2. the owner's rulings (locked inputs)

| # | Question | Ruling |
|---|----------|--------|
| 1 | Gate ordering in the four-wrap chain | **Cost innermost** (Option B). Registration order: cost first, reversibility second, safety third. Dispatch: safety → reversibility → cost → orig_activate. Rationale: system-kill and structural refusals surface before aggregate-affordability refusals — the most semantically-prior reason fires first. |
| 2 | Throttling / 80%-ceiling warning | **Ship in v1.0.** The spec explicitly names "throttling activates at a declared threshold below the ceiling and produces a user-facing notification before the ceiling is reached" as an acceptance criterion. Small code surface; ships with the rest of v1.0. |
| 3 | Session rollup retention | **365 days** (not 30). Rollup rows are small; longer window supports annual spend audit and monthly memory-system summaries when that indexer lands. |

---

## 3. Design shape (summary — detail in `research.md`)

### 3.1 Composition

A new package `cost-governance/` (Python, on `pos-v2`) exposes `CostController` composing:

- **`CostLedger`** — subscribes to `ScopeRuntime.emitter` (pyee) for `BudgetDebited`, `BudgetRefunded`, and `StateTransitioned` events. Updates session and rolling rollups in-place per debit; reconciles reservations on terminal state.
- **`Reservation`** — Pydantic-validated record (`scope_id`, `session_id`, per-axis reserved + actual amounts, `state ∈ {active, reconciled}`, timestamps). `ge=0` on every amount field (clause-(g) pattern — negative reservation is structurally impossible).
- **Activation-gate wrap** — IPC handler wrap of `activate_scope`, registered **first** so it becomes the innermost wrap at dispatch. Reads declared budget from `spec.budget.time_seconds / tokens / money_cents`; queries current rollups + active reservations; refuses if aggregate would exceed any applicable ceiling.
- **`CostConfig`** — loaded from `~/.pos/cost/ceilings.yaml`. Session ceilings (money / tokens / time_seconds, each `Optional[int]`) plus a list of rolling-window configurations, each with `window_kind`, `duration_seconds`, and per-axis caps.
- **Rollup runtime** — scheduled task; runs at `min(window.duration_seconds) / 10` interval (6 minutes for the default daily+hourly config). Idempotent interval-closure math keyed on `(window_kind, interval_end_unix)`.
- **Throttle notification** — when a scope's reservation would push aggregate spend past a configurable fraction (default 80%) of any ceiling, the ledger emits `loam.cost.ceiling_warning` and dispatches via `OneOnOneChannel` (one-on-one inherited; no group-channel escape).
- **SQLite store** at `~/.pos/cost/cost.sqlite` with four tables: `reservations`, `session_rollups`, `rolling_rollups`, `ceiling_adjustments`. WAL + `synchronous=FULL` + `foreign_keys=ON`.
- **CLI** — `pos cost status`, `pos cost scope <id>`, `pos cost session`, `pos cost rolling`, `pos cost adjust`.
- **Observability** — emits `loam.cost.*` spans via `trace.get_tracer("loam.cost_governance")` (aggregator-registered `TracerProvider`).

### 3.2 Composition with safety + reversibility

Cost registers **first** so it becomes the **innermost wrap**. Safety and reversibility then wrap around it. Call chain when an `activate_scope` IPC lands:

```
client → safety_wrap
           ├── system-kill block (if active)
           ├── ask-gate check
           └── dangerous-op gate check
                  ↓
            reversibility_wrap
                  └── activation_gate.check(spec)
                         ↓
                     cost_wrap
                        └── ledger.reserve_or_refuse(spec)
                               ↓
                           orig_activate → scope binding + start
```

Refusal precedence at dispatch (first-fired wins):
1. Safety system-kill (`-32042`)
2. Safety ask-gate pending (`-32040`)
3. Safety dangerous-op (`-32041`)
4. Reversibility missing-compensation (`-32050`)
5. Cost scope-budget (`-32060`)
6. Cost session-ceiling (`-32061`)
7. Cost rolling-ceiling (`-32062`)

Structural refusals (reversibility) and approval refusals (safety) surface before aggregate-affordability refusals (cost). If a scope would fail both safety and cost, the user sees the safety reason — more actionable.

### 3.3 Refusal boundary (error codes)

Reserve `-32060..-32069` to cost governance. Ship three:

- `-32060 COST_SCOPE_BUDGET_EXCEEDED` — scope's own declared budget exceeds remaining aggregate (diagnostic; signals a mid-session ceiling reduction without clearing reservations).
- `-32061 COST_SESSION_CEILING_EXCEEDED` — session aggregate on the named axis would exceed cap.
- `-32062 COST_ROLLING_CEILING_EXCEEDED` — named rolling-window aggregate on the named axis would exceed cap.

`-32063..-32069` reserved for future (ceiling-adjustment validation, reservation-reconcile errors).

### 3.4 Reservation arithmetic

For each axis where the scope declares a non-`None` cap:

```
committed_spend[axis] + active_reservations_sum[axis] + declared[axis] > ceiling[axis]  →  refuse
```

Applied for the session ceiling and each configured rolling-window ceiling. `None` on a declared axis means "this scope contributes nothing on this axis" — honest declaration, not validation failure.

Reservation row persists on gate pass; reconciles on terminal state (replace reserved with actual, flip `state='reconciled'`). Reservation audit preserved; row pruned 30 days after `reconciled_at`.

---

## 4. Acceptance criteria (ODD — 22 objectives)

Each is authored as an objective; tests target it directly.

### 4.1 Budget declaration (pass-through — scope-of-work enforces)

- **C1.** A scope created with no axis declared on `Budget` is refused at construction by scope-of-work (`model_post_init`). Cost governance does not duplicate — a test asserts the behaviour remains and exists upstream.

### 4.2 Activation-gate enforcement — scope × axis matrix (research §2.9)

- **C2.** A scope declaring `money_cents = X` with session money remaining `< X` → cost wrap raises `-32061 COST_SESSION_CEILING_EXCEEDED` with axis `money`. Orchestrator `orig_activate` does not run; scope stays `proposed`.
- **C3.** A scope declaring `tokens = X` with session tokens remaining `< X` → same with axis `tokens`.
- **C4.** A scope declaring `time_seconds = X` with session time remaining `< X` → same with axis `time`.
- **C5.** A scope declaring `money_cents = X` with rolling-window (daily) money remaining `< X` → cost wrap raises `-32062 COST_ROLLING_CEILING_EXCEEDED` with axis `money`, `window_kind=daily`.
- **C6.** Rolling-window (hourly) money — same pattern for the hourly window.
- **C7.** Per-axis independence: a scope declaring `money_cents` but with `tokens = None` and `time_seconds = None` is checked only on the money axis; `None`-axes contribute zero to their respective reservation math.
- **C8.** Baseline pass case: a scope declaring budget well under every ceiling passes the gate; `INSERT reservations` fires; `loam.cost.reservation_created` span emitted; `orig_activate` runs.

### 4.3 Reservation lifecycle (research §2.3, §4.2)

- **C9.** On gate pass, `reservations` row is INSERTed with `state='active'` and the declared amounts in reserved columns. Timestamps populated.
- **C10.** On `BudgetDebited` for an active scope, the session rollup + any applicable rolling-window rollup update in-place (total += debit amount). Reservation row accumulates actual values.
- **C11.** On `BudgetRefunded`, rollups decrement correctly.
- **C12.** On `StateTransitioned(to_state=terminal)` (completed / failed / cancelled / escalated), the reservation row flips to `state='reconciled'`, `reconciled_at` populated, final `actual_*` values written. `loam.cost.reservation_reconciled` span emitted.
- **C13.** A scope cancelled pre-debit has `actual_*` = 0; ceiling slack released for subsequent activations.

### 4.4 Throttling / pre-ceiling warning (ruling #2)

- **C14.** When a prospective reservation would push aggregate spend ≥ 80% of any ceiling (session or rolling), the ledger emits `loam.cost.ceiling_warning` and dispatches a single notification via the `OneOnOneChannel` (group-channel refusal inherited). The warning fires before the reservation is written — so a scope that activates at 85% of cap triggers the warning once, not repeatedly per debit.
- **C15.** The 80% threshold is configurable via `CostConfig.warning_fraction` with default `0.8`. Values outside `(0.0, 1.0)` are refused at config load.

### 4.5 Concurrent activation serialisation (research §2.3 Q10)

- **C16.** Two concurrent `activate_scope` IPC calls whose combined declared spend exceeds a ceiling are serialised by the `IPCServer` async dispatch such that exactly one succeeds and the second raises `-32061`. Integration test via `asyncio.gather`.

### 4.6 Rolling-window rollup (research §5)

- **C17.** The rollup task closes expired intervals idempotently: running it twice produces no duplicate rows; running it after a time-jump (clock skew / suspend-resume) closes all skipped intervals correctly.
- **C18.** `rolling_rollups` rows carry both `interval_start_unix` and `interval_end_unix`; PRIMARY KEY on `(window_kind, interval_end_unix)` prevents duplicates.

### 4.7 Retention (ruling #3, research §5.2)

- **C19.** Reservations with `state='reconciled'` and `reconciled_at < now - 30d` are pruned by the retention task. Active reservations are never pruned regardless of age.
- **C20.** `session_rollups` with `ended_at < now - 365d` are pruned. Open sessions are never pruned.
- **C21.** `rolling_rollups` are never pruned by time alone. (Low volume; audit record.)

### 4.8 Ceiling adjustment (research §2.2 Q7)

- **C22.** `cost.adjust_ceiling(ceiling_kind, axis, new_value, reason)` IPC writes a `ceiling_adjustments` row (audit), updates the in-memory cache, emits `loam.cost.ceiling_adjusted`, and returns `{ok: True, audit_record_id}`. Does NOT re-check active reservations — adjustments apply to new activations only.

### 4.9 Cross-cutting integration

- **C23.** `git diff --stat f657f8c..<cost-commit>` shows only `cost-governance/` changes. Zero deltas to any sealed component.
- **C24.** All OTel spans flow through `trace.get_tracer("loam.cost_governance")`. The component does not construct its own `TracerProvider`.
- **C25.** All user-facing notifications use `OneOnOneChannel` from `primary_persona.introduction`; `is_group=True` rejection inherited.
- **C26.** Zero imports from current-gen Ruby pOS rules-file machinery.

### 4.10 Structural-impossibility defence-in-depth

- **C27.** `Reservation` construction with any reserved or actual amount `< 0` raises Pydantic `ValidationError`. SQL `CHECK` constraints match the Pydantic constraints.
- **C28.** `CostConfig` refuses to load a YAML with a negative ceiling on any axis or `warning_fraction` outside `(0.0, 1.0)`.

---

## 5. Constraints

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb. **Test-only:** pytest, pytest-asyncio.
- **No amendments to sealed components.** Halt and signal with named component + surface + sidecar/wrap alternative considered.
- **Wrap registration order is load-bearing.** Cost first (innermost), then reversibility, then safety. Covered by integration test mirrored on `reversibility-primitive/tests/test_safety_wrap_composition.py`.
- **Deterministic enforcement.** Ceiling refusal is a Pydantic-validated raise from the wrap before `orig_activate` runs. No LLM inference.
- **Decaying retention.** 30d reservations, 365d session rollups, indefinite rolling rollups.
- **One-on-one channel only** for throttle notifications.
- **A1 correction held.** `trace.get_tracer(...)` only; no TracerProvider construction.
- **Error-code range `-32060..-32069`.** No overlap with safety or reversibility.
- **Max-first.**
- **Zero carryover from current pOS.**
- **Halt on deviation.**

---

## 6. Suggested file layout (research Appendix A)

```
cost-governance/
  src/
    spec.py              # Reservation, SessionRollup, RollingRollup, CeilingAdjustment, error codes
    config.py            # CostConfig loader from ~/.pos/cost/ceilings.yaml
    store.py             # SQLite schema + upsert/query for four tables
    ledger.py            # CostLedger core: reserve_or_refuse, reconcile, pyee subscriptions
    rollup.py            # rolling-window interval-closure task
    controller.py        # CostController composes ledger + store + notifier
    ipc_wiring.py        # register_cost_governance_ipc — innermost wrap registration
    observability.py     # loam.cost.* span helpers
    notification.py      # 80% threshold OneOnOneChannel dispatch
    cli.py               # `pos cost` subcommands
  tests/
    test_ceiling_enforcement.py        # C2–C8
    test_reservation_lifecycle.py      # C9–C13
    test_throttle_warning.py           # C14, C15
    test_concurrent_serialisation.py   # C16
    test_rolling_rollup.py             # C17, C18
    test_retention.py                  # C19–C21
    test_ceiling_adjustment.py         # C22
    test_ipc_wrap_composition.py       # integration test (4-wrap chain)
    test_no_sealed_amendments.py       # C23
    test_observability_routing.py      # C24
    test_one_on_one_channel_only.py    # C25
    test_no_legacy_imports.py          # C26
    test_structural_defence.py         # C27, C28
```

File cohesion is the builder's judgement to refine. Test list is the minimum mapped to acceptance criteria.

---

## 7. Build phases and estimate

**Calibrated AI-time estimate: 30–40 minutes wall-clock. Red line at 45.**

Anchors: reversibility ~30 min, safety ~35 min. Cost governance is structurally between them. Simpler than safety (no kill engine, no YAML floor). More surface than reversibility (three primary tables + one scheduled task).

If the build exceeds 45 minutes, halt and signal. Likely drag: rolling-window interval-closure math under clock skew, or 4-wrap composition subtlety.

Suggested phase shape (builder's call):

1. Pydantic schemas + store — C1 verification + C27, C28.
2. Config loader (ceilings.yaml) — C28.
3. `CostLedger` + pyee subscriptions — C9–C13.
4. Activation gate wrap (cost innermost) — C2–C8, C16.
5. Throttle notification — C14, C15.
6. Rollup task + retention task — C17–C21.
7. Ceiling adjustment IPC — C22.
8. CLI — `pos cost ...` family.
9. IPC wiring + composition test — wrap ordering.
10. OTel routing + cross-cutting tests — C23–C26.

Atomic commits per phase acceptable; single cohesive commit acceptable.

---

## 8. inferences recorded — flagged for the builder to challenge

These items are not direct quotes from the owner; challenge any with a halt signal and a proposed alternative:

1. **Default rolling windows ship as daily + hourly, money-only.** Research proposed; the owner did not explicitly name. If the builder thinks a different default set serves better (e.g. hourly + 4-hour), halt.
2. **`warning_fraction` default 0.8.** The spec says "threshold below the ceiling" without naming a value. 80% is conventional (AWS / GCP precedent). If the builder has reason to pick differently, halt.
3. **Session boundary = orchestrator process lifecycle.** Research recommended; there is no explicit session-id surface to bind to. If the workspace later needs finer session granularity, a schema migration handles it — but the v1.0 assumption is one-orchestrator-one-session. Challenge if wrong.
4. **Ceiling-adjustment does NOT re-check active reservations.** Research default (matches safety/reversibility mid-session-change semantics). If the builder believes active reservations should be refused retroactively when the ceiling is tightened below them, halt.
5. **Budget-extension interaction emits `loam.cost.ceiling_post_hoc_overrun` as diagnostic only.** Research §8 recommended; cost governance has no lever on an already-active scope. If the builder thinks the extension should itself be gated, halt (that would be a scope-of-work amendment anyway).
6. **Reservation rows prune 30d after reconciliation.** My extrapolation from decay-retention analysis candidate. Could be 7d or 90d depending on audit-query needs. Challenge if audit queries want longer retention.
7. **Rolling-window rollups retained indefinitely.** My call based on low volume (~10k rows/year for default config). If the builder sees a storage or query-performance concern, halt.
8. **Ceiling adjustment accepts absolute `new_value`, not delta.** Research §7.4 recommended to avoid sign confusion. If the builder thinks delta math is cleaner, halt.

---

## 9. Approval ask

sign-off on this proposal moves the component to `proposal_approved` and opens handoff-brief drafting. On brief review, the background agent is dispatched.

Specifically requesting approval of:

- The locked rulings in §2 as faithful to the conversation.
- The 28 ODD acceptance criteria in §4 (C1–C28) as the complete objective set.
- The constraints in §5 (wrap ordering, fail-closed, no amendments, decaying retention, error-code range).
- The 30–40 min estimate with 45-min red line.
- the primary persona's flagged inferences in §8 (approve as written, or adjust and re-land).

Approve as-is, approve with changes, or reject.
