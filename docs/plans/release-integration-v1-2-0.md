# Release integration — v1.2.0

**Status:** PREP COMPLETE → gates GREEN (owner-greenlit publish — Luke: "Go")
**Working tree:** `/Users/lukeivers/loam` (branch `main`; the 7-increment WMS
stack reconciled by fast-forward — no isolated release worktree needed because
the stack is already linear and contained, per the reconcile verification below)
**Version:** v1.2.0 — MINOR increment derived at release time from the
published v1.1.0 (`next_MINOR(v1.1.0) = v1.2.0` per
`docs/release-versioning-policy.md` §"Number derivation"). The new WMS
subsystem is additive (zero BREAKING) — MINOR, not MAJOR.
**Last published (Tier-0, git ref):** `v1.1.0` annotated tag → commit
`551ebada` (tag object `cb1993d9`).
**Release window (Tier-0):** `v1.1.0..main` = the 30-commit linear WMS
increment stack (`c6afcd6d..9192d1d7`, fast-forwarded onto the published
v1.1.0 baseline) + the release commits (lockstep version bump + this
bookkeeping). Working tree clean.

---

## §1 — What v1.2.0 ships

v1.2.0 is a single MINOR shaped around one objective sentence: **loam has a
unified, work-items-first Work Management System — one event-sourced work
graph surfaced through multiple per-user-chosen lenses, with conversational
intake, transparent derived prioritization, the relational web, and
action-ending analytics.** It bundles the 7-increment WMS roadmap (task #84,
the ★ major sub-component) as a single clean linear stack that fast-forwards
onto the published v1.1.0 baseline.

**The 7-increment WMS roadmap (all sealed-local, now reconciled to `main`):**

1. **Increment 1 — work-streams lens** (feat `33509273`, seal `23282c9`) — the
   FBM-derived attention-track lens; the first lens proving the surfacing path
   end-to-end on live FBM STATE (per-turn one-concise-subsuming-block surface,
   overflow-collapse, owner-gated deep-dive/pause, derived-not-stored state
   with a fail-soft deviation seam). The LitRPG production-state deriver lands
   the first concrete stream source.
2. **Increment 2 — unified work model (L1) + projects lens** (feat `c5fbe8cb`,
   seal `e0afa9c`) — the FOUNDATION. `objective_tracker` extended additively
   under a manifest to the §2a work-item schema (additive fields, blocks-on/
   waits-on edges + `unblocked_next` query + no-edge-fabrication guard,
   cold-rebuild-from-events). A projects lens lands over it; the streams lens
   is re-pointed at the L1 graph via the pre-L1 shim (no register rewrite).
3. **Increment 3 — intake** (feat `1c1de6a6`, seal `d8d10c7`) — conversational
   work-capture; LIGHT-default propose-and-confirm (create in `proposed`,
   promote on confirm), per-user via the #34 `work-tracking` /
   `intake-aggressiveness` cell; conservative dedup; `origin: conversation`
   provenance; fail-soft-to-silence.
4. **Increment 4 — prioritization + the relational web** (feat `7d9c1b99`,
   seal `1fb84d9c`) — a derived, TRANSPARENT, calibrate-on-use FIVE-signal
   ordering (priority-key · blocking-impact · goal-alignment · staleness ·
   explicit pin/defer-as-hard-override), a plain-language reason in place of a
   surfaced score; the relational web (unblocked-next / blocked-on-what /
   waiting-on-me-vs-others / decomposition tree) surfaced from existing read
   queries. Store consumed read-only; the edge-mutation self-heal is deferred
   to #71.
5. **Increment 5 — goals / on-my-plate / waiting-on lenses** (feat `dfab02e0`,
   seal `a236e49`) — the remaining lenses (OBJECTIVES.md as the goals-lens
   index, a plate filter reusing `prioritize`, a standalone waiting-on lens),
   a shared waiting-split single-source, ON-DEMAND render (no per-turn
   registration — the FBM-don't-bloat discipline).
6. **Increment 6 — per-user lens choice (L4 wiring)** (feat `da01078b`, seal
   `91d9a6b`) — `lens_choice.py` reads the #34 `work-tracking` profile and
   PICKS the per-user lens set; a plain switch changes the next turn's surface;
   fail-open to a non-empty deterministic default. Slimmed the always-on
   per-turn surface.
7. **Increment 7 — analytics** (feat `8aba88cc`, seal `fde2b17`) — the LAST
   increment, CLOSING the roadmap. THREE action-ending insights (where work
   piles up/stalls, chronically blocked/waiting items, completion-vs-intake
   balance), ON-DEMAND only, derived read-only over the event log + projection;
   every vanity metric CUT.

No new top-level component ships: the WMS extends the sealed `objective_tracker`
(additively, under a manifest) and lands the lens modules in the existing
`primary-persona` keep-pace package, with the LitRPG stream-source deriver in
`tools/loam`. Two components carry the touched code at the lockstep version
(objective-tracker, primary-persona, tools/loam).

Per MINOR discipline (`docs/release-versioning-policy.md`): the lockstep
version bump advances `docs/ACTIVE_MINOR` 1.1.0 → 1.2.0 + the 31 in-scope
pyprojects + the meta-package `loam --version` literal (1.1.0 → 1.2.0) in one
source-of-truth commit; the per-component lockstep regression test stays GREEN.

## §2 — Reconcile + gate framing

The 7 increment branches were each built stacked on the prior's verified tip,
so the inc-7 tip (`9192d1d7`, seal `fde2b170`) contains all of 1–7 linearly.
Tier-0 verification before the merge: `origin/main` unmoved at `c6afcd6d`; all
six increment branches are ancestors of inc-7; `main` is an ancestor of inc-7
(fast-forward possible); zero merge commits in the 30-commit window. The stack
was brought into `main` by **fast-forward** (no squash, no merge commit, no
amend — the increment+seal commits ARE the audit trail).

`loam release v1.2.0 --plan-doc docs/plans/release-integration-v1-2-0.md` runs
all pre-publish gates from the repo. The irreversible public tag + push +
GitHub Release is the owner-greenlit step ("Go"), run after a verified-GREEN
HARD smoke — no `--no-verify`, no force, no hand-edit to green a gate.

## §4 — Acceptance criteria

### AC.REL120.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
scope-descriptive slug (`release-integration-v1-2-0`), reached via `--plan-doc`.

### AC.REL120.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.1.0 → 1.2.0; the 31 in-scope `pyproject.toml`
version fields bump 1.1.0 → 1.2.0; the per-component lockstep regression test
(`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`) stays
GREEN with the bump. The meta-package `--version` literal folds into the
lockstep (`loam --version` → `1.2.0`).

### AC.REL120.3 — HARD smoke GREEN
`docs/experiments/release-integration-v1-2-0-hard-smoke.md` authored; REAL
cold-clone + REAL editable install + REAL spawn-isolated `claude -p`
(subscription-only, scrubbed `ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN`,
`--strict-mcp-config`) + outcome-altitude exercise of the user-visible deltas
(`loam --version` → 1.2.0; a WMS lens exercised end-to-end against a real
work store through the production entry point); the writeup carries the
`GREEN` aggregate-verdict token.

### AC.REL120.4 — Touched + WMS suites GREEN
`framework/objective-tracker/tests/` (176 passed), `framework/primary-persona/tests/`
(all passed / 1 skip), and `framework/tools/loam/tests/` (175 passed) all pass.
The full-repo sweep on reconciled `main` is GREEN except 3 PRE-EXISTING,
SHIPPED-IN-v1.1.0 byte-content-match failures in
`framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` (the
known-stale D.1 hash-pin test — task #22; verified red on the published v1.1.0
tip `c6afcd6d`, NOT a v1.2.0 regression). The reconcile in fact REDUCED the
hands-off-lifecycle failure count from 15 (on v1.1.0 tip) to 3 — the WMS
`session_start_emitter` rework fixed the 12 AC37/SE_4 failures.

### AC.REL120.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` change-log carries a `**v1.2.0 ... SHIPPED LOCAL**` entry
naming the WMS subsystem + the release-window tip. (The `SHIPPED PUBLIC` flip
is the POST-publish backfill, not done here.)

### AC.REL120.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.2.0 |` row with a seal token
reachable from HEAD; §3 carries the active-version entry.

### AC.REL120.7 — migration declared
`docs/state-migrations/v1-2-0-work-management-system.migration.yaml` declares
`version: v1.2.0` + `operation: no-op` (framework code/data + version metadata;
the WMS work-item store is created lazily on first use — no existing user
`.loam/` state changes).

### AC.REL120.8 — Architecture §7 + decision register reconciled
`docs/design/work-management-system-architecture.md` §7 increment table reads
all 7 rows BUILT (rows 1/2/5/6 flipped from stale "future"); the §9 decision
register carries CONFIRMED+BUILT on every WMS-D decision.

### AC.REL120.S — Outcome-altitude (cold-install user-visible deltas)
The HARD smoke exercises `loam --version` and a WMS lens from a cold clone with
no pre-arranged state and observes `loam 1.2.0` + a working lens surface over a
real work store at the production entry-point — the v1.2.0 user-visible delta,
proven cold. GREEN.

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL120.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc` |
| AC.REL120.2 | GREEN | `docs/ACTIVE_MINOR` == `1.2.0`; 31 in-scope pyprojects at 1.2.0; lockstep test 5 passed; meta-package `loam --version` → 1.2.0 |
| AC.REL120.3 | GREEN | `docs/experiments/release-integration-v1-2-0-hard-smoke.md` aggregate verdict GREEN |
| AC.REL120.4 | GREEN | objective-tracker 176 / primary-persona all-pass / tools-loam 175 passed; 3 pre-existing byte-match failures verified red on v1.1.0 tip `c6afcd6d` (not a regression — reconcile reduced hands-off failures 15→3) |
| AC.REL120.5 | GREEN | STATE.md change-log v1.2.0 SHIPPED LOCAL entry |
| AC.REL120.6 | GREEN | release-roadmap §2 `| v1.2.0 |` row + §3 active entry; seal token reachable from HEAD |
| AC.REL120.7 | GREEN | `docs/state-migrations/v1-2-0-work-management-system.migration.yaml` declared `version: v1.2.0` + `operation: no-op` |
| AC.REL120.8 | GREEN | architecture §7 all 7 rows BUILT; §9 WMS-D1..D7 all CONFIRMED+BUILT |
| AC.REL120.S | GREEN | HARD smoke cold-install `loam --version` → 1.2.0 + a WMS lens over a real store outcome-altitude probe, no pre-arranged state |
