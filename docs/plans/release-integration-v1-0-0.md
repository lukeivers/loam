# Release integration — v1.0.0

**Status:** PREP COMPLETE → dry-run (owner publishes)
**Working tree:** `/Users/lukeivers/loam` (main)
**Version:** v1.0.0 — owner-declared MAJOR over v0.14.0 (Luke, Telegram 13414:
"calling this 1.0"). Version is an explicit owner-set literal, not a policy
derivation; the `loam release` verb takes the version as an argument.
**Last published (Tier-0, git ref):** `v0.14.0` (tag on `origin/main`).

---

## §1 — What v1.0.0 ships

v1.0.0 is the 1.0 cut. Its substance is release-readiness, not new features:

1. **Pre-1.0 documentation health-check fixes** (task #58 /
   `docs/design/pre-1.0-documentation-health-check.md`):
   - Sealed dev-sdlc doc-accuracy amendment (`apply.py:158`→`:269` across
     three methodology surfaces + the AC.PASH.C.1 test prose; dropped the
     stale present-tense "thirteen sealed components" count) — sealed at
     `e335e6f9`.
   - Two new component-reference pages (`state-migration-engine`,
     `protection-matrix`) + index intro count eighteen→twenty.
2. **Per-component pyproject version lockstep bump** 0.14.0 → 1.0.0 (27
   in-scope pyprojects + `docs/ACTIVE_MINOR`), plus the fold-in of
   `state-migration-engine` (was 0.13.0) and `protection-matrix` (was 0.1.0)
   into the lockstep set, plus the meta-package → 1.0.0.
3. **v1.0.0 migration declaration** (no-op — release touches only
   framework-side metadata).

The substantive runtime components that landed in the v0.14.x arc
(state-migration-engine + `loam migrate`, protection-matrix + `loam guards`,
the N2 STATE-OF-LOAM substrate-audit gate, auto-upgrade #163) are already
sealed and reachable from HEAD; v1.0.0 is the release that publishes the cut.

## §2 — Dry-run gate framing

`loam release v1.0.0 --dry-run --plan-doc docs/plans/release-integration-v1-0-0.md`
runs all nine pre-publish gates from canonical main. The build STOPS at the
dry-run verdict; the irreversible public tag + push + GitHub Release is the
dispatcher's step, run by hand after a verified-GREEN dry-run.

## §4 — Acceptance criteria

### AC.REL10.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix.

### AC.REL10.2 — Lockstep bump applied
All 27 in-scope pyprojects at `version = "1.0.0"`; `docs/ACTIVE_MINOR`
content == `1.0.0`; `state-migration-engine` + `protection-matrix` folded into
lockstep at 1.0.0; meta-package at 1.0.0;
`pytest plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`
GREEN.

### AC.REL10.3 — HARD smoke GREEN
`docs/experiments/release-integration-v1-0-0-hard-smoke.md` authored; REAL
cold-clone + REAL editable install + REAL spawn-isolated `claude -p` + the
newly-documented verbs (`loam guards` / `loam migrate`) exercised from the cold
install at outcome-altitude; the writeup carries the `GREEN` aggregate-verdict
token.

### AC.REL10.4 — D.1 byte-content GREEN post-bump
The lockstep bump's invalidation of the primary-persona + scope-of-work
`pyproject.toml` D.1 frozen SHAs is rebaselined in-band;
`pytest framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py`
GREEN (16/16). FOURTH consecutive recurrence; root-cause fix still OWED + F2.

### AC.REL10.5 — STATE.md backfilled
`docs/STATE.md` change-log carries a `**v1.0.0 ... SHIPPED**` entry naming the
1.0-cut items + the v0.14.x-arc seals the cut publishes.

### AC.REL10.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.0.0 |` row with a seal token
reachable from HEAD.

### AC.REL10.7 — migration declared
`docs/state-migrations/v1-0-0-release-cut.migration.yaml` declares
`version: v1.0.0` + `operation: no-op`; gate 7 GREEN.

### AC.REL10.S — Outcome-altitude (cold-install verbs)
The HARD smoke exercises `loam guards` (real coverage report, 18 rows) +
`loam migrate` (registered, dry-run reached the engine) + the installed
component versions (1.0.0) from a cold clone with no pre-arranged state. GREEN.

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL10.1 | GREEN | this doc exists with §1 + §4 + §13 |
| AC.REL10.2 | GREEN | 27 pyprojects + 3 folded (smigration/protection-matrix/meta) at 1.0.0; ACTIVE_MINOR 1.0.0; lockstep test 5/5 |
| AC.REL10.3 | GREEN | `docs/experiments/release-integration-v1-0-0-hard-smoke.md` aggregate verdict GREEN |
| AC.REL10.4 | GREEN | D.1 byte-content 16/16 post-rebaseline |
| AC.REL10.5 | GREEN | STATE.md change-log v1.0.0 SHIPPED entry |
| AC.REL10.6 | GREEN | release-roadmap §2 `| v1.0.0 |` row; seal token reachable from HEAD |
| AC.REL10.7 | GREEN | `docs/state-migrations/v1-0-0-release-cut.migration.yaml` declared; gate 7 GREEN |
| AC.REL10.S | GREEN | HARD smoke cold-install `loam guards`/`loam migrate` outcome-altitude probe GREEN |
