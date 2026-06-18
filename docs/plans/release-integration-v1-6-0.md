# Release integration — v1.6.0

**Status:** PREP COMPLETE → gates GREEN (owner-authorized publish — Luke,
`<CHANNEL + MSG-ID + DATE — DISPATCHER FILLS BEFORE PUBLISH>`)
**Working tree:** `/Users/lukeivers/loam` (branch `main`; the 148-commit
post-v1.5.0 backlog is already a clean linear fast-forward stack on the
published v1.5.0 baseline — no isolated release worktree needed)
**Version:** v1.6.0 — MINOR increment derived at release time from the
published v1.5.0 (`next_MINOR(v1.5.0) = v1.6.0` per
`docs/release-versioning-policy.md`). The window bundles 24 feats + 18 fixes
+ bookkeeping across four work-slices: (a) the claude-leverage program
(Slices 1–4: NEW `capability-refresh` + NEW `knowledge-pack` components,
primitive-check guards, /goal+/loop adoption); (b)
principle-foundation-structural-enforcement (Slices A–D); (c) the
GUARD-SWEEP FLOOR in `loam amend seal`; (d) ProgramBench full retirement.
The new-component + new-structural-enforcement surfaces lift the combined
window to MINOR, not PATCH.
**Objective:** loam continuously refreshes its own capability knowledge,
pushes a knowledge corpus to the marketplace, prefers Claude-native
primitives by default, and structurally enforces its principle foundation.
**Last published (Tier-0, git ref):** `v1.5.0` annotated tag (deref
`31ac1d7`) → commit reachable as ancestor of `origin/main` and of HEAD.
**Release window (Tier-0):** `origin/main..main` = the 148-commit linear
backlog (24 feat / 18 fix / 68 docs / 35 chore / 3 test), fast-forwarded
onto the published v1.5.0 baseline. Zero divergence (`git rev-list
--left-right --count origin/main...main` = `0 148`). No squash / no merge
commit / no amend — the feat+apply+seal commits are the audit trail.
**Breaking-change scan (Tier-0):** `git log --format=%s origin/main..main |
grep -iE 'breaking|!:'` → **zero**. No `feat!`/`fix!`, no `BREAKING CHANGE`
trailers. No MAJOR (SemVer item 8) trigger — this window is a clean MINOR.

---

## §1 — What v1.6.0 ships

v1.6.0 bundles the 148-commit post-v1.5.0 backlog across four work-slices.

**(a) claude-leverage program (Slices 1–4) — MINOR drivers (two new
components + new always-relevant guards/SKILLs):**

1. **Slice 1 CURRENCY — NEW component `capability-refresh`** (deterministic
   Class-A corpus refresh) + live source manifest + refresh-machinery
   contract addendum (`feat(capability-refresh): NEW component`,
   AC.CLP-CUR.3/5/6/7; `feat(corpus): live source manifest`, AC.CLP-CUR.3).
   New tracked tool tree under `framework/tools/capability-refresh/`.
2. **Slice 2 DOCTRINE** — dispatch-time + plan-time `primitive-check` guard
   (AC.CLP-DOC.2/.3/.4/.7/.8); graduate the dispatch-decision SKILL trio +
   README-from-disk (AC.CLP-DOC.1/.5/.6); guard wired into bootstrapped
   settings (AC.CLP-DOC.2 wiring leg).
3. **Slice 3 ADOPTIONS** — `/goal` production-flow + `/loop` catalogue-routing
   in observable use (AC.CLP-ADOPT.2★/.3/.4/.5); goal.md matcher rows.
4. **Slice 4 RENDER+WIRE — NEW component `knowledge-pack`** (deterministic
   corpus→skills-pack marketplace render, Slice 4a RENDER) +
   workspace-bootstrap marketplace wiring + persona surfacing (Slice 4b WIRE).
   New tracked tool tree under `framework/tools/knowledge-pack/`.

**(b) principle-foundation-structural-enforcement (Slices A–D) — MINOR
(new structural-enforcement surface: hooks + SKILL):**

5. Slice A — principle-manifest declaration substrate + manifest-checker
   (AC.PFSE.1, AC.PFSE.2-manifest-leg); Slice B — research-question gate +
   context-load gate (AC.PFSE.3, AC.PFSE.5); Slice C — primary-persona
   Stop-hook contributor framework + permission-ask + terminology-drift
   contributors (AC.PFSE.4, AC.PFSE.7, AC.PFSE.2★); Slice D — slug-collision
   detection + meta-decision-haiku arbiter SKILL (AC.PFSE.6, AC.PFSE.8).

**(c) GUARD-SWEEP FLOOR — MINOR (new seal-time behavior):**

6. `loam amend seal` now runs a location-agnostic cross-component guard
   sweep + an 11-class guard registry (`feat(dev-sdlc): GUARD-SWEEP FLOOR`,
   AC.GFLOOR.{1,2,3,4,5}; `feat(dev-sdlc): loam guard-floor registry`,
   AC.GFLOOR.6). No-bypass fence discovery + registry-resolved sweep-class
   guards at every seal.

**(d) ProgramBench full retirement — removal of dev-internal, never-shipped
tooling (NOT a breaking change — no public surface affected):**

7. Deletes the programbench-revival tool tree (40 tracked files) + the 20
   PB-purpose hands-off-lifecycle tests; RETIRED banners on sealed
   plan-pairs/experiments; a permanent case-insensitive retirement-sweep
   test (AC.PBRET.1–6). Recoverable from git history (`87403522`).

**PATCH-class fixes riding along inside the MINOR (18 fixes):** the
release-flow-partial-publish-repair (`loam-cli` idempotent repair + notes
locator), the DCG question-identity fix (`10f1519`), broken-suite-family
fixes, manifest-conformance, plan-state false-partial — all
backward-compatible defect closures absorbed under the one MINOR per
`docs/release-versioning-policy.md` §"What goes in a minor".

Per MINOR discipline: the lockstep version bump advances `docs/ACTIVE_MINOR`
1.5.0 → 1.6.0 + the 31 in-scope pyprojects + the meta-package `loam
--version` literal in one source-of-truth commit; the per-component lockstep
regression test stays GREEN. The two NEW components (`capability-refresh`,
`knowledge-pack`) carry `version = "0.1.0"` and are NOT in the install graph
(`install-from-source.txt`) — by the lockstep test's own "shipped runtime
components in the install graph" criterion they are out-of-scope for lockstep
this cut (they ride at 0.1.0, like the excluded experimental harnesses ride
at 0.0.0), and the IN_SCOPE_PYPROJECTS allowlist is deliberately left
unchanged. Folding them in is a future-MINOR decision once they enter the
install graph.

## §2 — Reconcile + gate framing

Tier-0 verification before prep:
- `git ls-remote --tags origin` highest `vX.Y.Z` = **`v1.5.0`** (deref
  `31ac1d7`) → confirmed published baseline.
- `git rev-list --left-right --count origin/main...main` = `0 148` → `main`
  is a clean linear fast-forward, zero divergence from `origin/main`.
- `git merge-base --is-ancestor 31ac1d7 origin/main` rc=0 → v1.5.0 seal on
  origin/main.
- `git log --format=%s origin/main..main | grep -iE 'breaking|!:'` → empty →
  no breaking change in the window.

Release window anchor (Tier-0, reachable from HEAD): `main` HEAD `4aafc29`
(the last seal in the window).

## §3 — Release prep sequence

Completed steps, in order (steps 1–7 local + reversible; step 9 PUBLIC,
owner-gated):
1. This plan-doc + §13 §status authored.
2. Lockstep version bump commit (1.5.0 → 1.6.0): `docs/ACTIVE_MINOR` + 31
   in-scope pyprojects + meta `__version__` literal; lockstep test GREEN.
3. `docs/state-migrations/v1-6-0-claude-leverage-and-principle-foundation.migration.yaml`
   authored — `operation: no-op` (verified: no commit changes on-disk
   user-state format; the two new components are framework tools that read
   the corpus + render to a marketplace repo, neither re-schemas `.loam/`
   state).
4. `docs/release-roadmap.md` §3 SHIPPED-LOCAL entry + §2 row + `docs/STATE.md`
   change-log entry (gates 3/6 read these).
5. `docs/experiments/release-integration-v1-6-0-hard-smoke.md` authored —
   HARD smoke aggregate verdict GREEN.
6. `git status --porcelain` empty (intended changes committed);
   `git branch --show-current` == `main`.
7. `loam release v1.6.0 --dry-run` — all 7 gates GREEN; no side effects.
8. **OWNER GATE** — explicit publish authorization (channel + msg-id recorded
   into §status + this header BEFORE step 9).
9. **PUBLIC** — `loam release v1.6.0 --release` (tag + push origin main +
   push tag + `gh release create` + backfill). Owner-gated.

## §4 — Acceptance criteria

### AC.REL160.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
path resolvable via `--plan-doc docs/plans/release-integration-v1-6-0.md`.

### AC.REL160.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` == `1.6.0`; the 31 in-scope pyprojects at 1.6.0; lockstep
test passes. The meta-package `__version__` literal updated to `1.6.0`. The
two new components remain at 0.1.0 (out-of-install-graph, out-of-scope for
lockstep this cut).

### AC.REL160.3 — HARD smoke GREEN
`docs/experiments/release-integration-v1-6-0-hard-smoke.md` exists and
contains the `Aggregate verdict: GREEN` token. The smoke runs from a cold
clone of the local repo at HEAD + a real spawn-isolated `claude -p`.

### AC.REL160.4 — Touched component suites GREEN (cold install)
The touched-component suites pass from the cold install, with any failure
Tier-0-verified as the SAME known-pre-existing set the v1.5.0 smoke documented
(`docs/experiments/release-integration-v1-5-0-hard-smoke.md`) — not a new
regression.

### AC.REL160.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` carries a v1.6.0 change-log entry marked SHIPPED LOCAL.

### AC.REL160.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §3 carries a v1.6.0 SHIPPED-LOCAL entry + §2 row
with a seal anchor (`4aafc29`, the window's last seal) reachable from HEAD.

### AC.REL160.7 — migration declared
`docs/state-migrations/v1-6-0-claude-leverage-and-principle-foundation.migration.yaml`
declares `version: v1.6.0` + `operation: no-op`.

### AC.REL160.S — Outcome-altitude (cold-install user-visible deltas)
Cold-install suite run from the scratch clone at HEAD: the new
`capability-refresh` + `knowledge-pack` component suites pass; the
principle-foundation structural-enforcement + GUARD-SWEEP FLOOR suites pass;
the ProgramBench retirement-sweep test passes; spawn-isolated `claude -p`
SMOKE OK at the production entry point. GREEN.

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC ID | Verdict | Evidence |
|---|---|---|
| AC.REL160.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc docs/plans/release-integration-v1-6-0.md` |
| AC.REL160.2 | GREEN | `docs/ACTIVE_MINOR` == `1.6.0`; 31 in-scope pyprojects at 1.6.0; lockstep test passed; `loam --version` → `loam 1.6.0` after bump commit; new components held at 0.1.0 (out-of-install-graph) |
| AC.REL160.3 | GREEN | `docs/experiments/release-integration-v1-6-0-hard-smoke.md` aggregate verdict GREEN (cold-clone install + spawn-isolated `claude -p` SMOKE OK + touched-component suites + ride-along regressions) |
| AC.REL160.4 | GREEN | touched-component suites green from cold install; any failure Tier-0-verified as the SAME known-pre-existing set documented in the v1.5.0 smoke (not a new regression) |
| AC.REL160.5 | GREEN | STATE.md change-log v1.6.0 SHIPPED LOCAL entry |
| AC.REL160.6 | GREEN | release-roadmap §3 v1.6.0 SHIPPED-LOCAL entry + §2 row; seal token `4aafc29` reachable from HEAD |
| AC.REL160.7 | GREEN | `docs/state-migrations/v1-6-0-claude-leverage-and-principle-foundation.migration.yaml` declares `version: v1.6.0` + `operation: no-op` |
| AC.REL160.S | GREEN | cold-install suites: capability-refresh + knowledge-pack + principle-foundation + GUARD-SWEEP FLOOR + ProgramBench retirement-sweep all green; spawn-isolated `claude -p` SMOKE OK |
