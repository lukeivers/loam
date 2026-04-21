# Research — Cost Governance

**Component:** Cost Governance — enforces aggregate budget ceilings (money / tokens / wall-clock seconds) across scope, session, and rolling-window dimensions via a sidecar `CostLedger` + activation-wrap pattern composed after safety's and reversibility's wraps.
**Status:** research produced; ready for proposal authoring.
**Authored by:** general-purpose research agent, dispatched per the research plan at `components/cost-governance/research-plan.md`.
**Date:** 2026-04-20.
**Fact-verification baseline:** `pos-v2` HEAD — scope-of-work, safety-layer, reversibility-primitive, orchestrator, observability-aggregator sources all read directly before any design claim was asserted.

---

## 0. Fact-check summary (before design)

Two flags in the plan were verified against code first; the remaining design claims build on the verified substrate.

- **Q1 — `ScopeSpec.budget` field names.** Verified in `pos-v2/scope-of-work/src/spec.py` lines 91–142. The fields are **`time_seconds`** (not `seconds`), **`tokens`**, and **`money_cents`**, plus per-axis `time_policy` / `tokens_policy` / `money_policy` of type `BudgetExhaustionPolicy`. Each axis is `Optional[int]` with `ge=0`. `Budget` carries a `model_post_init` that raises on "no axis declared" — so at least one axis is required. `None` means "no cap on this axis"; `0` means "no budget granted" (exhaustion-immediate). `Budget` is `frozen=True, extra=forbid`. Helpers `Budget.cap_for(axis)` and `Budget.policy_for(axis)` are already present — the cost wrap will use them.

  - Design impact: the plan's proposed naming is subtly wrong (`seconds` → `time_seconds`). All code in the cost governance component must use the exact sealed names.
  - Design impact: the plan's proposal that `None` should be treated as "must declare for non-`fully_reversible`" is **stricter than what scope-of-work enforces today**. Scope-of-work accepts any single-axis declaration and leaves other axes `None` (= uncapped on that axis). Cost governance should respect this: a scope that declares money_cents but not tokens simply has no token cap; the ledger tracks what's declared and ignores what isn't. No cross-component amendment needed. (See §2.3 for the session/rolling-ceiling implication.)

- **Q16 — `BudgetDebit`-style emission on scope-of-work.** **Emission exists.** Verified in `pos-v2/scope-of-work/src/events.py` lines 82–110 and `runtime.py` lines 246–316. `BudgetDebited` carries `prompt_name`, `model`, `input_tokens`, `output_tokens`, `money_cents`, `call_id`. `BudgetRefunded` reverses a debit by `call_id`. Both are persisted to the event log AND fanned out via pyee (`ScopeRuntime._fan_out(scope_id, event)` → `emitter.emit(f"scope:{scope_id}", event)` and `emitter.emit("*", event)`). Cost governance can subscribe exactly like objective-tracker does (`ScopeRuntime.emitter.on("*", handler)`).

  - **Q16 is NOT a halt-signal.** No amendment to scope-of-work is required. The debit event shape is exactly what the ledger needs, including `prompt_name` for R12 per-prompt-type aggregation.

- **Bonus verification.** `per_prompt_costs()` already exists on scope-of-work's store (lines 226–266) — it returns per-prompt token + money totals across all scopes, with refunds subtracted via `call_id` join. v1.1 R12 ("per-prompt-type aggregation is queryable") is **already satisfied by scope-of-work**. Cost governance does not need to re-implement this; it references it or composes a session-filtered view.

- **Orchestrator `activate_scope` handler is a sealed IPC surface.** Verified in `orchestrator/src/orchestrator.py` lines 338–400 and `_register_ipc_methods` lines 610–688. The handler is registered on the shared `IPCServer` at orchestrator startup. Workspace bootstrap runs AFTER `_register_ipc_methods` and may override the registration by calling `server.register("activate_scope", wrapped)` — this is exactly how safety's and reversibility's wraps compose today (both captured as tests in `reversibility-primitive/tests/test_safety_wrap_composition.py`).

With the substrate verified, the design below commits to sidecar + activation wrap with no amendment to any sealed component.

---

## 1. Survey of existing patterns

The plan asks for four analogues; each is summarised and then mapped to what cost governance should borrow / reject.

### 1.1 OS resource limits — `rlimit`, cgroups

- **Pattern.** Hard and soft caps applied at process spawn or resource acquisition; kernel refuses the operation (setrlimit returns EPERM, cgroup OOM-kill, `ENOMEM` on allocation). Per-process AND cgroup-aggregate ceilings coexist.
- **What to borrow.** The *dual-tier* model — per-item (per-scope) cap AND aggregate (session/rolling) cap, enforced at the same point. Hard-refuse, not advisory. Structural.
- **What to reject.** Kernel-style kill-on-breach. pOS's scope primitive already has `BudgetExhaustionPolicy.request_extension` / `halt_and_signal` / `throttle` — the cost ledger's job is to prevent activation of an over-budget scope in the first place, not to kill an active one. Mid-flight enforcement is scope-of-work's job via the extension mechanism; cost governance is an *activation gate*.

### 1.2 Cloud cost governance — AWS Budgets, GCP Quotas

- **Pattern.** Budgets are a layer ABOVE resource allocation. Every provisioning call consults the budget; refusal is `QuotaExceededException`. Rollups happen continuously in the background; the budget is projected to end-of-period (e.g. "if you continue at this rate, you will exceed budget by day 28"). Alerts at 80% / 100% of cap.
- **What to borrow.** Separation of *budget* (governance layer) from *event log* (consumption layer). Cost governance is a pure consumer of scope-of-work's debit stream; it never mutates the event log. Separate SQLite store (`~/.pos/cost/cost.sqlite`) per the sidecar pattern.
- **What to reject — partially.** AWS projects forward ("you'll exceed at day 28"); pOS ships without projection. YAGNI: deterministic ceiling refusals at activation-time are the acceptance criterion. 80%-approaching alerts are flagged as a drop candidate (see §3.7). Projection, if it ever ships, is a v1.1 extension — not v1.0.

### 1.3 API rate limiting — token buckets, leaky buckets

- **Pattern.** A fixed-capacity "bucket" refills at a rate; every request consumes N tokens; when empty, requests are refused or queued. Rolling windows are implicit in the refill rate.
- **What to borrow.** The rolling-window semantics — "spend in the last K hours" is exactly a leaky-bucket projection. Cost governance's rolling-window rollup is a moving window, not a calendar-hour rollup; this is the user-facing mental model ("I've spent $X in the last 24 hours," not "I've spent $X since midnight UTC").
- **What to reject.** Token-bucket *refill rate* is not the model cost governance wants. The rolling window is a **retention slice of actual spend**, not a "budget that replenishes at rate R." the owner's spend limits are flat caps over rolling windows, not rate caps.

### 1.4 Database transaction budgets — query cost estimation

- **Pattern.** Postgres' `statement_timeout`, `work_mem`, query planner's estimated cost. Enforcement is after the planner has already estimated; refusal at timeout boundary; structurally the transaction is "reserved" before execution begins.
- **What to borrow.** The *reservation model* — reserve capacity at activation, reconcile against actual consumption on completion. Prevents the over-commitment anti-pattern where two concurrent activations each individually fit but together overflow. Database query budgets are the closest analogue to what cost governance is doing (though pOS is simpler: one monetary axis, not eight resource axes).
- **What to reject.** Planner-style estimation. pOS uses *declared* budget as the reservation amount (scope author declares "this scope will use up to X"). No cost estimation; deterministic Pydantic-validated reservation.

### 1.5 Closest prior-art one-liner

Cost governance is **reservation-based aggregate-ceiling enforcement with declared budgets**, not a rate limiter, not a projected budget, not a post-hoc auditor. Semantically closest: AWS Budgets minus projection, or a Postgres-style transaction budget generalised to three dimensions.

---

## 2. Recommended design shape — nine question groups

### 2.1 Budget declaration (plan Q1–Q3)

- **Q1 recommendation.** Use the sealed names verbatim. `ScopeSpec.budget.time_seconds`, `.tokens`, `.money_cents`. All optional; at least one required (scope-of-work's `model_post_init` enforces). `None` on an axis means "no cap on this axis"; cost governance treats `None` as "no scope-local contribution on that axis" — the scope does not contribute to the session/rolling ceiling on that axis.

- **Q2 recommendation.** `ScopeSpec.budget` carries *only* the scope's declared cap. Session and rolling-window ceilings live in cost-governance configuration (`~/.pos/cost/ceilings.yaml`) — not in the scope spec. This matches the precedent: safety's threshold lives in `safety.yaml`, not on the scope. The scope author declares what their scope will use; the workspace administrator declares the aggregate ceilings.

- **Q3 recommendation.** Reject the plan's "must-declare for non-`fully_reversible`" stipulation. scope-of-work already enforces "at least one axis declared"; layering a second "must declare money for non-reversible scopes" rule in cost governance would duplicate (and fight) safety's money-threshold gate. The clean boundary is:
  - scope-of-work: enforces "at least one axis declared."
  - safety: enforces "if money_cents declared AND money_cents >= threshold, hard gate fires."
  - cost governance: enforces "aggregate ceilings respected by declared spend." If a scope declares `money_cents=None`, it contributes zero to the money-axis reservation — an honest declaration that the scope does not spend money.

  Adding cost-governance restriction on `None` would turn an honest declaration into a validation failure — noise, not signal.

### 2.2 Session and rolling-window ceilings (plan Q4–Q7)

- **Q4 recommendation.** Workspace YAML config at `~/.pos/cost/ceilings.yaml`, loaded at cost-governance init. Shape:

  ```yaml
  session:
    money_cents: 5000          # $50.00 per session
    tokens: 2000000            # 2M tokens per session
    time_seconds: null         # no session wall-clock cap (default)
  rolling:
    - window_kind: daily
      duration_seconds: 86400
      money_cents: 20000       # $200.00 per rolling 24h
      tokens: null
      time_seconds: null
    - window_kind: hourly
      duration_seconds: 3600
      money_cents: 2000        # $20.00 per rolling 60min
      tokens: null
      time_seconds: null
  ```

  IPC-call-at-session-open is a later-value override — not needed for v1.0 (YAGNI). The YAML covers the acceptance criterion and keeps configuration surface in one place.

- **Q5 recommendation.** Support multiple concurrent rolling windows — the YAML shape above is a **list**. The plan's parenthetical ("plural window vs windows") is the right instinct; multiple windows cover the "$200/day AND no $20+ hour-spikes" case naturally. The data model for rolling rollups is keyed on `(window_kind, interval_end)` already; supporting N windows is free at the schema level. Default shipped config: daily + hourly, money-only.

- **Q6 recommendation.** Reuse the orchestrator's `session_id`. Cost governance observes it from the orchestrator's emitted context (span attribute `pos.orchestrator.session_id`) OR from an injection at init time. No new session concept. This keeps safety's session-kill semantics aligned with cost governance's session rollup — one session boundary, one rollup boundary.

  - **Minor concern — resolved.** The orchestrator's current session construct is implicit (the process lifecycle). When a new orchestrator process starts, a new session begins. Cost governance treats the `session_rollup` key as `(orchestrator_pid, started_at)` tuple at init, falling back to `started_at` alone if pid is unreliable across restarts. This is a workspace-local convention — the session boundary is "one orchestrator run."

- **Q7 recommendation.** Yes, mid-session ceiling adjustment is supported, exposed via IPC method `cost.adjust_ceiling(ceiling_kind, axis, delta, reason)`. Audit-logged as a typed Pydantic record in the cost store. Not auto-approved — the IPC method is intended to be called after the owner approves an overage via the one-on-one channel; it's structural support for the approval flow, not a bypass. YAGNI-alternative considered and rejected: in-session adjustment without approval is the approval flow.

### 2.3 Pre-activation gate logic (plan Q8–Q11)

- **Q8 recommendation — reservation model with declared-budget arithmetic.** At activation the wrap reads:
  - `declared = spec.budget.money_cents` (and same for tokens/time_seconds)
  - `active_reservations_sum[axis]` — sum of `declared` across currently-active-or-pending scopes in this session (and matching rolling windows).
  - `committed_spend[axis]` — sum of `(BudgetDebited - BudgetRefunded)` events that have been persisted.

  The gate rejects activation if, for any axis where `declared` is set:

  ```
  committed_spend[axis] + active_reservations_sum[axis] + declared > ceiling[axis]
  ```

  The ceiling is checked for each applicable ceiling (session + each configured rolling window).

  Rationale — declared vs actual: declared is the scope's own contract. If the scope exceeds its own budget mid-flight, scope-of-work's `_enforce_budget_exhaustion` kicks in and the scope pauses/escalates; the ceiling never sees an over-spend. Using actual spend alone (without the reservation) over-admits: two scopes each with declared $20 could both activate against a session cap of $30, then each spend $20, and the session cap would blow out.

- **Q9 recommendation — persisted reservation row.** On activation gate pass, write a `Reservation` row to the cost store with `scope_id`, `session_id`, per-axis reserved amounts, `reserved_at`, `state="active"`. On scope terminal state (completed/failed/cancelled/escalated), the pyee-subscribed reconciler reads actual spend from scope-of-work, replaces the reservation's reserved amounts with actual amounts, and flips state to `"reconciled"`. The row stays in the store until decay prunes it.

  Compute-on-read (reservations derived from open scopes without a dedicated table) was considered; rejected because (a) pyee events on scope terminal states require a place to land them idempotently, and (b) audit replay wants a typed record of "here is what was reserved at activation time," which compute-on-read loses.

- **Q10 recommendation.** Activation serialisation is handled correctly by the IPC wrap without further locking. Two concurrent `activate_scope` IPC calls land on the same `IPCServer._handlers["activate_scope"]`; the server's async handler path dispatches them sequentially (asyncio cooperative). The cost wrap therefore sees scope-A's `check_gates → write reservation` complete before scope-B's check begins — the second's read of `active_reservations_sum` includes A's reservation and correctly refuses if the aggregate would exceed.

  - This is the same serialisation safety's wrap depends on. Verified by reading safety's wrap (lines 145–161 of `safety-layer/src/ipc_wiring.py`) — there is no extra lock in safety, because the IPC dispatch is already the serialisation point.
  - Edge case: two workspace bootstrap processes. Not a real concern — pOS is single-orchestrator by design; `IPCServer.start()` binds to a Unix socket and refuses concurrent bind. One orchestrator, one IPC server, one dispatch queue.

- **Q11 recommendation.** Reservations release via a pyee subscription on scope state transitions. The cost ledger subscribes at construction:

  ```python
  scope_runtime.emitter.on("*", self._handle_scope_event)
  ```

  The handler checks `isinstance(event, StateTransitioned)` and — if `to_state` is terminal — reconciles the reservation (replace reserved with actual, flip state). `BudgetDebited` events are handled in the same subscription to update the session/rolling rollups in-place as spend accumulates. `BudgetRefunded` subtracts from the rollup.

  Failure handling: the reconciler is idempotent (keyed by `scope_id` + `session_id`) and safe under re-subscription. If pyee drops an event (shouldn't; pyee is in-process and reliable), a scheduled `reconcile_all_open_reservations()` task runs on cost-governance startup and every 5 minutes thereafter to detect orphans (reservation in `active` state whose scope-of-work projection is terminal).

### 2.4 Integration with safety and reversibility (plan Q12–Q14)

- **Q12 recommendation — orthogonal refusals.** Safety's `DangerousOpGate` fires on `spec.budget.money_cents >= money_threshold_cents` (verified, `dangerous_op.py` line 83). This is a **per-scope one-shot threshold**: any scope that spends more than $10 (default) fires safety, period. Cost governance's check is fundamentally different: does adding this scope's declared budget push the *aggregate* over the session or rolling ceiling?

  - A scope can fail cost governance and not safety (small per-scope declare, but aggregate crowded).
  - A scope can fail safety and not cost governance (over-threshold per-scope, but session cap untouched).
  - A scope can fail both (over-threshold and aggregate crowded).

  The gates are orthogonal on condition but compose on ordering (see Q13). No coordination logic required — each gate raises independently with its own error code.

- **Q13 recommendation — cost-third (per the plan's default).** Call chain: `reversibility → safety → cost → orig_activate`.

  Registration order (critical — each wrap captures the prior handler as its `orig_activate`):

  ```
  1. Orchestrator registers activate_scope  (step in _register_ipc_methods)
  2. Reversibility wraps it                 (register_reversibility_ipc)
  3. Safety wraps it                        (register_safety_ipc)
  4. Cost governance wraps it               (register_cost_governance_ipc)
  ```

  At dispatch, the call flows: `wrapped_cost → wrapped_safety → wrapped_reversibility → orig_activate`. The plan's stated order ("reversibility → safety → cost → orig_activate") matches this — cost is LAST-registered and therefore FIRST-dispatched after the wraps unwind.

  - **Wait — the plan says cost-third in ordering sense (cost after safety), but cost is the outermost wrap at registration time.** Let me resolve the ambiguity unambiguously:

    - **Registration order (temporal):** reversibility first, safety second, cost third.
    - **Call order (dispatch):** cost outermost, safety middle, reversibility innermost, orig_activate at core.
    - **Refusal precedence (what fires first at request time):** cost's check runs first at the Python level because it's the outermost wrap. A caller who is going to be refused for BOTH cost AND safety reasons sees the cost error, not the safety error.

  - **Does this ordering matter for correctness?** Three considerations:

    1. *Safety has a system-kill block at activation* — refuses ALL activation when system-kill is active, independent of cost. If cost is outermost and refuses first, a cost-governance-exceeded error precedes the system-kill error. This **is a regression** vs. today's behaviour where safety fires the system-kill error first. Acceptable? Marginal. System-kill is the harder stop and should be the first-surfaced reason; a cost overage hidden behind a cleared system-kill is confusing.

    2. *Reversibility's refusal is about structural correctness* (compensatable + no binding = malformed activation). Cost governance's refusal is about aggregate limits. Reversibility's refusal is semantically "prior" — you shouldn't hear "out of budget" for an activation that's structurally inadmissible.

    3. *Safety's ask-gate pending is a deferral, not a refusal* — the scope is parked until the user decides. A scope that would also fail cost governance gets "cost-exceeded" instead of "awaiting your approval," which is less informative.

  - **Recommendation — ordering the plan picked is defensible but I want to flag these UX wrinkles for ruling recorded.** Three options:

    - **Option A (plan's default) — cost outermost.** Order: cost → safety → reversibility → orig. Rationale: cost is the most transactional / most aggregated; fits the plan's framing.
    - **Option B — cost innermost (between safety and orig).** Order: reversibility → safety → cost → orig. Rationale: structural errors (reversibility, system-kill, safety ask) are more informative to surface first; cost is the last gate before orig. Requires cost to register BEFORE reversibility and safety.
    - **Option C — safety outermost.** Order: safety → reversibility → cost → orig. Rationale: system-kill is the hardest stop; safety gates run first; reversibility validates structure; cost checks aggregate. Requires reordering the existing reversibility → safety composition.

  **Recommended: Option B.** Registration order becomes: cost first, reversibility second, safety third. Dispatch: safety → reversibility → cost → orig. Rationale: surfaces the most-semantically-prior refusal first (system-kill > structural > aggregate). Cost fires *last*, which is correct — by the time we've passed safety and reversibility, the activation is structurally admissible and we only need to check aggregate affordability. This reorders the registration but keeps each individual wrap unchanged.

  **Flag for ruling recorded:** the plan default is Option A; I'm recommending Option B. If the owner prefers Option A for consistency with the plan's framing, that's defensible — Option A is documented and ships cleanly. Option B improves error-surfacing UX. Either is structurally sound.

- **Q14 recommendation — error codes `-32060..-32069`.** Reserve the block. Ship these three:

  - `-32060` `COST_SCOPE_BUDGET_EXCEEDED` — scope's own declared budget exceeds the remaining aggregate on any ceiling (shouldn't happen if the scope is well-formed; signal of a ceiling mid-session-reduction without clearing reservations).
  - `-32061` `COST_SESSION_CEILING_EXCEEDED` — session aggregate would exceed its cap on the named axis.
  - `-32062` `COST_ROLLING_CEILING_EXCEEDED` — named rolling-window aggregate would exceed its cap.

  Reserve `-32063..-32069` for future (approaching-ceiling advisories if they ever ship; ceiling-adjustment validation errors; reservation-reconcile errors). Distinct from safety (`-32040..-32049`) and reversibility (`-32050..-32059`).

### 2.5 Spend tracking — "actual spend" source (plan Q15–Q17)

- **Q15 (money) recommendation.** Read from scope-of-work's `BudgetDebited` events. `money_cents` is the authoritative field; the scope author's LLM-call wrapper is responsible for debiting with an accurate monetary amount at call completion. Cost governance does not translate tokens to money — the caller has the model's per-token rate; cost governance just aggregates whatever was debited.

- **Q16 (tokens) recommendation.** Same source — `BudgetDebited.input_tokens + .output_tokens`. No amendment needed; the emission is present on `pos-v2`. Q16 is **not a halt signal.**

- **Q17 (wall-clock seconds) recommendation.** Cost governance times scopes itself via the `StateTransitioned` subscription: record timestamp when scope enters `active`, accumulate elapsed on exit. Subtract the reserved `time_seconds` only for scopes that declared it; uncapped scopes (time_seconds=None) contribute their actual elapsed to rollups but not to reservation math.

### 2.6 Rollup and decaying retention (plan Q18–Q21)

Aligns with the owner's decaying-retention preference (observability-aggregator precedent) and the decay-retention-analysis doc's "per-scope spend lives in scope-of-work; cost governance owns its rollups" separation.

- **Q18 recommendation — three tables in `~/.pos/cost/cost.sqlite`:**

  1. `reservations` — active + reconciled reservations keyed on `scope_id`. Fields: `scope_id`, `session_id`, `reserved_money_cents`, `reserved_tokens`, `reserved_time_seconds`, `actual_money_cents`, `actual_tokens`, `actual_time_seconds`, `state` (`active` | `reconciled`), `reserved_at`, `reconciled_at`.

  2. `session_rollups` — one row per session. Fields: `session_id`, `started_at`, `ended_at` (null while active), `total_money_cents`, `total_tokens`, `total_time_seconds`, `scope_count`. Pruned per retention.

  3. `rolling_rollups` — one row per `(window_kind, interval_end)`. Fields: `window_kind`, `interval_end_unix`, `interval_start_unix`, `total_money_cents`, `total_tokens`, `total_time_seconds`, `scope_count`. Pruned per retention.

  All tables `PRIMARY KEY` and `UNIQUE` constraints as appropriate. WAL + `synchronous=FULL` + `foreign_keys=ON` per pos-v2 standard.

- **Q19 recommendation — rollup cadence.**

  - *Session rollup:* written on session close (orchestrator shutdown) AND updated in-place on every `BudgetDebited` subscription event for the running session. Two writes: the in-place update keeps rollup current; the on-close finalises it with `ended_at`.
  - *Rolling-window rollup:* scheduled task in the cost-governance runtime. Runs every `min(window.duration_seconds) / 10` — for daily window, every 144 minutes; for hourly window, every 6 minutes. On each run, close completed intervals and open new ones. YAGNI-alternative (lazy-evaluate on query): rejected because queries are infrequent but rollup table needs to stay bounded.

  Observability-aggregator's RetentionJob pattern is the direct precedent (`pos-v2/observability-aggregator/src/retention.py`). Same run-idempotent discipline applies.

- **Q20 recommendation — retention policy.**

  - *Per-scope reservations:* pruned when scope terminates AND scope-of-work's own terminal-scope `BudgetDebited` rollup runs (per decay-retention-analysis candidate 4). The reservation row holds the reservation audit; the detailed debits live in scope-of-work. Once scope-of-work rolls up, cost governance's reservation record can shed its debit cache. Default: reservation rows prune 30 days after `reconciled_at`.
  - *Session rollups:* retained 365 days. (Extends the plan's proposed 30 days — 365 matches the observability-aggregator "audit record" framing better; monthly memory-system summaries will reference session rollups for history.)
  - *Rolling-window rollups:* retained indefinitely (the audit record of system spend over time). Low volume — hourly * 365 = 8760 rows/year, daily * 365 = 365 rows/year. No storage concern.

- **Q21 recommendation — memory-system integration.** Opportunistic monthly-spend summary as a candidate weekly-synthesis input. Not a dependency — cost governance ships without any memory-system hook. The integration is a *consumer* extension: a future memory-system skill can pull `session_rollups` and `rolling_rollups` and compose them into a monthly artifact. Flagged for BACKLOG.

### 2.7 Querying and telemetry (plan Q22–Q24)

- **Q22 recommendation — IPC methods.**

  - `cost.get_scope_spend(scope_id)` → `{scope_id, reserved: {money, tokens, time_seconds}, actual: {...}, state}`
  - `cost.get_session_total()` → `{session_id, totals: {money, tokens, time_seconds}, ceiling: {...}, remaining: {...}, scope_count}`
  - `cost.get_rolling_total(window_kind)` → `{window_kind, totals, ceiling, remaining, interval_start, interval_end}`
  - `cost.adjust_ceiling(ceiling_kind, axis, new_value, reason)` → `{ok: true, audit_record_id}` (accepts absolute new value; delta-math on the caller's side — avoids sign confusion)
  - `cost.status()` → session + all rolling windows, compact view for CLI.

  All typed via Pydantic; error responses use the `-32060..-32069` block.

- **Q23 recommendation — CLI subcommands.**

  ```
  pos cost status                          # compact session + rolling view
  pos cost scope <id>                      # per-scope spend + reservation
  pos cost session                         # session-level detail
  pos cost rolling [--window daily|hourly] # rolling-window detail
  pos cost adjust --kind session --axis money --value 7500 --reason "approved overage"
  ```

- **Q24 recommendation — OTel spans.**

  Span namespace `pos.cost.*`. Emitted via the tracer-get pattern (A1 correction — no new TracerProvider; use `trace.get_tracer("pos.cost_governance")`).

  - `pos.cost.reservation_created` — attrs: `scope_id`, per-axis reserved amounts, `session_id`.
  - `pos.cost.reservation_reconciled` — attrs: `scope_id`, per-axis reserved vs actual, `state`.
  - `pos.cost.ceiling_enforced_block` — attrs: `scope_id`, `ceiling_kind`, `axis`, `reserved_plus_declared`, `ceiling`, `error_code`.
  - `pos.cost.rolling_window_tick` — attrs: `window_kind`, `interval_end`, `total_money_cents`, `total_tokens`, `total_time_seconds`, `scope_count`.

  Dropped per YAGNI from the plan's candidate list:

  - `pos.cost.reservation_released` (covered by `reconciled`).
  - `pos.cost.scope_completed_spend` (redundant with scope-of-work's own terminal-transition span attrs, which already include `pos.scope.budget.*.remaining`).
  - `pos.cost.ceiling_warning_80pct` — YAGNI. Approaching-ceiling advisories are a v1.1 extension if the owner ever wants them. The acceptance criteria in v1.0 do not require 80% warnings; the plan itself flagged this as drop-candidate.

### 2.8 Deterministic-layer enforcement — sidecar/wrap (plan Q25–Q26)

- **Q25 confirmation — sidecar + wrap fully delivers.** The reservation model + activation wrap refuses over-ceiling activations with `ApplicationError(-32060..62)` before `orig_activate` runs. No ScopeSpec amendment needed; no orchestrator amendment needed; no scope-of-work amendment needed. **Sidecar pattern holds throughout.**

- **Q26 recommendation — Pydantic shapes for `Reservation` and rollups:**

  ```python
  class Reservation(BaseModel):
      model_config = ConfigDict(extra="forbid", frozen=True)
      scope_id: str = Field(min_length=1)
      session_id: str = Field(min_length=1)
      reserved_money_cents: int = Field(ge=0)       # clause (g) — no negative reserved amounts
      reserved_tokens: int = Field(ge=0)
      reserved_time_seconds: int = Field(ge=0)
      actual_money_cents: int | None = Field(default=None, ge=0)
      actual_tokens: int | None = Field(default=None, ge=0)
      actual_time_seconds: int | None = Field(default=None, ge=0)
      state: Literal["active", "reconciled"]
      reserved_at: str  # ISO-8601
      reconciled_at: str | None = None
  ```

  `ge=0` on every amount field is the clause (g) pattern — a reservation with a negative reserved amount is structurally impossible.

  Rollup shape — same discipline:

  ```python
  class SessionRollup(BaseModel):
      model_config = ConfigDict(extra="forbid", frozen=True)
      session_id: str
      started_at: str
      ended_at: str | None = None
      total_money_cents: int = Field(ge=0)
      total_tokens: int = Field(ge=0)
      total_time_seconds: int = Field(ge=0)
      scope_count: int = Field(ge=0)

  class RollingRollup(BaseModel):
      model_config = ConfigDict(extra="forbid", frozen=True)
      window_kind: str
      interval_start_unix: int = Field(ge=0)
      interval_end_unix: int = Field(ge=0)
      total_money_cents: int = Field(ge=0)
      total_tokens: int = Field(ge=0)
      total_time_seconds: int = Field(ge=0)
      scope_count: int = Field(ge=0)
  ```

### 2.9 Testing discipline (plan Q27–Q29)

- **Q27 recommendation — test fixtures.** Tests construct fake `BudgetDebited` events and inject them into the cost-governance runtime's pyee subscription without ever touching an LLM. Pattern from safety-layer tests: construct a `ScopeRuntime` on tmp_path sqlite, call `runtime.debit(scope_id, ...)` directly to emit real `BudgetDebited` events, observe cost-governance's rollup state transitions. For pure unit tests of the ledger math, the ledger is instantiated standalone and fed `BudgetDebited` objects directly via its `_handle_scope_event` handler.

- **Q28 recommendation — gate-refusal matrix.** Minimum 9 acceptance cases:

  | Ceiling  | Axis   | Test                                                |
  |----------|--------|-----------------------------------------------------|
  | scope    | money  | over-declared vs remaining session (refuses -32061) |
  | scope    | tokens | over-declared vs remaining session (refuses -32061) |
  | scope    | time   | over-declared vs remaining session (refuses -32061) |
  | session  | money  | already-spent + reserved + new > session (refuses)  |
  | session  | tokens | — same —                                            |
  | session  | time   | — same —                                            |
  | rolling  | money  | rolling-window sum + new > rolling cap              |
  | rolling  | tokens | — same —                                            |
  | rolling  | time   | — same —                                            |

  Plus baseline pass cases for each axis (activation allowed when headroom present) and edge cases (`None` on an axis = uncapped = no contribution to that axis's reservation math).

- **Q29 recommendation — concurrent-activation serialisation test.** Integration test via shared `IPCServer`: construct the server, register orig_activate + safety_ipc + reversibility_ipc + cost_governance_ipc, fire two `activate_scope` calls via `asyncio.gather` whose combined declared spend exceeds the session cap. Assert exactly one succeeds and one raises `-32061`. Mirror of `reversibility-primitive/tests/test_safety_wrap_composition.py`.

---

## 3. Clause-by-clause spec coverage

Map each cost-governance acceptance criterion (v1.0 + v1.1) to the design piece that delivers it.

| Criterion | Design piece |
|-----------|--------------|
| Every scope declares a budget at creation | **Already delivered by scope-of-work `Budget.model_post_init`.** Cost governance depends on this and does not re-implement. |
| Missing budget rejects scope creation | **Already delivered by scope-of-work `Budget.model_post_init`.** |
| Budget ceilings enforced (scope / session / rolling) | `register_cost_governance_ipc` wrap's activation check: reservation + ceiling comparison raises `-32060..62`. §2.3, §2.4, §2.9 |
| Real-time spend queryable per-scope / per-session / per-rolling | IPC methods `cost.get_scope_spend` / `cost.get_session_total` / `cost.get_rolling_total` — §2.7. |
| Throttling activates at declared threshold below ceiling with user-facing notification *before* ceiling reached | **Scope note.** The v1.0 spec requires throttling at a pre-ceiling threshold. This research recommends **deferring 80%-approaching notifications to v1.1** (YAGNI per plan §2.7 / drop-candidate flag). Will flag in the proposal for ruling recorded — if he requires 80% throttling for v1.0, it's a small addition: one OTel span + one notification via the OneOnOneChannel. See §3.7 below. |
| Per-prompt-type aggregation queryable (v1.1 R12) | **Already delivered by scope-of-work `per_prompt_costs()`.** Cost governance references it; no duplication. Add a session-filter wrapper if per-session per-prompt is requested. |

**§3.7 — Flag for the owner on throttling.** The v1.0 spec says "throttling activates at a declared threshold below the ceiling and produces a user-facing notification before the ceiling is reached." Strictly read, this is an acceptance criterion, not a drop candidate. Two readings:

- **Strict reading:** ship 80% notification in v1.0. Cost governance emits a `pos.cost.ceiling_warning` span and dispatches via the OneOnOneChannel (one-on-one constraint — per the plan). Small addition.
- **YAGNI reading:** the spec's "throttling" word can be interpreted as the hard cap being a throttle (activation refused = scope throttled). In that reading, the refusal IS the throttle.

**Recommendation:** Ship the 80%-warning (strict reading). Cost: ~5 lines of code + one notification path. The acceptance criterion is explicit; YAGNI-dropping it would be reading the spec too liberally.

---

## 4. Reservation ledger specification

### 4.1 SQL schema (verbatim)

```sql
CREATE TABLE IF NOT EXISTS reservations (
    scope_id               TEXT PRIMARY KEY,
    session_id             TEXT NOT NULL,
    reserved_money_cents   INTEGER NOT NULL DEFAULT 0 CHECK (reserved_money_cents >= 0),
    reserved_tokens        INTEGER NOT NULL DEFAULT 0 CHECK (reserved_tokens >= 0),
    reserved_time_seconds  INTEGER NOT NULL DEFAULT 0 CHECK (reserved_time_seconds >= 0),
    actual_money_cents     INTEGER CHECK (actual_money_cents IS NULL OR actual_money_cents >= 0),
    actual_tokens          INTEGER CHECK (actual_tokens IS NULL OR actual_tokens >= 0),
    actual_time_seconds    INTEGER CHECK (actual_time_seconds IS NULL OR actual_time_seconds >= 0),
    state                  TEXT NOT NULL CHECK (state IN ('active', 'reconciled')),
    reserved_at            TEXT NOT NULL,
    reconciled_at          TEXT
);
CREATE INDEX IF NOT EXISTS idx_reservations_session ON reservations(session_id);
CREATE INDEX IF NOT EXISTS idx_reservations_state ON reservations(state);

CREATE TABLE IF NOT EXISTS session_rollups (
    session_id          TEXT PRIMARY KEY,
    started_at          TEXT NOT NULL,
    ended_at            TEXT,
    total_money_cents   INTEGER NOT NULL DEFAULT 0 CHECK (total_money_cents >= 0),
    total_tokens        INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    total_time_seconds  INTEGER NOT NULL DEFAULT 0 CHECK (total_time_seconds >= 0),
    scope_count         INTEGER NOT NULL DEFAULT 0 CHECK (scope_count >= 0)
);

CREATE TABLE IF NOT EXISTS rolling_rollups (
    window_kind         TEXT NOT NULL,
    interval_end_unix   INTEGER NOT NULL,
    interval_start_unix INTEGER NOT NULL,
    total_money_cents   INTEGER NOT NULL DEFAULT 0 CHECK (total_money_cents >= 0),
    total_tokens        INTEGER NOT NULL DEFAULT 0 CHECK (total_tokens >= 0),
    total_time_seconds  INTEGER NOT NULL DEFAULT 0 CHECK (total_time_seconds >= 0),
    scope_count         INTEGER NOT NULL DEFAULT 0 CHECK (scope_count >= 0),
    PRIMARY KEY (window_kind, interval_end_unix)
);
CREATE INDEX IF NOT EXISTS idx_rolling_end_unix ON rolling_rollups(interval_end_unix);

CREATE TABLE IF NOT EXISTS ceiling_adjustments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ceiling_kind   TEXT NOT NULL,     -- 'session' | 'rolling:<window_kind>'
    axis           TEXT NOT NULL,     -- 'money' | 'tokens' | 'time'
    new_value      INTEGER NOT NULL,
    reason         TEXT NOT NULL,
    adjusted_at    TEXT NOT NULL,
    adjusted_by    TEXT NOT NULL DEFAULT 'ipc'
);
```

WAL + `synchronous=FULL` + `foreign_keys=ON` matches the pos-v2 per-component SQLite convention (verified against reversibility's and objective-tracker's stores).

### 4.2 Lifecycle

```
scope activation
        │
        ▼
wrap reads spec.budget → computes reservation amounts
        │
        ▼
wrap queries session_rollups + rolling_rollups + active reservations
        │
        ├── over ceiling → raise ApplicationError(-32060..62) → orig_activate NEVER runs
        │
        └── under ceiling → INSERT INTO reservations (state='active', reserved_*, ...)
                                  │
                                  ▼
                           orig_activate runs → scope activates
                                  │
                                  ▼  (pyee subscription catches scope events)
                      BudgetDebited → update session_rollups + rolling_rollups
                                  │
                                  ▼
                    StateTransitioned(to_state=terminal)
                                  │
                                  ▼
             reconcile: UPDATE reservations SET actual_*, state='reconciled', reconciled_at
                                  │
                                  ▼
                    reservation row remains; pruned 30d after reconciled_at
```

---

## 5. Rollup and retention specification

### 5.1 Cadence

- **Session rollups:** updated in-place per `BudgetDebited` event (O(1) UPDATE on the session's row). Closed on orchestrator shutdown (`ended_at` set). Closed-session rows are append-only thereafter.

- **Rolling rollups:** scheduled task in cost-governance runtime. For the default daily+hourly config, run every 6 minutes (the min of 3600/10 = 360 seconds). On each run:
  - Close intervals where `now_unix >= interval_end_unix`.
  - For each new interval needed, compute the sum from reservations + completed session_rollups within `[interval_start_unix, interval_end_unix)`.
  - Idempotent: re-running does not duplicate rows (PRIMARY KEY on `(window_kind, interval_end_unix)` with `INSERT OR IGNORE`; updates are `UPDATE ... WHERE interval_end_unix = ?`).

### 5.2 Pruning policy

| Table | Default retention | Trigger |
|-------|-------------------|---------|
| `reservations` | 30 days after `reconciled_at` | Pruned by a scheduled retention task (daily). |
| `session_rollups` | 365 days | Same retention task. |
| `rolling_rollups` | Indefinite | No prune. Volume is bounded (~10k rows/year with default windows). |
| `ceiling_adjustments` | Indefinite | Audit record; small volume. |

Decay-retention discipline matches preference recorded and the observability-aggregator RetentionJob pattern (anchor: `observability-aggregator/src/retention.py`). The retention task is a single method called from a scheduled task registered on the cost-governance runtime init — no separate cron file.

---

## 6. Gate ordering diagram

Recommendation: **Option B — cost innermost**. Flagged in §2.4 Q13 for ruling recorded.

```
Registration order (workspace bootstrap):
  1. orchestrator._register_ipc_methods(server)           ← orig_activate registered
  2. register_cost_governance_ipc(server, cost_controller)    ← wraps orig
  3. register_reversibility_ipc(server, ...)              ← wraps cost
  4. register_safety_ipc(server, ...)                     ← wraps reversibility

Dispatch call chain when activate_scope IPC arrives:
  client → safety_wrap
              ├── system_kill block (if active)
              └── safety.check_gates(spec)
                    │
                    ▼
                reversibility_wrap
                      └── activation_gate.check(spec)
                            │
                            ▼
                        cost_wrap
                              └── ledger.reserve_or_refuse(spec)
                                    │
                                    ▼
                                orig_activate(params)
                                      │
                                      ▼
                                orchestrator binding + scope start
```

Refusal precedence (most-semantically-prior first):
1. Safety system-kill (`-32042`)
2. Safety ask-gate (`-32040`)
3. Safety dangerous-op (`-32041`)
4. Reversibility (`-32050`)
5. Cost scope budget (`-32060`)
6. Cost session ceiling (`-32061`)
7. Cost rolling ceiling (`-32062`)

If the owner chooses Option A (plan default, cost outermost), the registration order is: reversibility → safety → cost; call chain is: cost → safety → reversibility → orig. Both orderings are structurally sound; the research document commits to Option B with Option A available as a the owner-ruling variant.

---

## 7. Integration sequence diagrams

### 7.1 Reservation on activation

```
Caller                   IPC          safety_wrap    rev_wrap    cost_wrap    orchestrator     scope_runtime
  │                       │               │             │            │              │               │
  ├── activate_scope ─────►               │             │            │              │               │
  │                       ├── system_kill check OK      │            │              │               │
  │                       ├── check_gates(spec) PASS ───►            │              │               │
  │                       │               ├── activation_gate.check PASS            │               │
  │                       │               │             ├── compute reservation     │               │
  │                       │               │             ├── query rollups + active_reservations     │
  │                       │               │             ├── sum + declared <= ceiling? YES          │
  │                       │               │             ├── INSERT reservations (state=active)      │
  │                       │               │             ├── emit pos.cost.reservation_created span  │
  │                       │               │             └── forward ─────────────►  │               │
  │                       │               │             │            │              ├── bind_scope  │
  │                       │               │             │            │              └── start ─────►│
  │                       │◄──────────────┴─────────────┴────────────┴──────── {ok: true} ──────────│
  │◄──────────────────────┤
```

### 7.2 Reconciliation on completion

```
scope_runtime          cost_ledger (pyee subscriber)
     │                        │
     ├── BudgetDebited ──────►│
     │                        ├── UPDATE session_rollups totals += debit
     │                        ├── UPDATE reservations: accumulate actual
     │                        └── (no ceiling check — we passed at activation)
     │
     ├── StateTransitioned(to_state=completed) ──►
     │                        ├── compute final actual from session_rollup delta
     │                        ├── UPDATE reservations SET state='reconciled', actual_*, reconciled_at
     │                        ├── emit pos.cost.reservation_reconciled span
     │                        └── release capacity (other pending activations can now use the slack)
```

### 7.3 Refund on cancel

```
scope_runtime          cost_ledger
     │                        │
     ├── StateTransitioned(to_state=cancelled) ──►
     │                        ├── compute actual spend from session_rollup (includes refunds already)
     │                        ├── UPDATE reservations SET state='reconciled', actual_*, reconciled_at
     │                        └── emit pos.cost.reservation_reconciled span (state=cancelled in scope_id attr)
```

### 7.4 Ceiling adjustment

```
CLI                IPC            cost_controller
  │                 │                    │
  ├── pos cost adjust --kind session --axis money --value 7500 --reason "..."
  │                 │                    │
  ├── IPC ─────────►│                    │
  │                 ├── cost.adjust_ceiling(kind, axis, value, reason) ──►
  │                 │                    ├── Pydantic-validate (value >= 0, reason not empty)
  │                 │                    ├── INSERT ceiling_adjustments (audit)
  │                 │                    ├── update in-memory ceiling cache
  │                 │                    └── emit pos.cost.ceiling_adjusted span
  │                 │◄─────────────── {ok: true, audit_record_id: 42} ──────
  │◄────────────────┤
```

Note: ceiling adjustments do NOT re-check active reservations. If the session cap is lowered below the currently-reserved total, existing reservations stand (they're in-flight); the lower cap applies to new activations only. This is consistent with safety's and reversibility's mid-session-change semantics.

---

## 8. Relationship to safety's money-threshold and reversibility's budget_seconds

Precise boundary:

| Concern                 | Safety's `money_threshold_cents`       | Reversibility's `budget_seconds`            | Cost's ceilings                                 |
|-------------------------|-----------------------------------------|----------------------------------------------|--------------------------------------------------|
| **Scope**               | Per-scope one-shot                      | Per-scope rollback timeout                   | Aggregate across scopes per session / rolling  |
| **Shape**               | Single `money_cents >= threshold` boolean check | Timeout on compensation handler invocation | Sum of active reservations + committed + declared ≤ ceiling |
| **When it fires**       | Activation (safety wrap)                | Rollback invocation (not activation)         | Activation (cost wrap)                           |
| **Error code**          | `-32041` (dangerous-op)                 | Handler timeout → RollbackResult.outcome=failed | `-32060..62` |
| **Dimensions**          | Money only                              | Time only                                    | Money + tokens + time_seconds                    |
| **Per-scope state**     | Stateless (pure spec check)             | Bound to rollback invocation                 | Reservation row persisted                        |
| **Aggregate state**     | None (scope-local)                      | None (scope-local)                           | session_rollups + rolling_rollups                |

**Composability:** a single activation may trip zero, one, or multiple gates. Each gate raises independently with its own error code. Cost governance composes with — does not duplicate — the other two.

**Budget extension interaction:** when scope-of-work's extension mechanism grants additional budget (`BudgetExtended` event), cost governance observes the event via pyee subscription. The reservation row is NOT re-adjusted by an extension — the original reservation was based on the original declaration. If the scope subsequently spends beyond the reservation, the reconciliation writes `actual > reserved` (clause-(g) stays intact: `actual_money_cents` is `ge=0`, not `ge=reserved`). Session and rolling rollups track actual spend, so the aggregate remains truthful even if individual reservations under-state.

**Edge case flagged:** if extension pushes aggregate actual over the rolling-window ceiling, the cost wrap has no lever — the scope is already active. Recommended behaviour: emit `pos.cost.ceiling_post_hoc_overrun` span as a diagnostic signal; do not refuse the extension (that's scope-of-work's decision). the owner can review these events via OTel and decide whether to tighten per-scope declarations in future.

---

## 9. Dependency map

**Consumed by (future components may rely on cost governance):**
- **Self-correction loop** — retries must respect cost ceilings (a retry that would blow the session cap is refused by the cost wrap automatically; no special integration needed).
- **Onboarding / non-tech layer** — cost status dashboard for the user; reads `cost.status()`.
- **Memory system** — opportunistic monthly-spend summaries referencing `session_rollups` and `rolling_rollups`. Backlog, not dependency.

**Depends on (sealed components cost governance consumes):**
- **Scope-of-work** — `ScopeSpec.budget.time_seconds / tokens / money_cents` (activation read); `BudgetDebited` / `BudgetRefunded` / `StateTransitioned` events (pyee subscription); `ScopeRuntime.emitter` (subscription surface); `per_prompt_costs()` (CLI / IPC reference, no duplication).
- **Orchestrator** — `IPCServer.register("activate_scope", wrapped)` (wrap registration surface); `_register_ipc_methods` runs first (registration-order dependency).
- **Safety layer** — wrap composition only; no direct API consumption beyond the shared IPCServer.
- **Reversibility primitive** — wrap composition only; no direct API consumption.
- **Observability aggregator** — `trace.get_tracer("pos.cost_governance")` for OTel emission (A1 correction — aggregator's registered TracerProvider handles routing).

**Builds nothing new on:** memory system, graceful-degradation, primary-persona, self-upgrade, objective-tracker, session-resilient-orchestrator. Indirect only — via scope-of-work's emission surface. No amendment to any.

---

## 10. Complexity estimate

**Calibrated AI-time estimate: 30–40 minutes wall-clock, red-line 45.**

Anchors:
- **Reversibility primitive** ~30 min wall-clock (structurally the closest precedent — SQLite + wrap + Pydantic + OTel + pyee subscription).
- **Safety layer** ~35 min (kill engine + YAML floor + dangerous-op gate adds surface).

Cost governance is structurally between the two:
- **Simpler than safety:** no kill engine, no YAML floor, no dangerous-op gate. Ceiling-refusal arithmetic is straightforward.
- **More surface than reversibility:** three tables (not two), one scheduled task (retention/rollup), one additional IPC method family (`cost.*`).
- **Unique complexity:** reservation + reconciliation bookkeeping, rolling-window rollup scheduler.

**Pushback on the plan's 35–45 min / red-line 50 estimate:** I believe 30–40 is more accurate. The pattern is directly inherited from reversibility (which came in at ~30), with one extra table and one scheduled task. If the build exceeds 40 minutes, the probable drag is rolling-window rollup correctness (the window boundary math and idempotent re-run) or wrap-ordering subtlety under the new 4-wrap chain (cost added to reversibility + safety). Red-line 45 captures that. If it exceeds 45, halt and signal — likely class: rolling-window rollup edge cases (interval-boundary math under clock skew).

---

## 11. Prototyping priorities

Questions only a prototype can definitively answer (research cannot):

1. **Reservation reconciliation race condition under concurrent scope completions.** Two scopes complete within the same asyncio tick; both trigger reconciliation writes to `session_rollups`. The SQLite row update is sequenced by the store's thread lock, but the *in-memory* rollup cache (if any) could race. **Prototype test:** fire 100 concurrent `complete()` calls on 100 pre-activated scopes; assert `session_rollups.total_money_cents == sum(expected_actual)`. If races appear, add per-session lock on the rollup update path.

2. **Rolling-window boundary math under clock skew.** The scheduled rollup task computes interval boundaries from `datetime.now()`. If the orchestrator is suspended / resumed, `now` can jump. **Prototype test:** monkey-patch the clock, advance by 2 hours in one jump, assert the rollup correctly closes the two skipped hourly intervals.

3. **pyee subscription ordering under scope event bursts.** If a scope debits 1000 times in rapid succession and then transitions to completed, does the reconciliation see all 1000 debits before the terminal event fires the reconcile? pyee is in-process and ordered, but the cost-governance handler is async — the await chain could interleave. **Prototype test:** 1000-debit burst + terminal transition; assert reservation's `actual == sum(debits)`.

4. **IPC wrap composition under the new 4-wrap chain.** Safety + reversibility + cost + orig. Integration test modelled on `reversibility-primitive/tests/test_safety_wrap_composition.py`. **Prototype test:** assert each of the 4 failure modes (cost-exceeded, rev-unbound, safety-ask, safety-kill) fires the correct error code and short-circuits the downstream wraps.

5. **Ceiling adjustment during pending activation.** Scope A is mid-activation in the cost wrap; the owner adjusts the ceiling via CLI. Does scope A see the old or new ceiling? **Prototype test:** inject a CLI-adjust between the cost wrap's "read ceiling" and "raise or insert" steps; assert race-free outcome (recommended: cost wrap reads ceiling once at entry and uses that value for the full check — no re-read after the adjustment).

All five are integration-level and fit the existing test infrastructure (asyncio, tmp_path sqlite, fake-emitter, `IPCServer` under test). Each maps to a ~5-minute test case at build time.

---

## Appendix A — file-path inventory for the build

Workspace layout (all paths under `pos-v2/cost-governance/`):

```
cost-governance/
├── pyproject.toml
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py             — exports: CostController, CostLedger, register_cost_governance_ipc
│   ├── spec.py                 — Pydantic Reservation, SessionRollup, RollingRollup, CeilingAdjustment, IPC error codes
│   ├── config.py               — CostConfig loader from ceilings.yaml; session + list-of-rolling
│   ├── store.py                — SQLite store; three tables + ceiling_adjustments; WAL+FULL+FK
│   ├── ledger.py               — CostLedger core: reserve_or_refuse, reconcile, subscribe to scope events
│   ├── rollup.py               — rolling-window rollup task; idempotent
│   ├── controller.py           — CostController composes ledger + store + notifier; IPC check entry
│   ├── ipc_wiring.py           — register_cost_governance_ipc; activation wrap layered after safety's
│   ├── observability.py        — pos.cost.* span helpers; tracer-get pattern
│   └── cli.py                  — `pos cost` subcommand family
└── tests/
    ├── test_ceiling_enforcement.py
    ├── test_reservation_reconciliation.py
    ├── test_rolling_rollup.py
    ├── test_ipc_wrap_composition.py
    ├── test_ceiling_adjustment.py
    ├── test_per_prompt_reference.py
    ├── test_no_sealed_amendments.py
    └── conftest.py
```

## Appendix B — surfaces the build must NOT touch

Sealed components. Zero deltas required or permitted to any of:

- `scope-of-work/*`
- `orchestrator/*` (except the standard bootstrap convention that `register_cost_governance_ipc` is called from the workspace bootstrap AFTER `_register_ipc_methods`)
- `safety-layer/*`
- `reversibility-primitive/*`
- `graceful-degradation/*`
- `primary-persona-layer/*`
- `objective-tracker/*`
- `observability-aggregator/*`
- `self-upgrade-framework/*`
- `memory-system/*`
- `session-resilient-orchestrator/*`

The `test_no_sealed_amendments.py` test is mandatory — it diffs the component's build commit against the pos-v2 baseline and fails on any non-cost-governance + non-workspace-bootstrap delta. Pattern from reversibility's `test_no_sealed_amendments.py`.

---

*End of research.*
