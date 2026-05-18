# Release-integration plan — land FBM session-`/clear` safety onto mainline + correct three over-trusted stale status artefacts

**Status:** RELEASE-SEQUENCING PLAN — **OWNER-RATIFIED 2026-05-18 (Telegram msg 11562); D1–D5 all ratified as recommended; CLEARED for the LOCAL-reversible block (L1→L2→L3); push/tag (P1–P3) remains the OWNER-ASKED public gate.** Plan authored by loam-plan-author 2026-05-18; ratification recorded by loam-plan-author 2026-05-18 (this commit). No merges, no push, no build, no destructive git performed in authoring or in recording this ratification. This is a git-topology + gate plan; it is legitimately procedural. Every step names its reversibility and the LOCAL ↔ PUBLIC boundary. **Consolidated decision register with the owner ruling + the one ratified hardening condition: see §12.**

**WD:** `/Users/lukeivers/loam` (canonical loam; `origin` = `https://github.com/lukeivers/loam.git`).

**Parent objective:** the owner can rule the whole land-sequence from the ≤12-line executive summary in one pass.

**Tier-0 corroboration:** every SHA / branch / ancestry claim below was verified this turn by `git merge-base --is-ancestor`, `git rev-list --left-right --count`, `git ls-remote`, `git log --decorate`, and direct file reads (`file:line` cited inline). Where the dispatcher's context was wrong, the correction carries its evidence (F2 Ruthless Feedback).

---

## §0 — Executive summary (owner rules from here; ≤12 substantive lines)

1. **The dispatcher's central premise is materially wrong, in your favour.** persona-init + its venv patch + subloam-driver-fix are **NOT unpublished** — they shipped in **v0.10.9** (pushed to `origin` 2026-05-15; `f7ccc3d` carries `tag: v0.10.9`, ancestor of `origin/main`). v0.11.0 also published. Nothing about persona-init needs landing.
2. **The genuinely unpublished body is 38 commits off `origin/main` (`ba8471e`/v0.11.0)** on branch `build/session-clear-safety-2026-05-18` — and it is **not just FBM**: it also carries `programbench-revival` (v2 + real-pb + realpb-denoise, 14 commits) and `loop-behavioral-refine-cycle` (5 commits) that the dispatcher did not mention. FBM is the top 17 commits; the rest is pre-existing sealed-local backlog.
3. **The misnamed branch `amend/loam-init-persona-wiring` is a strict ancestor subset** of the FBM branch (its HEAD `26fd2e5` is commit #17-from-tip on `build/session-clear-safety-2026-05-18`). It carries nothing the FBM branch does not. There is no braid to untangle — it is one linear chain.
4. **D1 recommendation:** fast-forward `main` to `build/session-clear-safety-2026-05-18` @ `23ac61e` (zero-conflict — `origin/main` is the merge-base, `0` commits diverge). One linear FF preserves every seal's audit trail. No cherry-pick, no rebase, no merge commit.
5. **D2 recommendation:** the 21-entry working-tree drift is **not on any branch** and a fast-forward does not touch it — it cannot ride the release. Leave it in place untouched (it is mixed-ownership: programbench run-evidence + 4 unrelated plan-doc pairs + an owner-stopped artefact). No stash, no branch, no sweep needed.
6. **D3 recommendation:** fold three doc-status corrections as one scoped commit *before* the FF: (a) persona-init plan-doc line 3 + §13:245 are **triple-stale** (say PLAN-AUTHOR / NOT-published; reality = shipped v0.10.9); (b) canonical `docs/plans/session-clear-safety-build-report.md` is the stale *halted* report (completed report is in the /tmp worktree). Replace both with reality + a pointer.
7. **D4 recommendation:** ONE HARD smoke before publish, scoped to the FBM minor only (persona-init/programbench/loop already shipped or are non-runtime). HARD per `feedback_hard_smoke_per_minor_before_publish`: cold install no-key + real `claude -p` + Eric fixture e2e + F-LEAK/F-TIMEOUT/F-VERIFY-ORPHAN ride-alongs.
8. **D5 recommendation:** LOCAL-reversible = the doc-correction commit + the FF of local `main` + the HARD smoke. PUBLIC + OWNER-ASKED = `git push origin main` + `git tag` + tag push. The plan stops at the publish gate; publish is never autonomous (ASK-FIRST).
9. **One halt-class item, not a planning blocker:** the unpublished body bundles programbench + loop + FBM under one FF. If you want FBM to ship *without* programbench/loop, that needs cherry-pick (higher risk, breaks linearity) — flagged in §8/D1-alt; recommended answer is ship-all (they are sealed-local and were always queued).
10. **Effort:** doc-correction + FF ≈ 8–15 min AI-time (midpoint ~11). HARD smoke + owner gate-review + publish are **separate line items** (§9).

---

## §1 — Tier-0 verified topology (corroborate-or-correct; dispatcher context was wrong)

### 1.1 What is ALREADY PUBLISHED (dispatcher said unpublished — FALSE)

| Body | Seal | On `origin/main`? | Published in |
|---|---|---|---|
| persona-init (`loam-init-persona-wiring-and-isolated-subloam-driver`) | `a7625e0` (apply `4e4df50`, BASELINE `bb5ea69`) | **YES** — `git merge-base --is-ancestor a7625e0 origin/main` → true | **v0.10.9** (`f7ccc3d` carries `tag: v0.10.9`; retro-tag note: "pushed untagged 2026-05-15") |
| venv patch (`loam-init-framework-venv-or-robust-interpreter`) | `dcb2d89` (seal), `5c3b105` (feat) | **YES** | **v0.10.9** |
| subloam-driver-fix | `6b0f19a` / `a69efbf` (seal) | **YES** | **v0.10.9** |

> **F2 Ruthless Feedback — disagreement #1.** The dispatcher's framing ("persona-init … sealed local 2026-05-15 … NOT merged/pushed/published") is contradicted by Tier-0 git. **Evidence:** `git ls-remote --tags origin` shows `v0.10.9 → f7ccc3d`; `git merge-base --is-ancestor a7625e0 origin/main` exits 0 (true); `git rev-list --left-right --count v0.11.0...main` → `0 0`. **Alternative (taken in this plan):** drop persona-init entirely from the land-sequence — it is shipped. The *only* persona-init action is the stale-doc correction (D3), because the plan-doc still *says* PLAN-AUTHOR/unpublished while the work is in production. This is exactly the over-trust failure that motivated this dispatch — confirmed, and now corrected at the source instead of propagated.

### 1.2 What is GENUINELY UNPUBLISHED — 38 commits, not just FBM

`git rev-list --left-right --count origin/main...build/session-clear-safety-2026-05-18` → `0	38` (merge-base = `ba8471e` = `origin/main` = v0.11.0; **zero** divergence on the origin side → clean fast-forward is possible).

The 38 commits decompose (tip → base):

| Band | Commits | Slug | Seal status |
|---|---|---|---|
| **FBM (the dispatch's target)** | `23ac61e`…`a96f698` + ratifications `26fd2e5`,`5e08628` (17 commits) | session-clear-safety R2 → R1 → G | SEALED LOCAL (3 sub-amendments + 2 owner-ratification doc commits) |
| programbench-revival realpb-denoise | `ace6f87`…`7691f71` (4) | programbench-revival-realpb-denoise-and-cost-fix | SEALED LOCAL (STATE.md:115) |
| loop-behavioral-refine | `be3e269`…`5f6a028` (5) | loop-behavioral-refine-cycle | SEALED LOCAL |
| programbench-revival real-pb | `48418ff`…`3ae743e` (6) | programbench-revival-real-pb | SEALED LOCAL |
| programbench-revival v2 | `240d367`…`08a7b94` (6) | programbench-revival-v2 | SEALED LOCAL |

> **F2 Ruthless Feedback — disagreement #2.** The dispatcher described the unpublished body as "two bodies: persona-init + FBM." Tier-0: persona-init is shipped (§1.1); the unpublished body is FBM **plus 15 commits of programbench-revival + loop-behavioral-refine** the dispatcher did not enumerate. **Evidence:** `git log --oneline origin/main..build/session-clear-safety-2026-05-18` (38 lines, listed above); `STATE.md:115` confirms `programbench-revival-realpb-denoise-and-cost-fix SEALED LOCAL ON BRANCH`. **Alternative:** D1 must decide *the whole 38* (recommend ship-all, see §5); D4's HARD-smoke-per-minor must account for whether programbench/loop constitute their own "minor" (they do not gate runtime — §6).

### 1.3 The "misnamed braid" — there is no braid

- `amend/loam-init-persona-wiring` HEAD = `26fd2e5`. `git merge-base --is-ancestor 26fd2e5 build/session-clear-safety-2026-05-18` → true. It is commit #17-from-tip on the FBM branch — a **strict ancestor**, not a divergent braid.
- `git rev-list --left-right --count main...amend/loam-init-persona-wiring` → `0 23`; `…main...build/session-clear-safety-2026-05-18` → `0 38`. Both share merge-base `ba8471e`. The two branches are **the same linear chain at two depths**, not two braided lines.
- The FBM ratification commits `5e08628` (D-SCS.1/2/3) + `26fd2e5` (D-SCS.4) are on the misnamed branch's tip — and `git merge-base --is-ancestor 5e08628 origin/main` → false (NOT published), consistent with §1.2.

> **F2 Ruthless Feedback — disagreement #3 (mild).** "Braided on/around one branch" / "misnamed branch carrying a mix" overstates the entanglement. **Evidence:** the ancestry checks above — it is one linear history; the misnamed branch is just an earlier checkpoint of the FBM branch. **Alternative:** no untangling step is needed; the branch-name is cosmetically wrong but topologically harmless and a fast-forward of `main` makes the branch name irrelevant. A post-FF branch-name cleanup is OPTIONAL housekeeping (§7), not on the release path.

### 1.4 Worktrees (drift-safety context for D2)

`git worktree list`: canonical `/Users/lukeivers/loam` @ `26fd2e5`; two detached `f7ccc3d` spike worktrees (`/private/tmp/{loop-machinery-spike,programbench-step0}-2026-05-15`); the FBM build worktree `/private/tmp/session-clear-safety-build-2026-05-18/loam-wt` @ `23ac61e`. The FBM branch tip `23ac61e` is reachable from both the named branch and that worktree — consistent, no divergence.

---

## §2 — D1: mainline integration model + order

### Loam's release model (inspected, not invented)

- **Model:** trunk = `main` (= `origin/main` = `origin/HEAD`). Releases are **annotated tags `v0.MAJOR.MINOR`** on `main` commits, pushed to `origin`. Latest published: `v0.11.0` @ `ba8471e`. PATCH releases reuse the same minor lineage (v0.10.7/.8/.9 tag-message convention). No `release/*` branches; no GitHub Releases workflow observed; no `CONTRIBUTING.md` mandating a different model (`ls docs/plans | grep -i release` → none; tags are the release record).
- **Branch convention:** sealed-local work accumulates on a working branch off the last published `main`, then `main` is fast-forwarded and tagged. v0.10.9's retro-tag note ("pushed untagged 2026-05-15; tag added for history consistency") confirms the model is *FF main → push → tag*, and that tagging has historically lagged the push (a process nit, not a blocker; D4/D5 tighten it).

This is an **established model** — I am not inventing one, so the §Halt-and-surface condition does **not** fire.

### D1 RECOMMENDATION — fast-forward, ship-all-38

1. **Topology: fast-forward `main` → `build/session-clear-safety-2026-05-18` (`23ac61e`).** `origin/main` is the exact merge-base with `0` commits on the origin side → `git merge-base --is-ancestor origin/main 23ac61e` is true → an FF is possible with **zero conflicts** and **zero rewritten history**. Every seal commit, every `chore(amend)`/`chore(seals)`/`docs(plans)` audit commit lands byte-identical. This is the **lowest-risk topology** and the only one that preserves every seal's audit trail without rewrite.
2. **Order is intrinsic to the FF** — the 38 commits already sit in seal-order (programbench-v2 → real-pb → loop → realpb-denoise → FBM R2 → R1 → G). No reordering, no rebase. The two FBM ratification commits (`5e08628`, `26fd2e5`) are already interleaved correctly in-chain.
3. **Reject cherry-pick and rebase.** Cherry-pick (FBM-only) rewrites SHAs, breaks seal-anchor `chore(amend)` BASELINE pointers, and orphans the 15 programbench/loop commits that are *already sealed-local and were always queued to ship*. Rebase rewrites history on a branch whose commits are seal-anchored — strictly worse. **Reversibility:** an FF of a local branch is fully reversible pre-push (`git reset --hard ba8471e`); a cherry-pick/rebase that rewrites seal anchors is **not** cleanly reversible.

### D1-ALT (only if owner wants FBM-only)
If the owner explicitly wants FBM to ship *without* programbench/loop, that is a cherry-pick of the 17 FBM commits onto a fresh branch off `ba8471e` — higher risk (SHA rewrite breaks `chore(amend)` BASELINE self-references), needs per-commit seal re-verification, and defers 15 already-sealed commits with no stated reason. **Not recommended.** Surfaced as a halt-class option in §8.

---

## §3 — D2: drift disposition

**Finding:** the 21-entry working-tree drift (`git status --porcelain` = 21) is **uncommitted and on no branch**. A fast-forward moves a ref; it never commits working-tree changes. Therefore the drift **cannot ride the release** by construction — no exclude/stash/branch step is required to keep it off.

Composition (Tier-0 `git status --porcelain`, mixed ownership — do NOT destroy, not all yours):
- programbench-revival `realpb/.run_evidence/**` run-evidence (1 deleted `.gitignore`, 1 modified `disposition.json`, ~12 untracked evidence dirs/files) — programbench builder's run artefacts.
- 4 unrelated plan-doc pairs untracked: `binary-usage-observation-harness.{md,manifest.yaml}`, `principle-foundation-structural-enforcement.{md,manifest.yaml}`, `unified-memory-encounter-time-trust-gate.{md,manifest.yaml}`.
- `docs/experiments/programbench-revival-real-pb-PARTIAL-owner-stopped.md` — owner-stopped artefact.
- `docs/plans/session-clear-safety-build-report.md` — the stale halted-builder report (this one IS in scope: D3).

### D2 RECOMMENDATION
**Leave the drift in place, untouched. No stash, no branch, no sweep.** Rationale: (a) the FF release path provably does not include it (refs-only operation); (b) it is mixed-ownership and partly load-bearing run-evidence for an in-flight/unreviewed programbench thread — stashing or branching it risks losing another agent's working state; (c) the *only* drift entry that matters to this release is `session-clear-safety-build-report.md`, handled explicitly under D3. **Reversibility:** "do nothing" is maximally reversible. The one guard: the D3 doc-correction commit MUST use **scoped per-path `git add`** (never `git add -A`/`git add .`) so the FF base commit cannot accidentally absorb the 20 unrelated drift entries.

---

## §4 — D3: stale-artefact cleanup (the over-trust root cause)

Two canonical artefacts assert a status contradicted by Tier-0 reality. Per `feedback_locked_design_not_license`: stale artefacts producing bad outcomes (this dispatch *is* the bad outcome — a whole task spun up on an over-trusted stale line) are fixable; fold the fix in, do not preserve the stale state.

### 4.1 persona-init plan-doc — TRIPLE-stale (worse than dispatcher said)

`docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md`:
- **Line 3:** `**Status:** PLAN-AUTHOR ONLY (loam-plan-author, 2026-05-15). No source edits, no build, no apply, no seal.` — stale (build happened, sealed `a7625e0`, **shipped v0.10.9**).
- **Line 245 (§13):** `**Build cycle:** SEALED LOCAL ON BRANCH … NOT merged to main, NOT shipped, NOT published — sealed-local-on-branch is the deliverable.` — *also* stale: the work **is** on `origin/main` and **was** published in v0.10.9.

> **F2 Ruthless Feedback — disagreement #4.** The dispatcher said only "line 3 is stale, self-contradicted by §13/§14 (SEALED LOCAL)." Tier-0: **§13 is itself stale too** — it says "NOT merged/NOT shipped/NOT published," but `a7625e0` is an ancestor of `origin/main` and shipped in v0.10.9. **Evidence:** `sed -n '245p'` of the plan-doc vs `git merge-base --is-ancestor a7625e0 origin/main` (true) + `v0.10.9 → f7ccc3d` on `origin`. **Alternative:** fix BOTH line 3 and §13:245 (and check §14) to `PUBLISHED in v0.10.9 (origin/main @ ba8471e is post-seal; seal a7625e0; pushed 2026-05-15)`. Fixing only line 3 would leave §13 as the next over-trust trap.

### 4.2 Canonical FBM build-report — stale halted-first-attempt report

`docs/plans/session-clear-safety-build-report.md` (canonical, untracked drift) = the **first halted-builder** report: `**Status: HALTED at pre-build gate … Build NOT performed.**`. The **completed** report lives at `/private/tmp/session-clear-safety-build-2026-05-18/loam-wt/docs/plans/session-clear-safety-build-report.md` (`**Outcome:** ALL THREE sub-amendments SEALED LOCAL in sequence R2 → R1 → G`). Canonical asserts HALTED; reality = sealed.

### D3 RECOMMENDATION — one scoped doc-correction commit, BEFORE the FF

Land a single commit on local `main`-lineage (i.e. on `build/session-clear-safety-2026-05-18` tip *before* FF, OR as the first commit after FF — see §6 sequencing) that:
1. Rewrites persona-init plan-doc **line 3** → published-in-v0.10.9 status (preserve the historical PLAN-AUTHOR provenance as a dated prior-state note, do not erase the audit trail).
2. Rewrites persona-init **§13:245** "NOT merged/shipped/published" → "PUBLISHED v0.10.9; `a7625e0` ancestor of `origin/main`."
3. Audits **§14** of the same doc for the same NOT-published phrasing and corrects consistently.
4. Replaces canonical `docs/plans/session-clear-safety-build-report.md` with the completed report's substance (copy from the /tmp worktree) OR a one-line pointer to the sealed outcome + plan-doc §14 — builder's call on copy-vs-pointer; the *outcome* (canonical no longer asserts HALTED) is what is pinned.
5. **Scoped `git add` of exactly these paths.** Never `git add -A` (D2 guard). Commit message names each correction + cites the Tier-0 evidence SHA.

**Reversibility:** doc-only, pre-push → fully reversible (`git revert` or `reset` of one commit). **Local/public boundary:** this commit is LOCAL until the §5 push; it ships *with* the FBM minor.

---

## §5 — D5: publish-gate sequencing (LOCAL vs PUBLIC boundary — hard line)

The plan **stops at the publish gate.** Everything below the line is OWNER-ASKED (ASK-FIRST per `~/.claude/CLAUDE.md` channel rules + `feedback_no_closing_line_permission_asks` — state the recommendation, the *action* is owner-gated because it is a public action).

### LOCAL — reversible, autonomous-eligible once owner rules D1–D4
| # | Step | Reversibility | Boundary |
|---|---|---|---|
| L1 | D3 scoped doc-correction commit on `build/session-clear-safety-2026-05-18` tip | doc-only, `git revert` | LOCAL |
| L2 | Fast-forward local `main` → `23ac61e` (now incl. L1) | `git reset --hard ba8471e` (pre-push) | LOCAL |
| L3 | HARD smoke (D4) against the FF'd `main` | read-only verification | LOCAL |

### ── PUBLISH GATE (OWNER-ASKED — do NOT cross autonomously) ──

| # | Step | Reversibility | Boundary |
|---|---|---|---|
| P1 | `git push origin main` (FF push; non-force) | low — public; revert = follow-up public commit | **PUBLIC / OWNER-ASKED** |
| P2 | `git tag -a v0.NEXT … && git push origin v0.NEXT` (version derives at release time per `feedback_version_numbers_at_release_time` — do NOT pre-assign here) | low — published tag | **PUBLIC / OWNER-ASKED** |
| P3 | STATE.md / roadmap "PUBLISHED v0.NEXT" backfill commit + push | low — public | **PUBLIC / OWNER-ASKED** |

> **F2 Ruthless Feedback — disagreement #5 (process).** v0.10.9's tag note ("pushed untagged 2026-05-15; tag added later") shows push-then-tag has drifted historically. **Evidence:** `git cat-file tag v0.10.9` message. **Alternative:** make P1 and P2 a single owner-asked unit so the next minor is never pushed-but-untagged. Recommended in the gate above (P1+P2 atomic from the owner's ratification).

### D5 RECOMMENDATION
L1→L2→L3 are LOCAL and reversible; recommend executing them as one autonomous block *after* owner rules D1–D4 from this summary. P1–P3 are a single OWNER-ASKED publish action — surface the green HARD-smoke evidence + the version-at-release-time derivation, then **stop and ask**. Never plan an autonomous push/tag.

---

## §6 — Build/execution sequence (the procedural plan; method = integrator's call per ODD §1.1)

Outcome-shaped where it touches future seal; procedural where it is pure git topology (legitimate for a release plan). Each step states its reversibility + boundary.

1. **Re-Tier-0 the base before any ref move** (integrator's first action): re-run `git rev-list --left-right --count origin/main...build/session-clear-safety-2026-05-18` (expect `0 38`) and `git fetch origin && git rev-parse origin/main` (expect `ba8471e`). If origin moved since 2026-05-18, the FF assumption breaks → HALT (§8). *Reversible: read-only.*
2. **L1 — D3 doc-correction commit** on `build/session-clear-safety-2026-05-18` tip. Scoped per-path `git add` only (D2 guard). *Reversible: doc-only.*
3. **L2 — FF local `main`** to the new tip (L1's commit). `git checkout main && git merge --ff-only build/session-clear-safety-2026-05-18`. Refuse if not fast-forwardable (would signal an unexpected origin move → HALT). *Reversible pre-push: `git reset --hard ba8471e`.*
4. **L3 — HARD smoke** (§ D4 / §below). RED → corrective sub-amendment + re-smoke; do not cross the publish gate RED. *Reversible: verification-only.*
5. **── STOP. Surface green-smoke evidence + version derivation. OWNER-ASKED gate. ──**
6. **P1–P3** only on explicit owner go: push `main`, tag (version derived at release time), push tag, STATE/roadmap PUBLISHED backfill.

### D4 — HARD-smoke-per-minor scope (`feedback_hard_smoke_per_minor_before_publish`)

- **One minor lands at publish:** FBM session-`/clear` safety (the runtime-affecting body — `framework/objective-tracker`, `framework/primary-persona`, `framework/workspace-bootstrap`). programbench-revival + loop-behavioral-refine are *measurement-harness / loop-internal* and do not gate the fresh-init runtime path; they ride the same FF but do not constitute a separate publishable runtime minor (STATE.md:115 frames realpb-denoise as "semantics FROZEN, no measurement-semantics change"). **One HARD smoke, scoped to the FBM minor**, is sufficient; a second programbench smoke is coordination overhead with no tighter acceptance (Lens 5 stopping criterion).
- **→ RATIFIED HARDENING (2026-05-18, §12.F2H):** D4's one HARD smoke staying FBM-scoped is ratified — AND, because ratified D1 ships 3 sealed bodies (FBM + programbench-revival + loop-behavioral-refine) while this smoke covers only FBM, the programbench-revival + loop-behavioral-refine **seal-anchor + publish-readiness re-verification is a NON-SKIPPABLE pre-publish gate** (it runs inside the LOCAL block before the owner-asked push; its result is surfaced to the owner at the push gate alongside the FBM HARD-smoke result). This is the ratified resolution of the internal D1-ships-3 ↔ D4-smokes-1 inconsistency that §0 line 9 / §8 halt-trigger 2 / §10 RF item 2 already flagged — not a new decision. See §12.F2H.
- **HARD bar (per the memory rule):** cold install with **no API key** + real `claude -p` + the real Eric `rd-automation` fixture end-to-end + receipts + regression ride-alongs **F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN**. RED on any → corrective + re-smoke; never publish RED.
- **Where:** smoke runs against the FF'd local `main` (post-L2), BEFORE the publish gate, AFTER L1's doc-corrections are in (so the smoked tree == the tree that would publish).
- **Outcome-altitude:** the smoke invokes the production fresh-init + loop entry-point with no pre-arranged state (per `feedback_test_outcome_altitude_required`); a STUB-class pass does not satisfy D4.

---

## §7 — Out of scope (deferred + when)

- **Branch-name cosmetic cleanup.** `amend/loam-init-persona-wiring` / `build/session-clear-safety-2026-05-18` are mis/over-named. Post-publish OPTIONAL housekeeping (delete merged branches after FF+push); not on the release path, not gating. *Defer to: post-P3, owner discretion.*
- **The 20 non-report drift entries.** programbench run-evidence + 3 unrelated plan-doc pairs + owner-stopped artefact. Their disposition is a *separate* triage (programbench thread owner's call), not this release's scope. *Defer to: separate programbench/FIDRAFT triage.*
- **programbench/loop as their own published minor.** They ship in this FF but are not separately smoked/versioned here. If a future call wants them called out as a distinct minor in STATE/roadmap, that is a doc-framing decision at P3 time. *Defer to: P3 backfill authoring.*
- **Editing `docs/spec/`** — objectives spec, outside any cycle's fence; untouched.

---

## §8 — Halt triggers (in-flight conditions that abort the sequence)

1. **Origin moved.** Step 1 (or L2's `--ff-only`) shows `origin/main` ≠ `ba8471e` or the FF is rejected → the 38-commit clean-FF assumption is void → HALT, re-derive topology, re-surface.
2. **Owner wants FBM-only (D1-ALT).** If the owner rules "ship FBM but not programbench/loop," the FF model is invalid → HALT before any ref move; cherry-pick is a different (higher-risk) plan that needs its own seal re-verification pass. *This is the one planning-relevant decision that could require a pre-execution owner ruling — surfaced here, not silently resolved.* **→ RESOLVED 2026-05-18 (owner ratified ship-all-38; see §12 / §12.F2H). This halt-trigger no longer fires for the FBM-only branch; halt-trigger 4 (seal-anchor re-verification) is now hardened into a NON-SKIPPABLE pre-publish gate by §12.F2H.**
3. **HARD smoke RED.** Any of cold-install / `claude -p` / Eric e2e / F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN fails → do not cross the publish gate; corrective sub-amendment + re-smoke.
4. **A seal anchor fails re-verification.** If step-1 Tier-0 finds any of the 38 commits' `chore(amend)` BASELINE self-pointer inconsistent → HALT (would indicate the chain was rewritten since seal).

**No §Halt-and-surface fires at plan-authoring time:** loam *has* a defined main-integration model (FF `main` + annotated tag + push; §2). I did not invent one. The single decision that *could* need pre-execution owner input (ship-all vs FBM-only, halt-trigger 2) is surfaced with options + a recommendation rather than silently resolved.

---

## §9 — Bookkeeping (separate line items; AI-time bands w/ midpoint)

| Item | Owner | Estimate | Notes |
|---|---|---|---|
| L1 doc-correction commit (3 fixes, scoped add) | integrator (AI) | 4–8 min (mid ~6) | doc-only |
| L2 FF local `main` | integrator (AI) | 1–2 min (mid ~1.5) | ref move |
| **Subtotal LOCAL (L1+L2)** | | **8–15 min (mid ~11)** | reversible pre-push |
| L3 HARD smoke (cold install + `claude -p` + Eric e2e + 3 ride-alongs) | integrator (AI) | **separate line item** — 25–60 min (mid ~40), fetch/install-bound, NOT compressible by tool-call rubric | per `feedback_hard_smoke_per_minor` |
| Owner gate-review (rule D1–D4 from §0) | **owner** | **separate** — owner-availability-bound, not AI-time | gating |
| P1–P3 publish (push + tag + STATE/roadmap backfill) | **owner-asked** | **separate** — 3–6 min AI-time once owner says go | PUBLIC |
| STATE.md: persona-init → "PUBLISHED v0.10.9"; FBM → SEALED→PUBLISHED at P3 | integrator (AI) | folded into L1 (persona-init) + P3 (FBM) | — |
| Roadmap §8 / parent-plan §2 seal-SHA backfill for FBM | integrator (AI) | folded into P3 | — |

Per `feedback_duration_estimation_rubric`: ranges with midpoints, never point estimates; HARD-smoke + owner-review + publish are distinct line items, not summed into the LOCAL band.

---

## §10 — F2 Ruthless Feedback (consolidated; honest doubts)

1. **Dispatcher premise wrong on the biggest fact** (§1.1 disagreement #1) — persona-init is shipped, not unpublished. The whole "land persona-init + FBM" framing collapses to "land FBM + correct the stale persona-init doc." This is the over-trust failure the dispatch was created to fix, now confirmed at root.
2. **Unpublished body is 38 commits, not ~17** (§1.2 #2) — programbench + loop ride the same FF. Owner must consciously ship-all or explicitly carve out (halt-trigger 2).
3. **No braid** (§1.3 #3) — "braided/misnamed branch carrying a mix" overstates it; it is one linear chain at two depths. The plan is simpler than the dispatch implied.
4. **§13/§14 of the persona-init plan are stale too** (§4.1 #4) — fixing only line 3 leaves the next over-trust trap one section down.
5. **Honest doubt — programbench/loop seal provenance.** I verified they are *on the chain* and STATE.md:115 calls realpb-denoise "SEALED LOCAL." I did **not** independently re-run their AC suites (read-mostly scope; out of plan-author remit). Halt-trigger 4 makes seal-anchor re-verification an explicit integrator step before the FF — flagged rather than assumed.
6. **Honest doubt — D3 copy-vs-pointer for the FBM build-report.** I recommend builder's-call on whether to copy the /tmp completed report into canonical or leave a pointer. Pinning the *outcome* (canonical no longer asserts HALTED) not the *method* is deliberate (ODD §1.1); if the owner wants the full report canonicalized, that is a one-word D3 refinement.

---

## §11 — Provenance trail (load-bearing Tier-0 sources)

- `git ls-remote --tags origin` → `v0.10.9 → f7ccc3d`, `v0.11.0 → ba8471e` (both annotated `^{}` present) — persona-init/venv/subloam PUBLISHED.
- `git ls-remote origin refs/heads/main` → `ba8471e` == local `main` == `v0.11.0`.
- `git merge-base --is-ancestor a7625e0 origin/main` → 0 (true); same for `dcb2d89`, `6b0f19a`.
- `git rev-list --left-right --count origin/main...build/session-clear-safety-2026-05-18` → `0	38`; merge-base `ba8471e`.
- `git merge-base --is-ancestor 26fd2e5 build/session-clear-safety-2026-05-18` → true (misnamed branch ⊂ FBM branch).
- `git merge-base --is-ancestor 5e08628 origin/main` / `26fd2e5 origin/main` → false (FBM ratifications UNPUBLISHED).
- `docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md:3` (line-3 PLAN-AUTHOR) + `:245` (§13 NOT-published) — triple-stale.
- `docs/plans/session-clear-safety-build-report.md:3` (`Status: HALTED`) vs `/private/tmp/session-clear-safety-build-2026-05-18/loam-wt/docs/plans/session-clear-safety-build-report.md` (`ALL THREE … SEALED LOCAL`).
- `docs/STATE.md:115` — `programbench-revival-realpb-denoise-and-cost-fix SEALED LOCAL ON BRANCH`.
- `git status --porcelain | wc -l` → 21 (drift, on no branch).
- Release-model inspection: `git tag --sort=-creatordate`, `git cat-file tag v0.10.9` (retro-tag note), no `release/*` branches, no `CONTRIBUTING.md` integration mandate.

---

## §12 — Owner ruling / decision register (RATIFIED — recorded layer; §0–§11 are the recommended layer, preserved intact)

**This section is the consolidated decision register the plan-as-authored did not carry; it is appended, not a rewrite. §2–§6's `### D<N> RECOMMENDATION` blocks remain verbatim as the *recommended* layer. §12 is the *ratified* layer. The recommended→ratified trail is the two layers side-by-side; neither is collapsed into the other.**

**Ruling provenance:** owner, Telegram **msg 11562**, 2026-05-18 — verbatim intent: *"I want to get to a clean state. All work committed and published, local sync'd to latest, etc. agree with recommendations to get there."* (conversational source; recorded here as the durable artefact per the durable-capture rule — the ruling is not durable until it is in this doc). Recorded by loam-plan-author, 2026-05-18, in the same commit as the §0 status flip and the §6/§8 in-place RESOLVED annotations.

### §12.1 — D1–D5: RATIFIED AS RECOMMENDED

| D | Subject | Recommended layer (unchanged) | Ruling (msg 11562) | Maps to step |
|---|---|---|---|---|
| **D1** | Mainline integration model | §2 "D1 RECOMMENDATION — fast-forward, ship-all-38" + §0 line 4 | **RATIFIED.** FF `main` → `build/session-clear-safety-2026-05-18` @ `23ac61e`; ship all 38 commits (FBM 17 + programbench-revival 16 + loop-behavioral-refine 5). D1-ALT (FBM-only cherry-pick) is NOT taken. | §6 step 3 (L2); §5 L2 |
| **D2** | Drift disposition | §3 "D2 RECOMMENDATION" + §0 line 5 | **RATIFIED.** Leave the 21-entry working-tree drift untouched (FF is refs-only; drift cannot ride the release). No stash/branch/sweep. | §3; §6 D2 guard (scoped per-path `git add`) |
| **D3** | Stale-artefact cleanup | §4 "D3 RECOMMENDATION — one scoped doc-correction commit, BEFORE the FF" + §0 line 6 | **RATIFIED.** One scoped doc-correction commit before the FF: persona-init plan-doc line 3 + §13/§14 → PUBLISHED v0.10.9; replace the stale canonical FBM build-report. | §6 step 2 (L1); §5 L1 |
| **D4** | HARD-smoke-per-minor scope | §6 "D4 — HARD-smoke-per-minor scope" + §0 line 7 | **RATIFIED, with hardening §12.F2H.** ONE HARD smoke, FBM-scoped, per `feedback_hard_smoke_per_minor_before_publish`. | §6 step 4 (L3); §5 L3 |
| **D5** | Publish-gate sequencing | §5 "D5 RECOMMENDATION" + §0 line 8 | **RATIFIED.** Execute the LOCAL-reversible block (L1→L2→L3) as one autonomous block, then **STOP**. P1–P3 (push + tag + STATE/roadmap backfill) remain a single OWNER-ASKED public action — push/tag is owner-asked, never autonomous. | §5 LOCAL / PUBLISH-GATE tables; §6 steps 5–6 |

**Net effect of the ruling:** the plan is CLEARED to execute L1→L2→L3 autonomously. The plan-doc's own §Halt-and-surface did not fire (established FF model, §2); halt-trigger 2 (FBM-only) is now closed by D1's ratification (annotated in place at §8). Halt-triggers 1, 3, 4 remain live in-flight conditions for the integrator (origin moved / HARD-smoke RED / seal-anchor failure) — ratification does not dissolve them.

### §12.F2H — Ratified hardening condition on D1/D4 (dispatcher F2; resolution of a PRE-FLAGGED item, not a new decision)

**What was already flagged (recommended/flagged layer, unchanged):** §0 line 9, §8 halt-trigger 2, and §10 RF item 2 each flagged that the ratified body ships **3 sealed bodies** (FBM + programbench-revival + loop-behavioral-refine) while D4's HARD smoke is scoped to **FBM only** — i.e. ship-all-38 publishes programbench-revival + loop-behavioral-refine, whose seal-anchor / publish-readiness re-verification the plan deferred "to the integrator step" (halt-trigger 4) and which D4's smoke does not cover. This is an internal D1-ships-3 ↔ D4-smokes-1 inconsistency the plan itself surfaced; it was left as a flagged-but-unresolved item.

**Provenance of this resolution:** dispatcher F2 Ruthless Feedback (recorded 2026-05-18). This is **not a new decision** — it is the ratified resolution of the already-flagged item above. "Owner agreed to the recommendations" does not dissolve the gap that ship-all publishes two bodies the FBM-scoped smoke does not cover (locked-design-not-license): the gate is recorded, not erased by the blanket agree.

**Ratified resolution:** the programbench-revival + loop-behavioral-refine **seal-anchor + publish-readiness re-verification is a NON-SKIPPABLE pre-publish gate**, with these binding properties:

1. **It runs inside the LOCAL-reversible block, BEFORE the owner-asked push** (sequenced with / alongside halt-trigger-4's seal-anchor re-verification at §6 step 1 and L3; it does not move the publish gate, it gates *entry* to the publish gate).
2. **It is NOT skippable** — neither D4's FBM-only smoke scope nor "they are sealed-local and were always queued" (D1 rationale) discharges it. The seal-anchor + publish-readiness re-verification for programbench-revival (v2 + real-pb + realpb-denoise, 16 commits) and loop-behavioral-refine (5 commits) must be positively performed, not assumed.
3. **Its result is surfaced to the owner at the push gate, alongside the FBM HARD-smoke result** — the owner sees both the FBM HARD-smoke evidence AND the programbench/loop seal-anchor + publish-readiness re-verification result before ruling P1–P3. RED on either → do not cross the publish gate (consistent with §6 step 4 / §8 halt-trigger 3 + 4).

**Scope note (recording fidelity):** this condition records a verification *gate* on the already-ratified D1/D4; it does **not** alter the FF target (`23ac61e`), the integration topology (linear FF, ship-all-38), or the substance of any D. It closes the plan's own flagged internal inconsistency as the ratified answer to it. Per the recording mandate, no D's substance was re-opened to record this; had accurate recording required that, it would have been halted-and-surfaced instead.

### §12.2 — Recommended→ratified audit-trail integrity (ODD §2.5)

- Every D's *recommended* prose (§2–§6) is byte-unchanged. §12.1 adds the *ratified* column beside it. The two layers are both visible — the trail is not collapsed.
- The pre-flagged ship-all-vs-smoke-scope item retains its original flag text at §0 line 9 / §8 halt-trigger 2 / §10 RF item 2 / §6 D4-scope; each now carries an in-place `→ RESOLVED/RATIFIED (§12.F2H)` pointer so the flagged item is not silently left looking open while its origin prose stays intact.
- Every D and the F2H condition maps to a concrete step in §5/§6 (mapping column in §12.1; explicit sequencing in §12.F2H). No ratified item is register-only with no executable step.
- Build/FF/smoke/integrator-verify were NOT executed in recording this ratification (recording-scope only). The commit carrying this register is one tightly-scoped LOCAL `docs(plan)` child of `8194ec7` on `amend/loam-init-persona-wiring`, scoped per-path `git add`, no push/tag/branch-switch/`--amend` — same recording pattern as `5e08628` / `26fd2e5` / `8194ec7`.
