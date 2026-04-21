# Research Plan — Cost Governance

**Component:** Cost Governance — enforces budget ceilings (money / tokens / wall-clock seconds) per scope, per session, and per configurable rolling window, via the same sidecar+activation-wrap pattern the safety and reversibility primitives use.
**Status:** DRAFT — awaiting owner's approval before research begins.

---

## Objective this research must serve

Identify the design shape for cost governance such that:

- A scope whose activation would cause its own declared budget (money_cents / tokens / seconds) to be exceeded cannot activate. Deterministic refusal, not soft warning.
- A scope whose activation would cause an *enclosing* ceiling (session, rolling window) to be exceeded cannot activate.
- Real-time spend totals are queryable per scope, per session, per rolling window — both via IPC and via OTel emission.
- Refusal is structurally distinguishable from safety and reversibility refusals (error code + reason).
- The decaying-retention pattern applies: per-scope spend is ephemeral (lives as scope-of-work events), session rollup is hourly, rolling-window rollup is daily — rolled up and pruned in the component's own SQLite.
- Integration with sealed components is clean: cost governance reads scope budgets from `ScopeSpec`, reads completion/debit events from scope-of-work, owns its own rollup tables.

## Starting position

- **Sealed components:** nine on `pos-v2`. Safety layer and reversibility primitive both read `ScopeSpec.budget` for their own gate logic; neither enforces rolling ceilings.
- **`ScopeSpec.budget` already exists** on scope-of-work with `money_cents`, `tokens`, `seconds` fields (verify exact field names during research — research plan flags this as the first factual check).
- **`ScopeRuntime` emits debit events** as scopes consume budget during execution (verify exact event kinds during research). Cost governance is a read-only consumer of these emissions plus the activation wrap.
- **Precedent pattern** — sidecar table + activation wrap + SQLite store + OTel emission + IPC registration. Triply established (objective-tracker, safety, reversibility). Cost governance takes this as the default.
- **Python 3.13, `pos-v2` branch.** Permitted deps as per standard.

## Questions the research must answer

### 1. Budget declaration — what is actually on `ScopeSpec.budget`?

1. Verify against code: what are the exact field names on `ScopeSpec.budget`? (`money_cents`, `tokens`, `seconds` — or different?) Optional vs required? Does `None` mean "no budget declared" or "unlimited"?
2. Does `ScopeSpec.budget` carry only the scope's own declared cap, or does it also carry a hint about the session/rolling ceilings it's subject to? (If only scope-own, then session/rolling ceilings live in the cost-governance configuration, not in the scope spec.)
3. What happens when a scope declares `budget.money_cents = None`? Does the gate treat this as "no ceiling" or "must declare"? Proposed default: "must declare" for non-`fully_reversible` scopes; `None` permitted only for `fully_reversible`.

### 2. Session and rolling-window ceilings — where do they come from?

4. Where is a session ceiling declared? Candidates: (a) workspace-level YAML config file consumed by cost governance on init; (b) per-session IPC call at session open; (c) both.
5. What's the default rolling window? Hourly, daily, weekly, rolling-N-hours? Spec says "configurable rolling window" (plural "window" not "windows") — does the system support multiple concurrent rolling windows (e.g. "daily" AND "hourly"), or one primary window?
6. What's the session identity — the orchestrator's session_id (same one safety uses for session-kill), or a new cost-session concept? Default: reuse orchestrator session_id.
7. Can a ceiling be mid-session-adjusted? (E.g. user approves raising the daily money ceiling by $5 in-session.) Default: yes, via IPC method, audit-logged.

### 3. Pre-activation gate logic

8. At scope activation, the cost wrap must compute: (a) scope's own budget vs. prior spend for this scope (usually zero at activation); (b) session-total spend + scope's budget ≤ session ceiling; (c) rolling-window spend + scope's budget ≤ rolling ceiling. Verify the arithmetic model — is the scope's **declared budget** added to the running total, or only its **actual spend** after completion? Default proposed: declared budget at activation (reservation model), reconciled against actual spend on completion.
9. Reservation model: does the cost wrap write a "reservation" row that reserves capacity until the scope terminates, then reconciles? Or is it compute-on-read (SUM of active scope budgets + completed spend)?
10. Over-commitment — what if two scopes want to activate concurrently and together would exceed the ceiling but each alone fits? Serial activation via the wrap handles this automatically (one gets in, the other sees the first's reservation). Verify the IPC wrap pattern serialises correctly.
11. Refunds on cancel: when a scope is cancelled before completion, its reservation releases. What's the mechanism? Likely the pyee-subscribed listener on scope-state transitions (same pattern as reversibility's cascade trigger).

### 4. Integration with safety and reversibility refusals

12. Safety's dangerous-op gate already refuses `irreversible + money_cents >= threshold`. That's a one-shot ceiling for the scope itself. Cost governance's gate is about session/rolling ceilings. Do the two gates need to coordinate, or do they refuse on orthogonal conditions?
13. Gate ordering on the shared `IPCServer`: the existing order is reversibility-first → safety-second → orig_activate. Where does cost governance insert? Default proposed: **cost-third** (after safety), because cost is the most transactional and should not short-circuit the structural (reversibility) or approval (safety) refusals.
14. Error codes: reserve `-32060..-32069` for cost governance. Three at minimum: `COST_SCOPE_BUDGET_EXCEEDED`, `COST_SESSION_CEILING_EXCEEDED`, `COST_ROLLING_CEILING_EXCEEDED`. Distinct from safety (`-32040..-32049`) and reversibility (`-32050..-32059`).

### 5. Spend tracking — what does "actual spend" come from?

15. Money: LLM API call cost (Claude tokens × per-token rate); any external service invocation that charges. Where does the system learn the money cost? Default proposed: scope-of-work emits a typed `BudgetDebit` event at LLM-call completion; cost governance subscribes.
16. Tokens: Claude API usage. Same emission pattern. Does the emission already exist on `pos-v2` or does the cost-governance build require a sealed-component amendment to add it? This is the **most likely halt-signal** location — verify the event exists during research.
17. Wall-clock seconds: scope activation → scope termination. Easy — cost governance times this itself via the state-transition subscription.

### 6. Rollup and decaying retention

18. Per-scope spend lives in scope-of-work's event log (ephemeral, pruned with the scope). Cost governance's own SQLite stores: (a) active reservations; (b) session rollups (per session); (c) rolling-window rollups (per window kind).
19. Rollup cadence: session rollup on session close; rolling-window rollup on a schedule (hourly? daily?). The observability aggregator's rollup pattern is a precedent — likely same mechanism.
20. Retention: per-scope data pruned when scope terminates; session rollups retained for 30 days; rolling-window rollups retained indefinitely (they're the audit record of system spend over time).
21. What gets written to the memory system, if anything? Candidate: monthly spend summary as a weekly-synthesis-style artifact. Not a dependency; an opportunistic indexer.

### 7. Querying and telemetry

22. IPC methods: `cost.get_scope_spend(scope_id)`, `cost.get_session_total()`, `cost.get_rolling_total(window_kind)`, `cost.adjust_ceiling(ceiling_kind, delta, reason)`. All return typed records.
23. CLI: `pos cost status`, `pos cost scope <id>`, `pos cost session`, `pos cost rolling [--window daily|hourly]`, `pos cost adjust --kind session --delta +500 --reason "approved overage"`.
24. OTel emissions: `pos.cost.reservation_created`, `pos.cost.reservation_released`, `pos.cost.scope_completed_spend`, `pos.cost.ceiling_enforced_block` (refusal at gate), `pos.cost.ceiling_warning_80pct` (approaching ceiling, advisory — may be dropped per YAGNI), `pos.cost.rolling_window_tick` (rollup emission).

### 8. Deterministic-layer enforcement (sidecar/wrap per precedent)

Default assumption, per the three existing precedents (objective-tracker, safety, reversibility): cost governance owns a sidecar `CostLedger` + rollup tables in its own SQLite at `~/.pos/cost/cost.sqlite`. The structural refusal lives in a **cost-governance activation wrap** layered after safety's wrap (wrap registration order: reversibility → safety → cost → orig_activate).

25. Confirm or rebut: does the activation wrap + sidecar combination fully deliver "cannot activate without an available budget slot" without any ScopeSpec amendment? If an amendment seems needed, halt and signal with a named failure mode.
26. Pydantic shape of reservation and rollup records. Apply the clause-(g) pattern — a reservation with negative `reserved_money_cents` must be structurally impossible.

### 9. Testing discipline

27. How do tests simulate spend without actually calling the LLM? Fake `BudgetDebit` emissions; assert ledger state transitions; assert gate refusals on over-limit.
28. Test matrix for gate refusals: three ceiling types (scope / session / rolling) × three budget dimensions (money / tokens / seconds) = 9 acceptance cases at minimum.
29. Concurrent-activation serialisation: two scopes both pending at the gate, total exceeds ceiling, second gets refused. Integration test via the shared `IPCServer`.

## Constraints the research must respect

- **Python-native.** Permitted runtime as enumerated.
- **No amendments to sealed components.** Default: sidecar/wrap. If the `BudgetDebit` event or similar emission isn't present on scope-of-work, halt and signal with a named failure mode — do not improvise an amendment.
- **Max-first.** No LLM inference inside the primitive.
- **Zero carryover from current pOS.**
- **A1 correction held.** Emit OTel via aggregator's registered provider.
- **One-on-one channel only** for any user-facing ceiling-approach surfaces (though YAGNI may suggest not surfacing these at all).
- **Halt-on-deviation.**
- **Deterministic-layer enforcement** for the ceiling refusals.
- **Composes with safety and reversibility, does not duplicate.** Safety's `money_cents_threshold` is a *per-scope* one-shot check; cost governance is about *aggregate* ceilings across scopes.
- **Decaying retention pattern** applies — per-scope ephemeral, session rollup hourly, rolling-window rollup daily. See STATE.md rule 7 and BACKLOG.md for the context.

## Deliverable — what the research document must contain

A markdown document at `components/cost-governance/research.md` with:

1. **Survey of existing patterns** — OS resource limits (rlimit, cgroups), cloud cost governance (AWS Budgets, GCP Quotas), API rate limiting (token buckets, leaky buckets), database transaction budgets (query cost estimation).
2. **Recommended design shape** — for each of the nine question groups, options considered, recommended option, rationale.
3. **Clause-by-clause spec coverage** — each acceptance criterion mapped to the design piece.
4. **Reservation ledger specification** — Pydantic shapes, SQL schema, lifecycle.
5. **Rollup and retention specification** — cadence, schema, pruning policy.
6. **Gate ordering diagram** — where cost governance sits in the reversibility → safety → cost → orig_activate chain.
7. **Integration sequence diagrams** — reservation on activation; reconciliation on completion; refund on cancel; ceiling adjustment.
8. **Relationship to safety's money-threshold and reversibility's budget_seconds.** Precise boundary.
9. **Dependency map** — consumed by: self-correction loop (retries must respect cost ceilings). Depends on: scope-of-work, safety, reversibility, orchestrator, observability aggregator.
10. **Complexity estimate** — AI-time calibrated against safety (~35 min) and reversibility (~30 min). Cost governance has comparable surface area but more state (rollup tables + reservations). Anchor 35–45 AI-min wall-clock; red-line 50.
11. **Prototyping priorities** — questions only a prototype can answer (e.g. whether scope-of-work's `BudgetDebit` emission has the shape the ledger needs; whether reservation + reconciliation can be made race-free under concurrent activation).

## Execution note

On owner's approval, the plan is passed to a general-purpose Agent. Halt-on-deviation applies. Sidecar/activation-wrap is the default per triple precedent; amendment only as a last resort with a named failure mode.

---

## Awaiting owner's approval

- Approve as written → the primary persona dispatches the research agent.
- Approve with changes → the primary persona incorporates and resubmits.
- Reject → the primary persona reworks.
