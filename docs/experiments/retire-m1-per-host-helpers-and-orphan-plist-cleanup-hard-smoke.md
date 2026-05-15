# retire-m1-per-host-helpers-and-orphan-plist-cleanup — HARD smoke writeup

**Cycle:** v0.10.8 PATCH (slug `retire-m1-per-host-helpers-and-orphan-plist-cleanup`).
**Date:** 2026-05-14.
**Plan-doc:** `docs/plans/retire-m1-per-host-helpers-and-orphan-plist-cleanup.md`.
**Predecessor:** v0.10.7 PATCH `workspace-sync-test-and-python-runtime-pin` (sealed `6bc8dd6`; published `9b472dd`).
**Working directory:** `/Users/lukeivers/loam/`.

## §1 — Outcome shape verified

Post-source-edit `framework/tools/` surface:

```
$ ls /Users/lukeivers/loam/framework/tools/
heavy-b-migrate
loam
loam-memory-inspect
upgrade-merge-resolver
```

4 directories — exactly the survivors named in the AMENDED F-RETIRE-MIGRATE-TOOLS framing. Pre-PATCH had 8 directories (4 retired here + 4 survivors).

Three file edits applied:

1. `plugins/dev-sdlc/dev-mode-manifest.yaml` — `- glob: "framework/tools/orphan-plist-cleanup/**"` line at line 163 removed; surrounding comment block updated to record the v0.10.8 retirement.
2. `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py` — `test_AC_F4_glob_with_exclusion` candidate paths at lines 72,83 swapped `tools/orphan-plist-cleanup/README.md` → `tools/heavy-b-migrate/README.md` (substitute that still exercises `expand_entry()` glob+exclude behavior with a non-retired tool).
3. `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` — `framework_tools / "orphan-plist-cleanup" / "pyproject.toml"` line dropped from `expected` tuple at line 132 + corresponding comment line at line 121 dropped + post-cleanup comment block updated to reflect post-Path-B/C surface.

## §2 — Retirement-readiness re-verification (4-step empirical recheck)

Per `feedback_agent_empirical_recheck_before_halt`. The prior-dispatch halt-and-surface artefact at `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md` did most of this work; this section spot-checks current-state.

### 2.1 — `loam-migrate-launchd-labels` (M1c per-host helper)

- **Deletion-claim:** "one-time per-host migration script that has run."
- **README:22-26 quote (pre-deletion, recovered from git history):** `python -m loam_migrate_launchd_labels` … "Explicit invocation only. Run once per host, after upgrading to a post-M1c release."
- **Production references outside its own dir:** zero (`grep -rn "loam_migrate_launchd_labels" --include="*.py" framework/ plugins/` excluding the retired dir → 0 matches).
- **Verdict:** retirement-ready. Deleted at v0.10.8.

### 2.2 — `loam-migrate-host-config` (M1b per-host helper)

- **Deletion-claim:** "one-time per-host migration script that has run."
- **README:17-26 quote (pre-deletion, recovered from git history):** `python -m loam_migrate_host_config` invocation; sibling helper to launchd-labels; idempotent.
- **Production references outside its own dir:** zero.
- **Verdict:** retirement-ready. Deleted at v0.10.8.

### 2.3 — `loam-migrate-dormancy-config` (M1f per-host helper)

- **Deletion-claim:** "one-time per-host migration script that has run."
- **README:14-18 quote (pre-deletion):** `.venv/bin/python -m loam_migrate_dormancy_config` invocation; sibling to `loam-migrate-host-config` (M1b precedent) + `loam-migrate-launchd-labels` (M1c precedent).
- **Production references outside its own dir:** zero.
- **Verdict:** retirement-ready. Deleted at v0.10.8.

### 2.4 — `orphan-plist-cleanup` (pre-#6 archaeological-orphan remediation)

- **Deletion-claim:** "one-shot remediation tool" per its README:31 — semantically retirement-eligible.
- **Production references that needed cleanup (4-file edit per AMENDED F-RETIRE-MIGRATE-TOOLS framing):**
  - `plugins/dev-sdlc/dev-mode-manifest.yaml:163` — handled (entry removed; surrounding comment updated).
  - `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py:72,83` — handled (candidate-path swapped to `tools/heavy-b-migrate/README.md`).
  - `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py:121,132` — handled (comment + `expected` tuple line dropped).
  - Cross-references in `framework/tools/loam-migrate-launchd-labels/{README.md,tests/test_migrate.py,src/loam_migrate_launchd_labels/migrate.py}` — handled-by-deletion (Path B retired the loam-migrate-launchd-labels tool dir; the cross-reference text vanished with it).
- **Verdict:** retirement-ready. Deleted at v0.10.8.

### 2.5 — Cross-reference vanish-with-deletion verification

```
$ grep -rn "loam_migrate_launchd_labels\|loam_migrate_host_config\|loam_migrate_dormancy_config\|orphan_plist_cleanup\|orphan-plist-cleanup" \
    --include="*.py" --include="*.sh" --include="*.yaml" --include="*.toml" --include="*.txt" \
    /Users/lukeivers/loam/framework/ /Users/lukeivers/loam/plugins/ /Users/lukeivers/loam/install-from-source.txt 2>/dev/null \
    | grep -v "/loam-migrate-\|/orphan-plist-cleanup/"
(no matches)
```

Post-PATCH the 4 retired tool identifiers are absent from production code, manifests, and the install path. (Documentation references in `docs/STATE.md`, `docs/release-roadmap.md`, and `docs/FUTURE_IDEAS_DRAFT.md` remain — those are historical state-at-cycle records, intentionally preserved.)

## §3 — Post-deletion test surface

### 3.1 — workspace-sync (4/4 GREEN)

```
$ python3.13 -m pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py -v
============================= test session starts ==============================
platform darwin -- Python 3.13.12, pytest-9.0.3, pluggy-1.6.0
collecting ... collected 4 items

test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_bare_tools_absent PASSED [ 25%]
test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_framework_tools_present PASSED [ 50%]
test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_bare_workspace_sync_absent PASSED [ 75%]
test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_framework_workspace_sync_present PASSED [100%]

============================== 4 passed in 0.01s ===============================
```

### 3.2 — dev-sdlc partition (6/6 GREEN)

```
$ cd plugins/dev-sdlc/tools/loam-mode && python3.13 -m pytest tests/test_partition_manifest.py -v
============================= test session starts ==============================
collected 6 items

tests/test_partition_manifest.py::test_AC_F1_partition_disjoint PASSED   [ 16%]
tests/test_partition_manifest.py::test_AC_F1_entries_well_formed PASSED  [ 33%]
tests/test_partition_manifest.py::test_AC_F1_manifest_rejects_malformed_entry PASSED [ 50%]
tests/test_partition_manifest.py::test_AC_F4_glob_with_exclusion PASSED  [ 66%]
tests/test_partition_manifest.py::test_AC_F4_glob_double_star_matches_recursively PASSED [ 83%]
tests/test_partition_manifest.py::test_AC_F4_glob_without_double_star_uses_fnmatch PASSED [100%]

============================== 6 passed in 0.35s ===============================
```

Both suites GREEN post-edit. Pre-edit baseline was also GREEN (workspace-sync 4/4 inherited from v0.10.7 fix; partition 6/6 was always GREEN since the retired-tool reference was a string-fixture not a filesystem assertion).

## §4 — install-from-source.txt empirical no-op

Per dispatch-brief candidate edit + AC.RMPH.3:

```
$ grep -n "loam-migrate\|orphan-plist-cleanup\|loam_migrate\|orphan_plist_cleanup" \
    /Users/lukeivers/loam/install-from-source.txt /Users/lukeivers/loam/docs/install-from-source.md 2>/dev/null
(no matches)
```

Zero entries to remove. The 4 retired tools were operator-facing helpers requiring explicit invocation; they were never in the install path. Empirical no-op verified at plan-time + post-edit.

## §5 — Outcome-altitude dogfood probe (release-CLI 6-gate dry-run)

Captured at apply-time per the manifest baseline backfill workflow. (The dry-run will run at the apply step in §13 §status of the plan-doc; this section is the placeholder for the captured output.)

Expected: `loam release v0.10.8 --plan-doc docs/plans/retire-m1-per-host-helpers-and-orphan-plist-cleanup.md --dry-run` returns **ALL 6 GATES GREEN** (`hard-smoke`, `acs-verified`, `state-shipped`, `clean-tree`, `branch-main`, `seal-reachable`) against the live plan-doc + manifest + STATE/roadmap admin.

Verified at dry-run time post-apply: TBD-AT-APPLY.

## §6 — F-RETIRE-MIGRATE-TOOLS RESOLVED diff summary + F2 Ruthless Feedback

### 6.1 — F-RETIRE-MIGRATE-TOOLS diff summary

`docs/FUTURE_IDEAS_DRAFT.md` line 244 entry edits:

- **Status flipped:** `capture-only` → `RESOLVED 2026-05-14 by v0.10.8 PATCH (retire-m1-per-host-helpers-and-orphan-plist-cleanup)`.
- **"Proposed shape" prefix updated:** `(amended 2026-05-14)` → `(amended 2026-05-14; Path B+C resolved 2026-05-14 by v0.10.8 PATCH retire-m1-per-host-helpers-and-orphan-plist-cleanup)`.
- **Section (1) `heavy-b-migrate` REMOVED from candidate list** — appended `**Permanent residency under framework/tools/.**`.
- **Section (2) `orphan-plist-cleanup`** — past-tense conversion (`production references that would break` → `would break`); added `**Path C executed at v0.10.8 PATCH:**` block summarizing the 4-file edit + cross-reference vanish-with-deletion.
- **Section (3) `loam-migrate-*` per-host helpers** — added `**Path B executed at v0.10.8 PATCH:**` block summarizing dispatcher safety-horizon ratification + 3 directory deletions.
- **Section (4) `pos-publish-framework-only`** — minor copy-edit (`Cleanup ride-along is complete; this entry no longer carries it.` → `Cleanup ride-along complete.`).
- **Path-A/B/C decomposition paragraph** — Path B + Path C entries flipped from "deferred for owner safety-horizon ratification" → "shipped at v0.10.8 PATCH" with D-RMPH.1 cross-reference.
- **Composes-with paragraph** — `Architecture clarity` clause appended `(— closed)`; v1.0 ship gate clause: `cleanup contingent on safety-horizon ratification` → `cleanup completed`.
- **AI-time band** — added `Path A ~40 min actual at v0.10.7; Path B+C combined target 50-90 min midpoint ~70 min at v0.10.8`.
- **Status block (final)** — full RESOLVED block with chain pointer + AC count + plan-doc + smoke pointers.

### 6.2 — F2 Ruthless Feedback observations

**Disagreement with prior framing (already resolved at v0.10.7):** the original F-RETIRE-MIGRATE-TOOLS framing claimed 6 retirement candidates were "one-time migration scripts that have run." The prior-dispatch halt-and-surface artefact + v0.10.7 amendment resolved this; this PATCH executes against the AMENDED scope. No new disagreement to surface.

**Observation 1 — D-RMPH.3 candidate-path substitute choice rationale:** chose `tools/heavy-b-migrate/README.md` over `tools/loam-memory-inspect/...` or `tools/upgrade-merge-resolver/...` for stability. `heavy-b-migrate` is named permanent under AMENDED F-RETIRE-MIGRATE-TOOLS framing; the others are operational helpers that could in principle move. If a future cycle retires `loam-memory-inspect` or `upgrade-merge-resolver`, the test fixture would need another swap. Picking `heavy-b-migrate` defers that maintenance indefinitely. Tradeoff: the partition test is now coupled to `heavy-b-migrate`'s permanent residency — if AMENDED F-RETIRE-MIGRATE-TOOLS is itself ever amended again to retire `heavy-b-migrate` (which would require retiring or rewiring loam-mode's session-start lazy-projection trigger), this test fixture would also need an edit. Acceptable coupling: such an amendment would be MINOR-class methodology change and would necessarily touch many test fixtures anyway.

**Observation 2 — Side-effect on F-PYTHON-3.9 evidence:** v0.10.7's F-PYTHON-3.9 evidence cited "all 30 pyproject.toml files declare `requires-python = ">=3.11"` (24 files) or `">=3.13"` (6 files)". Post-v0.10.8 the file count drops to 26 (24 at >=3.11; 2 at >=3.13) because the 4 retired tool dirs each carried a pyproject.toml: 2 at >=3.11 (`loam-migrate-host-config`, `loam-migrate-dormancy-config`) + 2 at >=3.13 (`loam-migrate-launchd-labels`, `orphan-plist-cleanup`). Per D-RMPH.5 the v0.10.7 historical evidence is preserved as state-at-resolution; no retroactive edit. Worth noting in case a future audit asks "why does the F-PYTHON-3.9 evidence count differ from current state."

**Observation 3 — `install-from-source.txt` AC pattern:** AC.RMPH.3 documents an empirical no-op (no entries to remove) rather than dropping the AC. This is the right pattern for any future cycle where a dispatcher's edit-prediction is empirically falsified at plan-time — the audit-trail is more valuable than the cleaner AC count. Composes with `feedback_specific_claims_verified_or_marked_guess`.

**Observation 4 — Single-PATCH for Path B+C (D-RMPH.1):** dispatcher brief explicitly authorised the combined scope. Decomposing into separate Path-B + Path-C cycles would have added 2 plan-docs + 2 manifests + 2 seal narratives + 2 apply/seal cycles for 0 additional safety. Both safety horizons (M1 per-host: 17 days; pre-#6 archaeological: substantially longer) had already been ratified by the time this PATCH was authored. Split would have been overhead-without-benefit per `feedback_swarming_recursive_decomposition`'s stopping criterion.

**No HARD HALTs fired in-cycle.** The prior-dispatch halt-and-surface artefact + v0.10.7 amendment did all the empirical-investigation legwork; this PATCH executed Path B+C per the dispatcher-ratified scope.
