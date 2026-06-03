# Release integration — v1.1.0

**Status:** PREP COMPLETE → gates GREEN (owner-gated publish)
**Working tree:** `/Users/lukeivers/loam-release-v1.1.0-wt` (branch
`release/v1.1.0`; isolated worktree per `feedback_serialize_amendment_builds`)
**Version:** v1.1.0 — MINOR increment derived at release time from the
published v1.0.1 (`next_MINOR(v1.0.1) = v1.1.0` per
`docs/release-versioning-policy.md` §"Number derivation"). Owner-authorized:
Luke, Telegram 13626.
**Last published (Tier-0, git ref):** `v1.0.1` annotated tag → commit
`deb85f6a` (tag object `5c1021c9`).
**Release window (Tier-0):** `v1.0.1..release/v1.1.0` = the 55-commit linear
FBM/never-leak stack + 2 release commits (lockstep version bump `d71f450e` +
install-manifest fix `4c8e29e9`). Working tree clean.

---

## §1 — What v1.1.0 ships

v1.1.0 is a single MINOR shaped around one objective sentence: **loam's
file-backed memory retrieves the right thing, and loam never silently leaks
user data off-machine.** It bundles 13 features + 1 fix (zero BREAKING) as a
single clean linear stack that fast-forwards onto the published baseline.

**The retrieval half (FBM A–F + #80):**

1. **FBM write-time salience gate / cold tier** (feat `f0ae5397`) — diverts
   junk to a cold tier at ingest so it never pollutes retrieval.
2. **FBM load-time systematic filter + dedup** (feat `39cb9791`) — an
   absolute-floor relevance/quality filter + near-dup dedup at load time.
3. **FBM per-project STATE + registry + Cairn probe** (feat `23d8ee93`).
4. **FBM STATE → keep-pace lens** (feat `f7725309`).
5. **FBM multi-repo work-visibility** (feat `d47269f4`).
6. **FBM retrieval-relevance P@5 metric + guard** (feat `b327f054`).
7. **FBM #80 retrieval-quality fix** (feat `6a3595ad`) — anchor-flood cap +
   omnibus length-norm.

**The never-leak half:**

8. **egress-consent** (NEW component; feat `2304dea4`) — a fail-closed
   never-leak privacy gate before every off-machine send + secret
   auto-redaction; `loam report` (bug-report) is the first consumer.
9. **FM.SILENT-EGRESS protection-matrix rebind** (feat `502f9254`) — re-binds
   the silent-egress row (unbound `no guard` in v1.0.1) to the now-sealed
   egress-consent gate.
10. **FM.DROPPED-OPEN-LOOPS protection-matrix floor row** (feat `40ffde1b`).

**Supporting foundation:**

11. **usage-window-guard** (NEW component; feat `c0d94f91`) — OAuth
    rolling-window usage probe + parse + fail-open.
12. **deep-research → in-session subagent** (feat `353e5692`).
13. **handsoff swarm → in-session subagent** (feat `0135cbc3`).
14. **handsoff TPI6 fence fix** (**fix** `142585ca`) — AC.TPI.6 sealed
    manifest path + seal-bounded diff window.

Two NEW top-level components ship: `framework/egress-consent/` and
`framework/usage-window-guard/`. Both join the lockstep at 1.1.0.

Per MINOR discipline (`docs/release-versioning-policy.md`): the lockstep
version bump advances `docs/ACTIVE_MINOR` 1.0.0 → 1.1.0 + the 32 in-scope
pyprojects (the two new components folded into `IN_SCOPE_PYPROJECTS`) +
the meta-package `--version` literal 0.10.0 → 1.1.0 (closes the v1.0.1 §6
finding #1) in one source-of-truth commit (`d71f450e`). The install-from-source
manifest gains both new components (`4c8e29e9` — the HARD-smoke-caught
finding).

## §2 — Dry-run gate framing

`loam release v1.1.0 --dry-run --plan-doc docs/plans/release-integration-v1-1-0.md`
runs all nine pre-publish gates from the release worktree. The irreversible
public tag + push + GitHub Release is the owner-gated step, run after a
verified-GREEN dry-run — no `--no-verify`, no force, no hand-edit to green a
gate.

## §4 — Acceptance criteria

### AC.REL110.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
scope-descriptive slug (`release-integration-v1-1-0`), reached via `--plan-doc`.

### AC.REL110.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.0.0 → 1.1.0; the 32 in-scope `pyproject.toml`
version fields bump 1.0.0 → 1.1.0 (two new components folded into the
allowlist); the per-component lockstep regression test
(`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`) stays
GREEN with the bump + the new-component fold-in. The meta-package `--version`
literal folds into the lockstep (`loam --version` → `1.1.0`).

### AC.REL110.3 — HARD smoke GREEN
`docs/experiments/release-integration-v1-1-0-hard-smoke.md` authored; REAL
cold-clone + REAL editable install (from `install-from-source.txt` alone) +
REAL spawn-isolated `claude -p` (subscription-only, scrubbed
`ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN`, empty MCP) + outcome-altitude
exercise of the user-visible deltas (`loam --version` → 1.1.0; `loam guards`
→ 20 rows / 18 floor-class from the cold install); the writeup carries the
`GREEN` aggregate-verdict token.

### AC.REL110.4 — Touched + new-component suites GREEN
`framework/egress-consent/tests/` (45 passed), `framework/usage-window-guard/tests/`
(23 passed), `framework/protection-matrix/tests/` (42 passed),
`framework/workspace-bootstrap/tests/` (674 passed / 16 skipped), and
`framework/primary-persona/tests/` (944 passed / 1 skip / 1 pre-existing
failure — `test_AC_MSC_3`, shipped in v1.0.1, NOT a v1.1.0 regression) all pass.

### AC.REL110.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` change-log carries a `**v1.1.0 ... SHIPPED LOCAL**` entry
naming the bundled work + the release-window tip. (The `SHIPPED PUBLIC`
flip is the POST-publish backfill, not done here.)

### AC.REL110.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.1.0 |` row with a seal token
reachable from HEAD; §3 carries the active-version entry.

### AC.REL110.7 — migration declared
`docs/state-migrations/v1-1-0-fbm-retrieval-and-egress-consent.migration.yaml`
declares `version: v1.1.0` + `operation: no-op`; gate 7 GREEN.

### AC.REL110.S — Outcome-altitude (cold-install user-visible deltas)
The HARD smoke exercises `loam --version` and `loam guards` from a cold clone
with no pre-arranged state and observes `loam 1.1.0` + the 20-row report with
FM.SILENT-EGRESS bound to a release-gate (was unbound) + FM.DROPPED-OPEN-LOOPS
present — the v1.1.0 user-visible deltas, proven at the production
entry-points. GREEN.

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL110.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc` |
| AC.REL110.2 | GREEN | `docs/ACTIVE_MINOR` == `1.1.0`; 32 in-scope pyprojects at 1.1.0; lockstep test GREEN with the bump + new-component fold-in (smoke §5); meta-package `loam --version` → 1.1.0 (smoke §3) |
| AC.REL110.3 | GREEN | `docs/experiments/release-integration-v1-1-0-hard-smoke.md` aggregate verdict GREEN |
| AC.REL110.4 | GREEN | egress-consent 45 / usage-window-guard 23 / protection-matrix 42 / workspace-bootstrap 674 / primary-persona 944 passed (1 pre-existing `test_AC_MSC_3` failure, shipped in v1.0.1, not a regression — smoke §5/§6) |
| AC.REL110.5 | GREEN | STATE.md change-log v1.1.0 SHIPPED LOCAL entry |
| AC.REL110.6 | GREEN | release-roadmap §2 `| v1.1.0 |` row + §3 active entry; seal token reachable from HEAD |
| AC.REL110.7 | GREEN | `docs/state-migrations/v1-1-0-fbm-retrieval-and-egress-consent.migration.yaml` declared `version: v1.1.0` + `operation: no-op` |
| AC.REL110.S | GREEN | HARD smoke cold-install `loam --version` → 1.1.0 + `loam guards` → 20 rows (18 floor-class) outcome-altitude probe, no pre-arranged state (smoke §3) |
