# Component — Cost Governance

**Created:** 2026-04-20 08:19 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-20 10:48 CDT.** Commit `04951b6` on `pos-v2`; 46/46 cost-governance tests passing; zero sealed-component deltas; test-infrastructure defect in reversibility's and cost-governance's own `test_no_sealed_amendments.py` identified and fixed on a follow-up commit `f94d602` (structural remedy — pin to own-seal rather than HEAD). Full regression across all ten sealed components: 660 tests green. ~16.5 min wall-clock (well under 30–40 band). Third Phase 3 component closed.

---

## Parent objective (from spec v1.0 Foundational layer)

> **Cost governance.** Every scope declares a budget — money (USD cents), Claude tokens, wall-clock seconds. The system enforces ceilings per scope, per session, and per configurable rolling window. Exceeding a ceiling is a deterministic block, not a soft warning. Spend telemetry is first-class.
>
> Acceptance:
> - A scope whose activation would cause its own budget to be exceeded cannot activate.
> - A scope whose activation would cause a session or rolling-window ceiling to be exceeded cannot activate.
> - Real-time spend totals are queryable per scope, session, and rolling window with OTel surfacing.
> - The ceiling refusal is distinguishable (error code + reason) from other activation refusals (safety, reversibility).

## Why this component is next in Phase 3

1. **Safety and reversibility both read budget hints** but neither enforces rolling ceilings. Safety's dangerous-op gate reads `budget.money_cents` against a threshold for one-shot refusal; reversibility carries a `budget_seconds` for handler timeouts. Cost governance is the component that turns "budget is declared" into "budget is enforced across scopes."
2. **Self-correction loop depends on this.** A self-correcting system retries operations; retry loops without cost ceilings are the single most common way an autonomous agent burns through budget overnight. Cost ships before self-correction.
3. **Decaying-retention pattern finds a natural home here.** Per-scope spend is ephemeral; session rollup is hourly; rolling-window rollup is daily. The BACKLOG's preference for roll-ups, rotation, and decay maps directly onto cost telemetry's lifecycle.
4. **Sidecar/wrap precedent is now triply established** — objective-tracker, safety, reversibility. Cost governance should emulate without ceremony.

## Artifacts

- `research-plan.md` — drafted 2026-04-20; awaiting owner's approval
- `research.md` — produced 2026-04-20 08:34; ruling recorded on 3 questions 08:57
- `proposal.md` — drafted 2026-04-20 08:58; approved 09:07 ("approve")
- `brief.md` — drafted 2026-04-20 09:08; approved 10:25 ("approve")
- `outputs/` — empty

## History

- 2026-04-20 08:19 CDT — component created (third Phase 3 component, follows sealed safety layer and reversibility primitive); research plan drafted; awaiting owner's approval before research begins.
- 2026-04-20 08:24 CDT — owner approved plan ("ok, i approve, move forward"). Background research agent dispatched; Q16 (scope-of-work `BudgetDebit` emission shape) surfaced as the most likely halt-signal location. Awaiting return.
- 2026-04-20 08:34 CDT — research agent returned after ~10 min wall-clock. Zero halt signals. Q16 resolved cleanly: `BudgetDebited` emission is already present on scope-of-work with the exact shape the ledger needs (`input_tokens`, `output_tokens`, `money_cents`, `call_id`, `prompt_name`, `model`), plus `BudgetRefunded`, plus pyee fan-out via `ScopeRuntime.emitter`. Bonus finding: `ScopeRuntime.per_prompt_costs()` already exists — cost governance references it, does not re-implement. One factual correction: budget time field is `time_seconds`, not `seconds` as the plan said. Sidecar/wrap pattern held; the only care is wrap-ordering under the four-wrap chain. Three proposal-stage rulings surfaced. Calibrated build: 30–40 min wall-clock, red-line 45 (researcher pushed back on my 35–45).
- 2026-04-20 08:57 CDT — ruling recorded on all three questions ("approve"). (1) Gate ordering: cost innermost (Option B) — registration cost-first, reversibility-second, safety-third; dispatch safety → reversibility → cost → orig_activate. (2) Throttling / 80%-warning: ship in v1.0 per strict spec reading. (3) Session rollup retention: 365 days.
- 2026-04-20 08:58 CDT — proposal drafted at `proposal.md`. Encodes rulings as locked inputs, enumerates 28 ODD acceptance criteria (C1–C28), flags 8 primary-persona inferences for the builder to challenge, locks cost-innermost wrap order and `-32060..-32069` error-code range. Awaiting owner's approval.
- 2026-04-20 09:07 CDT — owner approved proposal ("approve").
- 2026-04-20 09:08 CDT — handoff brief drafted at `brief.md`. Points the builder at the proposal as authoritative; carries verify-against-code discipline (four sealed surfaces named), halt-at-45-minutes scope-creep trigger, cost-innermost wrap-ordering rule with mandatory integration test, throttle-warning fire-once discipline, and required return format. Awaiting owner's review before dispatch.
- 2026-04-20 10:25 CDT — owner approved brief ("approve"). Background build agent dispatched against the brief with the proposal as binding contract.
- 2026-04-20 10:42 CDT — Agent returned after ~16.5 min wall-clock (well under 30–40 band). Commit `04951b6` on `pos-v2`: 28 files, +3760 lines, all within `cost-governance/`. 46/46 tests passing in 2.06s. primary-persona inference #5 deferred (budget-extension diagnostic span not needed — no acceptance coverage; one-line addition if wanted later). Other inferences held exactly. Zero halt signals from the agent.
- 2026-04-20 10:43 CDT — the primary persona verification caught a halt-signal the agent missed: reversibility's `test_R21_only_reversibility_primitive_changed` now failing because it diffs `45a15b9..HEAD`, sweeping in cost-governance's legitimate files. Diagnosed as a class-failure: seal-time audit tests pinned to moving HEAD rather than own-seal commit. Cost-governance's own `test_C23_only_cost_governance_changed` has the same defect and will trip on the next component. Surfaced to the owner with recommendation.
- 2026-04-20 10:48 CDT — ruling recorded ("go ahead and seal and do your full recommended structural remedy"). Structural remedy executed: both tests pinned to own-seal commits (reversibility to `f657f8c`, cost-governance to `04951b6`). Follow-up commit `f94d602` on `pos-v2`. Full regression re-run: 660 tests green across all ten sealed+in-flight components. Cost-governance sealed. Third Phase 3 component closed.
