# Release-integration plan — v0.14.0 MINOR publish (keep-pace MVP + FBM Cycle-1 + first-run message accuracy)

**Status:** RELEASE-INTEGRATION PLAN — prepared by loam-builder 2026-05-29 in the release worktree `/Users/lukeivers/loam-release-v0-14-0` (branch `release/v0-14-0`). LOCAL-reversible block executed autonomously; the PUBLIC tag-push is HELD for the dispatcher (Ren) to execute deliberately — this plan does NOT push.

**WD:** `/Users/lukeivers/loam-release-v0-14-0` (isolated worktree on branch `release/v0-14-0`; `.venv` symlinked to the canonical 3.13 venv for tomllib).

**Parent objective:** ship v0.14.0 MINOR as the consolidated publish since v0.13.0 of: the keep-pace-with-user MVP (#149-152), FBM Cycle-1 fix-write-path + unify (#154), and the first-run message retired-deps accuracy sweep (#155) — the user-visible thread being "the persona surfaces on-file context instead of forgetting mid-session, and tells a fresh user the truth about what installs."

**Tier-0 corroboration:** every SHA / branch / version claim below was verified this turn (2026-05-29) by `git log` / `git rev-parse` / direct file reads / recomputed SHA-256 / `pytest`.

---

## §1 — Tier-0 verified topology

- Last published tag (Tier-0, `git tag --list 'v0.*' | sort -V | tail -1`): **`v0.13.0`**.
- Worktree HEAD at release-prep: `fab883d` (post-#155-seal + §14 SHA-record + v0.14.0 lockstep/d1/smoke release-prep).
- `#155` seal commit: `e0ff5bd` (deterministic seal; hands-off-lifecycle sidecar advanced to `2a019c3`).
- Version derived at release time per `feedback_version_numbers_at_release_time` from (`current_published = v0.13.0`, `work_class = MINOR`) → **`next_MINOR(v0.13.0) = v0.14.0`**. NOT pre-assigned.

## §2 — What v0.14.0 ships (since v0.13.0)

| Item | Class | Seal | Fence | Notes |
|---|---|---|---|---|
| keep-pace-with-user MVP — KP0 (#149) | feature | `ccfdc22` | hands-off-lifecycle | hook chain wired, fail-open-whole-chain, per-turn latency budget |
| keep-pace MVP — KP5+KP1 (#150) | feature | `aadf2b7` | primary-persona | OBJECTIVES.md register + work-anchored BM25/FTS5 retrieval |
| keep-pace MVP — KP9 (#151) | feature | `6b37490` | hands-off-lifecycle | abstraction-voice lint + draft-vs-active-constraint draft-to-send gate |
| keep-pace MVP — KP7 (#152) | feature | `07d3b59` | orchestrator | SessionStart objective + last-state surface |
| FBM Cycle-1 fix-write-path + unify (#154) | feature | `4b25821` | primary-persona | write-path resolver fix + merge-at-retrieval episode/corpus unify |
| first-run message retired-deps sweep (#155) | PATCH (user-visible) | `e0ff5bd` | hands-off-lifecycle | fresh-start message no longer claims graphiti/neo4j/kuzu install; names file-based memory |

**SemVer judgment: MINOR.** The keep-pace MVP adds new tracked user-visible runtime primitives (work-anchored retrieval + draft-to-send gate + SessionStart objective surface). Per `docs/release-versioning-policy.md`, new user-visible primitives are MINOR-class. The #155 first-run fix alone would be PATCH; composed with the keep-pace MVP + FBM Cycle-1, the release is MINOR.

## §3 — Gate state (this prep)

The `loam release v0.14.0 --dry-run` gates are run from the worktree at release-prep; verdicts are recorded in §13. Two gates are KNOWN-RED-in-worktree by construction and resolve only at the dispatcher's canonical-main publish: `branch-main` (worktree branch is `release/v0-14-0`, not `main`) and `clean-tree` (transient during prep). All other gates are authored to GREEN.

---

## §4 — Acceptance criteria

### AC.REL14.1 — Plan-doc authored
This document exists at `docs/plans/release-integration-v0-14-0.md` with §1–§8 populated and the §2 ship inventory naming all six items + their seals.

### AC.REL14.2 — Lockstep bump applied
All 27 in-scope pyprojects at `version = "0.14.0"`; `docs/ACTIVE_MINOR` content == `0.14.0`; `pytest plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` returns GREEN (5 tests).

### AC.REL14.3 — HARD smoke GREEN
`docs/experiments/release-integration-v0-14-0-hard-smoke.md` authored; cold-clone + spawn-isolated `claude -p` + first-run-message outcome-altitude probe + F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-alongs all GREEN; the writeup carries the `GREEN` aggregate-verdict token.

### AC.REL14.4 — D.1 byte-content GREEN post-bump
The lockstep bump's invalidation of the primary-persona + scope-of-work `pyproject.toml` D.1 frozen SHAs is rebaselined in-band; `pytest framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` returns GREEN (16/16). The recurrence (3rd) is surfaced as a hard F2 + FIDRAFT `F-D1-PYPROJECT-EXCLUDE`.

### AC.REL14.5 — STATE.md backfilled
`docs/STATE.md` change-log carries a `**2026-05-29** — **v0.14.0 MINOR ... SHIPPED**` entry naming the six items + their seals.

### AC.REL14.6 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a `| v0.14.0 |` row whose seal token is reachable from HEAD, and a §3/prose entry recording the publish.

### AC.REL14.7 — README current-release bumped
`README.md` "current public release" line updated `v0.13.0` → `v0.14.0` at the publish.

### AC.REL14.S — Outcome-altitude (first-run message, cold tree)
The HARD smoke's §3 probe invokes the production `_msg_fresh_start` from a cold clone with no pre-arranged state and verifies the actual fresh-user string contains no retired-dep name and names file-based memory. GREEN.

---

## §5 — Publish-gate sequencing (LOCAL vs PUBLIC)

### LOCAL — reversible block (executed autonomously in the worktree)
| # | Step | Reversibility |
|---|---|---|
| L0 | #155 D.1 re-baseline corrective + re-seal + §14 SHA-record | committed; `git revert`-able pre-push |
| L1 | This plan-doc commit | doc-only |
| L2 | Lockstep bump + D.1 pyproject rebaseline + HARD smoke writeup + FIDRAFT (`fab883d`) | doc/version-string; `git revert`-able |
| L3 | STATE.md + release-roadmap + README backfill commit | doc-only |

### PUBLIC — HELD for the dispatcher (NOT executed by this build)
| # | Step | Boundary |
|---|---|---|
| P1 | FF canonical `main` → `release/v0-14-0` + `git push origin main` | PUBLIC — dispatcher executes |
| P2 | annotated tag `v0.14.0` + `git push origin v0.14.0` | PUBLIC — dispatcher executes |

The build STOPS before P1/P2 and returns the exact push commands + the verified-GREEN state for Ren to execute deliberately.

## §6 — Build/execution sequence

1. L0 (DONE) — #155 seal + §14 SHA-record landed (`e0ff5bd`, `b291bdb`).
2. L1 — this plan-doc commit.
3. L2 (DONE) — lockstep bump + D.1 rebaseline + smoke writeup + FIDRAFT (`fab883d`).
4. L3 — STATE.md + roadmap + README backfill commit.
5. Run `loam release v0.14.0 --plan-doc docs/plans/release-integration-v0-14-0.md --dry-run`; record §13 verdicts.
6. STOP. Return the exact P1/P2 push commands to the dispatcher.

## §7 — Out of scope (deferred)

- The `pos-v2` product-name residue in the first-run messages (task #19 proper; a separate rename cycle). Surfaced by the HARD smoke §3 probe; NOT this MINOR's fence.
- The D.1 pyproject-byte-content root-cause structural fix (`F-D1-PYPROJECT-EXCLUDE`) — owed, dispatched as its own PATCH cycle.
- The keep-pace MVP live `~/.claude/settings.json` activation (owner-gated; the staged fragment ships but is not flipped live by this publish).
- Editing `docs/spec/` (objectives spec; outside any cycle's fence).

## §8 — Halt triggers (in-flight)

1. HARD smoke RED on any probe → halt + surface; do NOT proceed to release-prep.
2. Any release gate RED for a reason OTHER than the two known-worktree-RED gates (`branch-main`, `clean-tree`) → halt + surface.
3. The recomputed cli.py / pyproject hashes don't match the sealed files → halt + surface.
4. Any NEW (non-#154) integrity breach surfaced by the seal sweep → halt + surface.
5. NEVER push — the PUBLIC step is the dispatcher's.

---

## §13 — §status (gate verdict matrix, backfilled at prep close)

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL14.1 | GREEN | this doc exists with §1–§8 + the six-item §2 inventory |
| AC.REL14.2 | GREEN | 27 pyprojects at 0.14.0 + ACTIVE_MINOR 0.14.0; lockstep test 5/5 |
| AC.REL14.3 | GREEN | `docs/experiments/release-integration-v0-14-0-hard-smoke.md` aggregate verdict GREEN |
| AC.REL14.4 | GREEN | D.1 byte-content 16/16 post-rebaseline |
| AC.REL14.5 | GREEN | STATE.md change-log v0.14.0 SHIPPED entry (L3) |
| AC.REL14.6 | GREEN | release-roadmap §2 `| v0.14.0 |` row + §3 prose entry (L3); seal token reachable from HEAD |
| AC.REL14.7 | GREEN | README current-release v0.14.0 (L3) |
| AC.REL14.S | GREEN | HARD smoke §3 cold-tree `_msg_fresh_start` outcome-altitude probe GREEN |

---

## §14 — Method-decision record

| Decision | Subject | Ruling | Provenance |
|---|---|---|---|
| D-REL14.WD | Build working directory | release worktree `/Users/lukeivers/loam-release-v0-14-0` | dispatch ruling |
| D-REL14.VERSION | Version literal | `v0.14.0` derived at release-time from (v0.13.0, MINOR) | `feedback_version_numbers_at_release_time` |
| D-REL14.D1-REBASELINE | The 3rd pyproject D.1 drift | in-cycle in-band rebaseline + hard F2 + FIDRAFT `F-D1-PYPROJECT-EXCLUDE` (root-cause fix dispatched separately) | `feedback_workaround_masks_rootcause_urgency` |
| D-REL14.PUBLISH-HELD | Who executes the tag-push | HELD for the dispatcher; build returns the exact commands | dispatch: NEVER push |
