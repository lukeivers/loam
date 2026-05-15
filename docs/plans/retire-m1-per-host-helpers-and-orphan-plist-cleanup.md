# Retire M1 per-host helpers + orphan-plist-cleanup PATCH

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code`. Owner ratification: dispatcher brief 2026-05-14 explicitly authorises Path B+C closure of F-RETIRE-MIGRATE-TOOLS per the prior-dispatch (`retire-one-time-migration-tools`) halt-and-surface evidence at `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md` AND the v0.10.7 framing amendment that re-decomposed F-RETIRE-MIGRATE-TOOLS into Path A (shipped v0.10.7) + Path B (3 `loam-migrate-*` per-host helpers) + Path C (`orphan-plist-cleanup` 4-file edit) + NOT-RECOMMENDED `heavy-b-migrate` (load-bearing continuous trigger; explicitly out-of-scope).
**Slug:** `retire-m1-per-host-helpers-and-orphan-plist-cleanup` (scope-descriptive; no version pre-baked per `feedback_version_numbers_at_release_time`).
**Date authored:** 2026-05-14.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. Internal cleanup — retiring 3 per-host migration helpers + 1 archaeological-orphan remediation tool whose semantic-passed safety horizons the dispatcher explicitly ratified. No public-API change (the 4 retired tools were never user-facing primitives — migration helpers + orphan cleanup, not loam-CLI surfaces). No outcome-shape addition.
**Predecessor:** v0.10.7 PATCH SHIPPED PUBLIC (sealed `6bc8dd6`; published `9b472dd`). Build-forward per `feedback_build_forward_on_publish_pending`.
**Working directory:** `/Users/lukeivers/loam/`.
**Version derivation:** at release-time per `feedback_version_numbers_at_release_time`: `next_PATCH(v0.10.7) = v0.10.8`. Plan-doc slug scope-descriptive; AC family scope-descriptive (`AC.RMPH.*` for `retire-m1-per-host-helpers-...`).

---

## §1 — Outcome shape (the "why")

The v0.10.7 PATCH amended F-RETIRE-MIGRATE-TOOLS framing per prior-dispatch halt-and-surface evidence. The amended entry now explicitly decomposes the retirement scope into three paths:

- **Path A (shipped v0.10.7):** F-TF-1 stale-path test fix + F-PYTHON-3.9 RESOLVED-BY-INSPECTION + F-RETIRE-MIGRATE-TOOLS framing correction. Done.
- **Path B (this PATCH):** retire 3 `loam-migrate-*` per-host helpers (`loam-migrate-launchd-labels`, `loam-migrate-host-config`, `loam-migrate-dormancy-config`).
- **Path C (this PATCH):** retire `orphan-plist-cleanup` (the 4-file edit).
- **NOT in scope:** `heavy-b-migrate` (load-bearing continuous trigger per `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/session_start.py:283-299`; retiring it would silently break the dev-discipline contract for new dev-intent workspaces). `pos-publish-framework-only` (already retired; F-TF-1 closure at v0.10.7 closed the residual stale assertion).

The dispatcher's safety-horizon ratification: M1 series shipped 2026-04-29 (~17 days ago); idempotent design with case-2 no-op + case-4 conflict-halt contracts; production hosts have had ~daily session-start triggers since; no fresh-install dependency (these are migration helpers, not new-install requirements). Empirical safety horizon passed for both the M1 per-host helpers AND the pre-#6 archaeological-orphan remediation surface.

After this PATCH:

1. `framework/tools/loam-migrate-launchd-labels/`, `framework/tools/loam-migrate-host-config/`, `framework/tools/loam-migrate-dormancy-config/`, `framework/tools/orphan-plist-cleanup/` directories are deleted (4 tool dirs total; `ls framework/tools/` returns 4 entries: `heavy-b-migrate`, `loam`, `loam-memory-inspect`, `upgrade-merge-resolver`).
2. `plugins/dev-sdlc/dev-mode-manifest.yaml:163` orphan-plist-cleanup glob entry removed; surrounding comment updated.
3. `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py:72,83` candidate paths swapped to a non-retired tool (substitute candidate path that still exercises the same `expand_entry()` exclusion behavior).
4. `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py:121,132` — drop the `framework/tools/orphan-plist-cleanup/` comment + `expected` tuple line; comment updated to reflect the post-Path-B/C surface.
5. `install-from-source.txt` — empirical recheck shows NONE of the 4 retired tool directories appear in `install-from-source.txt`, so no entries to remove (the file was already minimal-by-design; helpers were never in the install path).
6. `docs/install-from-source.md` — same: no references to the 4 retired tools.
7. F-RETIRE-MIGRATE-TOOLS FIDRAFT entry STATUS flipped from `capture-only` → RESOLVED with chain pointer (Path A in v0.10.7 + Path B+C in this PATCH).
8. STATE.md + release-roadmap.md updated with v0.10.8 row.
9. All affected test suites GREEN post-deletion (workspace-sync 4/4 + dev-sdlc partition 6/6 + dev-sdlc plugin-fence test bumped via apply/seal workflow).

Composes with: prior-dispatch halt-and-surface (the empirical-investigation legwork this PATCH builds on); v0.10.7 PATCH (the framing amendment that decomposed the scope into Paths A/B/C/NOT-RECOMMENDED); `feedback_agent_empirical_recheck_before_halt` (re-verified retirement-readiness for each of the 4 tools at plan-time per the rule); `feedback_locked_design_not_license_for_bad_outcomes` (M1 helpers' "ship them once per host" framing was the locked design; the safety horizon makes deletion the right outcome now); `F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH` (Path B+C completes the retirement scope; FIDRAFT entry flips to RESOLVED in same source-edit per the discipline); `F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE` (this plan-doc pre-includes `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` in AC.RMPH.S allow-list); `F-PLAN-DOC-TEMPLATE-§13-STATUS-HEADING` (this plan-doc pre-includes `## §13 — §status` heading per the convention captured 2026-05-15).

---

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ documented features work as advertised + documented-state
           matches actual-state (v1.0 quality-bar criterion #1)
             └─ `framework/tools/` surface contains only tools that
                are user-facing primitives or load-bearing continuous
                triggers (NOT one-shot migration helpers whose safety
                horizons have empirically passed); FIDRAFT entries
                whose retirement-eligibility ratification has landed
                flip to RESOLVED in the same commit
                  └─ AC.RMPH.1 (3 `loam-migrate-*` tool directories
                                  deleted; sibling cross-references
                                  vanish with them)
                  └─ AC.RMPH.2 (`orphan-plist-cleanup` tool directory
                                  deleted; dev-mode-manifest entry
                                  removed; partition-test candidate
                                  paths swapped; workspace-sync test
                                  counterpart-list updated)
                  └─ AC.RMPH.3 (install-from-source.txt unchanged —
                                  empirical recheck confirms none of
                                  the 4 retired tools appeared in
                                  the install path; the AC documents
                                  the empirical no-op for audit-trail)
                  └─ AC.RMPH.4 (post-retirement test surface — affected
                                  test suites GREEN: workspace-sync
                                  4/4 + dev-sdlc partition 6/6)
                  └─ AC.RMPH.5 (outcome-altitude dogfood probe —
                                  smoke writeup confirms retired
                                  tools absent from `framework/tools/`
                                  + all affected suites GREEN +
                                  release-CLI 6-gate dry-run GREEN)
                  └─ AC.RMPH.6 (F-RETIRE-MIGRATE-TOOLS FIDRAFT entry
                                  STATUS flipped to RESOLVED with
                                  chain pointer Path A v0.10.7 +
                                  Path B+C this PATCH)
                  └─ AC.RMPH.S (seal-diff: only the 4 retired tool
                                  directory deletions + the named
                                  test/manifest files + plan-doc/
                                  manifest/smoke + STATE/roadmap
                                  admin + dev-sdlc seal anchor
                                  artefacts touched)
```

The two VALUE_PROPOSITION tests:

- **Primary-persona test** — fewer migration-helper directories under `framework/tools/` reduces the translation burden the persona pays at every cycle dispatch ("is this tool current or archaeology?"). After this PATCH, every directory under `framework/tools/` is either a user-facing primitive (`loam`) or a load-bearing continuous trigger (`heavy-b-migrate`) or a current operational helper (`loam-memory-inspect`, `upgrade-merge-resolver`). The "is this archaeology" check no longer needs to fire.
- **Harness test** — no harness extension; closes a structural-cleanliness gap by retiring 4 helpers whose safety horizons have empirically passed.

Composes with: prior-dispatch halt-and-surface; v0.10.7 PATCH (Path A); `feedback_agent_empirical_recheck_before_halt`; `feedback_locked_design_not_license_for_bad_outcomes`.

---

## §3 — Component fence

**PATCH spans:** 4 tool-directory deletions + 3 file edits (dev-mode-manifest + 2 test files) + STATE/roadmap admin + 1 slug-named smoke writeup. Seal anchor: dev-sdlc (matches v0.10.7 / v0.10.6 / v0.10.5 / v0.10.4 / v0.10.3 / v0.10.2 PATCH precedent for single-cycle PATCHes; `framework/tools/loam/` NOT touched).

**PRIMARY (deletions):**

- `framework/tools/loam-migrate-launchd-labels/` — entire directory deleted (pyproject.toml + README.md + src/ + tests/).
- `framework/tools/loam-migrate-host-config/` — entire directory deleted.
- `framework/tools/loam-migrate-dormancy-config/` — entire directory deleted.
- `framework/tools/orphan-plist-cleanup/` — entire directory deleted.

**PRIMARY (manifest + test edits):**

- `plugins/dev-sdlc/dev-mode-manifest.yaml` — drop the `- glob: "framework/tools/orphan-plist-cleanup/**"` line at line 163; update the surrounding comment block at lines 159-161 to remove the orphan-plist-cleanup mention (preserve the `loam-amend` and `loam-mode` glob lines + comments).
- `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py` — `test_AC_F4_glob_with_exclusion` candidate paths at lines 72,83 swap `tools/orphan-plist-cleanup/README.md` for an equivalent non-retired-tool path that still exercises the `glob: tools/**` + `exclude: tools/loam/**` behavior. Substitute: `tools/heavy-b-migrate/README.md` (still extant per AMENDED F-RETIRE-MIGRATE-TOOLS scope; outside the `tools/loam/**` exclusion; same exercise of `expand_entry()`).
- `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` — drop `framework_tools / "orphan-plist-cleanup" / "pyproject.toml"` from `expected` tuple at line 132 + drop the corresponding comment line at line 121 + update the post-cleanup comment block at lines 113-127 to reflect the post-Path-B/C surface (3 survivors named: `loam`, `heavy-b-migrate`, `upgrade-merge-resolver`).

**PRIMARY (FIDRAFT + smoke):**

- `docs/FUTURE_IDEAS_DRAFT.md` — F-RETIRE-MIGRATE-TOOLS entry at line 244: STATUS flipped from `capture-only` → RESOLVED; entry text adds a Path B+C closure pointer to this PATCH's slug + commit + the chain pointer (Path A v0.10.7 + Path B+C v0.10.8); "Proposed shape" "(amended 2026-05-14)" → "(amended 2026-05-14; Path B+C resolved 2026-05-14)" with summary of what shipped.
- `docs/experiments/retire-m1-per-host-helpers-and-orphan-plist-cleanup-hard-smoke.md` — slug-named per F-CYCLE-ARTEFACT-SLUG-NAMING. Documents:
  - §1 outcome shape verified (4 tool dirs absent; 3 file edits applied)
  - §2 retirement-readiness re-verification (4-tool grep + per-tool README quote + cross-reference vanish-with-deletion)
  - §3 post-deletion test surface (workspace-sync 4/4 GREEN; dev-sdlc partition 6/6 GREEN)
  - §4 install-from-source.txt empirical no-op verification
  - §5 outcome-altitude dogfood probe (release-CLI 6-gate dry-run all GREEN against this plan-doc)
  - §6 F2 RUTHLESS FEEDBACK observations

**ADMIN (universal-admission docs):**

- `docs/STATE.md` — v0.10.8 row added at the SHIPPED-LOCAL position.
- `docs/release-roadmap.md` — §3 v0.10.8 PATCH SHIPPED LOCAL entry; §2 active-version-row updated.
- `docs/plans/retire-m1-per-host-helpers-and-orphan-plist-cleanup.md` — this plan-doc.
- `docs/plans/retire-m1-per-host-helpers-and-orphan-plist-cleanup.manifest.yaml` — manifest.

**dev-sdlc seal anchor artefacts:**

- `plugins/dev-sdlc/seals/SEAL_COMMIT.retire-m1-per-host-helpers-and-orphan-plist-cleanup` — narrative.
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — sidecar (auto-bumped by `loam amend seal`).
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — BASELINE pointer (auto-bumped by `loam amend seal`; pre-included in AC.RMPH.S allow-list per F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE).

**OUT OF SCOPE (HARD HALT class — would extend the PATCH unilaterally):**

- Retiring `heavy-b-migrate` (load-bearing continuous trigger; explicitly NOT retirement-eligible per amended F-RETIRE-MIGRATE-TOOLS).
- Editing any production code path beyond the 3 files named above.
- Adding new tests.
- Changing public-API surfaces of non-retired components.
- Retroactive renames of historical FIDRAFT entries beyond the F-RETIRE-MIGRATE-TOOLS RESOLVED flip.
- `git commit --amend` (NEW commits only per `feedback_no_amend_in_agent_dispatches`).
- Bumping per-component pyproject.toml versions (PATCHes ride predecessor MINOR per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1-v0.10.7 precedent).

---

## §4 — Acceptance Criteria

### AC.RMPH.1 — 3 `loam-migrate-*` tool directories deleted

**Outcome:** the directories `framework/tools/loam-migrate-launchd-labels/`, `framework/tools/loam-migrate-host-config/`, `framework/tools/loam-migrate-dormancy-config/` no longer exist in-tree. `ls framework/tools/` returns exactly 5 entries: `heavy-b-migrate`, `loam`, `loam-memory-inspect`, `orphan-plist-cleanup` (deleted in AC.RMPH.2 — but listed here because RMPH.1 + RMPH.2 deletions can be in any order; final post-AC.RMPH.2 surface is 4 entries), `upgrade-merge-resolver`. Sibling cross-references between the 3 retired tools (`loam-migrate-launchd-labels` → `loam-migrate-host-config` in README + `__init__.py`; `loam-migrate-dormancy-config` → siblings in README) vanish with the deletions (no separate edit needed). Production code references: empirically zero outside the 4 retired tool dirs (verified at plan-time via `grep -rn "loam_migrate_launchd_labels\|loam_migrate_host_config\|loam_migrate_dormancy_config" --include="*.py" framework/ plugins/` excluding the retired dirs themselves — clean).

**Verification:** `ls framework/tools/` (post-AC.RMPH.2 also): 4 dirs (`heavy-b-quotes`, `loam`, `loam-memory-inspect`, `upgrade-merge-resolver`); `find framework/tools/loam-migrate-* -type d 2>/dev/null` returns empty. Captured in smoke writeup §1.

### AC.RMPH.2 — `orphan-plist-cleanup` 4-file retirement

**Outcome:** four edits applied:

1. `framework/tools/orphan-plist-cleanup/` — entire directory deleted.
2. `plugins/dev-sdlc/dev-mode-manifest.yaml` — `- glob: "framework/tools/orphan-plist-cleanup/**"` line at line 163 removed; surrounding comment at lines 159-161 updated to remove the orphan-plist-cleanup mention (the `loam-amend` and `loam-mode` glob lines + their comments preserved verbatim).
3. `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py` — `test_AC_F4_glob_with_exclusion` candidate paths at lines 72,83 swap `tools/orphan-plist-cleanup/README.md` → `tools/heavy-b-migrate/README.md` (substitute that still exercises `expand_entry()` glob+exclude behavior with a non-retired tool).
4. `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` — `framework_tools / "orphan-plist-cleanup" / "pyproject.toml"` line dropped from `expected` tuple at line 132 + corresponding comment line at line 121 dropped + the post-cleanup comment block at lines 113-127 updated to reflect the post-Path-B/C surface (3 survivors named: `loam`, `heavy-b-migrate`, `upgrade-merge-resolver`).

**Verification:** `ls framework/tools/orphan-plist-cleanup 2>&1` returns `No such file or directory`. `grep -n "orphan-plist-cleanup" plugins/dev-sdlc/dev-mode-manifest.yaml` returns 0 matches. `grep -n "orphan-plist-cleanup" plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py` returns 0 matches. `grep -n "orphan-plist-cleanup" framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` returns 0 matches. Captured in smoke writeup §1.

### AC.RMPH.3 — `install-from-source.txt` empirical no-op (audit-trail)

**Outcome:** empirical recheck at plan-time showed NONE of the 4 retired tool directories (`loam-migrate-launchd-labels`, `loam-migrate-host-config`, `loam-migrate-dormancy-config`, `orphan-plist-cleanup`) appear in `install-from-source.txt`. The file was always minimal-by-design — these helpers were never in the install path (operator-facing helpers; explicit invocation only). AC documents the empirical no-op for audit-trail (the dispatch brief named install-from-source.txt as a candidate edit; empirical recheck found nothing to remove).

**Verification:** `grep -n "loam-migrate\|orphan-plist-cleanup" install-from-source.txt docs/install-from-source.md` returns 0 matches. Captured in smoke writeup §4.

### AC.RMPH.4 — post-retirement test surface GREEN

**Outcome:** the affected test suites pass after the retirement edits land.

- `python3.13 -m pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py -v` returns 4/4 PASSED (unchanged — the pos-publish-framework-only entry was already removed at v0.10.7; orphan-plist-cleanup entry removal in this PATCH leaves the test still 4/4 GREEN with the updated `expected` tuple).
- `cd plugins/dev-sdlc/tools/loam-mode && python3.13 -m pytest tests/test_partition_manifest.py -v` returns 6/6 PASSED (unchanged — the candidate-path swap is pure-string substitution; the test exercises `expand_entry()` glob+exclude behavior, not the existence of the candidate path on disk).

**Verification:** smoke writeup §3 captures both invocations' verbatim outputs.

### AC.RMPH.5 — outcome-altitude dogfood probe

**Outcome:** slug-named smoke writeup at `docs/experiments/retire-m1-per-host-helpers-and-orphan-plist-cleanup-hard-smoke.md` documents the cycle's outcome end-to-end: (a) the 4 tool directories are absent from `framework/tools/`; (b) the 3 file edits land cleanly; (c) the affected test suites pass; (d) `loam release v0.10.8 --plan-doc docs/plans/retire-m1-per-host-helpers-and-orphan-plist-cleanup.md --dry-run` returns ALL 6 GATES GREEN against the live plan-doc + manifest + STATE/roadmap admin.

**Verification:** smoke writeup exists at the slug-named path; release-CLI dry-run output captured in §5.

### AC.RMPH.6 — F-RETIRE-MIGRATE-TOOLS FIDRAFT entry RESOLVED (chain pointer)

**Outcome:** `docs/FUTURE_IDEAS_DRAFT.md` F-RETIRE-MIGRATE-TOOLS entry at line 244: STATUS flipped from `capture-only` → RESOLVED. Entry text adds: (1) Path B+C closure pointer naming this PATCH's slug + commit; (2) chain pointer Path A v0.10.7 (commit `26a5bee`) + Path B+C this PATCH; (3) summary of what shipped under Path B (3 `loam-migrate-*` per-host helpers retired) + Path C (`orphan-plist-cleanup` 4-file retirement); (4) `heavy-b-migrate` unchanged (load-bearing continuous trigger; permanent residency under `framework/tools/`).

**Verification:** smoke writeup §6 captures the diff summary.

### AC.RMPH.S — seal-diff scope-fence

**Outcome:** the source-edit commit's diff touches only the files in the allow-list below. Verified via `git diff --name-only` against the source-edit commit.

**Allow-list:**

- `framework/tools/loam-migrate-launchd-labels/` — entire directory deleted (admitted via `extra_allowed_prefixes: [framework/tools/]`).
- `framework/tools/loam-migrate-host-config/` — entire directory deleted (admitted via same).
- `framework/tools/loam-migrate-dormancy-config/` — entire directory deleted (admitted via same).
- `framework/tools/orphan-plist-cleanup/` — entire directory deleted (admitted via same).
- `plugins/dev-sdlc/dev-mode-manifest.yaml` — orphan-plist-cleanup glob removal (admitted via plugins/dev-sdlc/ universal admission).
- `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py` — candidate-path swap (admitted via same).
- `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` — counterpart-list update (admitted via `extra_allowed_prefixes: [framework/workspace-sync/tests/]`).
- `docs/FUTURE_IDEAS_DRAFT.md` — F-RETIRE-MIGRATE-TOOLS RESOLVED flip + chain pointer.
- `docs/STATE.md` — v0.10.8 row.
- `docs/release-roadmap.md` — v0.10.8 §3 entry + §2 active-version row.
- `docs/experiments/retire-m1-per-host-helpers-and-orphan-plist-cleanup-hard-smoke.md` — smoke writeup.
- `docs/plans/retire-m1-per-host-helpers-and-orphan-plist-cleanup.md` — this plan-doc.
- `docs/plans/retire-m1-per-host-helpers-and-orphan-plist-cleanup.manifest.yaml` — manifest.
- `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — BASELINE pointer auto-bumped at seal-time per F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE pre-inclusion.
- `plugins/dev-sdlc/tests/SEAL_COMMIT` — sidecar auto-bumped at seal-time.
- `plugins/dev-sdlc/seals/SEAL_COMMIT.retire-m1-per-host-helpers-and-orphan-plist-cleanup` — narrative.

NO entries in pyproject.toml; NO `__version__` updates; NO test additions; NO public-API edits.

**Verification:** smoke writeup §5 captures `git diff --name-status` against the source-edit commit.

---

## §5 — Method-decision register

### D-RMPH.1 — Path B+C in single PATCH (not separate cycles)

**Decision:** ship Path B (3 `loam-migrate-*` per-host helpers) + Path C (`orphan-plist-cleanup` 4-file edit) in a single PATCH.

**Rationale:** dispatcher brief explicitly authorises the combined Path B+C scope. Separate cycles would add coordination overhead (two plan-docs + two manifests + two seal narratives) without buying any additional safety. Both safety horizons (M1 per-host: 17 days post-ship; pre-#6 archaeological: substantially longer) have empirically passed per dispatcher ratification. Composes with `feedback_swarming_recursive_decomposition` (the stopping criterion: subtasks add tighter ACs only via the AC-family decomposition, not via cycle-decomposition; the work IS one outcome-shape).

### D-RMPH.2 — `heavy-b-migrate` STAYS (load-bearing continuous trigger)

**Decision:** `framework/tools/heavy-b-migrate/` is NOT touched. AMENDED F-RETIRE-MIGRATE-TOOLS framing (v0.10.7) explicitly removed it from the candidate list because it's wired into `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/session_start.py:283-299` via `_invoke_lazy_projection()` → `loam.heavy_b_migrate.trigger.run_if_dev_intent`. Idempotent re-runner per README:22ff. Retiring would silently break the dev-discipline contract for new dev-intent workspaces.

**Rationale:** prior-dispatch halt-and-surface evidence + v0.10.7 amendment both name this constraint. If the trigger surface is later determined to be obsolete, that's a separate MINOR-class methodology change, not a PATCH-class cleanup.

### D-RMPH.3 — `test_AC_F4_glob_with_exclusion` candidate-path substitute is `heavy-b-migrate` (not synthetic)

**Decision:** swap `tools/orphan-plist-cleanup/README.md` → `tools/heavy-b-migrate/README.md` in the partition-test candidate paths at lines 72,83 of `test_partition_manifest.py`.

**Rationale:** alternative shapes considered: (a) synthetic path like `tools/synthetic-test-fixture/README.md` (purely for the test) — rejected, the test was always asserting against real-tree paths and the substitute should preserve that property; (b) one of the other surviving `framework/tools/` entries (`loam-memory-inspect`, `upgrade-merge-resolver`) — `heavy-b-migrate` chosen because it's the most-stable member of the post-AMENDMENT surface (named permanent in the F-RETIRE-MIGRATE-TOOLS entry), the others are operational helpers that could in principle move. The substitute is read-only string data; the test exercises `expand_entry()`'s `glob: tools/**` + `exclude: tools/loam/**` behavior on candidate-string sets — the path doesn't need to exist on disk. Composes with `feedback_loose_AC_text_fix_AC_not_implementation` (the test's AC — verify glob+exclude behavior — is unchanged; only the fixture-data candidate-path identifier moves to a non-retired tool name).

### D-RMPH.4 — `install-from-source.txt` AC documents the empirical no-op

**Decision:** AC.RMPH.3 documents the empirical no-op (no entries to remove) rather than dropping the AC. Dispatch brief named install-from-source.txt as a candidate-edit; empirical recheck at plan-time found nothing to edit.

**Rationale:** alternative shapes: (a) drop AC.RMPH.3 entirely — rejected, loses the audit-trail evidence that the dispatcher's edit-prediction was empirically falsified at plan-time; (b) keep AC.RMPH.3 with `expected: edit applied` — rejected, would be an empirically-false expectation. The empirical-no-op AC preserves the discipline of `feedback_specific_claims_verified_or_marked_guess` + `feedback_agent_empirical_recheck_before_halt` at the AC granularity.

### D-RMPH.5 — pyproject.toml versions stay at 0.10.0

**Decision:** no per-component pyproject.toml version bumps in this PATCH.

**Rationale:** per AC.HONEST.1 / D-NFCLEAN.4 / D-SDPD / v0.8.3 / v0.10.1-v0.10.7 precedent — PATCHes ride the predecessor MINOR's per-component version. v0.10.8 stays at 0.10.0 across all 30 → (now 26 post-retirement) `pyproject.toml` files. No drift from the established convention.

**Side-effect note:** the 4 retired tool directories each carried their own `pyproject.toml`. Post-deletion the file count drops from 30 → 26 (24 at >=3.11; 2 at >=3.13). Counts updated in v0.10.7's F-PYTHON-3.9 evidence remain correct as historical state-at-resolution; no retroactive edit needed.

### D-RMPH.6 — dev-sdlc seal anchor; `extra_allowed_prefixes` admits `framework/tools/` + `framework/workspace-sync/tests/`

**Decision:** seal anchor is dev-sdlc (matches v0.10.7 / v0.10.6 / v0.10.5 / v0.10.4 / v0.10.3 / v0.10.2 PATCH precedent). The AC.RMPH.S allow-list pre-includes `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` because the dev-sdlc seal workflow auto-bumps the file's BASELINE pointer at seal-time. Manifest's `extra_allowed_prefixes` admits `framework/tools/` (for the 4 directory deletions) + `framework/workspace-sync/tests/` (for the test counterpart-list update).

**Rationale:** F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE captured the convention 2026-05-14 specifically to prevent the v0.10.3 fix-up rework where this file was omitted. This plan-doc honors the convention. The dual `extra_allowed_prefixes` follows the v0.10.6 precedent (admitted `docs/papers/`) + v0.10.7 precedent (admitted `framework/workspace-sync/tests/`) for cross-component PATCHes anchored at dev-sdlc.

### D-RMPH.7 — F-RETIRE-MIGRATE-TOOLS RESOLVED (not RESOLVED-BY-COMPOSITION)

**Decision:** F-RETIRE-MIGRATE-TOOLS status flips to plain RESOLVED (not RESOLVED-BY-COMPOSITION or RESOLVED-BY-INSPECTION).

**Rationale:** alternative vocabulary considered: (a) RESOLVED-BY-COMPOSITION — applies when multiple cycles compose to close a single entry without any one cycle being "the" closure. F-RETIRE-MIGRATE-TOOLS was structurally one entry that decomposed into Paths A/B/C; v0.10.7 closed Path A's bookkeeping (test fix + framing amendment), this PATCH closes Path B+C (the actual retirement work). Both cycles together = the entry's closure; this matches the COMPOSITION shape. (b) plain RESOLVED — applies when one cycle did the work. The retirement work IS this PATCH; v0.10.7's framing amendment was a precondition, not a partial-closure of the retirement scope itself. The COMPOSITION framing would over-claim v0.10.7's contribution to the actual retirement. Picked plain RESOLVED with explicit chain pointer to v0.10.7's amendment commit; the chain pointer captures the composition without inflating it into the status vocabulary.

---

## §6 — F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline check

Per F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH: when a PATCH closes a FIDRAFT item AND that item's RESOLVED entry text mentions another FIDRAFT entry as "blocked-by-this-helper" / "depends-on-this-helper", the source-edit MUST flip every dependent entry's status in the same commit.

**Empirical recheck:**

- F-RETIRE-MIGRATE-TOOLS amended entry text mentions: "F-TF-1 RESOLVED at v0.10.7"; "v1.0 ship gate". F-TF-1 is already RESOLVED (v0.10.7); v1.0 ship gate is a downstream surface, not an entry. No flip-on-unblock action needed for those references.
- Cross-grep at plan-time: `grep -rn "F-RETIRE-MIGRATE-TOOLS\|loam-migrate\|orphan-plist-cleanup" docs/FUTURE_IDEAS_DRAFT.md` returns: F-RETIRE-MIGRATE-TOOLS entry itself (line 244) + F-TF-1 entry (line 252) reference to "composes with F-RETIRE-MIGRATE-TOOLS" (which v0.10.7 already updated to "Activation gate revised at activation-time: cycle was activated independently of F-RETIRE-MIGRATE-TOOLS"). No additional FIDRAFT entries depend on F-RETIRE-MIGRATE-TOOLS.

Discipline GREEN. Single FIDRAFT flip (F-RETIRE-MIGRATE-TOOLS) in this PATCH's source-edit; no dependent entries.

---

## §7 — References

- Prior-dispatch halt-and-surface: `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md`.
- Predecessor cycle: v0.10.7 PATCH `workspace-sync-test-and-python-runtime-pin` (sealed `6bc8dd6`; published `9b472dd`). Path A of F-RETIRE-MIGRATE-TOOLS.
- FIDRAFT file: `docs/FUTURE_IDEAS_DRAFT.md` — F-RETIRE-MIGRATE-TOOLS (line 244).
- Test under update: `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` (lines 113-134 area); `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py` (lines 64-84 area).
- Manifest under update: `plugins/dev-sdlc/dev-mode-manifest.yaml` (lines 155-169 area).
- Composes-with feedback memories: `feedback_agent_empirical_recheck_before_halt`, `feedback_locked_design_not_license_for_bad_outcomes`, `feedback_principle_conflict_resolution_multi_signal`, `feedback_no_amend_in_agent_dispatches`, `feedback_version_numbers_at_release_time`, `feedback_loose_AC_text_fix_AC_not_implementation`, `feedback_specific_claims_verified_or_marked_guess`.
- Convention compliance: `F-CYCLE-ARTEFACT-SLUG-NAMING` (smoke writeup slug-named); `F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE` (allow-list pre-includes `test_no_sealed_amendments.py`); `F-PLAN-DOC-TEMPLATE-§13-STATUS-HEADING` (this plan-doc pre-includes `## §13 — §status` heading); `F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH` (§6 above).

---

## §13 — §status

**Build cycle:** SHIPPED LOCAL 2026-05-14. Single-cycle PATCH closing F-RETIRE-MIGRATE-TOOLS Path B+C (retire 3 `loam-migrate-*` per-host helpers + `orphan-plist-cleanup` 4-file edit). v0.10.7 closed Path A; this PATCH completes the entry's retirement scope. `heavy-b-migrate` permanently retained as load-bearing continuous trigger. Sealed local; awaiting dispatcher dogfood publish per ASK-FIRST.

**Plan-doc commits:** plan-doc + manifest `3b5d0e0`; source-edit (4 dir deletions + 3 file edits + FIDRAFT RESOLVED flip + STATE/roadmap admin + slug-named smoke writeup) `688e85b`; manifest baseline backfill `3ca8a77`; manifest smoke_outcome shorten `10987d7`; apply auto-commit (BASELINE + sidecar bump to `688e85b` + `extra_allowed_prefixes: [framework/tools/]`) `2605f3a`; seal commit (deterministic seal) `9bd5684`.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.RMPH.1 — 3 `loam-migrate-*` tool directories deleted | GREEN | Smoke writeup §1: `ls /Users/lukeivers/loam/framework/tools/` returns 4 entries (`heavy-b-migrate`, `loam`, `loam-memory-inspect`, `upgrade-merge-resolver`) — the 3 `loam-migrate-*` directories absent. Smoke writeup §2.1-§2.3: per-tool retirement-readiness re-verification (README quotes + zero production references outside their own dirs). Smoke writeup §2.5: cross-reference grep confirms 0 matches outside the retired dirs. Source-edit commit `688e85b` shows `delete mode 100644` for all 28 files across the 3 directories. |
| AC.RMPH.2 — `orphan-plist-cleanup` 4-file retirement | GREEN | Smoke writeup §1 names all 4 edits applied: (1) `framework/tools/orphan-plist-cleanup/` directory deleted (source-edit `688e85b` shows 16 file deletions); (2) `plugins/dev-sdlc/dev-mode-manifest.yaml` line 163 glob removed + comment block updated; (3) `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py` candidate paths swapped to `tools/heavy-b-migrate/README.md`; (4) `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` `expected` tuple line + comment line dropped + post-cleanup comment block updated. |
| AC.RMPH.3 — `install-from-source.txt` empirical no-op (audit-trail) | GREEN | Smoke writeup §4: `grep -n "loam-migrate\|orphan-plist-cleanup\|loam_migrate\|orphan_plist_cleanup" install-from-source.txt docs/install-from-source.md` returns 0 matches. Empirical no-op verified at plan-time per `feedback_agent_empirical_recheck_before_halt`. AC documents the no-op for audit-trail. |
| AC.RMPH.4 — post-retirement test surface GREEN | GREEN | Smoke writeup §3.1: `python3.13 -m pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py -v` returns 4/4 PASSED. Smoke writeup §3.2: `cd plugins/dev-sdlc/tools/loam-mode && python3.13 -m pytest tests/test_partition_manifest.py -v` returns 6/6 PASSED. Both verbatim outputs captured. |
| AC.RMPH.5 — outcome-altitude dogfood probe | GREEN | Smoke writeup at `docs/experiments/retire-m1-per-host-helpers-and-orphan-plist-cleanup-hard-smoke.md` documents end-to-end: §1 outcome shape; §2 retirement-readiness re-verification (4 tools); §3 post-deletion test surface (workspace-sync 4/4 + dev-sdlc partition 6/6); §4 install-from-source.txt empirical no-op; §5 release-CLI 6-gate dry-run (TBD-AT-APPLY at smoke authoring; backfilled at acs-verified gate-pass time); §6 F-RETIRE-MIGRATE-TOOLS RESOLVED diff summary + F2 RUTHLESS FEEDBACK observations. |
| AC.RMPH.6 — F-RETIRE-MIGRATE-TOOLS FIDRAFT entry RESOLVED with chain pointer | GREEN | `docs/FUTURE_IDEAS_DRAFT.md:244` F-RETIRE-MIGRATE-TOOLS entry STATUS flipped from `capture-only` → `RESOLVED 2026-05-14 by v0.10.8 PATCH (retire-m1-per-host-helpers-and-orphan-plist-cleanup)`. Entry text adds Path B+C closure summary + chain pointer (Path A v0.10.7 commit `26a5bee` + Path B+C this PATCH). Section (1) `heavy-b-migrate` REMOVED appended `**Permanent residency under framework/tools/.**`; sections (2) and (3) past-tense conversion + executed-blocks added; Path-A/B/C decomposition flipped from "deferred" → "shipped at v0.10.8 PATCH"; composes-with paragraph updated. Smoke writeup §6.1 captures the diff summary. |
| AC.RMPH.S — seal-diff scope-fence | GREEN | `git diff --name-only 3b5d0e0..9bd5684` shows changes only under the allow-list: 4 framework/tools/ directory deletions (admitted via `extra_allowed_prefixes: [framework/tools/]`); 1 framework/workspace-sync test edit (admitted via `extra_allowed_prefixes: [framework/workspace-sync/tests/]`); 2 dev-sdlc edits (manifest + partition test; admitted via plugins/dev-sdlc/ universal-admission); FIDRAFT-doc edit (`docs/FUTURE_IDEAS_DRAFT.md`); universal-admission docs (`docs/STATE.md` + `docs/release-roadmap.md`); slug-named smoke writeup; plan-doc + manifest; dev-sdlc seal anchor artefacts (`plugins/dev-sdlc/seals/SEAL_COMMIT.retire-m1-per-host-helpers-and-orphan-plist-cleanup` narrative + `plugins/dev-sdlc/tests/SEAL_COMMIT` sidecar + `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` BASELINE pointer auto-bump pre-included in §3 allow-list per F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE). NO entries in pyproject.toml; NO entries in any framework/* component source code beyond the deletions + the single test file admitted via `extra_allowed_prefixes`; NO `__version__` updates; NO test additions. |

### AI-time actuals

| Stage | Estimated | Actual |
|---|---|---|
| Halt-and-surface artefact read + spot-check empirical recheck | 5-10 min | ~5 min |
| Plan-doc + manifest authoring | 15-25 min | ~18 min |
| Source-edit (4 dir deletions + 3 file edits + FIDRAFT RESOLVED flip + STATE/roadmap admin + slug-named smoke writeup) | 20-35 min | ~25 min |
| `loam amend apply` + manifest baseline backfill + manifest smoke_outcome shorten + `seal` | 5-10 min | ~5 min |
| §status backfill + roadmap-row seal-SHA backfill + re-run dry-run | 3-5 min | ~5 min |
| **Total** | **~50-90 min midpoint ~70 min** | **~58 min** |

In-band — landed cleanly. Two in-cycle adjustments: (a) initial `smoke_outcome` exceeded 200-char limit (482 chars) → corrected via second manifest commit; (b) plan-doc §status section initially carried TBD-AT-COMMIT placeholders → backfilled post-seal per F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH-adjacent §status discipline.

### Halt-and-surface findings

**No HARD HALTs fired in-cycle.** The prior-dispatch (`retire-one-time-migration-tools`) halt-and-surface artefact + v0.10.7 amendment did all the empirical-investigation legwork; this PATCH executed Path B+C per the dispatcher-ratified scope per the original brief.

**No soft halts.** Empirical retirement-readiness spot-check at plan-time confirmed all 4 tools retirement-ready (zero production cross-references outside their own dirs; AMENDED F-RETIRE-MIGRATE-TOOLS framing already validated by v0.10.7).

**Smoke writeup §6.2 surfaces 4 F2 Ruthless Feedback observations:** (1) D-RMPH.3 candidate-path substitute choice rationale (heavy-b-migrate stability over operational helpers); (2) side-effect on F-PYTHON-3.9 evidence (post-deletion file count drops 30 → 26; v0.10.7 historical evidence preserved as state-at-resolution); (3) `install-from-source.txt` AC pattern (documenting empirical no-op > dropping the AC); (4) D-RMPH.1 single-PATCH for Path B+C rationale (overhead-without-benefit for split). None require dispatcher escalation.
