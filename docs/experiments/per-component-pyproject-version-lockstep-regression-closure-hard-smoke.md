# PATCH — per-component pyproject version lockstep regression closure — HARD smoke

**Date:** 2026-05-23.
**Plan-doc:** `docs/plans/per-component-pyproject-version-lockstep-regression-closure.md`.
**Manifest:** `docs/plans/per-component-pyproject-version-lockstep-regression-closure.manifest.yaml`.
**ACs covered:** AC.PCVR.{1,2,3,4} + AC.PCVR.S.

## Outcome shape

Defects against v0.8.0 AC.HONEST.1 outcome shape (per-component-version
discipline established). The discipline silently broke between v0.10.0
(last honored at commit `3354f73`) and v0.11.0 / v0.12.0 (skipped). 27
in-scope component pyprojects were at `0.10.0`; target current shipped
MINOR `0.12.0` per D-NFCLEAN.4 (v0.8.1) + D-SDPD (v0.8.2) precedents.
4 measurement / experimental harness pyprojects at `0.0.0` excluded per
plan §16 finding #1 ruling.

## AC.PCVR.4 outcome-altitude probe — mutation-detection result

Probe: `test_AC_PCVR_4_mutation_detection_proves_assertion_fires` in
`plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`.

Method: write a fixture pyproject under `tmp_path` with `version =
"0.10.0"`; invoke `assert_pyproject_version_lockstep` against the
fixture tree with `expected_version="0.12.0"`; assert the helper
raises with the corrective-message header `"Pyproject version drift"`,
the drifted file path, and both stale + expected version strings; then
rewrite the fixture to `version = "0.12.0"`; assert the helper passes.

Result (verbatim from `python3.13 -m pytest plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py -v`):

```
plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py::test_AC_PCVR_3_pyproject_version_lockstep_against_active_minor PASSED [ 20%]
plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py::test_AC_PCVR_3_excluded_pyprojects_are_present_and_unbumped PASSED [ 40%]
plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py::test_AC_PCVR_4_mutation_detection_proves_assertion_fires PASSED [ 60%]
plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py::test_AC_PCVR_4_mutation_detection_missing_file_surfaces PASSED [ 80%]
plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py::test_AC_PCVR_4_anchor_file_resolution_works_from_test_dir PASSED [100%]

============================== 5 passed in 0.02s ===============================
```

Mutation detected end-to-end. AC.PCVR.4 verdict GREEN.

## Sweep verification (AC.PCVR.1)

```
$ grep -E '^version = "' framework/*/pyproject.toml framework/tools/*/pyproject.toml plugins/**/pyproject.toml | sort -u
```

27 in-scope files all at `version = "0.12.0"`. 4 excluded files all at
`version = "0.0.0"` (handsoff-loop, loam-spawn-isolation,
programbench-revival, programbench-revival/realpb). 31 pyproject files
total enumerated by `find . -name pyproject.toml -not -path '*/.venv/*'
-not -path '*/.git/*' -not -path '*/docs/archive/*' -not -path
'*/node_modules/*'`.

## Anchor verification (AC.PCVR.2)

```
$ cat docs/ACTIVE_MINOR
0.12.0
```

One-paragraph header explanation landed in
`docs/release-versioning-policy.md` ("Per-component pyproject version
anchor" section) explaining the file's role + the discipline + the
exclusion set.

## Regression closure summary

After this PATCH lands the discipline is structurally enforced:
`pytest plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py`
goes RED if any in-scope pyproject's `version` drifts from
`docs/ACTIVE_MINOR`. The v0.11.0 → v0.12.0 silent-skip failure mode
cannot recur silently — the next MINOR must bump the anchor + sweep the
27 in-scope pyprojects together or the test fires.

F-PCV-1 (v0.8.1 FIDRAFT capture proposing per-component patch-number
bumps for PATCHes) is moot under the established D-NFCLEAN.4 + D-SDPD
ruling (PATCHes ride predecessor MINOR; per-component-version discipline
advances with MINORs only); this PATCH closes the regression while
honoring that ruling.

## Halt-and-surface findings (build-time)

**Finding (F2 RF on plan-doc count claim):** plan-doc §3 prose claims "26
in-scope" but the §3 PRIMARY list enumerates 27 files and Tier-0
filesystem reality confirms 27 in-scope + 4 excluded = 31 pyproject files
(not 26 + 4 = 30 as plan-doc §16 finding #5 stated). The discrepancy is
harmless to the build — every in-scope pyproject was swept; every
excluded pyproject stayed at `0.0.0` — but the plan-doc's count is
internally inconsistent (the §3 list count contradicts the §3 prose
count). The regression test's `IN_SCOPE_PYPROJECTS` allowlist encodes
the verified 27-file set. Surfaced for the dispatcher to fold into the
final consistency review or to optionally correct the plan-doc prose
post-seal (doc-only correction, no AC implication).

No other halt-and-surface findings at build-time.
