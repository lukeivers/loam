# WS-A4 — Subscription cap-% into the cost-governance ledger

**Plan-doc (plan-before-code HARD GATE). Authored before any source edit.**
Source: BACKPLANE-PLAN.md §5 Track A, WS-A4. Target component:
`framework/cost-governance` in the **loam** repo (`/Users/lukeivers/loam`).

---

## 1. Objective

A dispatch that would run while the Claude **weekly cap** (`seven_day`
utilization) is above a configured fraction is **refused** (or **warned**, per
configured action) by the same ceiling machinery that already enforces
time/token/money ceilings (`CostLedger.reserve_or_refuse`). The account-wide
weekly utilization becomes a fourth ceiling source alongside the existing
session + rolling axes.

Closes the inventory-named gap: the ledger tracks what *it* dispatches but has
no knowledge of account-wide weekly utilization.

## 2. Sealed-status determination (dispatch AC — stated)

**cost-governance IS SEALED.** Evidence:
- `framework/cost-governance/tests/SEAL_COMMIT` sidecar present (`0143cf39…`).
- `framework/cost-governance/tests/test_no_sealed_amendments.py` is a
  BASELINE-aware fence (`BASELINE = "2bc872d"`) asserting `git diff
  BASELINE..SEAL_COMMIT` touches only `framework/cost-governance/` + admitted
  partner prefixes.
- Prior `chore(amend): …apply` commits in history.

→ Build runs the **loam amend cycle** (`loam amend validate` → `apply` →
`seal`), NOT free edits.

**F2 — the plan's claim is wrong.** BACKPLANE-PLAN.md §5 calls cost-governance
"working, unsealed: direct extension permitted." That is incorrect in the
strict sense: the component carries a live seal fence. The plan's *intent*
("this component is still open for extension, not frozen") is right — but the
mechanism is the amend cycle, not a free edit. Reported to dispatcher.

## 3. Fence

Single-component fence: `framework/cost-governance/`. Universal admissions:
`docs/plans/`, `CLAUDE.md`, `docs/STATE.md` (per manifest universal_paths).
No other sealed component touched. WS-A5 (parallel) does not amend
cost-governance source → parallel-safe, no serialization required.

## 4. Named decisions (recommendations — dispatcher rules only if it disagrees)

- **D1 — New config block, two fractions.** Add a NEW optional
  `cap_ceiling` config object with `refuse_fraction` + `warn_fraction` +
  `action` — do NOT overload the existing per-ceiling `warning_fraction`
  (that governs the session/rolling axes' 80% warning and has different
  semantics). AC1 needs three regions (refuse / warn / silent) which a single
  fraction cannot express.
- **D2 — Default-OFF.** With no `cap_ceiling` configured, `reserve_or_refuse`
  behaves EXACTLY as today (no probe call, no new branch taken). Required by
  AC3 (no regression).
- **D3 — Fail-OPEN on `UsageUnavailable`.** Per the WS-A4 constraint: a cap
  guard that failed closed on a network blip would freeze all authorized work.
  Dispatch proceeds; the categorical reason is recorded; NO numeric
  utilization appears in that record. (Contrast: protection guards fail
  closed; this asymmetry is explicit in the plan.)
- **D4 — Cached probe with short TTL.** `read()` hits the OAuth endpoint. The
  deterministic gate must consult a **cached** value (short TTL), never a live
  call per reservation, so N parallel dispatches don't hammer the endpoint and
  the gate stays deterministic. Module-level TTL cache keyed on nothing (single
  account); injectable for tests.
- **D5 — New IPC refusal code `-32063`.** Reserved range `-32060..-32069`;
  `-32060..-32062` are used, `-32063..-32069` free. Claim `-32063` =
  `IPC_COST_CAP_CEILING_EXCEEDED`. Honors the existing typed-refusal pattern
  (`ApplicationError`).
- **D6 — production-stake floor on the cap warn fraction.** The WS-A4
  constraint says the warning fraction "respects the existing `production-stake`
  floor behavior." Mirror `apply_safety_profile_floor`: under
  `production-stake`, the cap's `warn_fraction` is floored at 0.6 (clamp
  down, don't mutate the file). Reuse the existing floor constant/pattern.
- **D7 — Cap check placement.** The cap reading joins the existing
  ceiling-check path as an additional source AFTER session + rolling checks
  (account-wide is the outermost ring). Injected probe callable
  (default = `usage_window_guard.read`) so tests stub it without network.

## 5. Acceptance criteria (outcome-shape; method is builder's call)

- **AC.CAPC.1 ★ outcome-altitude.** With a stubbed probe at `seven_day`
  utilization **above** the refuse fraction, a dispatch through the production
  `reserve_or_refuse` path is **refused** with the typed error
  (`ApplicationError(-32063)`); **below** the warn fraction it proceeds
  silently; **between**, it proceeds with a warning emitted. Test hits the real
  `CostLedger.reserve_or_refuse` entry point with no pre-set ledger state
  beyond a configured cap.
- **AC.CAPC.2.** With the probe returning `UsageUnavailable(reason)`, the
  dispatch **proceeds** (fail-open) and the ledger/record captures the
  categorical reason; **no** numeric utilization appears anywhere in that
  record.
- **AC.CAPC.3.** Existing cost-governance tests still pass — no regression to
  time/token/money ceilings. Verified by default-OFF behavior (AC via the full
  existing suite green) + an explicit "cap unconfigured ⇒ probe never called"
  test.
- **AC.CAPC.4.** production-stake profile clamps the cap `warn_fraction` to the
  0.6 floor at runtime without mutating the config source (mirrors AC.PSAFE.3).
- **AC.CAPC.5.** The cached-probe layer is consulted by the gate: within the
  TTL, N reserve calls trigger exactly ONE probe invocation (determinism +
  no-hammer). Test via a counting stub.

Each AC ⇒ a `test_AC_CAPC_<n>_<desc>.py` (or parametrized within the file).
AC.CAPC.1 is the outcome-altitude test (real entry point, no pre-set state).

## 6. Build steps (order)

1. Branch `feat/ws-a4-cost-ceiling` off loam `main` (c53458da) in an isolated
   loam worktree — **pending dispatcher authorization** (see §8).
2. Copy this plan-doc to `docs/plans/ws-a4-cost-ceiling.md`. Commit plan FIRST
   (plan-before-code).
3. `config.py`: add `CapCeiling` pydantic model (`refuse_fraction`,
   `warn_fraction`, `action`: `"refuse"|"warn"`) + optional `cap_ceiling` field
   on `CostConfig`; validators (fractions in (0,1], warn ≤ refuse); extend
   `apply_safety_profile_floor` to clamp `cap_ceiling.warn_fraction` at 0.6
   under production-stake.
4. `spec.py`: add `IPC_COST_CAP_CEILING_EXCEEDED = -32063`.
5. New `cap_probe.py` (or fold into ledger): TTL-cached wrapper around
   `usage_window_guard.read`; injectable.
6. `ledger.py`: after rolling checks in `reserve_or_refuse`, if `cap_ceiling`
   configured, consult cached probe; branch refuse/warn/silent; fail-open with
   categorical reason on `UsageUnavailable`. Default-OFF short-circuit when
   `cap_ceiling is None`.
7. Depend on `loam-usage-window-guard` (import-only, sealed) — add to
   cost-governance `pyproject.toml` deps if not already present; compose, do
   not modify.
8. Author `tests/test_AC_CAPC_*.py` (5 ACs). Run touched tests + full existing
   suite locally.
9. Commit source+tests as `feat(cost-governance): …`.
10. Author manifest `docs/plans/ws-a4-cost-ceiling.manifest.yaml` (schema v3):
    baseline = main HEAD at plan time; one component (cost-governance,
    `new_component: false`); universal_paths; narrative target
    `docs/plans/sealed/ws-a4-cost-ceiling.md`.
11. `loam amend validate` → `apply` → `seal`. Trace the BASELINE advance the
    seal performs (docstring names it the failure-prone step) — verify post-seal
    `apply --dry-run` clean + seal-test green.
12. Pyright on cost-governance src/; fix component-specific errors; note the
    repo-wide test-file resolution artifact, don't chase.

## 7. Reuse (no re-rolling)

- `usage_window_guard.read()` → `UsageWindows | UsageUnavailable`;
  `UsageWindows.seven_day.utilization: float`; `UsageUnavailable.reason.value`.
- `apply_safety_profile_floor` + `PRODUCTION_STAKE_WARNING_FRACTION_FLOOR`
  pattern (extend, mirror).
- `ApplicationError` typed-refusal + `_check_axis` refusal shape in ledger.
- Existing `CostConfig` load path + pydantic validators.

## 8. Halt-and-surface (BEFORE build)

**ACTIVE HALT — dispatcher decision required before code.** Two facts
contradict the dispatch premise:
1. My worktree is a **pos3-workspace** worktree, NOT a loam worktree, and does
   not contain `framework/cost-governance`. The dispatch's premise ("you are in
   an isolated worktree of the loam repo") is factually false.
2. The only viable build location is the loam repo; but `git worktree add` +
   source commits + `amend apply/seal` all write to loam's shared `.git`,
   which the dispatch explicitly prohibits ("do NOT touch loam directly").

Recommendation (a decision, not a question): authorize an isolated loam
worktree `/Users/lukeivers/loam-ws-a4-cost-ceiling-wt` off `main`
(c53458da) on branch `feat/ws-a4-cost-ceiling`; I run the amend cycle there.
This is the standard loam isolation pattern (siblings: loam-ctxmgmt-c1-wt,
loam-fbm-89-wd-guard-wt, …); it does NOT disturb the ws-a5 main checkout's
working tree; WS-A5 is parallel-safe (does not amend cost-governance source).

In-flight halt triggers: out-of-fence drift; a surrounding-code ODD violation;
seal-test fails for reasons unrelated to my edits.
