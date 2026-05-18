# Release-publish execution report — canonical loam → completely clean PUBLISHED state (2026-05-18)

**Executor:** loam-builder (release-execution dispatch). **Date:** 2026-05-18 (Tier-0 `date`: Mon May 18 16:50 CDT 2026; push window ~16:55–17:05 CDT).
**Tree:** canonical `/Users/lukeivers/loam` (pos-sync canonical_source; GitHub `lukeivers/loam`, PUBLIC). pos3 NEVER touched.
**Authorization:** owner Telegram 11562 / 11566 (publish to completely clean state, after verified HARD-smoke-GREEN + §12.F2H-PASSED). Push was the authorized terminus, not a halt.
**Companion:** `docs/experiments/clean-state-review-2026-05-18.md` (pre-publish inventory + F2 findings A/B/C).

---

## Outcome (Tier-0, every SHA verified)

| Phase | Result |
|---|---|
| L0 audit persist | `docs/experiments/clean-state-review-2026-05-18.md` + 2 release-integration-fbm-* reports captured (committed in L1 `47c2725`) |
| L1 6-banner correction | commit **`47c2725`** on the `main`/`release-ff-staging` lineage (built in the `release-ff-staging` worktree, NOT the stale `amend/loam-init-persona-wiring` working copy) |
| Pre-push HARD gate | ALL 5 PASS (live `origin/main`==`ba8471e`; `23ac61e` ancestor; FF-able; delta 42; no secret/unrelated subject) |
| P1 push | `ba8471e..47c2725  main -> main` fast-forward, no force. Tier-0: live `origin/main` == **`47c2725`** (== pushed tip) |
| P2 tag | annotated **`v0.12.0`** (tag object `0d25d0a`) → `47c2725`; pushed; Tier-0 remote `refs/tags/v0.12.0` == `0d25d0a` |
| P3 backfill | STATE.md change-log v0.12.0 PUBLISHED record + roadmap §2 SHIPPED-PUBLIC record + Total-shipped narrative correction + this report; one scoped commit, FF main, pushed |
| Reconcile + prune | see below |

### Version derivation (per `feedback_version_numbers_at_release_time`)

NOT pre-assigned. Inputs: current_published `v0.11.0` (= `ba8471e`, Tier-0 from git tag); work-class = **MINOR** (the dominant new user-visible outcome in the 41-commit delta is session-`/clear` safety — FIDRAFT `F-FBM-SESSION-CLEAR-SAFETY` RESOLVED, a workspace `/clear`/compaction no longer silently loses end-user state without a hand-maintained RESUME-STATE file; AC.PO.1 + AC.PO.2 laddered up — a "new outcome-shape capability" per `docs/release-versioning-policy.md` line 13). The programbench-revival / loop / phase-b work is META-FRAMEWORK / honest-negative experiment + internal-loop work (no new user outcome). `next_MINOR(v0.11.0) = v0.12.0`. No `v0.11.x`>0 / `v0.12.0` tag pre-existed (local or remote, Tier-0).

### The 9-banner post-state (Tier-0)

| # | file | post-state |
|---|---|---|
|1|loam-init-persona-wiring…:3|ALREADY correct on push lineage ("PUBLISHED in v0.10.9 …" + dated superseded note, from `222b68c` D3) — not re-edited (ODD §2.5)|
|2|same §13|ALREADY correct ("PUBLISHED in v0.10.9" + superseded note) — not re-edited|
|3|session-clear-safety-build-report.md|version ON `main` already the completed sealed report ("ALL THREE SEALED LOCAL … NOT pushed", correct content) — not re-edited; "NOT pushed" line is a P3-class clause superseded by the STATE/roadmap published record (the untracked working-tree "HALTED" drift copy was left untouched, out of scope)|
|4|loop-behavioral-refine-cycle.md|CORRECTED → SEALED, seal `dd73ad6`, dated superseded note retained|
|5|programbench-revival-realpb-denoise-and-cost-fix.md|CORRECTED → SEALED, seal `bfe76fc` (source-edit `541a19b` noted), superseded note retained|
|6|programbench-revival-real-pb.md|CORRECTED → SEALED, seal `5694ff2` (`f7497f7` = §9-backfill/amendment-BASELINE, noted), superseded note retained|
|7|programbench-revival-v2.md|CORRECTED → SEALED, seal `e273966` (source-edit `fd0eda4` noted), verdict honest-negative noted, superseded note retained|
|8|phase-b-intake-fix.md|CORRECTED → SEALED, seal `ceb629b`, honest-negative re-harden noted, superseded note retained|
|9|loop-goal-refinement.md|CORRECTED → SEALED, seal `ef59d1f`, superseded note retained|

All 6 corrected banners cite the authoritative §14/register seal SHA (each Tier-0-verified a real commit AND an ancestor of pushed `origin/main` `47c2725`); prior text preserved verbatim as dated superseded notes (history not erased).

## F2 findings (named / evidence / alternative — surfaced, not silently resolved)

- **A — "9 stale banners" framing inaccurate.** #1/#2/#3 were already correct on the push lineage (`git show main:<file>`). Alternative applied: corrected only the 6 genuinely-stale (#4–#9); did not re-edit correct text (ODD §2.5 — non-objective churn avoided). Not a critical-call decision; operational objective (no false public docs) gave the clear answer; executed autonomously, recorded here.
- **B — dispatch-table "truth" SHAs were source-edit/doc-backfill, not the §14 seal.** Evidence: each plan's own §14 register (`bfe76fc`≠`541a19b`; `5694ff2`≠`f7497f7`; `e273966`≠`fd0eda4`). Alternative applied: cited the authoritative §14 seal, noting the dispatch SHA where it is the source-edit/BASELINE (provenance).
- **C — STATE.md is itself a pre-push banner; STATE.md:119 stale.** STATE.md:115/117/119/127/186/188 carried true-on-their-date "NOT pushed / origin unchanged at ba8471e" clauses; STATE.md:119 still said persona-init "NOT published" while `a7625e0` was already an ancestor of `ba8471e` (public v0.10.9). Per `feedback_published_state_only_from_git_refs` the git tag ancestry is authoritative. Alternative applied: added a single authoritative dated PUBLISHED record at the top of the change-log that explicitly supersedes the embedded clauses; historical entries retained verbatim as the dated audit trail (NOT mutated — mutating them would erase when each was local-only).
- **D — Total-shipped aggregate count not recomputed.** Per `feedback_arithmetic_verification` a fragile row-grep recompute would risk an unverified computed claim; the project's release-CLI walker maintains the aggregate. Corrected the narrative published-state clauses surgically (v0.10.8 → public, persona-init → public v0.10.9, +v0.12.0); left the numeric aggregate to its owning mechanism. Deliberate non-action, recorded.

## Reconcile + prune

- **Working-tree reconcile:** the owner working tree at `/Users/lukeivers/loam` is on `amend/loam-init-persona-wiring` `d126802` with ~21-entry mixed-ownership drift + owner-stopped real-PB run-evidence + 3 unrelated draft pairs. The release was built entirely in the `release-ff-staging` worktree via `git update-ref` FF of `main` — the owner tree was NEVER checked out / switched / cleaned (Tier-0: HEAD still `d126802`, `disposition.json` drift still present + untouched). Bringing the on-disk owner tree into agreement with published `main` requires a checkout that would collide with the owner's untracked drift copy of `session-clear-safety-build-report.md` (the stale "HALTED" copy) — **deliberately NOT forced**: that is owner-disciplined working-tree hygiene (the published `main` already carries the correct sealed report; the drift is the owner's to disposition). Surfaced, not silently resolved.
- **Worktree prune:** removed stale `/private/tmp` worktree registrations (see Tier-0 log).
- **Branch prune:** `-d` only branches Tier-0-verified merged into the pushed tip; unmerged / out-of-list branches preserved with reason (see Tier-0 log).

## Untouched (explicit confirmation)

- **pos3** — never touched (different tree, main session cwd; separate owner-disciplined sync phase).
- **owner-stopped work** — `programbench-revival-real-pb-PARTIAL-owner-stopped.md` + realpb `.run_evidence/*` + `disposition.json` M + `.gitignore` D — not staged, not reverted, not cleaned.
- **3 unrelated plan-only draft pairs** — `binary-usage-observation-harness`, `principle-foundation-structural-enforcement`, `unified-memory-encounter-time-trust-gate` (`.md`+`.manifest.yaml` each) — entirely untouched.
- No force-push, no history rewrite, no `--amend`, no rebase of pushed lineage. All pushes fast-forward.

---

*Durable release-execution audit trail. The return message to the dispatcher carries the tight summary; this file is the full record.*
