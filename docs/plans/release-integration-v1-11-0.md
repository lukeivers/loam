# Release Integration — v1.11.0 (memory write-side facts-discipline + recall volume-limits reshape + capability-refresh model-extractor robustness)

**Version:** v1.11.0 (MINOR over published v1.10.0). **Class:** MIXED.
**WD:** `/Users/lukeivers/loam` (canonical single-writer this cycle).
**Status target:** SEALED-LOCAL + HARD-smoke-GREEN + `loam release v1.11.0 --dry-run` all-gates-GREEN, then STOP. **The public tag + push + GitHub Release is the owner's command to run — NOT pushed by this cycle** (`feedback_no_public_action_during_build`).
**Authority:** `docs/release-process.md` (runbook) + `docs/release-versioning-policy.md` (SemVer commitment) + this doc's §4/§13.

---

## 1. Objective

**v1.11.0 hardens loam's per-user memory substrate and keeps its model-lineup tracking honest: the scored recall path is bounded only by relevance and attention — the count caps that silently starved relevant memories are retired — the memory write path records facts under a discipline that curbs confidently-wrong entries, and the automated capability-refresh again detects every live Claude model after an upstream table-formatting change had left it under-reporting the lineup.**

The objective sentence DESCRIBES the whole cut; it does not gate a split. Per the deterministic-cut rule (§3, folded into policy this cycle as AC.REL.9), a release cut is all unreleased seals at release time minus only explicitly owner-held items; "how many versions / which grouping" is never a decision to surface.

**Class — MIXED (per `docs/release-versioning-policy.md` §quality-gate).**

- **END-USER portion (named user-visible delta):** the memory recall + write changes alter what the user actually experiences of loam's memory. The user's relevant stored memories are recalled without being silently truncated by an internal count cap — the scored recall path is now bounded only by a relevance floor (quality) and a byte budget (attention), matching the human-memory north star (`docs/design/keep-pace-with-user.md`) — and the write path records facts under a discipline that reduces confidently-wrong entries. This is protection-floor advancement against the Lens-0 "no real memory" betrayal (inventing/losing facts), and it is user-experienced, not merely internal coherence.
- **Foundational portion (rationale + why-now):** the capability-refresh model-extractor robustness fix is internal accuracy of the automated model-lineup tracking. An upstream "Latest models comparison" table reformatted most Claude-API-IDs from backticked to plain text, so the backtick-only extractor under-detected live models and faked add/remove deltas. It is foundational because the model-lineup artifact feeds model-selection surfaces; those surfaces are only correct if the lineup is complete. Why now: it ships unreleased and the deterministic cut takes all unreleased seals — and a wrong lineup silently degrades every downstream model-selection decision until corrected.

---

## 2. What is unpublished (verified from git refs — Tier-0)

Three LOCAL branches carry sealed-but-unreleased cycles; all base at merge-base `a1166b8` and main has advanced **7 commits** past that base (via PR #3, whose merge landed a *separate* capability-refresh seal, #194 run-cadence bash-portability). Consequently **none of the three is fast-forwardable onto main**, and `fix/capability-refresh-model-extractor-robust` conflicts with main on `framework/tools/capability-refresh/tests/SEAL_COMMIT` (two independent seals from one baseline diverge on the sidecar). This falsified the original dispatch premise ("all three conflict-free / fast-forwardable"); the dispatcher ratified reconciliation by **re-apply/re-seal against current main baseline** (the S1a precedent, `docs/STATE.md` 2026-07-07) instead of fast-forward. main's tip `75adf102` is itself a PR merge commit (parents `a1166b8` + `783d0d3c`); acknowledged, published, not unwound.

| Branch (source-of-record) | Component fence | Feature ACs (sealed) | Reconciled seal window |
|---|---|---|---|
| `fix/capability-refresh-model-extractor-robust` | `capability-refresh` (existing) | `AC.CLP-MDLR.1-5` | re-baselined onto current main |
| `build/memory-write-side` | `primary-persona` (existing) | `AC.WFD.1-9` (WFD.6 outcome-altitude) | re-baselined onto cap-refresh seal |
| `build/recall-volume-cycle1` (stacks on write-side) | `primary-persona` (existing) + `plugins/dev-sdlc/docs/` admit | `AC.RVL.1-9` | re-baselined onto write-side seal |

Already on `main` since v1.10.0 and riding automatically: memory S1a ground-floor extraction, standing-retrieval-telemetry, S2 ranker, S4 rules-store + situational recall; capability-refresh Actions-cadence migration + the #194 zsh→bash portability fix.

**HELD OUT — owner gate, NOT in this cut:** `build/memory-redesign-s1b-safe-populate` (S1b — owner ruled revise-first). The only subtraction.

The feature ACs above are sealed + verified in each cycle's own sub-plan §status/§14 register; they are DISTINCT from this doc's `AC.REL.*` gate ladder (§4/§13).

---

## 3. Version decision — v1.11.0, single MINOR release (SemVer derivation)

```
current_published (highest tag on ORIGIN) = v1.10.0
  [git ls-remote --tags origin | grep -oE 'v[0-9.]+' | sort -V | tail -1]
HEAD == origin/main                        = 75adf102   (no local-but-unpushed tag; recipe unambiguous)
breaking markers in v1.10.0..<cut union>   = NONE
  [git log --format=%s v1.10.0..<each branch> | grep -iE 'breaking|!:' -> empty on all three]
new backwards-compatible capability present = YES
  [feat commits present: AC.WFD.*, AC.RVL.*, AC.CLP-MDLR.*]
=> class = MINOR (not MAJOR: zero breaking; not PATCH: new capability)
=> bump_minor(v1.10.0) = v1.11.0, ONE release.
```

If any of the above had contradicted (a breaking change surfaced, or class resolved ≠ MINOR), that is a HALT-and-surface trigger, not a silent re-number. It did not; the determination holds and is fixed (dispatcher-ruled) — not re-opened.

**Deterministic-cut rule (folded into `docs/release-versioning-policy.md` + `docs/release-process.md` this cycle — AC.REL.9):**

> A release cut = all unreleased seals at release time (main + merging branches) minus only explicitly owner-held items; SemVer class from content (breaking→MAJOR, else any new backwards-compatible capability→MINOR, else PATCH); number = bump(current_published_on_origin, class); ALWAYS one version per cut; the objective sentence describes the cut and never drives a split; "how many versions / which grouping" is never a decision to surface.

---

## 4. Build + release steps

1. **Reconcile the three cycles (re-apply/re-seal, dependency order).** For each of `capability-refresh` (model-extractor) → `write-side` → `recall-volume` (recall already contains write-side): restore the amendment's plan + manifest + source/test files from its source-of-record branch onto current HEAD, retarget the manifest `baseline:` to the pre-plan HEAD, commit plan+manifest then source+test, then `loam amend validate` → `loam amend apply` → `loam amend seal`. Each regenerated seal is HEAD-reachable; each fence window (`BASELINE..SEAL_COMMIT`) contains only that amendment's own delta. Original branches preserved as source-of-record; stale-SHA bookkeeping commits skipped.
2. **Lockstep version bump.** `docs/ACTIVE_MINOR` 1.10.0 → 1.11.0; the in-scope `pyproject.toml` version fields + the `loam_cli __version__` literal (`loam --version`) fold to 1.11.0; `test_AC_PCVR_pyproject_version_lockstep` GREEN. New out-of-graph components (if any) ride at their own 0.x, excluded from the in-scope set.
3. **State-migration doc.** `docs/state-migrations/v1-11-0-*.migration.yaml` — verify whether no-op; declare explicitly.
4. **HARD smoke (per-minor gate).** `docs/experiments/v1-11-0-hard-smoke.md` — cold-clone/cold-install + a REAL spawn-isolated `claude -p` exercise + an outcome-altitude fixture exercising the new recall behavior + touched-component regression + the F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN ride-along checks + the gate-7 `which loam` / `loam --help` evidence; literal `GREEN` verdict token.
5. **Backfill state.** `docs/STATE.md` SHIPPED-LOCAL change-log entry + `docs/release-roadmap.md` §3 SHIPPED-LOCAL entry + the §2 seal-row (seal SHA reachable from HEAD, read by gate-6).
6. **Deterministic-cut doc-fix.** Add the §3 rule verbatim to BOTH `docs/release-versioning-policy.md` AND `docs/release-process.md` under a "No grouping discretion — deterministic cut rule" clause (AC.REL.9).
7. **Dry-run.** `loam release v1.11.0 --dry-run`; confirm 7 gates GREEN (gate-4 clean-tree may RED on the two pre-existing untracked `docs/plans/per-session-resume-handoff.*` files — NOT this cut; that RED is expected + dispatcher-handled; all OTHER gates GREEN is the bar). STOP before push.

## 5. Pre-publish gates (enforced by `loam release`)

The seven gates per `docs/release-process.md` §1: hard-smoke, acs-verified, state-shipped, clean-tree, branch-main, seal-reachable, system-binary-operational. `--dry-run` runs the full set without acting. Publish (tag/push/`gh release`) is the dispatcher's owner-authorized action, never this cycle's.

---

## §4 — Acceptance criteria

These `AC.REL.*` criteria are the release-integration gate ladder; the `acs-verified` gate reads their §status verdicts from §13. They are DISTINCT from the per-cycle feature ACs (`AC.CLP-MDLR.*` / `AC.WFD.*` / `AC.RVL.*`), which are sealed + verified in each cycle's own sub-plan §status/§14 register.

### AC.REL.1 — Plan-doc authored
This doc exists at a version-slug-resolvable path (`docs/plans/release-integration-v1-11-0.md`, resolved by the release-side fallback in `gates.py`) with §1 objective + §2 inventory + §3 SemVer derivation + §4 ACs + §13 §status, so the `acs-verified` + `hard-smoke` gates resolve it with NO `--plan-doc` flag.

### AC.REL.2 — Three unreleased cycles reconciled onto main
The three sealed cycles (`AC.CLP-MDLR.*`, `AC.WFD.*`, `AC.RVL.*`) land on `main` via re-apply/re-seal against the current main baseline (dependency order cap-refresh → write-side → recall-volume). Each regenerated seal commit is reachable from HEAD; each component seal-test (`test_no_sealed_amendments.py`) passes with a fence window (`BASELINE..SEAL_COMMIT`) containing only that amendment's own delta; the original branches are preserved unchanged as source-of-record.

### AC.REL.3 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.10.0 → 1.11.0; the in-scope `pyproject.toml` version fields bump to 1.11.0; the meta `loam --version` literal folds in (`loam --version` → `1.11.0`); `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` stays GREEN. Any new out-of-graph component rides at its own 0.x, EXCLUDED from the in-scope set.

### AC.REL.4 — HARD smoke GREEN (the per-minor gate)
`docs/experiments/v1-11-0-hard-smoke.md` authored; REAL cold-clone of the release HEAD + REAL editable install with no Anthropic API key + spawn-isolated `claude -p` (scrubbed `ANTHROPIC_API_KEY` / `TELEGRAM_BOT_TOKEN` / `DISCORD_BOT_TOKEN`, `--strict-mcp-config`) + the outcome-altitude recall fixture (AC.REL.S) + touched-component regression ride-alongs + the F-LEAK / F-TIMEOUT / F-VERIFY-ORPHAN checks; the writeup carries the `GREEN` aggregate-verdict token + the gate-7 `which loam` / `loam --help` evidence.

### AC.REL.5 — Touched component suites GREEN (cold install)
The touched-component suites — `capability-refresh` + `primary-persona` — pass in the cold-installed release tree, evidenced in the HARD smoke writeup.

### AC.REL.6 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` carries a `**v1.11.0 MIXED SHIPPED LOCAL**` change-log entry naming the objective, the class, the three reconciled cycles + their reconciled SHAs, the lockstep bump, the migration verdict, and the HARD smoke path.

### AC.REL.7 — release-roadmap.md backfilled
`docs/release-roadmap.md` §2 carries a v1.11.0 row whose right column records the reconciled seal SHAs (the final content-tip seal reachable from HEAD, read by gate-6 `seal-reachable`); §3 Active-version carries a SHIPPED-LOCAL entry.

### AC.REL.8 — Migration declared
`docs/state-migrations/v1-11-0-*.migration.yaml` exists and explicitly declares the migration verdict (expected `no-op`; declared, not assumed).

### AC.REL.9 — Deterministic-cut clause folded into policy (root-cause fix)
The verbatim "No grouping discretion — deterministic cut rule" clause (§3) is added to BOTH `docs/release-versioning-policy.md` AND `docs/release-process.md`, so the grouping-discretion question is closed at the doc layer, not re-litigated per cut.

### AC.REL.S — Outcome-altitude (production entry-points, no pre-set state)
Two production entry-points are exercised with no pre-set release state: (1) a spawn-isolated `claude -p` run against the cold-installed tree reproduces the new recall behavior (the count cap no longer truncates a relevant-memory set below the relevance floor), evidenced in the HARD smoke writeup; and (2) `loam release v1.11.0 --dry-run` runs the real 7-gate release CLI and reports every structural gate GREEN (the pre-existing untracked-file clean-tree RED excepted + dispatcher-handled).

---

## §13 — §status (gate verdict matrix)

The `loam release v1.11.0 --dry-run` `acs-verified` gate reads these verdicts. Filled GREEN as each AC is verified during the cycle; a RED here blocks the dry-run's `acs-verified` gate.

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL.1 | GREEN | this doc at `docs/plans/release-integration-v1-11-0.md` (resolved by the release-side fallback in `gates.py`) |
| AC.REL.2 | GREEN | four fences reconciled (§14); each `test_no_sealed_amendments.py` passes with window = own delta; seals `f2d88060` / `c9c94f0d` / `2cd8b714` / `badd2d6f` HEAD-reachable; original branches source-of-record |
| AC.REL.3 | GREEN | lockstep bump `4a86b816` (ACTIVE_MINOR 1.11.0 + 31 pyprojects + `loam --version`→1.11.0); `test_AC_PCVR_pyproject_version_lockstep` 5 passed |
| AC.REL.4 | GREEN | `docs/experiments/v1-11-0-hard-smoke.md` carries the `GREEN` token + gate-7 evidence |
| AC.REL.5 | GREEN | cold-tree suites: capability-refresh 46, primary-persona green (exit 0), dev-sdlc 399/7-skip (HARD smoke §3) |
| AC.REL.6 | GREEN | `docs/STATE.md` `**v1.11.0 MIXED MINOR SHIPPED LOCAL**` change-log entry |
| AC.REL.7 | GREEN | `docs/release-roadmap.md` §2 seal-row (final seal reachable from HEAD) + §3 SHIPPED-LOCAL entry |
| AC.REL.8 | GREEN | `docs/state-migrations/v1-11-0-memory-substrate-and-model-extractor.migration.yaml` (`operation: no-op`) |
| AC.REL.9 | GREEN | "No grouping discretion" clause verbatim in `docs/release-versioning-policy.md` + `docs/release-process.md` (`979e9341`) |
| AC.REL.S | GREEN | HARD smoke §4 (real spawn-isolated `claude -p` → `SMOKE_OK_V1110`, rc 0) + §5 (AC.RVL.7 production retrieve, floor over count) + `loam release v1.11.0 --dry-run` all structural gates GREEN (clean-tree RED excepted, dispatcher-handled) |

**Cross-component collision (surfaced by the HARD smoke, resolved this cut):** recall's required AC.RVL.8 cap-bias checklist grew `odd-methodology.md` 360→373, colliding with dev-sdlc's `AC.KDOC.1` ≤360 guard. Dispatcher-ruled resolution: a **4th dev-sdlc fence** (`docs/plans/dev-sdlc-kdoc-methodology-line-budget-raise.md`, **AC.MSLB.1**) raising the guard 360→380 per `feedback_loose_AC_text_fix_AC_not_implementation`. Its own §status is GREEN in that sub-plan; it joins this cut as required-to-ship-recall.

## §14 — reconciled SHA register (backfilled at cycle close)

Release plan-doc commit: `7eb8f982`. Reconciled cycles (dependency order):

- capability-refresh (model-extractor, AC.CLP-MDLR.1-5): plan+manifest `ef8e4cd5` · source `927639ac` · apply `4cd0b821` · seal `f2d88060` (BASELINE `7eb8f982`)
- write-side (facts-discipline, AC.WFD.1-9): plan+manifest+source `6d0e20a5` (combined — branch checkout pre-staged source; fence window clean, no history surgery) · apply `fb0cf1f2` · seal `c9c94f0d` (BASELINE `f2d88060`)
- recall-volume (cycle 1, AC.RVL.1-9): plan+manifest `0f19525a` · source `ec9dd982` · apply `c17fb90` · seal `2cd8b714` (BASELINE `c9c94f0d`)
- dev-sdlc KDOC line-budget raise (AC.MSLB.1, 4th fence — collision resolution): plan+manifest `8919a713` · tests `4094467b` · apply `20700c2` · seal `badd2d6f` (BASELINE `dd25353a`)
- release-prep: lockstep bump `4a86b816` · migration + doc-fix `979e9341` · STATE/roadmap `dd25353a` · HARD smoke + §status backfill (this commit).
- **final content-tip seal (gate-6 reads a reachable seal from roadmap §2):** `badd2d6f` (dev-sdlc) is the latest; `2cd8b714` / `c9c94f0d` / `f2d88060` are all HEAD-reachable.
