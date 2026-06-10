# Release integration — v1.4.0

**Status:** PREP COMPLETE → gates GREEN (owner-authorized publish — Luke,
Discord 1514274994857709700, 2026-06-10; decision record
`<pos3-workspace>/.loam/memory/decisions/2026-06-10-publish-recent-loam-work-v140.md`)
**Working tree:** `/Users/lukeivers/loam` (branch `main`; the six sealed-local
amendments are already a clean linear fast-forward stack on the published
v1.3.0 baseline — no isolated release worktree needed)
**Version:** v1.4.0 — MINOR increment derived at release time from the
published v1.3.0 (`next_MINOR(v1.3.0) = v1.4.0` per
`docs/release-versioning-policy.md` §"Number derivation"). All six bundled
amendments are new-capability, backward-compatible (zero BREAKING) — MINOR,
not MAJOR. ONE consolidated MINOR over six sequential minors per the owner-
ratified version call (a single public changelog narrative: the memory +
build-from-intent release).
**Last published (Tier-0, git ref):** `v1.3.0` annotated tag (`10ef8f2a`) →
commit `7ebbe45a`; `origin/main` at `22df8683`.
**Release window (Tier-0):** `origin/main..main` = the 61-commit linear
amendment stack (`b16b49f2..a3f58a21`, six seals, fast-forwarded onto the
published v1.3.0 baseline) + the release commits (off-vertical smoke RUN_LOG
entry `d6c216a2`, lockstep bump `f3501210`, D.1 hash-pin rebaseline
`2c38e77f`, this bookkeeping). No squash / no merge commit / no amend — the
feat+apply+seal commits are the audit trail.

---

## §1 — What v1.4.0 ships

v1.4.0 is a single MINOR shaped around one objective sentence: **loam
remembers its owner's rulings and builds working software from a
plain-language ask — decisions are recorded at ruling time, recalled and
surfaced when relevant, and bundled into every dispatched agent's context;
the general build-from-intent path turns a non-technical request into
verified working software; and subagent frame governance keeps every
dispatched context consistent in and out.**

**The six sealed-local amendments (all reconciled to `main`):**

1. **frame-kernel SLICE 1a — subagent context handoff (the IN-guarantee)**
   (feat `b16b49f2`, apply `b338ab70`, sealed at `053379fa`) — a
   `SubagentStart` hook injects one `additionalContext` bundle into every
   dispatched subagent: identity, frame, active-workstream state. The
   loam-realignment keystone.
2. **frame-kernel SLICE 1b — subagent stop frame-check (the OUT-guarantee)**
   (feat `bf1108df`, apply `69e28416`, sealed at `3b0e4eaa`) — a
   `SubagentStop` hook runs an out-of-band frame-consistency check on what
   the subagent did, pairing with 1a's IN-handoff. A post-seal corrective
   (`17529112`) routes the active-workstream probe through
   `workspace_paths.pos_subdir` (AC.D.2.5).
3. **workspace-sync settings-fragment auto-composer (RF-1 closure)**
   (feat `45cdf973`, apply `5825803d`, sealed at `728b2ef0`) — workspace
   `.claude` settings fragments compose automatically at sync time; the
   scale-free governance rule becomes live code instead of hand-merge.
4. **FBM-correctness cycle — plan-state index + claim guard + supersession**
   (feats `6f7deb1f` / `10776ee5` / `7f163755`, fix `7e6621f9`, apply
   `3b060f14`, sealed at `cb0082b6`; fence `loam-cli` + `primary-persona` +
   `hands-off-lifecycle`) — a git-derived plan-state index (turn-start plans
   block + scoped query), a claim-vs-stored-state guard on the KP9
   draft-gate seam, and supersession correctness (marking entry point +
   corpus-retrieval honor).
5. **memory-recall cycle — decision ledger + surfacing + dispatch packs**
   (feats `1ba0ee29` / `13d6ea60` / `6b65e85a` / `28cbe6cf` / `aecb8e47`,
   apply `935cb0db`, sealed at `926bdf07`; fence `primary-persona` +
   `frame-kernel` + `hands-off-lifecycle`) — the June-7 eval verdict
   executed (co-citation spread DELETED; activation default-off behind
   `LOAM_FBM_ACTIVATION`), the surfacing rebuild on BOTH render paths
   (paths + salient pointers + 5KB whole-record budget), the decision
   ledger (rulings as first-class records, write-at-ruling-time +
   steer-on-miss + unified retrieval), dispatch memory packs (decision-aware
   memory bundles via the gated keep-pace retrieval), and the decision-claim
   guard (settled rulings cannot be silently re-opened).
6. **general build-from-intent — the corrected #86 capability**
   (feats `33c018e9` / `6aa33800` / `080e1107` / `5b692343` / `6c5ce02c` /
   `77b88f5d` + fixes `60d886a5` / `493fa2de` / `cc394548` / `21422aa4`,
   applies `969d6a5e` / `7dcec73a`, sealed at `f4fd93b0`; fence
   `workspace-bootstrap`) — six sequenced slices: per-request live intent +
   meaningful questions, in-pipeline domain-grounding research, the
   generative middle, convergence as canonical default, the in-loop progress
   surface, and the S6 smoke harness with the four-domain honest RUN_LOG
   proof (3-app back-office trio + an off-vertical probe, all `done`).

No new top-level component ships: every amendment extends sealed components
under manifests (frame-kernel, workspace-sync, loam-cli, primary-persona,
hands-off-lifecycle, workspace-bootstrap; the build-from-intent loop lives in
the measurement-class `framework/tools/handsoff-loop/` tool at its deliberate
`0.0.0` version, excluded from lockstep by policy).

Per MINOR discipline (`docs/release-versioning-policy.md`): the lockstep
version bump advances `docs/ACTIVE_MINOR` 1.3.0 → 1.4.0 + the 32 in-scope
pyprojects + the meta-package `loam --version` literal in one source-of-truth
commit (`f3501210`); the per-component lockstep regression test stays GREEN
(5 passed). The known D.1 byte-content hash-pin coupling (every lockstep bump
invalidates the two pinned pyproject SHAs — SIXTH consecutive recurrence;
root-cause fix still owed, F2-surfaced) is closed in-band by the established
retire-and-rebaseline pattern (`2c38e77f`).

## §2 — Reconcile + gate framing

Tier-0 verification before prep: `git merge-base origin/main main` ==
`origin/main` (`22df8683`) — `main` is a clean linear fast-forward, zero
merge commits in the window. A secret scan over the full
`origin/main..main` diff (23,103 lines) found zero token/key/private-key
matches; no secret-bearing file names in the window.

`loam release v1.4.0 --plan-doc docs/plans/release-integration-v1-4-0.md`
runs all pre-publish gates from the repo. The irreversible public tag + push
+ GitHub Release is the owner-authorized step (Discord 1514274994857709700),
run after a verified-GREEN HARD smoke — no `--no-verify`, no force, no
hand-edit to green a gate.

## §4 — Acceptance criteria

### AC.REL140.1 — Plan-doc authored
This doc exists with §1 inventory + §4 ACs + §13 §status gate matrix at a
scope-descriptive slug (`release-integration-v1-4-0`), reached via
`--plan-doc`.

### AC.REL140.2 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.3.0 → 1.4.0; the 32 in-scope
`pyproject.toml` version fields bump 1.3.0 → 1.4.0; the per-component
lockstep regression test
(`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`) stays
GREEN with the bump. The meta-package `--version` literal folds into the
lockstep (`loam --version` → `1.4.0`).

### AC.REL140.3 — HARD smoke GREEN
`docs/experiments/release-integration-v1-4-0-hard-smoke.md` authored; REAL
cold-clone + REAL editable install + REAL spawn-isolated `claude -p`
(subscription-only, scrubbed `ANTHROPIC_API_KEY`/`TELEGRAM_BOT_TOKEN`,
`--strict-mcp-config`) + the build-from-intent App-1 documented command
reproduced end-to-end from the cold clone (every run reported honestly,
fails included) + the touched-component regression ride-alongs; the writeup
carries the `GREEN` aggregate-verdict token.

### AC.REL140.4 — Touched component suites GREEN (cold install)
`framework/frame-kernel/tests/`, `framework/workspace-sync/tests/`,
`framework/primary-persona/tests/`, `framework/hands-off-lifecycle/tests/`,
`framework/tools/loam/tests/`, `framework/workspace-bootstrap/tests/`, and
`framework/tools/handsoff-loop/tests/` all pass from the cold install, with
any failure Tier-0-verified pre-existing on the published v1.3.0 tip (not a
v1.4.0 regression) and documented in the smoke writeup.

### AC.REL140.5 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` change-log carries a `**v1.4.0 ... SHIPPED LOCAL**` entry
naming the six amendments + the release-window tip. (The `SHIPPED PUBLIC`
flip is the post-publish backfill, done by the release tool.)

### AC.REL140.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v1.4.0 |` row whose final seal
token (`f4fd93b0` — the general-build-from-intent seal, the release-window
content tip) is reachable from HEAD.

### AC.REL140.7 — migration declared
`docs/state-migrations/v1-4-0-memory-and-build-from-intent.migration.yaml`
declares `version: v1.4.0` + `operation: no-op` (all new state is created
lazily or derived at read time — no existing user `.loam/` state changes).

### AC.REL140.S — Outcome-altitude (cold-install user-visible deltas)
The HARD smoke exercises the v1.4.0 user-visible deltas from a cold clone
with no pre-arranged state: `loam --version` reports `loam 1.4.0`, and the
general build-from-intent path runs the documented App-1 reconciliation ask
end-to-end through the production CLI entry point (live intent + grounded
research + generation + convergence + progress surface). GREEN.

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL140.1 | GREEN | this doc exists with §1 + §4 + §13; resolved via `--plan-doc` |
| AC.REL140.2 | GREEN | `docs/ACTIVE_MINOR` == `1.4.0`; 32 in-scope pyprojects at 1.4.0; lockstep test 5 passed; cold-install `loam --version` → `loam 1.4.0` (bump commit `f3501210`) |
| AC.REL140.3 | GREEN | `docs/experiments/release-integration-v1-4-0-hard-smoke.md` aggregate verdict GREEN (App-1 run 1 honest gate-leak refusal + run 2 `done`; both reported) |
| AC.REL140.4 | GREEN | frame-kernel 62 / workspace-sync 126 / primary-persona 1190+1skip / hands-off-lifecycle 772+7skip / tools-loam 179 / workspace-bootstrap 674+16skip / handsoff-loop 89+7skip — all from the cold install; the single primary-persona failure (`test_AC_MSC_3`) Tier-0-verified pre-existing-environmental (fails identically at published tip `22df8683` in the same cold clone; passes in canonical) |
| AC.REL140.5 | GREEN | STATE.md change-log v1.4.0 SHIPPED LOCAL entry |
| AC.REL140.6 | GREEN | release-roadmap §2 `| v1.4.0 |` row; final seal token `f4fd93b0` reachable from HEAD |
| AC.REL140.7 | GREEN | `docs/state-migrations/v1-4-0-memory-and-build-from-intent.migration.yaml` declares `version: v1.4.0` + `operation: no-op` |
| AC.REL140.S | GREEN | HARD smoke cold-install `loam --version` → 1.4.0 + App-1 build-from-intent `done` from the cold clone through the production entry point, no pre-arranged state |
