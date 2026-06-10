# Release integration — v1.5.0

**Status:** PREP COMPLETE → gates GREEN (owner-authorized publish — Luke,
Discord 1514378120, 2026-06-10 16:17 CDT)
**Working tree:** `/Users/lukeivers/loam` (branch `main`; the four sealed-local
amendments are already a clean linear fast-forward stack on the published
v1.4.0 baseline — no isolated release worktree needed)
**Version:** v1.5.0 — MINOR increment derived at release time from the
published v1.4.0 (`next_MINOR(v1.4.0) = v1.5.0` per
`docs/release-versioning-policy.md`). The four bundled amendments span two
work classes: (a) three frame-kernel corrective patches (PATCH-class defects
in v1.4.0's SubagentStart envelope contract) + (b) KEEL adoption Phase 1
(META-FRAMEWORK MINOR-class: docs-only honesty debts + Charter genesis). The
MINOR-class work lifts the combined window to MINOR, not PATCH.
**Last published (Tier-0, git ref):** `v1.4.0` annotated tag (`7dc1e38`) →
commit reachable as ancestor of HEAD.
**Release window (Tier-0):** `origin/main..main` = the 35-commit linear
amendment stack (four seals, fast-forwarded onto the published v1.4.0
baseline) + the release commits (this plan-doc, lockstep bump, bookkeeping).
No squash / no merge commit / no amend — the feat+apply+seal commits are
the audit trail.

---

## §1 — What v1.5.0 ships

v1.5.0 bundles four sealed-local amendments across two work classes:

**Three frame-kernel corrective patches (PATCH-class — defect closures in
v1.4.0's SubagentStart envelope contract):**

1. **frame-kernel SubagentStart envelope cwd-fallback**
   (fix `39bb45d7`, apply `4f9ba3e9`, sealed at `c39de619`) — `parse_envelope`
   now resolves workspace_root from real Claude Code envelopes which carry
   `cwd` (not `workspace.project_dir`); all three bundle tiers populate on
   real dispatches. Closes the contract gap where the memory + context bundle
   degraded to placeholders on every real SubagentStart dispatch.

2. **frame-kernel real-dispatch memory tier**
   (feat `2d69c8ea`, apply `760a4bb7`, sealed at `9eeef654`) — `task_text`
   derived from the parent transcript's last user message + a query-less
   standing decision floor; the bundle's memory tier now populates on real
   SubagentStart envelopes.

3. **frame-kernel stop-judge agent-transcript objective**
   (feat `5a75d832`, apply `9a808123`, sealed at `9e4c0727`) — the frame-judge
   now judges each subagent result against the subagent's actual dispatched
   objective (using `agent_transcript_path` as the sole source, never the
   parent transcript); the off-frame flag self-identifies as a frame-judge
   advisory naming the judged dispatch.

**One META-FRAMEWORK MINOR — KEEL adoption Phase 1 (docs-only):**

4. **KEEL adoption program Phase 1 — doctrine rewrite + Charter genesis**
   (feats `76eddb9c` / `d9f2b3cb` / `730ab987`, apply `bd95f081`, sealed at
   `31ac1d70`) — honesty debts paid (novelty retraction, VERIFIED rename in
   doctrine, dormant-gates archive note, Outcomes-equivalence overclaim fixed)
   + the root contract installed (Charter #0 verbatim, AC.PO.1/2 derived from
   it, the 62 citing plans retroactively well-founded without editing any
   sealed plan). Grafts (Cycles A–F) follow as separate amendments.

No new top-level component ships: every amendment extends sealed components
under manifests (frame-kernel, dev-sdlc).

Per MINOR discipline (`docs/release-versioning-policy.md`): the lockstep
version bump advances `docs/ACTIVE_MINOR` 1.4.0 → 1.5.0 + the 32 in-scope
pyprojects + the meta-package `loam --version` literal in one
source-of-truth commit; the per-component lockstep regression test stays
GREEN (5 passed pre-bump at 1.4.0; will re-pass post-bump at 1.5.0).

## §2 — Reconcile + gate framing

Tier-0 verification before prep: `git log --oneline origin/main..HEAD | wc -l`
= 28 (content commits) + release prep commits — `main` is a clean linear
fast-forward, zero divergence from `origin/main`.

Seal SHAs (all reachable from HEAD, Tier-0 verified):
- frame-kernel cwd-fallback: `c39de619`
- frame-kernel real-dispatch memory tier: `9eeef654`
- frame-kernel stop-judge transcript objective: `9e4c0727`
- KEEL P1: `31ac1d70` (the last seal, anchoring this release window)

## §3 — Release prep sequence

Completed steps, in order:
1. Full test suite run (canonical venv) — GREEN.
2. Hard smoke (cold clone `.scratch/smokes/v1-4-1-smoke/`) — GREEN.
3. This plan-doc + §13 §status.
4. `docs/experiments/release-integration-v1-5-0-hard-smoke.md` authored.
5. `docs/state-migrations/v1-5-0-frame-kernel-patches-and-keel-p1.migration.yaml` authored.
6. `docs/release-roadmap.md` §2 row for v1.5.0 + seal anchor added.
7. `docs/STATE.md` v1.5.0 SHIPPED LOCAL entry added.
8. Lockstep version bump commit (1.4.0 → 1.5.0).
9. `loam release v1.5.0` gates GREEN; tag + push.

## §4 — Acceptance criteria

### AC.REL150.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
path resolvable via `--plan-doc docs/plans/release-integration-v1-5-0.md`.

### AC.REL150.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` == `1.5.0`; 32 in-scope pyprojects at 1.5.0; lockstep
test 5 passed. The meta-package `--version` literal updated to `1.5.0`.

### AC.REL150.3 — HARD smoke GREEN
`docs/experiments/release-integration-v1-5-0-hard-smoke.md` exists and contains the
`GREEN` aggregate-verdict token. The smoke runs the full v1.4.0 ride-along
suite from a cold clone of the local repo at HEAD.

### AC.REL150.4 — Touched component suites GREEN (cold install)
frame-kernel 92 passed; dev-sdlc 336/7skip; primary-persona 1190/1skip/1fail
(pre-existing-environmental, Tier-0-verified at v1.4.0 tip); workspace-sync
126; tools-loam 179. The single primary-persona failure is the same
cold-clone environmental test that failed identically at published v1.4.0.

### AC.REL150.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` carries a v1.5.0 change-log entry marked SHIPPED LOCAL.

### AC.REL150.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 row for `v1.5.0` carries a seal anchor
(`31ac1d70`, the KEEL P1 seal) reachable from HEAD.

### AC.REL150.7 — migration declared
`docs/state-migrations/v1-5-0-frame-kernel-patches-and-keel-p1.migration.yaml`
declares `version: v1.5.0` + `operation: no-op`.

### AC.REL150.S — Outcome-altitude (cold-install user-visible deltas)
Cold-install suite run from the scratch clone at HEAD: dev-sdlc
`test_AC_KDOC_S_outcome_altitude_honesty_sweep` PASSES (the KEEL P1
doc-honesty sweep at the production entry point). Frame-kernel 92 tests pass
including the new real-dispatch envelope tests. GREEN.

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC ID | Verdict | Evidence |
|---|---|---|
| AC.REL150.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc docs/plans/release-integration-v1-5-0.md` |
| AC.REL150.2 | GREEN | `docs/ACTIVE_MINOR` == `1.5.0`; 32 in-scope pyprojects at 1.5.0; lockstep test 5 passed; `loam --version` → `loam 1.5.0` after bump commit |
| AC.REL150.3 | GREEN | `docs/experiments/release-integration-v1-5-0-hard-smoke.md` aggregate verdict GREEN (frame-kernel 92, dev-sdlc 336, spawn-isolated `claude -p` SMOKE OK, system binary operational) |
| AC.REL150.4 | GREEN | frame-kernel 92 / dev-sdlc 336/7skip / primary-persona 1190/1skip/1fail (pre-existing-environmental Tier-0-verified at v1.4.0 tip) / workspace-sync 126 / tools-loam 179 / lockstep 5 |
| AC.REL150.5 | GREEN | STATE.md change-log v1.5.0 SHIPPED LOCAL entry |
| AC.REL150.6 | GREEN | release-roadmap §2 `| v1.5.0 |` row; seal token `31ac1d70` reachable from HEAD |
| AC.REL150.7 | GREEN | `docs/state-migrations/v1-5-0-frame-kernel-patches-and-keel-p1.migration.yaml` declares `version: v1.5.0` + `operation: no-op` |
| AC.REL150.S | GREEN | cold-install dev-sdlc suite 336/7skip including AC.KDOC.S outcome-altitude honesty sweep; frame-kernel 92 including real-dispatch envelope tests |
