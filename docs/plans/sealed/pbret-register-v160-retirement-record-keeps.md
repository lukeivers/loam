# pbret-register-v160-retirement-record-keeps (PATCH)

**Status:** RATIFIED (owner-ratified corrective — Luke, Discord
2026-06-22, "both plz"). Corrective cycle authorized as JOB A of a
two-job dispatch (clear the guard breach, then complete the held
deliberate-reasoning slice-1 seal).

**Working directory:** `/Users/lukeivers/loam` (canonical loam; branch
per the active corrective branch).

**Class:** PATCH — a justified-keep register addition to an existing
guard (AC.PBRET.5). No production-behaviour change; the guard stays
ENFORCING and uses its designed exception path.

---

## §1 Objective

The ProgramBench retirement-sweep guard
(`plugins/dev-sdlc/tests/test_AC_PBRET_5_programbench_retirement_sweep.py`,
AC.PBRET.5) flags two live ProgramBench references that are legitimate
HISTORICAL retirement-record mentions, not live usages:

- `docs/plans/release-integration-v1-6-0.md`
- `docs/state-migrations/v1-6-0-claude-leverage-and-principle-foundation.migration.yaml`

Both are completed-work v1.6.0 records whose every PB mention
DOCUMENTS the retirement of ProgramBench (the release-integration
record lists "(d) ProgramBench full retirement" as one of the four
bundled v1.6.0 work-slices; the migration yaml records the PB deletions
as a declared no-op state change). They are PRE-EXISTING — last touched
in the v1.6.0 cycle, ancestors of the deliberate-reasoning slice-1
baseline (not in the slice diff). They surfaced now only because the
slice-1 seal's cross-component guard-sweep walks the whole tracked tree.

This is exactly the D-K9 historical-record class the guard's
`REGISTERED_KEEPS` register already covers (precedent: D-K9 / D-K10).

Objective: clear the breach the sanctioned way — register the two files
as justified keeps so the guard PASSES by virtue of the legitimate
register addition, not by weakening the assertion. Do NOT loosen the
guard. Do NOT delete the references (deleting retirement-record prose
falsifies release history — the D-K1/D-K4/D-K5 sealed-history class).

## §2 Named decisions

- **D-1 — keep, not delete.** Both files are documentation OF the
  retirement; removing the mentions would falsify the v1.6.0 release +
  migration record. Keep + register, matching the D-K9 precedent.
- **D-2 — REGISTERED_KEEPS only, not the sealed §10 register.** The plan
  §10 D-PBRET.6 register lives in `docs/plans/sealed/programbench-full-retirement.md`
  (sealed history). Editing it would rewrite the owner-carved-out audit
  trail (D-K1/D-K2). Per the established D-K10 precedent (test lines
  97-104), a build-time keep whose §10 register has sealed is recorded
  in this test's `REGISTERED_KEEPS` and surfaced in the build report.
  This corrective follows that precedent exactly under a new D-K11
  sub-block.
- **D-3 — guard stays enforcing.** The mutation-detection test
  (`test_AC_PBRET_5_mutation_injected_stray_mention_goes_red`) is
  unchanged and still goes RED on an injected stray live mention. The
  assertion is not weakened; only the justified-keep allowlist grows by
  the two legitimately-historical files.

## §3 Halt triggers (satisfied at build time)

- If re-verification showed EITHER file's PB mentions were live/active
  usages rather than historical records, HALT and surface — fix would
  differ. RESULT: re-verification confirmed both files are purely
  historical retirement-records; no live usage. Proceeded.

## §4 Acceptance criteria

- **AC.PBRET.5** (existing) — the production sweep returns zero
  unaccounted live PB references. Satisfied by the D-K11 register
  addition: both flagged files become accounted-for justified keeps.
  The mutation-detection sibling stays RED on injected strays (guard
  not weakened).

No NEW AC family is introduced; this corrective ladders up to the
existing AC.PBRET.5 via its designed REGISTERED_KEEPS exception path.

## §5 Fence

Single sealed component: `dev-sdlc`. The only source surface touched is
`plugins/dev-sdlc/tests/test_AC_PBRET_5_programbench_retirement_sweep.py`
(inside the `plugins/dev-sdlc/` fence). The two flagged files are
READ-ONLY inputs (re-verified, not edited).

## §14 Method-decision register (populated at build + seal time)

SHA register: TBD-AT-SEAL (source …; apply …; seal …).

### Commit SHAs

- Amendment commit: `fea022dac8c212a9d8bd995bc5ab250826e3e2a9` —
  `chore(amend): pbret-register-v160-retirement-record-keeps manifest+apply — dev-sdlc BASELINE+sidecar bump to 6542865`
- Seal commit: `dfda5bbff1a7da77f65f7764ada50354c42fed4e` —
  `chore(seals): pbret-register-v160-retirement-record-keeps — dev-sdlc at fea022d`
