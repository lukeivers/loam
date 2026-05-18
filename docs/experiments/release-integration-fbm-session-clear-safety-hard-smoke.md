# release-integration FBM session-`/clear`-safety — HARD smoke writeup

**Cycle:** release-integration LOCAL block L3 (ratified D4; release-integration plan §6 step 4).
**Date:** 2026-05-18.
**Plan-doc:** `docs/plans/release-integration-fbm-session-clear-safety-and-stale-status-corrections.md` (OWNER-RATIFIED Telegram 11562; D1–D5 + §12.F2H).
**Slug-named per** `F-CYCLE-ARTEFACT-SLUG-NAMING` (NOT `v0-NEXT-hard-smoke.md` — version derives at release time per `feedback_version_numbers_at_release_time`).
**Smoke scope:** the FBM minor only (`feedback_hard_smoke_per_minor_before_publish`) — persona-init shipped v0.10.9, programbench/loop are non-runtime measurement/loop-internal (their seal-anchor + publish-readiness is the separate §12.F2H gate, GREEN, recorded below).
**Smoke target:** the FF'd publishable tree, local `main` @ `222b68c` (= `23ac61e` + the 2 ratified-plan commits + L1 D3), exercised via the byte-identical `release-ff-staging` worktree.

---

## §1 — Verdict

**GREEN.** Every HARD-bar element passed against the publishable tree. Receipts: `/private/tmp/session-clear-safety-build-2026-05-18/fbm_hard_smoke_receipts.json`.

| Stage | Verdict | Evidence |
|---|---|---|
| no-key-invariant | GREEN | `ANTHROPIC_API_KEY` absent (subscription-only — `feedback_no_anthropic_api_key`) |
| cold-install | GREEN | brand-new venv + 32-component intra-repo editable closure (FBM runtime: objective-tracker / primary-persona / workspace-bootstrap + loam-spawn-isolation), 40.3s, no PyPI for loam-*, no API key, FBM imports OK cold |
| isolation-mandate-guard | GREEN | un-isolated `claude` argv correctly rejected (`ValueError`) — Telegram-death-#5 structural guard live, not decorative (AC.PROMO.4) |
| F-LEAK | GREEN | isolated env scrubbed (no `TELEGRAM_BOT_TOKEN`/`CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN`/`ANTHROPIC_API_KEY` spellings) + `CLAUDE_PERSONA=loam-isolated-spawn` |
| claude-p-real | GREEN | real `claude -p` (sonnet, routed through the mandated `loam_spawn_isolation.spawn_isolated_claude`) returned READY in 2.8s, rc=0 |
| F-TIMEOUT | GREEN | bounded real spawn returned 2.8s < 240s wall ceiling (no hang) |
| eric-e2e-outcome-altitude | GREEN | PRODUCTION fresh-init + session-`/clear`-safety path against a never-seeded workspace, **0 pre-arranged tracker rows**: `owner_pending` reached via async `mark_owner_pending`; queryable back via `get`; `owner_pending_count=1` / `active_count=0` (distinct from active + terminal — FBM R2 core); `start` after owner-pending → `active` (resolves when owner rules); primary-persona digest entry wired; `backfill_tracker_for_existing_workspace` → `TrackerSeedResult` |
| F-VERIFY-ORPHAN | GREEN | no `bun server.ts` orphan attributable to the isolated smoke (the present bun is the operator's own; the isolation excludes the telegram plugin — exactly the #5 defense) |

Outcome-altitude (`feedback_test_outcome_altitude_required`): the e2e stage invokes the production `ObjectiveTracker` async API + `backfill_tracker_for_existing_workspace` against a workspace with zero pre-arranged state — a STUB-class pass would not satisfy it; this is the real FBM R2 owner_pending lifecycle exercised end-to-end.

## §2 — §12.F2H NON-SKIPPABLE pre-publish gate (programbench-revival + loop-behavioral-refine)

The ratified ship-all-38 FF carries programbench-revival (v2 + real-pb + realpb-denoise, 16 commits) + loop-behavioral-refine-cycle (5 commits) which the FBM-scoped HARD smoke does not cover. §12.F2H makes their seal-anchor + publish-readiness re-verification a non-skippable pre-publish gate. Positively performed (not assumed):

- **Seal-anchor integrity:** workspace-bootstrap `tests/test_no_sealed_amendments.py` (the BASELINE-aware seal-test covering all four bodies' workspace-bootstrap BASELINE bumps) — **2 passed** at `23ac61e`. objective-tracker + primary-persona seal-tests (FBM R2/R1) — **2 passed each**. Every `chore(seals)` correctly anchors its `chore(amend)`/feat; all BASELINE self-pointers resolve; SEAL_COMMIT sidecars consistent. No seal anchor rewritten (all 38 still ancestors after the 2-commit cherry-pick + L1).
- **Publish-readiness (own ACs):** programbench-revival + loop-behavioral-refine AC suites (`AC.PBD.*` 6 + `AC.BRC.*` 6 + `AC.PBR.*` 7 + `AC.RPB.*` 7 = 26 files) — **67 passed, 3 skipped** (the 3 skips are the documented env-gated real-claude lead end-tests behind `HANDSOFF_RUN_BRC=1`/`HANDSOFF_RUN_RPB=1` — collected-but-skipped by design per the plan-docs, the intended deterministic-seal behaviour).

§12.F2H verdict: **programbench-revival + loop-behavioral-refine PUBLISH-READY** on both axes (seal-anchor intact + own-ACs GREEN). Surfaced to the owner at the push gate alongside this FBM HARD-smoke GREEN per §12.F2H.3.

## §3 — Method note (harness correctives, not FBM defects — `feedback_no_false_fault_admission`)

Two harness REDs were corrected in-environment before GREEN, neither an FBM-code defect (four-test applied — upstream production code behaved exactly as designed):

1. **cold-install RED** — initial harness did `pip install <component-dir>` expecting PyPI resolution; loam is not a PyPI distribution. The established loam cold-install model (HARD-smoke history) is a fresh venv editable-installing the intra-repo dependency closure from the source tree. Harness corrected to install the 32-component closure; "cold" = brand-new venv + no key + from the publishable tree (not "from PyPI"). Smoke method is the integrator's call (ODD §1.1); this did NOT loosen the HARD bar.
2. **eric-e2e RED** — probe called the sync `backfill_tracker_for_existing_workspace` (which owns its own `asyncio.run`) from inside a running event loop → `RuntimeError: asyncio.run() cannot be called from a running event loop`. The production function behaved correctly (a sync wrapper is not callable from a running loop — exactly as the sealed AC test invokes it sync). Probe sequencing corrected to call it outside the async scope.

Both corrections followed `feedback_agent_empirical_recheck_before_halt`: the RED conclusion had a non-FBM alternative hypothesis (wrong install method / wrong call context), tested and confirmed in-environment before any halt.
