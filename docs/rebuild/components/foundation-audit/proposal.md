# Proposal — Foundation Audit Disposition + Power-Through Pass

**Component:** Foundation Audit — the disposition stage. The audit produced the gap report; this proposal rules on each finding and scopes the power-through pass asked for.
**Status:** DRAFT — awaiting owner's approval before brief authoring.

**Checkpoint anchor:** `86cb261` on `pos-v2` (landed as an empty commit immediately before this proposal; preserves the pre-power-through state for rollback).

---

## 1. Objective

Dispose every finding in the audit's gap table — accept-with-rationale, fix-now, or defer-with-trigger — and execute the fix-now items as a single power-through build before sealing the foundation-audit component.

directive recorded 2026-04-20 16:12: *"let's just power through and blow out all the remaining things. but. i want a checkpoint here. i want to be able to return to this point. fixing bugs is where regressions can happen and they can be terribly hard to unwind."* The checkpoint (`86cb261`) is landed; the scoping is this proposal's job.

## 2. The scope question — what "power through" actually covers

the owner's "blow out all the remaining things" intersects with the reality that some BACKLOG items require their own proper research → proposal → build → seal cycle because they amend a sealed component's source. Six decay-retention patches fit that shape; each is a one-session component in itself. Trying to blow through six amendment cycles in one pass is the over-reach class.

**the primary persona's scoping ruling (subject to owner's approval):** power-through covers finished-now items — fix-smalls from the audit, trivial promotions of already-queued defers, BACKLOG grooming, and the foundation-audit component seal. Decay-retention patches remain in BACKLOG as genuine deferrals with named triggers; each gets its own cycle when the owner picks it up.

Three scope options for ruling recorded in §3.

## 3. Scope options

| Option | What's in | Wall-clock estimate | Recommendation |
|---|---|---|---|
| **A — tight** | Fix-smalls (3) + BACKLOG grooming + foundation-audit seal | ~20–30 min | recommendation |
| **B — expanded** | Option A + the three ⭐⭐⭐ decay-retention patches (orchestrator heartbeat, memory JSONL, graceful-degradation events) | ~90–180 min | If wanted the high-value decay items in this session |
| **C — everything fit for one session** | Option B + budget-extension diagnostic span + defensive-regex retirement | ~120–240 min | If wanted the cleanest residual BACKLOG possible |

Items **never in scope for one session** regardless of option: wire real dispatch primitive (awaits dispatch primitive design), launchd re-activation (awaits running-state), 250k-edge chaos test (requires live infrastructure), memory detection blind-spot (needs own research cycle), first-run-orientation auto_update_mode (depends on onboarding which is deferred), the three ⭐⭐/⭐ decay-retention patches under Option B (not in scope for that option; C folds them in).

the primary persona recommends **Option A.** The audit's value lands cleanly; the three big decay items remain honest deferrals rather than being rushed through six-in-a-row sealed-component amendments. If wanted B or C, the proposal re-expands accordingly.

## 4. Dispositions — every audit finding

From audit research.md §9. Each gets a classification that holds regardless of scope option.

### 4.1 Accept-with-rationale (9 items) — one-line ratifications, no action

| # | Finding | Rationale |
|---|---------|-----------|
| A1 | `runtime.py` ~460 lines in scope-of-work | STATE.md rule 9 exempts new-pOS; cohesion-first |
| A2 | PostCompact workaround (flag-and-detect) | Python Agent SDK limitation; the owner-approved 2026-04-18 17:07 |
| A3 | 1 pre-existing skipped test in objective-tracker | Depends on live memory-system infra; design-correct |
| A4 | Self-upgrade failed-rollback path manual-only | ruling recorded prototype-only; CI overengineering |
| A5 | Reversibility `get_spec_hash` identity via import re-export | `import` provides single-source-of-truth equivalence |
| A6 | Primary-persona `type: ignore[import-not-found]` on monitor.py | Editor hint for solo-package install envs |
| A7 | A20 safety-beats-degradation added during build | Exact ODD re-extension pattern working as intended |
| A8 | 1 pre-existing skipped live-memory test at scope-of-work | Design-correct; opt-in integration |
| A9 | Self-correction OTel `retention_class="high"` → `NORMAL` remap | Builder correctly resolved the primary persona's phantom-value ruling |

### 4.2 Fix-small (3 items in Option A, +variable in B/C)

| # | Finding | Action |
|---|---------|--------|
| F1 | Workspace-bootstrap proposal §3.2 ordering claim stale (code correct; doc wrong) | Doc edit on `components/workspace-bootstrap/proposal.md` |
| F2 | SEAL_COMMIT sidecar retrofit for reversibility-primitive + cost-governance | Create `tests/SEAL_COMMIT` files; update the two `test_no_sealed_amendments.py` to use sidecar pattern (same class as self-correction/workspace-bootstrap) |
| F3 | Memory-system has its own `.venv` by design (Graphiti deps) — test-discipline note | One-paragraph addition to the workspace's test-running doc or BACKLOG |

Option B adds F4–F6 (three ⭐⭐⭐ decay patches). Option C adds F7–F10 (remaining ⭐⭐/⭐ decay patches + budget-extension diagnostic). Each of F4 onwards is a full sealed-component amendment cycle.

### 4.3 Defer-with-trigger (preserved in BACKLOG)

Eight items kept in BACKLOG as still-valid deferrals with explicit triggers:

| # | Finding | Trigger condition |
|---|---------|-------------------|
| D1 | Wire real dispatch primitive | Dispatch primitive designed |
| D2 | 250k-edge chaos stress test | Long-term-volume durability claims desired |
| D3 | Launchd plist re-activation | First "running pOS" handoff |
| D4 | Memory-system detection blind-spot enhancement | Next time memory is touched, or tightening detection valuable |
| D5 | First-run-orientation `auto_update_mode` integration | Orientation-component design work (deferred per 2026-04-20 15:28 ruling) |
| D6 | Three ⭐⭐⭐ decay-retention patches (if Option A) | the owner picks up each component-cycle |
| D7 | Three ⭐⭐/⭐ decay-retention patches (if Option A or B) | the owner picks up each component-cycle |
| D8 | Budget-extension diagnostic span (if Option A or B) | If observability ever surfaces unexplained post-hoc overruns |

### 4.4 Retire-as-resolved (from audit §10)

Four items retired as already-done:

- Wire real scope-of-work primitive (memory) — done via `RealScopeSourceAdapter`
- Build observability aggregator — sealed 2026-04-19 11:24
- Build self-upgrade framework — sealed 2026-04-19 14:12
- Seal-test template pattern (cost-gov follow-on) — structurally remedied on `f94d602`
- Defensive gate-refusal exclusion regex note — documentation only; no action needed

### 4.5 Audit-surfaced BACKLOG addition

One item added to BACKLOG as an audit-surfaced defer:

- Live pytest re-run to verify full-tree count (now resolved mid-audit by the primary persona: 824 tests passing; retire alongside).

## 5. Build plan (Option A — recommendation)

Six sequential actions. No wraps, no engines, no new packages — this is tidy-up work against existing code and docs.

1. **Checkpoint commit on `pos-v2`** — already landed at `86cb261`. Preserves pre-power-through state.
2. **F1 — workspace-bootstrap proposal §3.2 doc fix** — edit the proposal.md table entry; zero code change.
3. **F2 — SEAL_COMMIT sidecar retrofit for reversibility + cost-governance** — create the two sidecar files, update the two test files to read from sidecar (same pattern as self-correction's `tests/SEAL_COMMIT` + test), verify both tests still pass.
4. **F3 — Memory-system own-venv test-discipline note** — add to BACKLOG.md or a test-discipline doc at workspace root.
5. **BACKLOG.md replacement** — retire resolved items, preserve valid defers, add audit-surfaced additions. Single commit.
6. **Foundation-audit seal** — component.md to COMPLETE, STATE.md row to COMPLETE, populate `components/foundation-audit/` with its own SEAL_COMMIT sidecar if it carries tests (it doesn't — research component only — so this step reduces to component.md + STATE.md updates).

Commit granularity: recommendation is one commit per logical action (4 commits: F1, F2, F3+BACKLOG, foundation-audit-seal) so individual actions can be reverted to the checkpoint if anything regresses. the owner's call if the owner prefers fewer commits.

## 6. Build plan (Option B — expanded)

Option A's six actions, plus three proper amendment cycles — each for a ⭐⭐⭐ decay-retention patch — each going through research → proposal → build → seal.

| Patch | Sealed component it amends | Estimated cycle time |
|---|---|---|
| Orchestrator heartbeat rollup | orchestrator | ~30–45 min |
| Memory JSONL rotation | memory-system | ~30–45 min |
| Graceful-degradation detection_events rollup | graceful-degradation | ~30–45 min |

These are sequential; each opens, runs, seals, with its own SEAL_COMMIT ritual. Total Option-B addition: ~90–135 min on top of Option A's 20–30.

## 7. Build plan (Option C — everything fit)

Option B's cycles, plus:

| Patch | Sealed component it amends | Estimated cycle time |
|---|---|---|
| Scope-of-work terminal-scope `BudgetDebited` rollup | scope-of-work | ~30–45 min |
| Orchestrator `bind_refused` / `scope_activated` rollup | orchestrator | ~20–30 min |
| Scope-of-work state-defining events for aged terminal scopes | scope-of-work | ~30–45 min |
| Budget-extension diagnostic span | cost-governance | ~10–15 min |
| Retire defensive gate-refusal exclusion regex note | self-correction docs | ~5 min |

Option-C addition over Option B: ~95–140 min. Total Option-C span: ~4–5 hours.

## 8. Effort estimate

| Option | Wall-clock estimate | Risk profile |
|---|---|---|
| A | 20–30 min | Low — doc edits + small sidecar retrofits |
| B | 110–210 min (~2–3.5 hr) | Medium — three full amendment cycles back-to-back |
| C | 205–350 min (~3.5–6 hr) | High — six amendment cycles + trailers; likely to overrun or produce subtle interaction bugs across multiple rolled-up event streams |

Calibration note against the pattern flagged 2026-04-19 (research agents' AI-min = 5–10× calendar minutes): these estimates are **calendar minutes, not AI-min**. the primary persona is anchoring honestly given the recent audit miss.

Red-line suggestions:
- Option A: halt at 45 min; scope has drifted.
- Option B: halt at 3.5 hr; one of the patches surfaced a design issue needing own-cycle treatment.
- Option C: the primary persona would genuinely push back on this option; the cross-component event-stream interactions between six near-simultaneous rollup patches invite regression in ways the checkpoint can partially but not fully protect against.

## 9. inferences recorded — flagged for ruling recorded

1. **Scope option recommended is A.** Inference; the owner's "power through" energy might want B. Flag if I'm under-reading.
2. **Commit granularity per fix-small.** One commit per logical action for revertability. If the owner prefers one big "power-through-pass" commit, challenge.
3. **Retirement of the defensive regex documentation note.** Audit classified as "documentation only; no action." the primary persona is treating this as retirable rather than keeping as a BACKLOG entry. Challenge if wanted it kept.
4. **Memory-system test-discipline note location** (BACKLOG vs workspace-root doc vs component README). the primary persona leans BACKLOG because that's where operational gotchas already aggregate; other locations arguable.
5. **Foundation-audit component doesn't carry its own test suite**, so its seal ritual reduces to component.md + STATE.md updates rather than a SEAL_COMMIT sidecar. If the owner prefers we populate a dummy sidecar for uniformity, challenge.
6. **Option B's three ⭐⭐⭐ choices.** Research §10 ranked these as ⭐⭐⭐; the primary persona carried the ranking forward. If the owner sees different priority ordering, challenge.

## 10. Approval ask

sign-off opens brief drafting for the chosen scope. Specifically requesting:

- **Scope ruling** — Option A, B, or C (or a custom carve-out).
- **Per-disposition dissent (if any)** — if any accept-with-rationale item should actually be fix-now, or any fix-now should be defer, surface now.
- **Commit granularity ruling** — one commit per logical action (recommendation) or fewer.
- **Ratification of primary-persona inferences in §9** — approve as written, or adjust.

Approve as-is, approve with changes (pick scope option + any adjustments), or reject.
