# Release Integration — v1.12.0 (per-session episodic resume + release-CLI/guard-floor/brittle-guard hardening + memory-smoke supersession stale-test correction)

**Version:** v1.12.0 (MINOR over published v1.11.0). **Class:** MIXED.
**WD:** `/Users/lukeivers/loam` (canonical single-writer this cycle).
**Status target:** SEALED-LOCAL + HARD-smoke-GREEN + `loam release v1.12.0 --dry-run` all-gates-GREEN, then STOP. **The public tag + push + GitHub Release is the owner's command to run — NOT pushed by this cycle** (`feedback_no_public_action_during_build`).
**Authority:** `docs/release-process.md` (runbook) + `docs/release-versioning-policy.md` (SemVer commitment) + this doc's §4/§13.

---

## 1. Objective

**v1.12.0 makes loam's episodic memory resume private to the exact channel-session that produced it — so a resume never bleeds another session's handoff — while hardening the release machinery that ships loam itself: the release CLI now resolves a tag target by ancestor-dominance and refuses an ambiguous cut, the cross-component shared-doc guard floor is complete and rot-proof, brittle exact-value guards read as intent assertions, and the memory-smoke supersession leg asserts the sealed hard-exclude contract it had drifted from.**

The objective sentence DESCRIBES the whole cut; it does not gate a split. Per the deterministic-cut rule (§3), a release cut is all unreleased seals at release time minus only explicitly owner-held items; "how many versions / which grouping" is never a decision to surface.

**Class — MIXED (per `docs/release-versioning-policy.md` §quality-gate).**

- **END-USER portion (named user-visible delta):** the per-session episodic resume (AC.PSR.1-8) changes what the user experiences of loam's memory across channel-sessions. Episodic resume is now scoped by `CLAUDE_PERSONA` / channel-session key so a session resumes ITS OWN last-state, never another simultaneous session's handoff. This is protection-floor advancement against the Lens-0 "no real memory / broken surrounding context" betrayal: with multiple simultaneous bot-sessions (Telegram DM + several Discord channels) a shared resume was a real cross-session context leak. It is user-experienced, not merely internal coherence.
- **META-FRAMEWORK portion (rationale + why-now):** four foundational cycles harden the machinery that builds and ships loam — (1) the release CLI's tag-target dominance resolver + deterministic-cut gate + preflight verb (AC.DOM/CUT/PRE); (2) the shared-doc guard-floor completeness + rot-proof meta-check (AC.SDG/SDC); (3) brittle exact-value guards converted to intent assertions (AC.BVG); (4) the FBM Tier-1 smoke supersession leg realigned to the sealed AC.SUP.1 hard-exclude contract (AC.SMKSUP.1, a stale-test correction, no runtime change). They are foundational because they govern release correctness, guard-floor coverage, and test-fidelity of loam's own build discipline. Why now: they ship unreleased and the deterministic cut takes all unreleased seals — and this cut DOGFOODS the release-CLI hardening it contains (its own dominance + deterministic-cut gates gate this publish).

---

## 2. What is unpublished (verified from git refs — Tier-0)

Five cycles sealed LINEARLY on `main` since v1.11.0 (published tag `01001ba`, seal `badd2d6f`). Unlike v1.11.0, NO reconciliation was needed — every cycle applied + sealed directly on `main` in dependency-free linear order; each seal is HEAD-reachable and each fence window (`BASELINE..SEAL_COMMIT`) contains only that amendment's own delta. This is the release-integration layer over already-sealed content, NOT a set of new amendments.

| Cycle | Component fence(s) | Feature ACs (sealed) | Seal |
|---|---|---|---|
| 1 — release-CLI tag-target/cut/preflight hardening | `loam-cli` (existing) | `AC.DOM.*` / `AC.CUT.*` / `AC.PRE.*` | `c074dc18` |
| 2 — shared-doc guard-floor coverage | `dev-sdlc` (existing) | `AC.SDG.1-2`, `AC.SDC.1-4` | `a8a34b47` |
| 3 — brittle exact-value guards → intent conversion | `dev-sdlc` + `hands-off-lifecycle` (existing) | `AC.BVG.1-2`, `BVG.S` | `30a3aaef` |
| 4 — per-session episodic resume | `primary-persona` (existing) | `AC.PSR.1-8` | `0fa74f79` |
| 5 — FBM Tier-1 smoke supersession hard-exclude | `dev-sdlc` (existing) | `AC.SMKSUP.1` | `69a345ba` |

Already on `main` since v1.11.0 and riding automatically: the v1.11.0 post-publish SHIPPED-PUBLIC backfill + roadmap seal-anchor fix (docs bookkeeping).

**HELD OUT — owner gate, NOT in this cut:** none. There is no owner-held subtraction this cut; every unreleased seal ships.

The feature ACs above are sealed + verified in each cycle's own sub-plan §status/§14 register; they are DISTINCT from this doc's `AC.REL.*` gate ladder (§4/§13).

---

## 3. Version decision — v1.12.0, single MINOR release (SemVer derivation)

```
current_published (highest tag on ORIGIN) = v1.11.0
  [git ls-remote --tags origin -> refs/tags/v1.11.0 at 01001ba]
HEAD local highest tag                     = v1.11.0   (== origin; no local-but-unpushed tag; recipe unambiguous)
breaking markers in v1.11.0..HEAD          = NONE
  [git log --format=%s v1.11.0..HEAD | grep -iE 'breaking|!:' -> empty]
new backwards-compatible capability present = YES
  [feat commits present: c290d211 feat(primary-persona AC.PSR.*),
   0f61d193 feat(loam-cli AC.DOM/CUT/PRE), c325e358 feat(dev-sdlc AC.SDG/SDC)]
=> class = MINOR (not MAJOR: zero breaking; not PATCH: new capability)
=> bump_minor(v1.11.0) = v1.12.0, ONE release.
```

Tier-0 corroboration: `loam release preflight v1.12.0` reports `computed cut: class=MINOR expected=v1.12.0 (published=v1.11.0, 134 unreleased commit(s); breaking-markers=no)`. If any of the above had contradicted (a breaking change surfaced, or class resolved ≠ MINOR), that is a HALT-and-surface trigger, not a silent re-number. It did not; the determination holds and is fixed — not re-opened. Per the deterministic-cut rule folded into policy at v1.11.0:

> A release cut = all unreleased seals at release time (main + merging branches) minus only explicitly owner-held items; SemVer class from content (breaking→MAJOR, else any new backwards-compatible capability→MINOR, else PATCH); number = bump(current_published_on_origin, class); ALWAYS one version per cut; the objective sentence describes the cut and never drives a split; "how many versions / which grouping" is never a decision to surface.

---

## 4. Build + release steps

1. **Lockstep version bump.** `docs/ACTIVE_MINOR` 1.11.0 → 1.12.0; the 31 in-scope `pyproject.toml` version fields + the `loam_cli __version__` literal (`loam --version`) fold to 1.12.0; `test_AC_PCVR_pyproject_version_lockstep` GREEN. The bump is a PLAIN commit landing AFTER all five cycle seals, OUTSIDE every fence window (the pyproject version field is not part of any `BASELINE..SEAL_COMMIT` guarded diff — each touched component's seal-test stays GREEN post-bump, verified Tier-0). No new out-of-graph component this cut; the two excluded 0.0.0 measurement harnesses stay excluded.
2. **State-migration doc.** `docs/state-migrations/v1-12-0-*.migration.yaml` — verify whether no-op; declare explicitly.
3. **HARD smoke (per-minor gate).** `docs/experiments/v1-12-0-hard-smoke.md` — cold-clone/cold-install of the release content tip + a REAL spawn-isolated `claude -p` exercise + an outcome-altitude fixture at the production entry-point + touched-component regression + the F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-alongs + the gate-7 `which loam` / `loam --help` evidence; literal `GREEN` verdict token.
4. **Backfill state.** `docs/STATE.md` SHIPPED-LOCAL change-log entry + `docs/release-roadmap.md` §3 SHIPPED-LOCAL entry + the §2 seal-row naming ALL FIVE cycle seals (the dominance resolver picks the single dominating seal `69a345ba` reachable from HEAD).
5. **Dogfood the new gates + dry-run.** `loam release v1.12.0 --dry-run`; confirm ALL 12 gates GREEN, including this cut's own `check_seal_dominance` (resolves `69a345ba` as the dominator of the 5-seal row) + `check_deterministic_cut` (recomputes MINOR → v1.12.0). STOP before push.

## 5. Pre-publish gates (enforced by `loam release`)

The 12 gates `run_all` runs per `gates.py`: hard-smoke, acs-verified, state-shipped, clean-tree, branch-main, seal-reachable, migration-declared, substrate-audit, boundary-respected, **seal-dominance**, **deterministic-cut**. `--dry-run` runs the full set without acting. Publish (tag/push/`gh release`) is the dispatcher's owner-authorized action, never this cycle's.

---

## §4 — Acceptance criteria

These `AC.REL.*` criteria are the release-integration gate ladder; the `acs-verified` gate reads their §status verdicts from §13. They are DISTINCT from the per-cycle feature ACs (`AC.DOM/CUT/PRE`, `AC.SDG/SDC`, `AC.BVG`, `AC.PSR`, `AC.SMKSUP`), which are sealed + verified in each cycle's own sub-plan §status/§14 register.

### AC.REL.1 — Plan-doc authored
This doc exists at a version-slug-resolvable path (`docs/plans/release-integration-v1-12-0.md`, resolved by the release-side fallback in `gates.py`) with §1 objective + §2 inventory + §3 SemVer derivation + §4 ACs + §13 §status, so the `acs-verified` + `hard-smoke` gates resolve it with NO `--plan-doc` flag.

### AC.REL.2 — Five unreleased cycles integrated on main
The five sealed cycles (`AC.DOM/CUT/PRE`, `AC.SDG/SDC`, `AC.BVG`, `AC.PSR`, `AC.SMKSUP`) are on `main` in linear order; each seal commit is reachable from HEAD; each component seal-test (`test_no_sealed_amendments.py` / seal-diff-window suite) passes with a fence window (`BASELINE..SEAL_COMMIT`) containing only that amendment's own delta. No reconciliation was needed (linear, dependency-free).

### AC.REL.3 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.11.0 → 1.12.0; the 31 in-scope `pyproject.toml` version fields bump to 1.12.0; the meta `loam --version` literal folds in (`loam --version` → `1.12.0`); `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` stays GREEN. The two excluded 0.0.0 measurement harnesses stay at 0.0.0.

### AC.REL.4 — HARD smoke GREEN (the per-minor gate)
`docs/experiments/v1-12-0-hard-smoke.md` authored; REAL cold-clone of the release content tip + REAL editable install with no Anthropic API key + spawn-isolated `claude -p` (scrubbed `ANTHROPIC_API_KEY` / `TELEGRAM_BOT_TOKEN` / `DISCORD_BOT_TOKEN`, `--strict-mcp-config`) + the outcome-altitude PSR fixture (AC.REL.S) + touched-component regression ride-alongs + the F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN checks; the writeup carries the `GREEN` aggregate-verdict token + the gate-7 `which loam` / `loam --help` evidence.

### AC.REL.5 — Touched component suites GREEN (cold install)
The touched-component suites — `loam-cli` + `dev-sdlc` + `primary-persona` + `hands-off-lifecycle` — pass in the cold-installed release tree, evidenced in the HARD smoke writeup.

### AC.REL.6 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` carries a `**v1.12.0 MIXED MINOR SHIPPED LOCAL**` change-log entry naming the objective, the class, the five cycles + their seal SHAs, the lockstep bump, the migration verdict, and the HARD smoke path.

### AC.REL.7 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a v1.12.0 row whose right column records all five cycle seal SHAs (the dominance resolver picks the single dominating seal `69a345ba`, reachable from HEAD, read by gate `seal-reachable`); §3 Active-version carries a SHIPPED-LOCAL entry.

### AC.REL.8 — Migration declared
`docs/state-migrations/v1-12-0-*.migration.yaml` exists and explicitly declares the migration verdict (expected `no-op`; declared, not assumed).

### AC.REL.9 — New-gate dogfood (dominance + deterministic-cut GREEN on this cut's own machinery)
`loam release v1.12.0 --dry-run` runs this cut's OWN newly-shipped gates against this cut: `check_seal_dominance` resolves `69a345ba` as the unique dominator of the five-seal §2 row (exercising the multi-seal `dominates` path, not the vacuous single-seal path), and `check_deterministic_cut` recomputes the cut as MINOR → v1.12.0 matching the target. Both GREEN.

### AC.REL.S — Outcome-altitude (production entry-points, no pre-set state)
Two production entry-points are exercised with no pre-set release state: (1) a spawn-isolated `claude -p` run against the cold-installed tree returns its exact token (`SMOKE_OK_V1120`), evidenced in the HARD smoke writeup, and the cold-tree `test_AC_PSR_6_OA_worker_stamps_session_key_from_record` outcome-altitude fixture passes at the production entry-point; and (2) `loam release v1.12.0 --dry-run` runs the real 12-gate release CLI and reports every structural gate GREEN.

---

## §13 — §status (gate verdict matrix)

The `loam release v1.12.0 --dry-run` `acs-verified` gate reads these verdicts. A RED here blocks the dry-run's `acs-verified` gate.

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL.1 | GREEN | this doc at `docs/plans/release-integration-v1-12-0.md` (resolved by the release-side fallback in `gates.py`) |
| AC.REL.2 | GREEN | five seals HEAD-reachable (`c074dc18` / `a8a34b47` / `30a3aaef` / `0fa74f79` / `69a345ba`); each seal-test passes with window = own delta; linear on main, no reconciliation |
| AC.REL.3 | GREEN | lockstep bump `7faa5514` (ACTIVE_MINOR 1.12.0 + 31 pyprojects + `loam --version`→1.12.0); `test_AC_PCVR_pyproject_version_lockstep` 5 passed |
| AC.REL.4 | GREEN | `docs/experiments/v1-12-0-hard-smoke.md` carries the `GREEN` token + gate-7 evidence |
| AC.REL.5 | GREEN | cold-tree suites: loam-cli 221, dev-sdlc 399/7-skip, primary-persona 1432/1-skip, hands-off-lifecycle 743/5-skip (HARD smoke §3) |
| AC.REL.6 | GREEN | `docs/STATE.md` `**v1.12.0 MIXED MINOR SHIPPED LOCAL**` change-log entry |
| AC.REL.7 | GREEN | `docs/release-roadmap.md` §2 five-seal row (dominator `69a345ba` reachable from HEAD) + §3 SHIPPED-LOCAL entry |
| AC.REL.8 | GREEN | `docs/state-migrations/v1-12-0-per-session-resume-and-release-machinery-hardening.migration.yaml` (`operation: no-op`) |
| AC.REL.9 | GREEN | `loam release v1.12.0 --dry-run`: `seal-dominance` resolves `69a345ba` dominating the 5-seal row (`dominates`); `deterministic-cut` = MINOR → v1.12.0 |
| AC.REL.S | GREEN | HARD smoke §4 (real spawn-isolated `claude -p` → `SMOKE_OK_V1120`, rc 0) + §5 (cold-tree `test_AC_PSR_6_OA` production stamp) + `loam release v1.12.0 --dry-run` all 12 gates GREEN |

## §14 — cycle SHA register (backfilled at cycle close)

Release plan-doc + smoke + migration + STATE/roadmap: this release-prep commit. Lockstep bump: `7faa5514`. Cycles (linear order on main):

- cycle 1 — release-CLI tag-target/cut/preflight hardening (`AC.DOM/CUT/PRE`): source `0f61d193` · plan+manifest `160700e0` · apply `9e51a18e` · seal `c074dc18`.
- cycle 2 — shared-doc guard-floor coverage (`AC.SDG.1-2`, `AC.SDC.1-4`): source `c325e358` · apply `d5e7e63f` · corrective registry+manifest `425a69c5` · seal `a8a34b47`.
- cycle 3 — brittle exact-value guards → intent (`AC.BVG.1-2`, `BVG.S`): plan+manifest `dbce3097` · source `f610448d` + `0bcbe5b5` · apply `f4b3cf48` · seal `30a3aaef`.
- cycle 4 — per-session episodic resume (`AC.PSR.1-8`): source `c290d211` · apply `c6de4247` · seal `0fa74f79`.
- cycle 5 — FBM Tier-1 smoke supersession hard-exclude (`AC.SMKSUP.1`): plan+manifest `a1adbef7` · source `ae461621` · apply `53c73f16` · seal `69a345ba`.
- **Release tag target — dominating seal `69a345ba`:** the unique seal in the §2 five-seal row that has every other row-seal as an ancestor (Tier-0: `c074dc18` / `a8a34b47` / `30a3aaef` / `0fa74f79` all ancestors of `69a345ba`); reachable from HEAD. Per the v1.10.0 pattern, the lockstep bump lands on `main` AFTER the tag target — the tag marks the sealed content tip; `origin/main` HEAD carries the bump.
