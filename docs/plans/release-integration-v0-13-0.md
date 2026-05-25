# Release-integration plan — v0.13.0 MINOR publish (ECC absorption Wave 1 + ride-alongs)

**Status:** RELEASE-INTEGRATION PLAN — **OWNER-RATIFIED** at dispatcher level: public release authorized Telegram 12368; SemVer-MINOR judgment ratified Telegram 12372; six gate rulings (HARD-smoke author+run, release-integration plan-doc author, STATE.md author, release-roadmap §3 author, worktree-based execution, per-component pyproject lockstep apply) relayed via Telegram 12373. CLEARED for the LOCAL-reversible block + the OWNER-AUTHORIZED tag push (publish authorization carried in this brief). Plan authored by loam-builder 2026-05-24 in the release-staging worktree `/Users/lukeivers/loam-release-v0-13-0`.

**WD:** `/Users/lukeivers/loam-release-v0-13-0` (isolated worktree on branch `release-staging-v0-13-0` off `main` HEAD `2df36f5`; canonical `/Users/lukeivers/loam` is on `main` `2df36f5` == `origin/main` `2df36f5`, zero divergence, FF trivially possible).

**Parent objective:** ship v0.13.0 MINOR as the consolidated publish of Wave 1 ECC absorption (5 sealed work-items + ride-along bookkeeping) since v0.12.21, with the per-MINOR per-component pyproject version lockstep advancing 0.12.0 → 0.13.0 in one source-of-truth commit.

**Tier-0 corroboration:** every SHA / branch / topology claim below was verified this turn (2026-05-24) by `git rev-parse`, `git ls-remote`, `git log`, direct `pyproject.toml` reads, and structural-test grep against `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`.

---

## §0 — Executive summary (≤12 substantive lines)

1. **Current state.** `main` @ `2df36f5` == `origin/main` @ `2df36f5` (zero divergence, FF trivial). Last published tag `v0.12.21` (lightweight) underlies commit `1d40311`. v0.12.0 was the last annotated tag and last MINOR. 32 commits land in v0.13.0 (`git rev-list --count v0.12.21..HEAD` = 32).
2. **What v0.13.0 ships (5 Wave 1 WIs + ride-alongs).** Wave 1 ECC absorption (everything-claude-code absorption master plan, Wave 1): (i) `readme-restructure-decision-doc-positioning` seal `a39d5ce`; (ii) `readme-ac3-synonym-list-widening` (corrective, smoke-driven) seal `0a76e12`; (iii) `strategic-compact-skill-graduation` seal `84aa38a`; (iv) `token-defaults-optin-skill` seal `e4c3123`; (v) `security-hooks-bundle` seal `a7fc68b`. Ride-along bookkeeping: per-component-pyproject-version-lockstep regression closure PATCH seal `7402a09` (predates Wave 1, but lands in this MINOR window); README.3 corrective bookkeeping rolled into (ii); strategic-compact STATE.md backfill rolled into (v) `871f052`; d1 byte-content drift correction `5d53983`; security-hooks-bundle manifest correction `28cf3f5`; SECHK.1 push-protection fix `2df36f5`; ratify-commit `64c8f24` (records owner rulings into 4 plan-docs); bafi-stale-test-retire amendment #148 seal `8fea4b9` (predates Wave 1 in lineage; lands in this window).
3. **F2 Ruthless Feedback — disagreement #1 (count clarification, not substance).** The dispatcher's F2 named "4 Wave 1 WI plan-doc references." Tier-0 (commit 871f052's message + STATE.md change-log walk): there are **5** sealed Wave 1 entries — Wave 1.1 readme-restructure + Wave 1.1-corrective readme-ac3-synonym-widening (a separate sealed cycle, not a rolled-in bookkeeping commit) + Wave 1.2 strategic-compact + Wave 1.3 token-defaults + Wave 1.4 security-hooks-bundle. **Evidence:** `git log --oneline v0.12.21..HEAD` + `docs/STATE.md` lines beginning `**2026-05-24** — **AC.README.3 wrapper synonym list widening SEALED LOCAL (corrective to predecessor cycle)**` (independent SEAL clause with its own seal SHA `0a76e12`). **Alternative (taken in this plan):** the §2/§3 inventory carries all 5 explicitly; the SemVer judgment stays MINOR (Telegram 12372 was scoped to the absorption substance, not the count; new sealed cycles do not promote MINOR→MAJOR by count); the Wave 1.1-corrective is sub-numbered (1.1-corrective) so the "Wave 1 = 4 WI families" framing remains intact at the bookkeeping altitude.
4. **F1 — HARD smoke ratified AUTHOR + RUN.** Per `feedback_hard_smoke_per_minor_before_publish`. Writeup at `docs/experiments/release-integration-v0-13-0-hard-smoke.md`. Scope: cold install no-key + real `claude -p` + Wave 1.4 safety-hooks empirical exercise + F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN regression ride-alongs. GREEN gate before tag push.
5. **F6 — per-component lockstep applies.** 27 in-scope pyprojects + `docs/ACTIVE_MINOR` bump 0.12.0 → 0.13.0 in one source-of-truth commit. Verified at plan-time: 27 pyprojects currently at 0.12.0 (`grep -rn 'version = "0.12.0"' framework plugins --include='pyproject.toml' | wc -l` → 27); `docs/ACTIVE_MINOR` currently `0.12.0`; the structural test `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` enforces. AC.PCVR.4's hard-coded fixture-internal `"0.12.0"` string at lines 287/294/308/316/321 stays as-is (tmp_path fixture-only, decoupled from real ACTIVE_MINOR).
6. **F5 — worktree-based execution.** All edits + commits in `/Users/lukeivers/loam-release-v0-13-0` on branch `release-staging-v0-13-0`. Owner's WIP drafts in the canonical tree (`docs/plans/drafts/` + `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md`) are untracked and unaffected by the worktree branch.
7. **Topology + publish path.** Build commits land on `release-staging-v0-13-0`. After HARD smoke GREEN, FF `main` → `release-staging-v0-13-0` (in canonical tree), then `git push origin main` + `git tag -a v0.13.0` + `git push origin v0.13.0`. The publish IS authorized (Telegram 12368 public release + 12372 SemVer + 12373 gate rulings); the only halt-gates are HARD-smoke RED, structural-test fail, push fail.
8. **Sequenced steps (§6).** L1 plan-doc + this commit → L2 lockstep bump → L3 HARD smoke → L4 STATE.md + roadmap + README backfill → L5 FF canonical main → L6 tag + push.
9. **Halt triggers (§8).** HARD smoke RED/UNCLEAR; structural test fail; worktree creation fail (already passed); tag push fail; out-of-fence drift discovered mid-cycle.

---

## §1 — Tier-0 verified topology

### 1.1 Branch/tag state

- Local `main` @ `2df36f5` == `origin/main` @ `2df36f5` (`git ls-remote origin refs/heads/main` → `2df36f5...`).
- `git rev-list --left-right --count origin/main...HEAD` → `0	0` (zero divergence).
- Last annotated MINOR tag: `v0.12.0` underlying commit `47c2725` (`git cat-file tag v0.12.0` → MINOR annotated by tagger Luke Ivers 2026-05-18).
- Last lightweight tag: `v0.12.21` underlying commit `1d40311` (current Active-Version per `docs/release-roadmap.md` §3 line 166 + README.md line 155).
- 32 commits in window: `git rev-list --count v0.12.21..HEAD` → 32 (confirmed).

### 1.2 In-scope WI seals (Wave 1 ECC absorption — 5 sealed cycles)

| Wave | Slug | Seal SHA | Plan-doc | Notes |
|---|---|---|---|---|
| 1.1 | `readme-restructure-decision-doc-positioning` | `a39d5ce` | `docs/plans/sealed/readme-restructure-decision-doc-positioning.md` | README restructured for audience-routing per D-README.* family |
| 1.1-corrective | `readme-ac3-synonym-list-widening` | `0a76e12` | `docs/plans/sealed/readme-ac3-synonym-list-widening.md` | Closes D-build.README.2 (loose AC text widening per `feedback_loose_AC_text_fix_AC_not_implementation`) |
| 1.2 | `strategic-compact-skill-graduation` | `84aa38a` | `docs/plans/sealed/strategic-compact-skill-graduation.md` | Graduates `feedback_compact_clear_decision_heuristic` memory rule to discoverable SKILL |
| 1.3 | `token-defaults-optin-skill` | `e4c3123` | `docs/plans/sealed/token-defaults-optin-skill.md` | Documenter section + opt-in SKILL bundle with non-destructive merge helper |
| 1.4 | `security-hooks-bundle` | `a7fc68b` | `docs/plans/sealed/security-hooks-bundle.md` | Three PreToolUse safety-layer hooks + B2 migration from bash_guard per D-SECHK.OVERLAP option B (owner-overridden A→B, TG 12311) |

### 1.3 Ride-along / non-Wave-1 lineage commits (rolled into v0.13.0 publish)

- `7402a09` chore(seals): per-component-pyproject-version-lockstep-regression-closure (PATCH; predates Wave 1 in lineage but ships in this MINOR window).
- `8fea4b9` chore(seals): amendment #148 loam-bafi-stale-test-retire (predates Wave 1; in window).
- `64c8f24` ratify(ecc-absorption-wave-1): records owner rulings into 4 plan-docs.
- `871f052` docs(state): backfill strategic-compact (Wave 1.2) + add security-hooks-bundle (Wave 1.4) STATE.md change-log entries.
- `5d53983` fix(test_d1_byte_content): retire-and-rebaseline two pyproject.toml SHAs (out-of-cycle-fence corrective surfaced by Wave 1.4 seal sweep).
- `28cf3f5` chore(security-hooks-bundle): correct manifest frozen_baseline for hands-off-lifecycle.
- `2df36f5` fix(test_AC_SECHK_1): bypass GitHub push-protection on Stripe test literals (current HEAD).

### 1.4 Per-component pyproject version state (pre-bump)

`grep -rn 'version = "0.12.0"' framework plugins --include='pyproject.toml' | wc -l` → **27** (matches the lockstep allowlist `IN_SCOPE_PYPROJECTS` exactly). `docs/ACTIVE_MINOR` → `0.12.0`. Excluded set (4 measurement/experimental harnesses) confirmed at `0.0.0` per `EXCLUDED_PYPROJECTS` allowlist semantics.

---

## §2 — SemVer judgment (RATIFIED Telegram 12372)

**v0.13.0 = MINOR.** Owner-ratified Telegram 12372. Rationale verbatim (mirroring v0.12.0 tag-message pattern):

> Wave 1 of the everything-claude-code-absorption master plan adds new user-visible outcome shape: (i) two new loam SKILLs (`strategic-compact`, `cost-optimised-defaults`) discoverable in any fresh workspace via the existing `_symlink_plugin_skills` walk, (ii) three new always-on PreToolUse safety-layer hooks (`secret_pattern_guard`, `dangerous_flag_guard`, `config_write_guard`) installed by default in every fresh workspace via the existing `merge_pre_tool_use` multi-contributor mechanism, (iii) audience-routing rewrite of the project README with new "Is this for you?" segmentation. Items (i) and (ii) constitute new tracked user-visible primitives (SKILLs + safety hooks) — MINOR-class per `docs/release-versioning-policy.md`. Item (iii) alone would be doc-only (PATCH-class); composed with (i)+(ii) the release is MINOR.

Version derived at release time per `feedback_version_numbers_at_release_time` from (`current_published = v0.12.21`, `work_class = MINOR`) → `next_MINOR(v0.12.21) = v0.13.0`. NOT pre-assigned (this slug-named release-integration plan-doc carries the version in its filename only because it was authored post-derivation, per dispatcher's explicit ruling).

---

## §3 — Gate rulings (recommended → ratified, all RATIFIED)

| Gate | Subject | Recommended | Ruling (dispatcher 12373 / owner 12368+12372) | Maps to step |
|---|---|---|---|---|
| F1 | HARD smoke for v0.13.0 MINOR | AUTHOR + RUN per `feedback_hard_smoke_per_minor_before_publish` | **RATIFIED.** Writeup at `docs/experiments/release-integration-v0-13-0-hard-smoke.md`. GREEN required before tag push. | §6 step 3 (L3) |
| F2 | Release-integration plan-doc | AUTHOR per v0.12.0 precedent | **RATIFIED.** This document. | §6 step 1 (L1) |
| F3 | STATE.md v0.13.0 entry | AUTHOR per standard rollup shape | **RATIFIED.** Prepend to change-log. | §6 step 4 (L4) |
| F4 | release-roadmap.md §3 entry | AUTHOR with seal SHA `2df36f5` + WI bullets | **RATIFIED.** Append §3 entry; SHA list per §1.2 + §1.3. | §6 step 4 (L4) |
| F5 | Working-tree-clean gate | WORKTREE per v0.12.0 precedent | **RATIFIED.** `/Users/lukeivers/loam-release-v0-13-0` branch `release-staging-v0-13-0`. | §6 step 0 (W0; DONE) |
| F6 | Per-component pyproject lockstep | APPLY (27 pyprojects + ACTIVE_MINOR) | **RATIFIED.** Single source-of-truth commit. Structural test enforces. | §6 step 2 (L2) |

---

## §4 — Acceptance criteria

- **AC.REL.1 — Plan-doc authored.** This document exists at `docs/plans/release-integration-v0-13-0.md` with §1–§8 populated.
- **AC.REL.2 — Lockstep bump applied.** All 27 in-scope pyprojects at `version = "0.13.0"`; `docs/ACTIVE_MINOR` content == `0.13.0`; `pytest plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` returns GREEN (5 tests).
- **AC.REL.3 — STATE.md backfilled.** Top of `docs/STATE.md` change-log carries a `**2026-05-24** — **v0.13.0 MINOR (Wave 1 ECC absorption …)**` entry naming the 5 WI seals + ride-alongs.
- **AC.REL.4 — release-roadmap.md §3 backfilled.** New entry appended to §3 with `SHIPPED PUBLIC 2026-05-24 (tag v0.13.0, annotated <SHA>; seal 2df36f5)` once tag is created; entry includes the 5 WI list.
- **AC.REL.5 — README current-release bumped.** Line 155 of `README.md` updated to `v0.13.0`.
- **AC.REL.6 — HARD smoke GREEN.** `docs/experiments/release-integration-v0-13-0-hard-smoke.md` authored; cold install no-key + real `claude -p` + Wave 1.4 safety-hooks exercise + F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-alongs all GREEN; outcome-altitude per `feedback_test_outcome_altitude_required`.
- **AC.REL.7 — Tag created + pushed.** Annotated tag `v0.13.0` exists locally + on origin; tag message carries SemVer rationale + 5 WI list + seal SHA `2df36f5`.
- **AC.REL.8 — Owner WIP untouched.** Canonical tree (`/Users/lukeivers/loam`) `git status --porcelain` post-execution shows the same two untracked entries (`docs/plans/drafts/`, `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md`) and nothing else changed in canonical tree directly (canonical tree only sees the FF of `main`, not the worktree-side commits as new changes).

---

## §5 — Publish-gate sequencing (LOCAL vs PUBLIC)

The publish IS authorized (Telegram 12368 + 12372 + 12373 gate rulings). No further owner-gate inside this plan; the gates that remain are mechanical: HARD-smoke verdict + structural-test pass + push success.

### LOCAL — reversible block (autonomous execution)

| # | Step | Reversibility | Boundary |
|---|---|---|---|
| L1 | This plan-doc commit on `release-staging-v0-13-0` | doc-only, `git revert` | LOCAL |
| L2 | Lockstep bump commit (27 pyprojects + ACTIVE_MINOR) on `release-staging-v0-13-0` | doc-only / version-string, `git revert` | LOCAL |
| L3 | HARD smoke (writeup + execution) | verification-only | LOCAL |
| L4 | STATE.md + release-roadmap §3 + README current-release commit on `release-staging-v0-13-0` | doc-only, `git revert` | LOCAL |
| L5 | FF canonical `main` → `release-staging-v0-13-0` (in `/Users/lukeivers/loam`) | `git reset --hard 2df36f5` (pre-push) | LOCAL |

### PUBLIC — authorized push (mechanical, halt only on push failure)

| # | Step | Reversibility | Boundary |
|---|---|---|---|
| P1 | `git push origin main` (FF, non-force) | follow-up public commit | PUBLIC (authorized) |
| P2 | `git tag -a v0.13.0 -m '...' <FF-tip-SHA> && git push origin v0.13.0` | tag deletion (rare) | PUBLIC (authorized) |
| P3 | (Optional follow-on) STATE.md SHIPPED-PUBLIC flip / roadmap §3 flip-to-SHIPPED-PUBLIC commit + push — folded into the L4 commit because the publish gate is the same turn | doc-only | PUBLIC (authorized) |

---

## §6 — Build/execution sequence

1. **W0 (DONE)** Worktree created at `/Users/lukeivers/loam-release-v0-13-0`, branch `release-staging-v0-13-0` off `main` HEAD `2df36f5`. Verified clean.
2. **L1** This plan-doc commit (scoped per-path `git add docs/plans/release-integration-v0-13-0.md`).
3. **L2** Lockstep bump: edit 27 pyprojects + `docs/ACTIVE_MINOR` 0.12.0 → 0.13.0; run `pytest plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` to confirm GREEN; commit scoped.
4. **L3** HARD smoke writeup + execution per F1 ruling; commit writeup.
5. **L4** STATE.md prepend + release-roadmap.md §3 append + README current-release bump; one commit (scoped per-path).
6. **L5** Canonical-tree `cd /Users/lukeivers/loam && git fetch origin && git checkout main && git merge --ff-only release-staging-v0-13-0` (refuse if not FF — would signal an unexpected origin move; halt).
7. **── HARD smoke GREEN gate; halt-and-surface if RED/UNCLEAR ──**
8. **P1** `git push origin main` from canonical tree.
9. **P2** Annotated tag `v0.13.0` + push.

---

## §7 — Out of scope (deferred)

- **Branch cleanup.** `release-staging-v0-13-0` worktree branch is post-publish OPTIONAL housekeeping (delete merged branch + remove worktree). Not gating.
- **Wave 2 planning.** Wave 2 of everything-claude-code-absorption master plan is a separate roadmap concern. Not this MINOR.
- **Editing `docs/spec/`.** Objectives spec, outside any cycle's fence.
- **v1.0.0 promotion.** Dispatcher ruled NOT YET — quality-bar criteria (real third-party user shipping with loam) not empirically met.

---

## §8 — Halt triggers (in-flight)

1. **HARD smoke RED on any cold-install / `claude -p` / safety-hooks exercise / regression ride-along.** Halt + surface specific failure to dispatcher; corrective sub-amendment + re-smoke before publish gate.
2. **HARD smoke UNCLEAR** (could not reach verdict — environment-broken, timeout, partial probe). Halt + surface.
3. **Structural test fail** (`test_AC_PCVR_pyproject_version_lockstep.py` RED after L2 bump). Halt + diagnose drift between allowlist and actual pyproject set.
4. **Origin moved** between W0 and L5. `git fetch origin && git rev-parse origin/main` returns something other than `2df36f5` → FF assumption void → halt, re-derive topology.
5. **Tag push fails** (network, auth, naming collision). Halt + surface; do not retry blindly.
6. **Out-of-fence drift discovered mid-cycle** (e.g., a sealed-component test fails for reasons unrelated to my edits). Halt + surface as F2 finding — do NOT silently extend scope.

---

## §9 — Bookkeeping (separate AI-time line items, midpoint bands)

| Item | Owner | Estimate (AI-time, midpoint) | Notes |
|---|---|---|---|
| L1 plan-doc commit | builder (AI) | 3–5 min (~4) | this commit |
| L2 lockstep bump commit (27 pyprojects + ACTIVE_MINOR) | builder (AI) | 6–12 min (~9) | scripted batch |
| L3 HARD smoke (writeup + cold install + `claude -p` + safety-hooks + regression rides) | builder (AI) | 25–60 min (~40) | install/probe-bound; not compressible by tool-call rubric |
| L4 STATE.md + roadmap + README backfill | builder (AI) | 5–10 min (~7) | scoped doc edits |
| L5 FF canonical main | builder (AI) | 1–2 min (~1.5) | ref move |
| **Subtotal LOCAL** | | **40–89 min (~62)** | reversible pre-push |
| P1+P2 push + annotated tag + tag push | builder (AI; authorized) | 2–4 min (~3) | mechanical |

Per `feedback_duration_estimation_rubric`: ranges with midpoints, never point estimates.

---

## §10 — F2 Ruthless Feedback (consolidated)

1. **§0.3 — count clarification.** Dispatcher F2 said "4 Wave 1 WI plan-doc references"; actual count is 5 (Wave 1.1-corrective `readme-ac3-synonym-list-widening` is a separate sealed cycle, not a rolled-in bookkeeping commit). Captured here as a count clarification; does NOT alter the MINOR judgment (SemVer ruled on substance, not cycle count) and does NOT alter any gate ruling.
2. **Honest doubt — HARD smoke scope.** Wave 1.4 introduces three always-on PreToolUse hooks that fire on `Bash|Edit|Write|MultiEdit` tool calls. The HARD smoke should exercise at least one path through each hook (allow + block cases) to verify they don't silently break in fresh-init context. The existing 84+ AC.SECHK.* tests cover correctness in the component fence; the HARD smoke's additional value is end-to-end-from-cold-install. This is captured in the HARD smoke writeup's probe design.
3. **Honest doubt — Wave 2 absorption coupling.** This plan covers Wave 1 ONLY. If Wave 2 plan-docs were drafted in parallel and inadvertently introduced changes inside this window, they would have surfaced as additional sealed cycles in `git log v0.12.21..HEAD`. Tier-0: no Wave 2 seals in window (verified by reading the full 32-commit list).

---

## §11 — Provenance trail

- `git rev-parse HEAD` → `2df36f5ae91877023d5e4233ba7e3a4f111bf62d` (release-staging-v0-13-0 tip == canonical main at worktree creation).
- `git ls-remote origin refs/heads/main` → `2df36f5...` (zero divergence).
- `git rev-list --count v0.12.21..HEAD` → 32.
- `grep -rn 'version = "0.12.0"' framework plugins --include='pyproject.toml' | wc -l` → 27 (matches lockstep allowlist).
- `cat docs/ACTIVE_MINOR` → `0.12.0`.
- `cat README.md | sed -n '155p'` → "current public release is v0.12.21. The project remains intentionally".
- Wave 1 seal SHAs verified by `git log --oneline v0.12.21..HEAD` walk + STATE.md change-log read.
- v0.12.0 precedent for release-integration plan-doc: `docs/plans/release-integration-fbm-session-clear-safety-and-stale-status-corrections.md`.
- v0.8.0 precedent for HARD smoke shape: `docs/experiments/v0-8-0-hard-smoke.md`.
- Owner authorizations: Telegram 12368 (public release), 12372 (SemVer MINOR), 12373 (six gate rulings via dispatcher).

---

## §12 — Method-decision register (build-time)

| Decision | Subject | Ruling | Provenance |
|---|---|---|---|
| D-REL.WD | Working directory for build | `/Users/lukeivers/loam-release-v0-13-0` (worktree) | F5 ruling Telegram 12373 |
| D-REL.LOCKSTEP-METHOD | How to bump 27 pyprojects | Scripted batch with verification grep | Builder's call (ODD §1.1); single-commit per F6 |
| D-REL.HARD-SMOKE-SHAPE | What constitutes GREEN | Cold install + `claude -p` + 3 safety-hooks exercise + 3 regression ride-alongs | `feedback_hard_smoke_per_minor_before_publish` |
| D-REL.TAG-SHAPE | Annotated vs lightweight | **Annotated** (matches v0.12.0 precedent for MINOR tags; v0.12.1..v0.12.21 PATCHes were lightweight) | v0.12.0 precedent + SemVer-MINOR semantics |
| D-REL.WAVE-1.1-CORRECTIVE-FRAMING | Count 4 vs 5 | Carry 5 in inventory; carry "Wave 1 = 4 WI families" framing at SemVer altitude | §10.1 F2 + ratify-commit framing |
| D-REL.RIDE-ALONGS-ROLLUP | Whether to enumerate ride-alongs in tag message | YES — surface in tag message for audit-trail completeness | Audit-trail discipline + v0.12.0 precedent |
