# Release integration — v1.0.1

**Status:** PREP COMPLETE → gates GREEN (owner-authorized publish)
**Working tree:** `/Users/lukeivers/loam` (main)
**Version:** v1.0.1 — PATCH increment derived at release time from the
published v1.0.0 (`bump_patch(v1.0.0) = v1.0.1` per
`docs/release-versioning-policy.md` §"Number derivation"). Owner-authorized:
Luke, Telegram 13481 ("make a patch update with the minor fixes").
**Last published (Tier-0, git ref):** `v1.0.0` (tag on `origin/main`).
**Release window (Tier-0):** `origin/main..HEAD` = 5 commits, working tree
clean.

---

## §1 — What v1.0.1 ships

v1.0.1 is a PATCH bundling exactly the two already-sealed minor fixes sitting
ahead of `origin/main` on `main`, plus their seal/BASELINE bookkeeping:

1. **FBM salience-gate fix** (seal `949fced9`; feat `69a82c41` + BASELINE-advance
   `209d7d43`). The file-memory episode retrieval gains a 5th salience
   signature that drops compaction-summary context-dumps from episode
   retrieval —
   `framework/primary-persona/src/loam/primary_persona/file_memory.py`. A
   compaction-summary dump is no longer surfaced as a retrievable episode.
   Plan-doc: `docs/plans/fbm-salience-gate-compaction-summary-dump.md`.

2. **FM.SILENT-EGRESS protection-matrix floor row** (seal `5c1021c9`; feat
   `73155755`). A new floor-class row in the protection failure-mode/guard
   matrix recording the silent-data-egress floor gap —
   `framework/protection-matrix/data/failure-mode-guard-matrix.yaml`. Surfaced
   by `loam guards` (the matrix advances 18 rows → 19, 16 → 17 floor-class).
   Plan-doc: `docs/plans/protection-matrix-silent-egress-row.md`.

Per PATCH discipline (`docs/release-versioning-policy.md` §131; D-NFCLEAN.4 /
D-SDPD): a PATCH never touches `docs/ACTIVE_MINOR` and rides the predecessor
MINOR's per-component versions — no pyproject lockstep bump, no `__version__`
change. `docs/ACTIVE_MINOR` stays `1.0.0`; the lockstep regression test stays
GREEN untouched. v1.0.1 ships ZERO source/metadata version changes beyond the
two sealed fixes + this release-prep admin batch.

## §2 — Dry-run gate framing

`loam release v1.0.1 --dry-run --plan-doc docs/plans/release-integration-v1-0-1.md`
runs all nine pre-publish gates from canonical main. The irreversible public
tag + push + GitHub Release is the owner-authorized step (Luke, TG 13481), run
after a verified-GREEN dry-run — no `--no-verify`, no force, no hand-edit to
green a gate.

## §4 — Acceptance criteria

### AC.REL11.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
scope-descriptive slug (`release-integration-v1-0-1`), reached via `--plan-doc`.

### AC.REL11.2 — No version bump (PATCH discipline)
`docs/ACTIVE_MINOR` content unchanged at `1.0.0`; no in-scope `pyproject.toml`
version field changed; the per-component lockstep regression test
(`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`) stays
GREEN with no edit. v1.0.1 carries no version-field churn.

### AC.REL11.3 — HARD smoke GREEN
`docs/experiments/release-integration-v1-0-1-hard-smoke.md` authored; REAL
cold-clone + REAL editable install + REAL spawn-isolated `claude -p` +
outcome-altitude exercise of the two fixes' surfaces (`loam guards` shows the
new FM.SILENT-EGRESS row from the cold install; the FBM salience-gate fix
exercised via its component suite); the writeup carries the `GREEN`
aggregate-verdict token.

### AC.REL11.4 — Touched-component suites GREEN
`framework/protection-matrix/tests/` and `framework/primary-persona/tests/`
both pass, including the two new AC tests
(`test_AC_PMROW_3_silent_egress_row.py`,
`test_AC_FBM_SAL_7_compaction_summary_dump_gated.py`).

### AC.REL11.5 — STATE.md backfilled
`docs/STATE.md` change-log carries a `**v1.0.1 ... SHIPPED**` entry naming the
two fixes + their seals.

### AC.REL11.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.0.1 |` row with a seal token
reachable from HEAD.

### AC.REL11.7 — migration declared
`docs/state-migrations/v1-0-1-minor-fixes.migration.yaml` declares
`version: v1.0.1` + `operation: no-op`; gate 7 GREEN.

### AC.REL11.S — Outcome-altitude (cold-install fix surface)
The HARD smoke exercises `loam guards` from a cold clone with no pre-arranged
state and observes the FM.SILENT-EGRESS row present in the live 19-row report —
the v1.0.1 user-visible delta, proven at the production entry-point. GREEN.

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL11.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc` |
| AC.REL11.2 | GREEN | `docs/ACTIVE_MINOR` == `1.0.0` unchanged; no pyproject touched; lockstep test GREEN untouched (PATCH rides predecessor MINOR per policy §131) |
| AC.REL11.3 | GREEN | `docs/experiments/release-integration-v1-0-1-hard-smoke.md` aggregate verdict GREEN |
| AC.REL11.4 | GREEN | protection-matrix 37 passed (AC.PMROW.3 4-passed); primary-persona 895 passed/1 skip (AC.FBM.SAL.7 3-passed) |
| AC.REL11.5 | GREEN | STATE.md change-log v1.0.1 SHIPPED entry |
| AC.REL11.6 | GREEN | release-roadmap §2 `| v1.0.1 |` row; seal token `5c1021c9` reachable from HEAD |
| AC.REL11.7 | GREEN | `docs/state-migrations/v1-0-1-minor-fixes.migration.yaml` declared `version: v1.0.1` + `operation: no-op`; gate 7 GREEN |
| AC.REL11.S | GREEN | HARD smoke cold-install `loam guards` outcome-altitude probe — FM.SILENT-EGRESS row present in the live 19-row report, no pre-arranged state |
