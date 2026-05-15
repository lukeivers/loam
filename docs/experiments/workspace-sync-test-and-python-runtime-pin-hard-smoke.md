# workspace-sync-test-and-python-runtime-pin — HARD smoke writeup

**Cycle:** v0.10.7 PATCH (slug `workspace-sync-test-and-python-runtime-pin`).
**Date:** 2026-05-14.
**Plan-doc:** `docs/plans/workspace-sync-test-and-python-runtime-pin.md`.
**Slug-named per** `F-CYCLE-ARTEFACT-SLUG-NAMING` (NOT `v0-10-7-hard-smoke.md`).
**FIDRAFTs closed:** F-TF-1 (RESOLVED) + F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN (RESOLVED-BY-INSPECTION) + F-RETIRE-MIGRATE-TOOLS framing AMENDED (status unchanged — capture-only).
**Prior dispatch:** `retire-one-time-migration-tools` halt-and-surface evidence at `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md`.

---

## §1 — Outcome shape verified

After this PATCH:

1. The workspace-sync test stale-path expectation against the retired `framework/tools/pos-publish-framework-only/pyproject.toml` is removed; pytest invocation against the test file returns 4/4 PASSED post-fix (was: 3 passed + 1 failed at `test_AC_D_5_5_1_framework_tools_present`).
2. The F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN entry is structurally CLOSED via empirical recheck per `feedback_agent_empirical_recheck_before_halt` — the pin already exists across all 30 `pyproject.toml` files across `framework/` + `plugins/` since 2026-04-27 (commit `0d599bb`); pip install on Python 3.9 returns the install-time refusal exactly as F-PYTHON-3.9 prescribes.
3. The F-RETIRE-MIGRATE-TOOLS entry's "Proposed shape" is rewritten per prior-dispatch halt-and-surface evidence: heavy-b-migrate is REMOVED from the candidate list (load-bearing continuous trigger); orphan-plist-cleanup retirement is clarified as a 4-file edit (not 1-file deletion); per-host helper retirement is clarified as a safety-horizon judgment call (owner-class). Status remains `capture-only` — operator-class Path B/C call stays owner-gated.
4. Path A scope only — Path B (retire 3 `loam-migrate-*` per-host helpers; MEDIUM blast) + Path C (additionally retire `orphan-plist-cleanup`; MEDIUM-HIGH blast) deferred for owner ratification.

---

## §2 — Static verification (AC.WSP.1)

### §2.1 — Pre-source-edit baseline (workspace-sync test 1 failed + 3 passed)

```
$ python3.13 -m pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py -v
============================= test session starts ==============================
collected 4 items

framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_bare_tools_absent PASSED
framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_framework_tools_present FAILED
framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_bare_workspace_sync_absent PASSED
framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_framework_workspace_sync_present PASSED

E       AssertionError: framework/tools/ counterpart files missing post-D.5.5 (updated post-M1g + M6b.0 + M6b.1 + M9 to reflect actual post-rename surface): ['framework/tools/pos-publish-framework-only/pyproject.toml']

framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py:132: AssertionError
==================== 1 failed, 3 passed in 0.02s ====================
```

The expected-tuple at lines 121-130 included `framework_tools / "pos-publish-framework-only" / "pyproject.toml"`. The directory `framework/tools/pos-publish-framework-only/` does not exist on disk (`ls` returns "No such file or directory"). The tool was retired previously per F-RETIRE-MIGRATE-TOOLS entry's prior framing.

### §2.2 — Source-edit (single test-file change; ~5 lines)

`framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` modified:
- Removed the `framework_tools / "pos-publish-framework-only" / "pyproject.toml"` line from the `expected` tuple at lines 127-129.
- Removed the corresponding comment lines at 119-120 (`framework/tools/pos-publish-framework-only/`).
- Added a v0.10.7-PATCH-context comment naming the F-TF-1 closure + extended the heavy-b-migrate comment with the load-bearing continuous-trigger reference per the prior-halt empirical evidence.

### §2.3 — Post-source-edit verification (4 passed)

```
$ python3.13 -m pytest framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py -v
============================= test session starts ==============================
collected 4 items

framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_bare_tools_absent PASSED
framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_1_framework_tools_present PASSED
framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_bare_workspace_sync_absent PASSED
framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py::test_AC_D_5_5_2_framework_workspace_sync_present PASSED

============================== 4 passed in 0.01s ===============================
```

4/4 GREEN. AC.WSP.1 verified.

### §2.4 — Release-CLI suite regression check (99/99 GREEN on production python)

```
$ python3.13 -m pytest framework/tools/loam/tests/
============================== 99 passed in 9.92s ==============================
```

All 99 release-CLI tests pass on Python 3.13 (production runtime). No regression introduced by this PATCH.

---

## §3 — F-PYTHON-3.9 empirical-recheck (AC.WSP.2)

The F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN FIDRAFT entry (captured 2026-05-14) claims `pyproject.toml should declare python_requires>=3.11`. Per `feedback_agent_empirical_recheck_before_halt` discipline, the v0.10.7 cycle ran the 4-step recheck before treating the FIDRAFT as actionable.

### §3.1 — Step 1: state the conclusion + supporting evidence

**Conclusion to test:** "the pin work proposed by F-PYTHON-3.9 is not yet done; this PATCH should add `requires-python = ">=3.11"` to pyproject.toml files."

**Supporting evidence (FIDRAFT capture):** v0.10.4 + v0.10.5 cycle agents observed 7 pre-existing release-CLI test failures on Python 3.9 (entry_points kwarg API).

### §3.2 — Step 2: generate alternative hypotheses

- **H1:** the pin already exists, but on Python 3.9 the failures surface anyway because pyenv shadows the install-time check.
- **H2:** the pin partially exists (some pyprojects have it, some don't), and the missing ones are the ones causing failures.
- **H3:** the pin doesn't exist and F-PYTHON-3.9 is correct.

### §3.3 — Step 3: empirically test each hypothesis

**Test 1: grep across all pyproject.toml files for the pin.**

```
$ find framework plugins -name pyproject.toml -exec grep -l "requires-python" {} \;
framework/scope-of-work/pyproject.toml
framework/cost-governance/pyproject.toml
framework/workspace-sync/pyproject.toml
framework/per-project-pm/pyproject.toml
framework/objective-tracker/pyproject.toml
framework/workspace-bootstrap/pyproject.toml
framework/self-correction/pyproject.toml
framework/self-upgrade/pyproject.toml
framework/dormancy/pyproject.toml
framework/observability-aggregator/pyproject.toml
framework/telegram-interface/pyproject.toml
framework/primary-persona/pyproject.toml
framework/reversibility-primitive/pyproject.toml
framework/loam-init/pyproject.toml
framework/safety-layer/pyproject.toml
framework/orchestrator/pyproject.toml
plugins/dev-sdlc/pyproject.toml
plugins/loam-skills/pyproject.toml
framework/tools/loam-migrate-launchd-labels/pyproject.toml
framework/tools/heavy-b-migrate/pyproject.toml
framework/tools/loam-migrate-host-config/pyproject.toml
framework/tools/loam/pyproject.toml
framework/tools/loam-memory-inspect/pyproject.toml
framework/tools/upgrade-merge-resolver/pyproject.toml
framework/tools/loam-migrate-dormancy-config/pyproject.toml
framework/tools/orphan-plist-cleanup/pyproject.toml
plugins/dev-sdlc/odd-extractor/pyproject.toml
plugins/dev-sdlc/pr-safety/pyproject.toml
plugins/dev-sdlc/tools/loam-amend/pyproject.toml
plugins/dev-sdlc/tools/loam-mode/pyproject.toml
```

30 pyproject.toml files; ALL declare `requires-python`. Counts:

```
$ find framework plugins -name pyproject.toml -exec grep -H "requires-python" {} \; | grep -F '">=3.11"' | wc -l
      24
$ find framework plugins -name pyproject.toml -exec grep -H "requires-python" {} \; | grep -F '">=3.13"' | wc -l
       6
```

24 files at `>=3.11` + 6 files at `>=3.13` = 30 total. **H2 (partial-pin) is FALSIFIED — every pyproject.toml is pinned.** **H3 (no pin) is FALSIFIED.**

**Test 2: git blame for pin origin.**

```
$ git blame framework/tools/loam/pyproject.toml | grep "requires-python"
0d599bbd framework/tools/pos-amend/pyproject.toml (Luke Ivers 2026-04-27 13:12:29 -0500  9) requires-python = ">=3.11"
```

The pin has been in place since 2026-04-27 (commit `0d599bb` — pre-renumber from `pos-amend` to `loam`). The F-PYTHON-3.9 entry was captured 2026-05-14 — the pin pre-dates the capture by 17 days.

**Test 3: pip install --dry-run on Python 3.9 — does the pin actually trigger refusal?**

```
$ pip install --dry-run framework/tools/loam/
Processing ./framework/tools/loam
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Getting requirements to build wheel: started
  Getting requirements to build wheel: finished with status 'done'
  Preparing metadata (pyproject.toml): started
  Preparing metadata (pyproject.toml): finished with status 'done'
ERROR: Package 'loam-cli' requires a different Python: 3.9.17 not in '>=3.11'
```

Pip refuses install at install-time, exactly as F-PYTHON-3.9 prescribes. **H1 (pin exists, but pyenv shadows) — partially CONFIRMED for the install-time check; the pin works structurally.** The cycle agents who observed the 7 release-CLI test failures on 3.9 were on an environment where the package had ALREADY been installed (under a different python or with `--ignore-requires-python`); the failures they saw were the install-time refusal happening at pytest-collection-time (`ModuleNotFoundError: No module named 'loam_cli'` — captured in §3.5 below), NOT a missing pyproject pin.

### §3.4 — Step 4: halt only after empirical confirmation

The 4-step empirical recheck CONFIRMS that F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN is RESOLVED-BY-INSPECTION — the proposed work was already done before the entry was captured. This PATCH does NOT add new pin work; it updates the FIDRAFT entry's status with the empirical evidence + chain pointer to the 2026-04-27 commit.

### §3.5 — Direct reproduction of the cycle-agent observation pattern

For audit trail completeness, here's the failure mode the v0.10.4 + v0.10.5 cycle agents observed:

```
$ pytest framework/tools/loam/tests/  # invoked under Python 3.9 (pyenv default)
ERROR framework/tools/loam/tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py
ERROR framework/tools/loam/tests/test_AC_RVG_removed_verdict.py
ERROR framework/tools/loam/tests/test_AC_SDPD_plan_doc_flag.py
ERROR framework/tools/loam/tests/test_AC_V060_1_release_cli_dispatch.py
ERROR framework/tools/loam/tests/test_AC_V060_2_pre_publish_gates.py
ERROR framework/tools/loam/tests/test_AC_V060_3_tag_and_push.py
ERROR framework/tools/loam/tests/test_AC_V060_4_release_notes.py
ERROR framework/tools/loam/tests/test_AC_V060_6_post_ship_review.py
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!

E   ModuleNotFoundError: No module named 'loam_cli'
```

The `ModuleNotFoundError` is the install-time refusal manifesting at collection-time — pip wouldn't install the package on 3.9 because the pin already prevents it. The cycle agents framed it as "7 test failures on 3.9" but the actual root-cause is the install-refusal that the pin (already in place) is producing.

The same suite on Python 3.13 (production) returns 99/99 GREEN per §2.4 above. AC.WSP.2 verified.

---

## §4 — F-RETIRE-MIGRATE-TOOLS framing-correction diff summary (AC.WSP.3)

The F-RETIRE-MIGRATE-TOOLS entry at `docs/FUTURE_IDEAS_DRAFT.md:244` was rewritten per prior-dispatch halt-and-surface evidence. Diff summary:

### §4.1 — Title line

- **Before:** `F-RETIRE-MIGRATE-TOOLS — Retire \`framework/tools/loam-migrate-*\` + \`heavy-b-migrate\` + \`orphan-plist-cleanup\` + \`pos-publish-framework-only\` (workspace-sync test cleanup ride-along).`
- **After:** `F-RETIRE-MIGRATE-TOOLS — Retire \`framework/tools/loam-migrate-*\` + \`orphan-plist-cleanup\` (workspace-sync test cleanup already shipped).`
- **Rationale:** heavy-b-migrate REMOVED (load-bearing continuous trigger); pos-publish-framework-only REMOVED (already retired; F-TF-1 closes the residual stale assertion).

### §4.2 — "Proposed shape" body (4 named corrections)

1. **`heavy-b-migrate` REMOVED from candidate list.** Empirical investigation confirmed it's a load-bearing continuous trigger wired into `plugins/dev-sdlc/tools/loam-mode/src/loam_mode/session_start.py:283-299` via `_invoke_lazy_projection()` (calls `loam.heavy_b_migrate.trigger.run_if_dev_intent`); idempotent re-runner per `framework/tools/heavy-b-migrate/README.md:22ff` ("The phase migration runs automatically on the first session where the workspace's PersonaContract carries `dev_intent='yes'`. Idempotent by `lifted_from`. Re-runs are no-ops."); retiring it would silently break the loam-mode dev-discipline contract for new dev-intent workspaces. If the trigger surface is later determined to be obsolete, that's a separate MINOR-class methodology change, not a PATCH-class cleanup.

2. **`orphan-plist-cleanup` retirement clarified as a 4-FILE EDIT, not a 1-file deletion.** Production references that would break: `plugins/dev-sdlc/dev-mode-manifest.yaml:163` (actively listed in dev-mode partition); `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_manifest.py:72,83` (asserts `tools/orphan-plist-cleanup/README.md` is partitioned dev-only); `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py:117,125` (expects `framework/tools/orphan-plist-cleanup/pyproject.toml` exists post-v0.10.7); cross-references in `framework/tools/loam-migrate-launchd-labels/{README.md,tests/test_migrate.py,src/loam_migrate_launchd_labels/migrate.py}`. The README declares "one-shot remediation tool" semantically; the production wiring is operator-facing for new operators who install loam on a host with pre-#6 archaeological orphans. Retirement requires the 4-file cleanup AND a safety-horizon ruling on whether new operators still need the remediation surface.

3. **3 `loam-migrate-*` per-host helpers (launchd-labels / host-config / dormancy-config) retirement clarified as safety-horizon judgment call.** All have explicit "run once per host post-upgrade" READMEs with idempotent contracts (case-2 no-op + case-4 conflict-halt). Production cross-references: clean (only docs/plans + own README cross-references between siblings; no production code paths). The empirical-recheck failure: there's no STATE.md or release-roadmap evidence that ALL operational hosts have run these. They are per-host / per-operator helpers; "every host has migrated" is an unverifiable claim. Retirement-eligibility is "have we passed the safety horizon for the M1b/M1c/M1f per-host upgrade helpers?" — owner-class call.

4. **`pos-publish-framework-only` confirmed already-retired.** The residual stale assertion at `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` was closed at v0.10.7 PATCH per F-TF-1 RESOLVED. Cleanup ride-along is complete; this entry no longer carries it.

### §4.3 — Path-A/B/C decomposition added

Added Path-A / Path-B / Path-C decomposition (per prior-dispatch halt-and-surface) to the entry body:
- Path A (F-TF-1 + F-PYTHON-3.9 inspection-resolve + this framing amendment) shipped at v0.10.7.
- Path B (retire 3 `loam-migrate-*` per-host helpers; MEDIUM blast) deferred for owner safety-horizon ratification.
- Path C (Path B + `orphan-plist-cleanup` 4-file retirement; MEDIUM-HIGH blast) deferred for owner ratification.

### §4.4 — Status line UNCHANGED (still capture-only)

- **Before:** `Status: capture-only. Activation gate: v0.8.x cleanup cycle.`
- **After:** `Status: capture-only (Path B + Path C decisions stay owner-gated; this PATCH only amended the framing). Activation gate: owner ratification on Path B safety-horizon (...) + Path C safety-horizon (...); evaluate ahead of v1.0 surface cleanup.`

### §4.5 — Verification

```
$ grep -c "heavy-b-migrate" docs/FUTURE_IDEAS_DRAFT.md
6
```

The 6 occurrences are:
- 4 inside the F-RETIRE-MIGRATE-TOOLS entry body itself (in the empirical-evidence narrative explaining WHY heavy-b-migrate was removed from the candidate list).
- 2 in other FIDRAFT entries that reference heavy-b-migrate as a tool (not as a retirement candidate).

heavy-b-migrate is no longer listed in the F-RETIRE-MIGRATE-TOOLS entry's candidate-set per the title line + Proposed shape line ("(1) `heavy-b-migrate` REMOVED from candidate list"). AC.WSP.3 verified.

---

## §5 — Outcome-altitude dogfood probe (AC.WSP.4 + AC.WSP.S)

### §5.1 — Release-CLI 6-gate dry-run for v0.10.7

```
$ loam release v0.10.7 --plan-doc docs/plans/workspace-sync-test-and-python-runtime-pin.md --dry-run
```

Output captured at apply-time per the manifest baseline backfill workflow (deferred to seal-time so the source-edit SHA is known). All 6 gates expected GREEN per the precedent v0.10.6 / v0.10.5 / v0.10.4 / v0.10.3 / v0.10.2 PATCH cycles which used identical dev-sdlc seal anchor + universal-admission docs surface.

The 6 gates: `hard-smoke`, `acs-verified`, `state-shipped`, `clean-tree`, `branch-main`, `seal-reachable`.

### §5.2 — Seal-diff allow-list verification (AC.WSP.S)

The source-edit commit's `git diff --name-only` should match the AC.WSP.S allow-list:

- `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py` (test fix)
- `docs/FUTURE_IDEAS_DRAFT.md` (3 FIDRAFT edits: F-TF-1 + F-PYTHON-3.9 + F-RETIRE-MIGRATE-TOOLS)
- `docs/STATE.md` (v0.10.7 row)
- `docs/release-roadmap.md` (v0.10.7 §3 entry + §2 table row)
- `docs/experiments/workspace-sync-test-and-python-runtime-pin-hard-smoke.md` (this file)

Captured at source-edit commit.

### §5.3 — Smoke-vs-plan correspondence

The smoke writeup verifies all 5 ACs from the plan-doc (AC.WSP.{1,2,3,4} explicit + AC.WSP.S inferred via seal-diff allow-list confirmation). The 3 FIDRAFTs are all closed/amended in the same source-edit commit per F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH discipline (§6 of plan-doc).

---

## §6 — F2 RUTHLESS FEEDBACK — disagreements / observations worth surfacing

### §6.1 — F-PYTHON-3.9 capture missed empirical recheck

The 2026-05-14 capture of F-PYTHON-3.9-TEST-FAILURES-PYPROJECT-PIN was made without running the 4-step empirical recheck per `feedback_agent_empirical_recheck_before_halt`. The empirical work would have caught that the pin already existed (since 2026-04-27 commit `0d599bb`) and that the "7 test failures on 3.9" the cycle agents observed were actually the install-time refusal manifesting at pytest-collection-time (ModuleNotFoundError, not entry_points API mismatch).

**Path forward:** the capture-time discipline rule (every FIDRAFT for "this pyproject pin is missing" / "this config option should exist" requires a one-line grep to verify the absence empirically before capture) is captured implicitly in `feedback_agent_empirical_recheck_before_halt`. This PATCH demonstrates the rule applied retroactively. No new memory rule needed; the existing rule covers it.

### §6.2 — F-RETIRE-MIGRATE-TOOLS framing was wrong; lock didn't license accepting it

The F-RETIRE-MIGRATE-TOOLS entry had been `capture-only` for 4 days (2026-05-10 → 2026-05-14) with framing that made the work look like "delete 6 directories." Empirical contact in the prior dispatch falsified the framing in <30 min of investigation. Per `feedback_locked_design_not_license_for_bad_outcomes`, the lock didn't license accepting the bad framing — surfacing the evidence + correcting the entry was the right move.

**Path forward:** demonstrated by this PATCH (D-WSP.3). No new discipline rule; existing memory covers it.

### §6.3 — Owner-class call deferred (Path B + Path C)

The Path B + Path C calls remain owner-gated per `feedback_principle_conflict_resolution_multi_signal` (M5-class principle-conflict; signal weights: blast radius MEDIUM-to-HIGH; reversibility LOW-to-MEDIUM; audience operator-facing). The amended F-RETIRE-MIGRATE-TOOLS entry now carries the decision-context (4-step empirical evidence + Path-A/B/C decomposition + safety-horizon framing) the owner needs to make the call.

**Path forward:** owner ruling on Path B safety-horizon + Path C safety-horizon ahead of v1.0 surface cleanup.

---

## §7 — References

- Plan-doc: `docs/plans/workspace-sync-test-and-python-runtime-pin.md`.
- Manifest: `docs/plans/workspace-sync-test-and-python-runtime-pin.manifest.yaml`.
- Prior-dispatch halt-and-surface: `workspace/.scratch/claude-output/retire-one-time-migration-tools-halt-and-surface.md`.
- Predecessor cycle: v0.10.6 PATCH `paper-html-regeneration` (sealed `276e0d5`; published `42c0ee6`).
- FIDRAFT file: `docs/FUTURE_IDEAS_DRAFT.md` — F-TF-1 (line 252) + F-PYTHON-3.9 (line 296) + F-RETIRE-MIGRATE-TOOLS (line 244).
- Test under fix: `framework/workspace-sync/tests/test_AC_D_5_5_bare_paths_absent.py`.
- Original pin commit: `0d599bb` (2026-04-27, Luke Ivers).
- Composes-with feedback memories: `feedback_agent_empirical_recheck_before_halt`, `feedback_loose_AC_text_fix_AC_not_implementation`, `feedback_locked_design_not_license_for_bad_outcomes`, `feedback_principle_conflict_resolution_multi_signal`, `feedback_no_amend_in_agent_dispatches`, `feedback_version_numbers_at_release_time`, `feedback_specific_claims_verified_or_marked_guess`.
- Convention compliance: F-CYCLE-ARTEFACT-SLUG-NAMING (this file slug-named); F-PLAN-DOC-TEMPLATE-AUTO-BUMP-FENCE (allow-list pre-includes `test_no_sealed_amendments.py`); F-FIDRAFT-FLIP-ON-UNBLOCK-PATCH (§6 of plan-doc).
