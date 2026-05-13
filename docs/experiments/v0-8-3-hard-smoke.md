# v0.8.3 HARD smoke writeup — `acs-verified` gate accepts REMOVED as a non-failure verdict

**Date:** 2026-05-13. **Build cycle:** v0.8.3 PATCH (third orthogonal defect closure on the v0.6.0 release-process outcome shape — `check_acs_verified` now recognises REMOVED as a non-failure verdict alongside GREEN; closes the last gate-side defect surfaced by the v0.9.0 paper publish flow).
**Plan-doc:** `docs/plans/v0-8-3-acs-verified-removed-verdict-parser.md`.
**Component fence:** `framework/tools/loam/` (release-CLI: gates.py verdict-loop extension + new test file `test_AC_RVG_removed_verdict.py`) + universal-admission docs.

**Verdict: GREEN.** Aggregate verdict for v0.8.3 AC.RVG.{1,2,3,4,S}: ok. The REMOVED verdict is recognised by `check_acs_verified` in both the canonical table-row form and the prose em-dash form; missing-verdict still RED (regression preserved); backward-compat preserved (82 existing release-CLI tests pass unmodified); AC.RVG.4 dogfood probe against the live paper-publish artefacts returns all 6 gates GREEN post-patch.

---

## §1 — AC.RVG.4 outcome-altitude dogfood probe

**Probe shape:** real production entry-point (`loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run`) invoked against the live paper-publish artefacts that already exist on HEAD (v0.9.0 SHIPPED LOCAL at seal `4a4535f`; paper plan-doc carries `| AC.ODDPAPER.3 | REMOVED | Build-time D-ODDPAPER.5.2 Path C — ... |` in §status verdict matrix).

Per `feedback_test_outcome_altitude_required` at least one AC must verify against the real production surface; AC.RVG.4 is that AC. The probe also closes the v0.8.2 AC.SDPD.4 dogfood's outstanding RED on `acs-verified` (which was the v0.8.3 build's motivating defect).

### Stage 1 — Pre-v0.8.3 baseline (verified at v0.8.2 seal `a54295f`)

Before v0.8.3's source edit, the dogfood probe returned 5 GREEN + 1 RED on `acs-verified` for the REMOVED-marker recognition gap:

```
$ loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run
== Pre-publish gates ==
  [GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md
  [RED] acs-verified: plan-doc docs/plans/odd-paper-methodology-publish.md §status does not mark these ACs GREEN: AC.ODDPAPER.3. Backfill §status (or §13) with the verdict matrix; each AC must appear with a GREEN marker. Re-run once backfilled.
  [GREEN] state-shipped: v0.9.0 marked SHIPPED in docs/STATE.md
  [GREEN] clean-tree: working tree clean
  [GREEN] branch-main: on branch main
  [GREEN] seal-reachable: seal 4a4535f reachable from HEAD

FAIL: 1 gate(s) RED; aborting. Address the corrective hints above + re-run.
```

The `acs-verified` RED was a false-positive: AC.ODDPAPER.3 was legitimately struck at build-time per D-ODDPAPER.5.2 Path C (stale HTML couldn't be regenerated; ship dropped that AC; markdown-only). The §status matrix records this as `| AC.ODDPAPER.3 | REMOVED | Build-time D-ODDPAPER.5.2 ... |`. The pre-v0.8.3 parser recognised only `GREEN` as a pass token, so the structurally-complete REMOVED verdict tripped the gate.

### Stage 2 — Post-v0.8.3 source-edit probe

After v0.8.3's source edit (verdict-loop extension in `check_acs_verified` adding the REMOVED proximity-pattern), the dogfood probe was re-run from `/Users/lukeivers/loam/`:

```
$ loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run
== Pre-publish gates ==
  [GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md
  [GREEN] acs-verified: all 5 AC(s) verified (GREEN or REMOVED) in docs/plans/odd-paper-methodology-publish.md §status
  [GREEN] state-shipped: v0.9.0 marked SHIPPED in docs/STATE.md
  [RED] clean-tree: uncommitted changes in canonical tree:
  M framework/tools/loam/src/loam_cli/release/gates.py
  ?? framework/tools/loam/tests/test_AC_RVG_removed_verdict.py
Commit, stash, or revert; re-run.
  [GREEN] branch-main: on branch main
  [GREEN] seal-reachable: seal 4a4535f reachable from HEAD

FAIL: 1 gate(s) RED; aborting. Address the corrective hints above + re-run.
```

`acs-verified` flipped from RED → GREEN. The new success message names the §4-declared AC count (5: AC.ODDPAPER.{1,2,3,4,S}) and the two recognised verdicts (GREEN or REMOVED). AC.ODDPAPER.3 (REMOVED) is recognised alongside the four GREEN-verdict ACs.

The `clean-tree` RED is expected at this snapshot (uncommitted source-edit + new test file mid-build). Per `feedback_serialize_amendment_builds`, the working tree clears after the source-edit commit lands; the clean-tree RED is not a gate-logic finding.

### Stage 3 — Post-seal probe (all 6 gates GREEN)

After the source-edit + apply + seal commits land, the dogfood probe was re-run a third time from a clean working tree:

```
$ loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run
== Pre-publish gates ==
  [GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md
  [GREEN] acs-verified: all 5 AC(s) verified (GREEN or REMOVED) in docs/plans/odd-paper-methodology-publish.md §status
  [GREEN] state-shipped: v0.9.0 marked SHIPPED in docs/STATE.md
  [GREEN] clean-tree: working tree clean
  [GREEN] branch-main: on branch main
  [GREEN] seal-reachable: seal 4a4535f reachable from HEAD

OK: all 6 gates GREEN. Dry-run only; no tag, no push (per --dry-run flag).
```

(See §3 for the verbatim post-seal capture.) All 6 gates GREEN. The v0.6.0-substrate gate defects surfaced by the v0.9.0 paper publish flow are now fully closed:

1. v0.7.2 closed the §4-scoping defect (cross-reference AC IDs in §6/§8/§13 wrongly flagged).
2. v0.8.2 closed the version-slug-glob defect (added `--plan-doc` flag for scope-descriptive plan-docs).
3. v0.8.3 (this PATCH) closes the REMOVED-verdict-recognition defect.

The v0.9.0 paper publish can now run through `loam release` cleanly when the owner gates publish — no manual fallback needed for gate-side reasons.

---

## §2 — Test suite verification

Full release-CLI test suite at post-source-edit state:

```
$ /opt/homebrew/opt/python@3.13/bin/python3.13 -m pytest framework/tools/loam/tests/ -v
...
======================== 86 passed in 9.72s ========================
```

Breakdown:

- 82 existing release-CLI tests (v0.6.0 + v0.7.2 + v0.7.3 + v0.7.4 + v0.8.0 + v0.8.1 + v0.8.2): GREEN unmodified.
- 4 new AC.RVG.* tests at `test_AC_RVG_removed_verdict.py`: GREEN.

Backward-compat verified: the v0.6.0 default behaviour (GREEN-only recognition) is preserved as the first proximity-pattern in the verdict-loop; the REMOVED pattern is a fall-through only reached when GREEN doesn't match. Plan-docs that don't use REMOVED at all (every release-CLI test fixture) take the GREEN-only code path verbatim.

### Per-AC test mapping

- **AC.RVG.1** — `test_acs_verified_green_when_status_marks_ac_removed_table_form` (canonical table-row form; matches the live paper plan-doc shape).
- **AC.RVG.2** — `test_acs_verified_green_when_status_marks_ac_removed_em_dash_form` (prose form for plan-docs without a verdict-matrix table).
- **AC.RVG.3** — `test_acs_verified_red_when_status_omits_ac_entirely` (missing-verdict regression: §4-declared AC with NEITHER GREEN nor REMOVED still RED).
- **Regression** — `test_acs_verified_green_when_all_acs_green_regression` (v0.6.0 default unchanged).

---

## §3 — Verbatim post-seal CLI capture

Captured at HEAD = `6024faf` (seal commit) on 2026-05-13:

```
$ loam release v0.9.0 --plan-doc docs/plans/odd-paper-methodology-publish.md --dry-run
== Pre-publish gates ==
  [GREEN] hard-smoke: HARD smoke GREEN at docs/experiments/odd-paper-methodology-publish-hard-smoke.md
  [GREEN] acs-verified: all 5 AC(s) verified (GREEN or REMOVED) in docs/plans/odd-paper-methodology-publish.md §status
  [GREEN] state-shipped: v0.9.0 marked SHIPPED in docs/STATE.md
  [GREEN] clean-tree: working tree clean
  [GREEN] branch-main: on branch main
  [GREEN] seal-reachable: seal 4a4535f reachable from HEAD

DRY-RUN: would create annotated tag v0.9.0 at 4a4535f with message: ...
DRY-RUN: would push origin main + tag v0.9.0
DRY-RUN: would apply post-publish backfill — 5 edit(s):
  - STATE.md: replaced 'v0.9.0 SHIPPED LOCAL — owner gates publish.' → '**v0.9.0 SHIPPED PUBLIC 2026-05-13 at tag `v0.9.0` (annotated `4a4535f`)**.'; STATE.md leading title: '**v0.9.0 MINOR SHIPPED LOCAL**' → '**v0.9.0 MINOR SHIPPED PUBLIC**'
  - roadmap §2 row: appended SHIPPED-PUBLIC marker
  - summary line: '**Total shipped:** 9 minor + 21 patches. v0.1.0 → v0.9.0 published.' → '**Total shipped:** 9 minor + 21 patches. v0.9.0 published.'
  - §3 Active Version: appended '**v0.9.0 MINOR (...) SHIPPED PUBLIC 2026-05-13** (tag `v0.9.0`, annotated `4a4535f`; seal `4a4535f`).'

== Next-scope proposal ==
...
```

ALL 6 GATES GREEN at sealed state. The v0.9.0 paper publish is now structurally ready for `loam release` publish pending owner gate per ASK-FIRST.

---

## §4 — Halt-and-surface findings

**No halt-and-surface findings.** AC.RVG.4 dogfood probe surfaced no gate other than `acs-verified` + the expected transient `clean-tree` RED (uncommitted source-edit before commit). Per dispatch-brief HARD HALT #2 ("if AC.RVG.4 dogfood probe surfaces a gate other than `acs-verified` still RED post-patch, surface but DO NOT extend scope"), the only post-patch RED is the transient working-tree state, which clears at source-edit commit time.

The v0.9.0 paper publish is now structurally ready for `loam release` publish when the owner gates it — pending the dispatcher's publish decision per ASK-FIRST.
