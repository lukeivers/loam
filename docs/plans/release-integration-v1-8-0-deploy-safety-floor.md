# Release Integration — v1.8.0 (deploy-safety FLOOR)

**Status:** RATIFIED — owner cleared prep + publish 2026-06-28 (Discord
message 1520815197982560318: "you do literally everything you can, and at
the end, give me a list of commands"). Public push remains the owner's
command to run.
**Author:** primary persona (pos3 session), 2026-06-28.
**Type:** MINOR over v1.7.0. Single release.
**Ground-truth basis:** git refs (tags + `gh release list` + `origin/main`),
not STATE/roadmap prose (per `feedback_published_state_only_from_git_refs`).

---

## 1. Objective

Publish the work accumulated on local `main` since the last public
release (v1.7.0) as a single MINOR, v1.8.0, landing on the GitHub
releases page with auto-generated notes — via the framework's own
`loam release` flow.

## 2. What is unpublished (verified from git)

- **Last public release:** v1.7.0 (GitHub release, 2026-06-26; tag `v1.7.0`).
- **`origin/main`** = `1fcad587` — "v1.7.0 post-publish backfill — SHIPPED
  PUBLIC". Already pushed + public; carries no unreleased *feature* work.
- **Local `main` HEAD** = `4a0ebed7`, **15 commits ahead of `origin/main`,
  0 behind** (clean fast-forward; no divergence to reconcile).

Those 15 commits are **one feature area — the deploy-safety FLOOR** —
built in three sealed sub-cycles:

| Sub-cycle | Feature commit | What it adds |
|-----------|----------------|--------------|
| A — gate primitives | `c0eae5ae` | Framework-native deploy-safety FLOOR gate primitives |
| B — fail-policy | `14d5f90d` | Per-gate fail-policy primitive (AC.DSF.5) on `safety-layer` |
| C — secure-build baseline | `bd11429c` | Secure-build FLOOR: secrets-at-commit scan + dependency audit + artifact-cleanliness (AC.SBB.1–4 + AC.COV.1) |

The remaining 12 commits are the amend/seal/SHA-register/STATE-backfill
bookkeeping for those three, ending in the seal-backfill `4a0ebed7`.

## 3. Version decision — v1.8.0, single release

- **MINOR (1.7.0 → 1.8.0):** the floor is a backward-compatible feature
  addition (new gates/primitives; no breaking change to existing
  surfaces). Semver MINOR. Consistent with v1.7.0 (also a feature MINOR).
- **Single release, not three:** sub-cycles A/B/C are facets of one floor,
  built and sealed together, with no independent user value shipped apart.
  Splitting into three patches would add release overhead and three sets of
  notes for what reads as one capability. **Rejected:** A/B/C as separate
  patch releases.
- **Lockstep version bump:** 1.7.0 → 1.8.0 across all components carrying a
  `pyproject.toml` version (the established release discipline; v1.7.0 used
  the same lockstep bump).

## 4. Release steps

**Prep (persona-side, up to but excluding the public push):**

1. Author this plan + record owner ratification (this doc).
2. Lockstep version bump 1.7.0 → 1.8.0 + release bookkeeping commit.
3. Update `STATE.md` + `release-roadmap.md` for the v1.8.0 shipped line.
4. Run the **HARD smoke** (cold install + real `claude -p` + fixture +
   regression ride-alongs) per `feedback_hard_smoke_per_minor_before_publish`;
   record the writeup GREEN.
5. `loam release v1.8.0 --dry-run` from the canonical repo — confirm every
   pre-publish gate GREEN, record the gate states.

**Publish (owner-side — the only step the persona cannot run):**

6. `loam release v1.8.0 --release` — creates the annotated tag at the seal
   commit, pushes `main` + tag to origin, creates the GitHub Release with
   auto-generated notes, surfaces the post-ship review.

## 5. Pre-publish gates (enforced by `loam release`)

HARD smoke GREEN · ACs verified · STATE.md updated · clean working tree ·
branch == main · seal commit reachable from HEAD. The dry-run reports each;
publish refuses on any RED. This is the safety net that catches an
incompletely-sealed floor before anything goes public.

## 6. Impact on the `~/loam-eric-1/2/3` instances

The three instances are clean clones of `origin/main` at `1fcad587` —
i.e. **one release behind**; they lack the deploy-safety floor. They are
download-only (not installed, not initialized) and carry **no local
changes**, so after publish they update with a clean fast-forward:

```
git -C ~/loam-eric-1 pull && git -C ~/loam-eric-2 pull && git -C ~/loam-eric-3 pull
```

**No recreate required.** (Re-clone is equivalent but unnecessary.) Since
they were never installed, there is no venv/workspace to rebuild — the pull
is the whole update.

## 7. Owner ratification

- [x] Owner ratified v1.8.0 single MINOR for prep + publish — 2026-06-28,
      Discord 1520815197982560318.

Recorded here before the prep build is dispatched, per
`feedback_record_owner_ratification_before_dispatch`.

---

## §4 — Acceptance criteria

The release-process AC family (`AC.REL.*`) — the same family v1.4.0 / v1.6.0 /
v1.7.0 used. These are the prep-completion criteria the `loam release
--dry-run` `acs-verified` gate reads from this doc's §13 §status. They are
DISTINCT from the deploy-safety FLOOR feature ACs (`AC.DSF.*` / `AC.SBB.*` /
`AC.COV.*`), which are sealed + verified in
`docs/plans/deploy-safety-floor-gate-primitives.md` §12/§13/§14.

### AC.REL.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
scope-descriptive slug (`release-integration-v1-8-0-deploy-safety-floor`),
reachable via `--plan-doc`.

### AC.REL.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.7.0 → 1.8.0; the 31 in-scope `pyproject.toml`
version fields bump 1.7.0 → 1.8.0; the per-component lockstep regression test
(`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`) stays
GREEN with the bump. The meta-package `--version` literal folds in (`loam
--version` → `1.8.0`). The two NEW components `deploy-safety-floor` (0.1.0) +
`secure-build-baseline` (0.1.0) are EXCLUDED from the in-scope set per D-LOCK +
policy (new components ride out-of-graph at 0.1.0); the sealed-component extends
`safety-layer` + `protection-matrix` ARE in-scope and ride the bump.

### AC.REL.3 — HARD smoke GREEN (the per-minor gate)
`docs/experiments/release-integration-v1-8-0-deploy-safety-floor-hard-smoke.md`
authored; REAL cold-clone of the release HEAD + REAL editable install with no
API key + spawn-isolated `claude -p` (subscription-only, scrubbed
`ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN`, `--strict-mcp-config`) + the
outcome-altitude floor deltas reproduced from the cold tree (AC.REL.S) + the
touched-component regression ride-alongs; the writeup carries the `GREEN`
aggregate-verdict token + the gate `which loam` / `loam --help` evidence
(`feedback_hard_smoke_per_minor_before_publish`).

### AC.REL.4 — Touched component suites GREEN (cold install)
From the cold tree, all pass: `framework/deploy-safety-floor/tests/` (AC.DSF.*
incl. the outcome-altitude `test_AC_DSF_7_*`), `framework/secure-build-baseline/tests/`
(AC.SBB.* incl. the outcome-altitude `test_AC_SBB_C_*`), `framework/safety-layer/tests/`
(AC.DSF.5 fail-policy + the existing fail-open regression suites),
`framework/protection-matrix/tests/` (AC.COV.1 catalogue rows), and
`plugins/dev-sdlc/tests/` (incl. the lockstep AC.PCVR at 1.8.0). Any failure is
Tier-0-verified pre-existing on the published v1.7.0 tip (not a v1.8.0
regression) + documented with the same-known-set discipline used at v1.7.0.

### AC.REL.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` change-log carries a `**v1.8.0 ... SHIPPED LOCAL**` entry naming
the deploy-safety-floor + secure-build-baseline components + the safety-layer /
protection-matrix extends + the release-window tip. (The `SHIPPED PUBLIC` flip
is the post-publish backfill, done by the release tool.)

### AC.REL.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.8.0 |` row whose final seal token
(`3225eeee` — the Sub-cycle C secure-build-baseline seal, the release-window
content tip) is reachable from HEAD; §3 Active-version updated.

### AC.REL.7 — migration declared
`docs/state-migrations/v1-8-0-deploy-safety-floor.migration.yaml` declares
`version: v1.8.0` + `operation: no-op` (the floor's gates READ config + scan
staged diffs at runtime; they persist no user `.loam/` state to migrate).

### AC.REL.S — Outcome-altitude (cold-install user-visible deltas)
The HARD smoke exercises the v1.8.0 user-visible deltas from a cold tree with no
pre-arranged state: (1) `loam --version` reports `loam 1.8.0`; (2) the
deploy-safety-floor PreToolUse hook entry-point, fed a fabricated destructive
command in an `is_production` / no-attestation context, returns a DENY naming
the target + sub-action in plain words — and still denies (fail-closed) when its
classifier is made to raise (AC.DSF.7); (3) the secure-build-baseline secret
guard blocks a staged credential at the commit boundary (AC.SBB.1) — all through
production entry points, no pre-arranged state. GREEN.

---

## §5 — Publish gates (what this release's HARD smoke must cover)

Single release (v1.8.0). The HARD smoke (AC.REL.3 /
`feedback_hard_smoke_per_minor_before_publish`) is the load-bearing pre-publish
gate. AFTER local seal and BEFORE any tag/push it must cover:

1. **Cold install** — real `git clone` of the release HEAD into a fresh tmp dir
   + real editable install from the install manifest alone (catch any
   new-component install-graph gap — confirm `deploy-safety-floor` +
   `secure-build-baseline` either install cleanly or are correctly excluded at
   0.1.0 out-of-graph).
2. **Real `claude -p`** — spawn-isolated (`--strict-mcp-config`, scrubbed
   `ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN`) per
   `feedback_spawned_claude_must_isolate_telegram_plugin`; subscription-only per
   `feedback_no_anthropic_api_key`. CRITICAL: an un-isolated `claude -p`
   SIGTERM-steals the one bot slot and drops the owner's live channel session.
3. **Real fixtures — the floor at outcome altitude:** (a) the deploy-safety
   PreToolUse hook denies a fabricated destructive command in a prod /
   no-attestation context AND stays fail-closed on a raising classifier
   (AC.DSF.7); (b) the secure-build secret guard blocks a staged credential at
   the commit boundary (AC.SBB.1) — both from the cold tree, no pre-arranged
   state.
4. **Regression ride-alongs** — the touched suites from AC.REL.4 swept from the
   cold tree; every failure Tier-0-classified pre-existing on the published
   v1.7.0 tip or fixed, never waved through.
5. **Gate evidence** — `which loam` resolves + `loam --help` exits 0 and lists
   every documented subcommand (operator-verified, recorded in the writeup).

All nine `loam release` gates run via `loam release v1.8.0 --plan-doc <this
doc> --dry-run` and report GREEN before the owner-authorized publish. The
publish itself is owner-gated (ASK-FIRST).

---

## §13 — §status (gate verdict matrix)

Owner ratified prep+publish 2026-06-28 (Discord 1520815197982560318). Prep +
HARD smoke executed 2026-06-28 DIRECTLY on `main` in the canonical tree
`/Users/lukeivers/loam` (no concurrent session owns it this cut, so no isolated
worktree was needed — branch-main resolves GREEN, unlike the v1.7.0 worktree
staging). All ACs GREEN. **PUBLISH remains the owner's command to run.**

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc docs/plans/release-integration-v1-8-0-deploy-safety-floor.md` |
| AC.REL.2 | GREEN | `docs/ACTIVE_MINOR` → 1.8.0; 31 in-scope pyprojects → 1.8.0 (grep sweep: ALL 31 == 1.8.0, none left at 1.7.0); lockstep test `test_AC_PCVR_pyproject_version_lockstep` → 5 passed at 1.8.0; meta `loam --version` literal → 1.8.0; new components `deploy-safety-floor`/`secure-build-baseline` correctly at 0.1.0 out-of-scope; off-version siblings (frame-kernel 1.5.0, loam-init/meta 1.1.0) untouched |
| AC.REL.3 | GREEN | HARD smoke `docs/experiments/release-integration-v1-8-0-deploy-safety-floor-hard-smoke.md` carries the `GREEN` aggregate-verdict token + the gate `loam --version`/`loam --help` evidence |
| AC.REL.4 | GREEN | from the cold tree: deploy-safety-floor + secure-build-baseline + safety-layer + protection-matrix + dev-sdlc (incl. lockstep AC.PCVR at 1.8.0) suites pass; any single failure Tier-0-classified pre-existing-environmental on the v1.7.0 tip, never a v1.8.0 regression — smoke §6 |
| AC.REL.5 | GREEN | `docs/STATE.md` carries the `**v1.8.0 MINOR SHIPPED LOCAL**` change-log entry naming deploy-safety-floor + secure-build-baseline + the safety-layer/protection-matrix extends + release-window tip `3225eeee` |
| AC.REL.6 | GREEN | `docs/release-roadmap.md` §2 `| v1.8.0 |` row carries final seal token `3225eeee` (Tier-0: ancestor of release HEAD); §3 Active-version updated |
| AC.REL.7 | GREEN | `docs/state-migrations/v1-8-0-deploy-safety-floor.migration.yaml` declares `version: v1.8.0` + `operation: no-op` |
| AC.REL.S | GREEN | cold-tree `loam --version` → `loam 1.8.0`; deploy-safety PreToolUse hook denies a fabricated prod destructive command + stays fail-closed on a raising classifier (AC.DSF.7); secure-build secret guard blocks a staged credential at the commit boundary (AC.SBB.1) — smoke §5 |
