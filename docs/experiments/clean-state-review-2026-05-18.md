# Clean-state review inventory — canonical loam pre-publish (2026-05-18)

**Author:** loam-builder (release-execution dispatch). **Date:** 2026-05-18 (Tier-0 `date`: Mon May 18 16:50 CDT 2026).
**Tree:** canonical `/Users/lukeivers/loam` (pos-sync canonical_source; GitHub `lukeivers/loam`, PUBLIC). NOT pos3.
**Why this file:** the read-only reviewer that produced the dispatch findings could not persist its inventory; this is the durable audit trail of the pre-publish state, reconstructed from a fresh Tier-0 sweep.

---

## 1. Git ref state (Tier-0, verified this turn)

| Ref | SHA | Note |
|---|---|---|
| `origin/main` (live `ls-remote`) | `ba8471e` | == tag `v0.11.0`; FF-able target; verified immediately pre-push |
| local `main` / `release-ff-staging` | `222b68c` | = `ba8471e` + 41 commits; FF (linear, `ba8471e` is ancestor) |
| checked-out `HEAD` | `d126802` | branch `amend/loam-init-persona-wiring` (FF was a ref update, not a checkout) |
| `build/session-clear-safety-2026-05-18` | `23ac61e` | ancestor of `222b68c` (in the 41-delta) |
| `amend/memory-session-continuity` | `4e8c41f` | Tier-0: ancestor of `222b68c` (MERGED) — NOT in brief prune list, surfaced not auto-deleted |

41-commit delta `ba8471e..222b68c`: 38 sealed FBM/programbench/loop commits + release-integration plan `7233659` + owner ratification `9e25d2a` + D3 doc-fix `222b68c`. Delta subjects scanned — no secret, no unrelated body, all seal anchors well-formed.

Remote tags present: `v0.10.0`..`v0.10.9`, `v0.11.0` (no `v0.11.x`>0 / `v0.12.x` tag exists locally or remotely).

## 2. The 9-banner table vs Tier-0 reality (F2 reconciliation)

The dispatch table listed 9 stale banners. Tier-0 cross-check against STATE.md seal lines + git seal-SHA ancestry found **3 already correct on the push lineage**; **6 genuinely stale**; and several cited SHAs were source-edit/doc-backfill commits, not the authoritative §14 seal:

| # | file | dispatch said | Tier-0 reality | action |
|---|---|---|---|---|
|1|loam-init-persona-wiring…:3|"PLAN-AUTHOR ONLY" → fix to PUBLISHED v0.10.9|ALREADY corrected on `main` (`222b68c` D3): reads "PUBLISHED in v0.10.9 … superseded provenance retained"|none — already correct|
|2|same §13|"NOT merged/shipped" → fix|ALREADY corrected on `main`: "PUBLISHED in v0.10.9" + dated superseded note|none — already correct|
|3|session-clear-safety-build-report.md:3|"HALTED…Build NOT performed"|The version **on `main`** already reads the completed sealed report ("ALL THREE SEALED LOCAL … NOT pushed"). The "HALTED" text is the **untracked working-tree drift copy**, which does NOT ride the push.|none on push lineage — already correct; untracked drift left untouched (out of scope)|
|4|loop-behavioral-refine-cycle.md:3|plan-only → SEALED dd73ad6|STATE:117 SEALED; authoritative §14 seal `dd73ad6`|CORRECT|
|5|programbench-revival-realpb-denoise-and-cost-fix.md:3|plan-only → SEALED 541a19b|STATE:115 SEALED; §14:198 seal is `bfe76fc` (`541a19b` is source-edit)|CORRECT — cite seal `bfe76fc`|
|6|programbench-revival-real-pb.md:3|plan-only → SEALED f7497f7|§14:255 seal `5694ff2` (`f7497f7` is the §9-backfill doc commit / amendment BASELINE)|CORRECT — cite seal `5694ff2`|
|7|programbench-revival-v2.md:3|plan-only → SEALED fd0eda4|STATE:186 SEALED; delta-log seal `e273966` (`fd0eda4` is source-edit/BASELINE)|CORRECT — cite seal `e273966`|
|8|phase-b-intake-fix.md:3|plan-only → SEALED ceb629b|STATE:127 SEALED; register seal `ceb629b`|CORRECT|
|9|loop-goal-refinement.md:3|plan-only → SEALED ef59d1f|STATE:117 cites "(ef59d1f)"; §14 seal `ef59d1f`|CORRECT|

**F2 finding A (named, evidence, alternative):** The dispatch's "9 banners, all stale" framing was inaccurate — banners #1/#2/#3 are already correct on the push lineage (`222b68c` D3 commit + the sealed build-report already on `main`). Evidence: `git show main:<file>` line 3 / §13 for #1/#2; `git cat-file -e main:docs/plans/session-clear-safety-build-report.md` + its on-`main` line 6 for #3. Alternative applied: correct only the 6 genuinely-stale banners (#4–#9); do NOT re-edit already-correct content (ODD §2.5 — every edit maps to the objective; re-editing correct text is non-objective churn).

**F2 finding B:** Several dispatch-table "truth" SHAs were source-edit/doc-backfill commits, not the authoritative §14 seal. Evidence: each plan's own §14 register (`bfe76fc` for #5 vs dispatch's `541a19b`; `5694ff2` for #6 vs `f7497f7`; `e273966` for #7 vs `fd0eda4`). Alternative applied: each correction cites the authoritative §14 seal SHA, with the dispatch-cited SHA noted where it is the source-edit/BASELINE (provenance, not the seal).

**F2 finding C (STATE.md is itself a pre-push banner):** STATE.md:115/117/119/127/186/188 all carry "SEALED LOCAL ON BRANCH … NOT pushed, not published, `origin/main` unchanged at ba8471e". These are TRUE pre-push and go false at the moment of push. Per `feedback_published_state_only_from_git_refs` the published-state truth source is the git ref / tag ancestry, NOT STATE.md prose. STATE.md:119 specifically still says persona-init "NOT published" while its seal `a7625e0` IS an ancestor of `ba8471e` (already published v0.10.9) — STATE.md:119 is itself stale; the git tag ancestry wins. The STATE.md pre-push lines are corrected in P3 (post-push backfill), exactly as the dispatch scoped.

## 3. Working-tree drift (23 entries — ALL left untouched per scope)

- 2 realpb run-evidence changes (`.run_evidence/.gitignore` D, `yj/disposition.json` M) — owner-stopped run evidence.
- `docs/experiments/programbench-revival-real-pb-PARTIAL-owner-stopped.md` + realpb `.run_evidence/{figlet,gron,verdict.json,yj/*}` + `.run_evidence.prefix-archive-2026-05-16/` — owner-stopped real-PB run; explicitly out of scope.
- `docs/plans/session-clear-safety-build-report.md` (untracked drift copy, stale "HALTED" text) — the tracked sealed version on `main` is correct; the untracked copy is drift, out of scope to disposition.
- 3 unrelated plan-only draft pairs — `binary-usage-observation-harness.{md,manifest.yaml}`, `principle-foundation-structural-enforcement.{md,manifest.yaml}`, `unified-memory-encounter-time-trust-gate.{md,manifest.yaml}` — explicitly out of scope.
- 2 release-integration FBM reports untracked — `release-integration-fbm-LOCAL-block-execution-report.md`, `release-integration-fbm-session-clear-safety-hard-smoke.md` — these ARE the FBM HARD-smoke evidence; captured into the L1 scoped commit per dispatch L0 ("ensure existing release-integration-fbm-* reports are captured").

Scoped per-path `git add` only — never `-A`/`.`. The drift, owner-stopped work, and 3 unrelated drafts are NOT staged, NOT reverted, NOT cleaned.

## 4. Worktrees + branches (prune plan)

| Worktree | SHA | Disposition |
|---|---|---|
| `/Users/lukeivers/loam` | d126802 | primary — keep |
| `/private/tmp/loop-machinery-spike-2026-05-15/loam-clean` | f7ccc3d (detached) | stale /tmp — prune |
| `/private/tmp/programbench-step0-2026-05-15/loam-clean` | f7ccc3d (detached) | stale /tmp — prune |
| `/private/tmp/session-clear-safety-build-2026-05-18/loam-wt` | 222b68c [release-ff-staging] | holds release-ff-staging; remove worktree post-push, then `-d` branch |

| Branch | SHA | Merged into 222b68c? | Disposition |
|---|---|---|---|
| `amend/loam-init-persona-wiring` | d126802 | n/a (checked out, ahead by D3 only) | keep (active; D3 doc-fix `222b68c` is the push tip's parent lineage) |
| `release-ff-staging` | 222b68c | == tip | `-d` after push (trivially merged) |
| `build/session-clear-safety-2026-05-18` | 23ac61e | YES (ancestor) | `-d` after push |
| `amend/memory-session-continuity` | 4e8c41f | YES (ancestor) | NOT in brief prune list — surface, do not auto-delete |
| `main` | 222b68c | self | the pushed branch |

---

*This inventory is the durable Tier-0 record of pre-publish state. The release-execution log is `docs/experiments/release-publish-execution-2026-05-18.md`.*
