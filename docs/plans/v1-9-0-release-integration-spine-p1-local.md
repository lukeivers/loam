# Release Integration — v1.9.0 (dev→build→deploy spine P1 LOCAL tier + refinements)

**Status:** PREP — persona-side prep up to but excluding the public
tag/push. Public push remains the owner's command to run.
**Author:** loam-builder (pos3 session), 2026-07-01.
**Type:** MINOR over v1.8.0. Single release.
**Class:** MIXED — an END-USER outcome (the first LOCAL deploy tier a
non-technical owner can build+verify against; a memory read-correctness
delta) plus a foundational portion (model-lineup capability-refresh
tracking, a work-visibility hook-output fix, a deploy-safety floor
fail-policy de-dup). Both halves named below (§1).
**Ground-truth basis:** git refs (tags + `origin/main` + seal SHAs), not
STATE/roadmap prose (per `feedback_published_state_only_from_git_refs`).

---

## 1. Objective

Publish the work accumulated on local `main` since the last public
release (v1.8.0) as a single MINOR, v1.9.0, landing on the GitHub
releases page with auto-generated notes — via the framework's own
`loam release` flow.

**Objective sentence (the version's identity):** *"loam ships the first
deploy tier on the sealed deploy-safety floor — a non-technical owner can
build and verify their project against a LOCAL environment, with the
safety floor idle and the build's proof produced in the shared
build→deploy proof shape; rolled up with a model-lineup
capability-refresh, a memory-volatility read disposition that stops a
stale operational-status claim being recalled as current (its durable
decision preserved), and a work-visibility hook-output fix."*

**MIXED class — the two halves named (policy §"END-USER vs
META-FRAMEWORK" gate):**

- **END-USER portion (user-visible delta):** (1) the LOCAL deploy tier —
  a non-technical owner can now build + verify their project against a
  LOCAL environment on the sealed floor, a capability absent at v1.8.0;
  (2) memory recall-correctness — a recent, stale operational-status
  claim is no longer surfaced as current, while the durable decision
  behind it stays queryable.
- **Foundational portion (enables future end-user work):** the
  model-lineup capability-refresh tracking (keeps loam's own model
  awareness current for downstream selection), the work-visibility
  hook-output fix (unblocks Claude Code hook acceptance), and the
  deploy-safety floor fail-policy de-dup (strictly behaviour-preserving
  cleanup on the sealed floor). None ship a standalone user outcome; they
  service the spine + the sealed floor.

## 2. What is unpublished (verified from git)

- **Last public release:** v1.8.0 (tag `v1.8.0`, annotated `b6df7e4`;
  content tip / seal `3225eeee`).
- **`origin/main`** = `b03ec0e2` = local `main` HEAD (already pushed +
  public on the branch; carries no *tag/release* yet — the v1.9.0 tag +
  GitHub Release is what this prep sets up).
- **`v1.8.0` tag → HEAD:** a clean linear advance (`git rev-list
  --left-right --count origin/main...HEAD` = `0 0`; zero divergence).
  Zero BREAKING commits (`git log --format=%s v1.8.0..HEAD | grep -iE
  'breaking|!:'` → empty). MINOR-class.

The v1.9.0 window is **five sealed cycles** on the sealed floor:

| Cycle | Feature/fix commit | Apply | Seal | What it adds |
|-------|--------------------|-------|------|--------------|
| A — dev→build→deploy spine P1 LOCAL | `434880a5` | `e8425bfe` | `7439fad6` | NEW opt-in component `framework/local-deploy-tier/` (0.1.0, out-of-graph): a non-technical owner builds + verifies against a LOCAL environment on the sealed floor; acceptance record in the shared P0 proof shape; command-set with no irreversible verbs; parity-gap surface; secrets from keychain, never committed (AC.LOCAL.1-4 + OA) |
| B — memory-volatility read disposition | `779d306f` | `f9fb305c` | `fe7e2de2` | EXTENDS sealed `primary-persona`: `classify_volatility` (write-side, deterministic) + read-side hard-exclude/soft-annotate disposition on the existing bitemporal interval machinery — stale operational-status claims filtered from the current view, durable decision preserved (AC.VOL.1-5) |
| C — work-visibility hook-event-name fix | `d88c6c59` | `a4f62384` | `3f54722b` | BUG FIX on sealed `primary-persona`: `hooks_work_visibility.run()` now emits the required `hookEventName` field on all return paths (Claude Code was rejecting the hook output) (AC.WVS-HOOK-EN.1-5) |
| D — deploy-safety floor fail-policy adoption | `c7ce8767` | `e8c5d3b4` | `ff9a61ce` | EXTENDS sealed `deploy-safety-floor`: the floor gate ADOPTS the shared fail-policy primitive (de-dup; strictly behaviour-preserving) (AC.DSF.8) |
| E — capability-refresh model-lineup | `35610096` | `2a7f62c5` | `5e96f08f` | EXTENDS `capability-refresh`: a model-lineup tracking extension over the capability corpus (keeps loam's own model awareness current) (AC.CLP-MDL.1-4) |

The remaining commits in the window are the plan/manifest + amend/seal +
STATE/roadmap/§14-register bookkeeping for those five, plus the P0
shared-contract spec doc (`a7c9f1b2`) and the v1.8.0 post-publish
backfill tail (v1.8.0's own bookkeeping, after the v1.8.0 content tip).

## 3. Version decision — v1.9.0, single release

- **MINOR (1.8.0 → 1.9.0):** every cycle is a backward-compatible
  addition — a NEW opt-in out-of-graph component (local-deploy-tier),
  additive extends of sealed components (memory-volatility frontmatter is
  additive + read-back-safe; the hook fix restores a required field; the
  fail-policy adoption is behaviour-preserving; model-lineup extends the
  capability corpus). No breaking change to any existing public surface.
  Semver MINOR. `next_MINOR(v1.8.0) = v1.9.0` per
  `docs/release-versioning-policy.md` (derive at release from
  `current_published` + `candidate_class`).
- **Single release, not five:** the five cycles roll up under one
  objective (the spine's first LOCAL tier headlines; the rest refine the
  sealed floor + memory + capability awareness). Splitting into five
  patches would add release overhead for what ships as one coherent
  advance.
- **Lockstep version bump:** 1.8.0 → 1.9.0 across the 31 in-scope
  `pyproject.toml` version fields + `docs/ACTIVE_MINOR` + the meta
  `loam --version` literal (the established release discipline; v1.7.0 /
  v1.8.0 used the same lockstep bump). The NEW `local-deploy-tier`
  (0.1.0) rides out-of-graph; the sealed-component extends
  (`primary-persona`, `deploy-safety-floor`, `capability-refresh`) are
  in-scope and ride the bump.

## 4. Release steps

**Prep (persona-side, up to but excluding the public push):**

1. Author this plan (this doc) — plan-before-code.
2. Lockstep version bump 1.8.0 → 1.9.0 + release bookkeeping commit.
3. Update `STATE.md` + `release-roadmap.md` for the v1.9.0 shipped line.
4. Run the **HARD smoke** (cold install + real spawn-isolated
   `claude -p` + outcome-altitude fixtures + regression ride-alongs) per
   `feedback_hard_smoke_per_minor_before_publish`; record the writeup
   GREEN.
5. `loam release v1.9.0 --dry-run` from the canonical repo — confirm
   every pre-publish gate GREEN; record the gate states here (§13).

**Publish (owner-side — the only step the persona cannot run):**

6. `loam release v1.9.0 --release` — creates the annotated tag at the
   seal commit, pushes `main` + tag to origin, creates the GitHub
   Release with auto-generated notes, surfaces the post-ship review.

## 5. Pre-publish gates (enforced by `loam release`)

The nine structural gates: HARD smoke GREEN · ACs verified · STATE.md
SHIPPED · clean working tree · branch == main · seal reachable from
HEAD · migration declared · substrate-audit clean · boundary respected.
The dry-run reports each; publish refuses on any RED. This is the safety
net that catches an incompletely-sealed release before anything goes
public.

---

## §4 — Acceptance criteria

The release-process AC family (`AC.REL.*`) — the same family v1.7.0 /
v1.8.0 used. These are the prep-completion criteria the `loam release
--dry-run` `acs-verified` gate reads from this doc's §13 §status. They
are DISTINCT from the per-cycle feature ACs (`AC.LOCAL.*` / `AC.VOL.*` /
`AC.WVS-HOOK-EN.*` / `AC.DSF.8` / `AC.CLP-MDL.*`), which are sealed +
verified in each cycle's own sub-plan §status/§14 register.

### AC.REL.1 — Plan-doc authored
This doc exists with §1 objective + §2 inventory + §4 ACs + §13 §status
gate matrix at a version-slug-glob-resolvable slug
(`v1-9-0-release-integration-spine-p1-local`), so the `acs-verified` +
`hard-smoke` gates resolve it with NO `--plan-doc` flag.

### AC.REL.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.8.0 → 1.9.0; the 31 in-scope
`pyproject.toml` version fields bump 1.8.0 → 1.9.0; the per-component
lockstep regression test
(`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`)
stays GREEN with the bump; the meta `loam --version` literal
(`loam_cli/__init__.py __version__`) folds in (`loam --version` →
`1.9.0`). The NEW `local-deploy-tier` (0.1.0) is EXCLUDED from the
in-scope set (new component out-of-graph at 0.1.0); the sealed-component
extends ARE in-scope and ride the bump.

### AC.REL.3 — HARD smoke GREEN (the per-minor gate)
`docs/experiments/v1-9-0-hard-smoke.md` authored; REAL cold-clone of the
release HEAD + REAL editable install with no API key + spawn-isolated
`claude -p` (subscription-only, scrubbed `ANTHROPIC_API_KEY` /
`TELEGRAM_BOT_TOKEN` / `DISCORD_BOT_TOKEN`, `--strict-mcp-config`) + the
outcome-altitude deltas reproduced from the cold tree (AC.REL.S) + the
touched-component regression ride-alongs; the writeup carries the
`GREEN` aggregate-verdict token + the gate `loam --version` /
`loam --help` evidence (`feedback_hard_smoke_per_minor_before_publish`).

### AC.REL.4 — Touched component suites GREEN (cold install)
From the cold tree, all pass: `framework/local-deploy-tier/tests/`
(AC.LOCAL.* incl. the outcome-altitude `test_AC_LOCAL_C_*`),
`framework/primary-persona/tests/` (AC.VOL.* + AC.WVS-HOOK-EN.*),
`framework/deploy-safety-floor/tests/` (AC.DSF.8 fail-policy adoption),
`framework/capability-refresh/tests/` (AC.CLP-MDL.*), and
`plugins/dev-sdlc/tests/` (incl. the lockstep AC.PCVR at 1.9.0). Any
failure is Tier-0-verified pre-existing on the published v1.8.0 tip (not
a v1.9.0 regression) + documented with the same-known-set discipline.

### AC.REL.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` change-log carries a `**v1.9.0 ... SHIPPED LOCAL**`
entry naming the local-deploy-tier + memory-volatility +
work-visibility-hook-fix + fail-policy-adoption + capability-refresh
model-lineup slices + the release-window tip. (The `SHIPPED PUBLIC` flip
is the post-publish backfill, done by the release tool.)

### AC.REL.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.9.0 |` row whose final seal
token (`5e96f08f` — the capability-refresh model-lineup seal, the
release-window content tip) is reachable from HEAD; §3 Active-version
updated.

### AC.REL.7 — migration declared
`docs/state-migrations/v1-9-0-spine-p1-local.migration.yaml` declares
`version: v1.9.0` + `operation: no-op` — the memory-volatility
frontmatter is additive + backward-compatible at read-time (absent-field
reads default to durable, fail-safe); the LOCAL deploy tier is a NEW
opt-in component whose state is created fresh (nothing prior to migrate);
capability-corpus is a repo artifact, not user `.loam/` state. A user
upgrading v1.8.0 → v1.9.0 needs no state transformation.

### AC.REL.S — Outcome-altitude (cold-install user-visible deltas)
The HARD smoke exercises the v1.9.0 user-visible deltas from a cold tree
with NO pre-arranged state, through production entry points: (1) `loam
--version` reports `loam 1.9.0`; (2) the LOCAL deploy tier produces an
acceptance record in the shared proof shape with a command-set carrying
no irreversible verb (AC.LOCAL.C); (3) a HARD-volatile operational-status
claim written via the real `write_episode` is FILTERED from the current
recall view while its history stays queryable (AC.VOL.5) — all through
production entry points, no pre-arranged state. GREEN.

---

## §13 — §status (gate verdict matrix)

Prep + HARD smoke executed 2026-07-01 DIRECTLY on `main` in the canonical
tree `/Users/lukeivers/loam` (no concurrent session owns it this cut, so
no isolated worktree was needed — `branch-main` resolves GREEN). All ACs
GREEN. **PUBLISH remains the owner's command to run.**

Backfilled after the HARD smoke (`docs/experiments/v1-9-0-hard-smoke.md`,
GREEN) + the `loam release v1.9.0 --dry-run` (9 GREEN / 0 RED). All ACs GREEN.

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL.1 | GREEN | this doc exists with §1 + §4 + §13 at slug `v1-9-0-release-integration-spine-p1-local`; resolved by the `v1-9-0-*` version-slug glob with NO `--plan-doc` flag (acs-verified + hard-smoke gates both GREEN) |
| AC.REL.2 | GREEN | `docs/ACTIVE_MINOR` → 1.9.0; 31 in-scope pyprojects → 1.9.0 (Tier-0 sweep: ALL 31 == 1.9.0, none left at 1.8.0, 0 stray non-in-scope); meta `loam --version` literal → 1.9.0; lockstep test `test_AC_PCVR_pyproject_version_lockstep` → 5 passed at 1.9.0 (canonical + cold clone); new `local-deploy-tier` correctly at 0.1.0 out-of-scope |
| AC.REL.3 | GREEN | HARD smoke `docs/experiments/v1-9-0-hard-smoke.md` carries the `GREEN` aggregate-verdict token + the gate `loam --version` (`loam 1.9.0`) / `loam --help` (exit 0) evidence + the spawn-isolated `claude -p` SMOKE OK |
| AC.REL.4 | GREEN | from the cold tree: local-deploy-tier 28 passed, deploy-safety-floor 28 passed (incl. AC.DSF.8), capability-refresh 32 passed (incl. AC.CLP-MDL), primary-persona VOL+WVS-HOOK-EN families GREEN + full sweep 1287 passed/1 skipped/1 failed, dev-sdlc 396/7skip (incl. lockstep AC.PCVR at 1.9.0). The single `test_AC_MSC_3` failure is Tier-0-classified pre-existing-environmental (cold-clone dev-mode sensitivity; PASSES in the canonical tree; untouched by v1.9.0) — smoke §10 |
| AC.REL.5 | GREEN | `docs/STATE.md` carries the `**v1.9.0 MINOR SHIPPED LOCAL**` change-log entry naming local-deploy-tier + memory-volatility + work-visibility-hook-fix + fail-policy-adoption + capability-refresh model-lineup + release-window tip `5e96f08f` |
| AC.REL.6 | GREEN | `docs/release-roadmap.md` §2 `| v1.9.0 |` row carries final seal token `5e96f08f` (Tier-0: ancestor of release HEAD); §3 Active-version updated |
| AC.REL.7 | GREEN | `docs/state-migrations/v1-9-0-spine-p1-local.migration.yaml` declares `version: v1.9.0` + `operation: no-op` (additive read-back-safe memory frontmatter; new opt-in component state created fresh; capability-corpus is a repo artifact) |
| AC.REL.S | GREEN | cold-tree `loam --version` → `loam 1.9.0`; LOCAL deploy tier acceptance-record OA (AC.LOCAL.C) within 28 passed; HARD-volatile status claim FILTERED from current recall while history preserved (AC.VOL.5 OA) — smoke §5 |
