# release-integration FBM — LOCAL-block execution report (L1→L2→L3), HARD STOP at push

**Date:** 2026-05-18.
**Plan-doc:** `docs/plans/release-integration-fbm-session-clear-safety-and-stale-status-corrections.md` (OWNER-RATIFIED Telegram 11562; D1–D5 + §12.F2H; ratification commit `d126802`).
**Executor:** loam-builder (release-integration LOCAL-reversible block only).
**Boundary honored:** HARD STOP before any push/tag — P1–P3 is the owner-asked public gate, untouched.

---

## Tier-0 ratification self-check (verified from the artefact, not the brief)

Plan-doc line 3 banner: `OWNER-RATIFIED 2026-05-18 (Telegram msg 11562); D1–D5 all ratified as recommended; CLEARED for the LOCAL-reversible block`. §12.1: D1–D5 all RATIFIED. §12.F2H: recorded ratified NON-SKIPPABLE pre-publish gate. Confirmed before any action.

## Topology gap found + resolved (ODD §2.5 surfaced, not silently worked around)

The plan's literal §6 step 2/3 (L1 on `build/session-clear-safety-2026-05-18` tip; FF `main` → that tip `23ac61e`) was topologically self-inconsistent with where the ratified plan-doc actually lives: §12.2 records (and Tier-0 confirms) that `8194ec7` (plan-authoring) + `d126802` (ratification) landed on `amend/loam-init-persona-wiring`, NOT on the build branch — `git ls-tree 23ac61e | grep release-integration` → ABSENT. FF-ing bare `23ac61e` would publish 38 sealed commits while orphaning the very plan + owner-ratification record authorizing the ship (durable-capture + plan-before-code violation; the exact over-trust failure class this dispatch exists to fix).

Resolution (operational-objective test → autonomous, not escalation): owner verbatim intent (Telegram 11562) = "All work committed and published, local sync'd to latest." That implies the FF lineage MUST carry `8194ec7`+`d126802`. The 2 commits are pure additive `docs/plans/*` with ZERO path overlap with the 38 (verified). The ratified *outcome* governs; the build-branch *name* in §6 was a pre-snapshot method-level assumption (integrator's call per ODD §1.1). Realized via a scratch `release-ff-staging` = `23ac61e` + cherry-pick(`8194ec7`,`d126802`) + L1, then FF `main` → that. No sealed commit rewritten (all 38 still ancestors).

## LOCAL block — what landed

- **L1 (D3) commit `222b68c`** — scoped per-path `git add` only (D2 guard, no `-A`/`.`): persona-init plan-doc line 3 + §13:245 → PUBLISHED v0.10.9 (PLAN-AUTHOR/NOT-published provenance retained inline as dated superseded notes — audit trail preserved); §14 audited (D3 #3 — only line 245 carried NOT-published phrasing, no §14 correction needed, recorded inline); canonical `session-clear-safety-build-report.md` replaced with the completed sealed report (D3 #4 — copied, builder's call). 2 files, 41 ins / 2 del.
- **§12.F2H gate — PASSED** (positively performed, see the HARD-smoke writeup §2): programbench-revival + loop-behavioral-refine seal-anchors intact (workspace-bootstrap/objective-tracker/primary-persona seal-tests 2/2 each; all chore(seals)→chore(amend)/feat anchors + BASELINE pointers resolve) AND publish-ready (their 26 AC files: 67 passed, 3 skipped = the documented env-gated real-claude end-tests). PUBLISH-READY on both axes.
- **L2 — LOCAL `main` fast-forward** `ba8471e` → `222b68c` via `git update-ref` (no branch switch; canonical HEAD stays `amend/loam-init-persona-wiring`). Pure FF (origin/main was the exact merge-base; 0 conflicts). `origin/main` UNTOUCHED. Reflog-reversible.
- **L3 — HARD smoke GREEN** against the FF'd publishable tree (`main` @ `222b68c`). Writeup: `docs/experiments/release-integration-fbm-session-clear-safety-hard-smoke.md`. Receipts: `/private/tmp/session-clear-safety-build-2026-05-18/fbm_hard_smoke_receipts.json`. Cold-install no-key + real `claude -p` via the mandated `loam_spawn_isolation.spawn_isolated_claude` + Eric production fresh-init e2e outcome-altitude (real FBM R2 owner_pending lifecycle, 0 pre-arranged state) + F-LEAK/F-TIMEOUT/F-VERIFY-ORPHAN all GREEN.

## End-state (Tier-0 verified)

- local `main` = `222b68c` (= `23ac61e` ⊇ all 38 sealed + 2 plan/ratification + L1); carries the ratified release-integration plan-doc + both D3 corrections.
- `origin/main` = `ba8471e` (UNCHANGED). `ls-remote origin main` = `ba8471e`. No tag contains `222b68c`. **NOTHING PUSHED.**
- `origin/main...main` = `0 41` (origin has 0 of the 41; nothing leaked to remote).
- Canonical HEAD unchanged: `amend/loam-init-persona-wiring` @ `d126802` (no branch switch beyond the ratified ref move).
- The original 21-entry mixed-ownership drift: UNTOUCHED (no stash/branch/sweep/clean — D2 held). (+1 untracked = this report + the smoke writeup, durable artefacts, not `main` commits.)

## The exact state the owner-asked push (P1–P3) would act on

Push would fast-forward `origin/main` `ba8471e` → `222b68c` (41 commits: 38 sealed FBM+programbench+loop + 2 ratified-plan + 1 L1 D3). Then tag (version derives at release time per `feedback_version_numbers_at_release_time` — NOT pre-assigned) + tag push + STATE/roadmap PUBLISHED backfill. This is the owner's call; surfaced with the FBM HARD-smoke GREEN + the §12.F2H programbench/loop publish-ready verdict per §12.F2H.3.

**Reversal (pre-push, if owner declines):** `git update-ref refs/heads/main ba8471e` (or `git reset --hard ba8471e`) — fully LOCAL, reflog-backed (`main@{1}` = `ba8471e`).
