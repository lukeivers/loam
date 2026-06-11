# ProgramBench retirement inventory — /Users/lukeivers/loam — 2026-06-11

Owner ruling: full retirement unless cost-prohibitive (decision record
`<pos3>/workspace/.loam/memory/decisions/2026-06-11-programbench-full-retirement.md`,
Discord 1514747695972094165). Inventory produced by a read-only research
agent (45 tool-uses, content-verified classifications); landed by the
dispatcher. Tracked-status for files inside `.run_evidence/` is inferred
from the committed `.gitignore` policy (marked where so), not git-verified.

## Summary table

| Bucket | File count | Action | Est. AI-time |
|---|---|---|---|
| A — LIVE CODE | ~60 whole-file + 3 entangled | Delete via house amendment; 3 surgical edits | 45–90 min (one amendment cycle) |
| B — LIVE DOCS/QUEUE | 11 files | Edit: remove or mark RETIRED | 20–40 min |
| C — SEALED HISTORY | ~27 files | Mark RETIRED banner only; never delete | 15–30 min |
| D — INCIDENTAL | ~45–50 files | Leave as-is (recommendations per group below) | 0 (optional 10–20) |
| **Total** | | | **80–160 min, midpoint ~110 (estimate band)** |

## Bucket A — LIVE CODE

**A1. Whole-file — `framework/tools/programbench-revival/` (entire tree, ~40 tracked files; band 38–42, tracked-status inferred from `.run_evidence/.gitignore`):**
- v2 package: `pyproject.toml`; `src/programbench_revival/{__init__,loader,verdict,scorer,runner,report,arms}.py` (7); `tasks/tasks.json` + `tasks/check_pb{1-6}.py` + `tasks/heldout_pb{1-6}.py` (13).
- realpb package: `realpb/pyproject.toml`; `realpb/src/programbench_revival_realpb/{__init__,runner,report,loader,verdict,upstream_eval}.py` (6); `realpb/tasks/{tasks.json,realpb_structural_floor.py}` (2).
- Committed run evidence (reproducibility-bearing per `.run_evidence/.gitignore` lines 25–27): `.run_evidence/{.gitignore,verdict.json}` + `PB{1-6}-*/disposition.json` (8); `realpb/.run_evidence/{.gitignore,yj/disposition.json}` (2). **Carve-out flag:** these 10 evidence files are the reproducibility substrate the sealed experiment reports cite; deleting them with the tool dir orphans the audit trail in `docs/experiments/programbench-revival-*.md`. Owner decides: delete-with-tool (cheapest) vs move-to-history. Default recommendation: delete — the reports themselves (bucket C) remain the audit record.
- Disk also carries untracked transcripts/work-dirs/`run.log`/`__pycache__` (gitignored) — removed for free with the directory.

**A2. Whole-file — PB-purpose tests in `framework/hands-off-lifecycle/tests/` (20 files, all import `programbench_revival*`, VERIFIED by content grep):**
- `test_AC_PBR_{1,2,3,4,5,6,7}_*.py` (7)
- `test_AC_RPB_{1,2,3,4,5,6,7}_*.py` (7)
- `test_AC_PBD_{1,2,3,4,5,6}_*.py` (6)

**A3. Entangled — surgical edits (3 files, exact symbols):**
1. `framework/hands-off-lifecycle/tests/test_AC_BRC_6_generic_true_replacement.py` — imports `programbench_revival.arms.run_loam_arm` (line 85) and reads `arms.py` via the `ARMS` path constant (lines 38–44). Two of its three tests die with PB; `test_AC_BRC_6_construct_is_generic_not_realpb_specific` (line 96) survives standalone. Either delete the file with a one-test salvage into the BRC suite, or trim to the generic test.
2. `plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py` — `EXCLUDED_PYPROJECTS` lines 113–114 list both PB pyprojects, and line 235 `assert path.is_file()` makes this test **FAIL on deletion** (its own message says "update EXCLUDED_PYPROJECTS ... if the component was retired"). Remove the two tuple entries + the line-28 docstring mention.
3. `framework/workspace-bootstrap/tests/test_AC_LIPW_4_pty_driver_interactive_multiturn.py` — `_resolve_frozen_build_prompt` (lines 198–230) hard-defaults to the pos3 path `/Users/lukeivers/pos3/workspace/experiments/programbench-derivative/harness` and imports `run_agent` from it. Env-gated (`PB_SUBLOAM_REAL_CLAUDE=1`), so default runs skip; but the opt-in SLF.4/SLF.5 end-test leg uses the frozen PB prompt as fixture. Surgical: retire the opt-in leg or re-point to a non-PB frozen prompt. Owner-visible choice.

**Q1 (test-suite breakage): YES, VERIFIED.** Deleting `framework/tools/programbench-revival/` without test edits breaks the default framework test run at three points: the 20 A2 tests (import failures), `test_AC_BRC_6` (2 assertions), and `test_AC_PCVR`'s line-235 existence assert. LIPW_4 breaks only under its opt-in env flag.

**Q2 (hands-off-lifecycle dependency): NO.** The component's production source (`hooks/*.py`, first-run scaffolding) has zero PB matches (VERIFIED by grep across the component); PB lives only in its `tests/` and `seals/` dirs. The `handsoff-loop` tool source (`behavioral_selfcheck.py`, `orchestrator.py`, `cli.py`) carries comment-only realpb mentions — no imports. The generic behavioral-refine-cycle survives PB retirement intact.

## Bucket B — LIVE DOCS/QUEUE (retire by edit)

1. `docs/release-roadmap.md` — queue row line 244 (`binary-usage-observation-harness`), full Candidate 1 section lines 255–296, public-actions row line 557 (ProgramBench leaderboard submission), forward refs lines 73/82/112/156/562–563. The biggest single edit. *(Candidate 1 replacement landed by the dispatcher 2026-06-11 alongside this inventory; the remaining roadmap refs are builder scope.)*
2. `docs/release-roadmap-dependency-map.md` — lines 27, 39, 56–58, 80 (binary-usage-observation-harness HARD dependency rows + the soft-halt note).
3. `docs/FUTURE_IDEAS_DRAFT.md` — PB-substance entries: `F-REALPB-RUNNER-NO-AUTO-REPORT` (line 279), `F-REALPB-EVAL-EMULATION-TIMEOUT-BLOCKS-SCORE` (line 281), `F-INVERTED-FRAME` (line 249, PB corrective experiment) → mark RETIRED. PB-provenance-only entries (`F-EXTRACT-CONVERGE` 243, `F-VERIFIER-LAYERS` 245, `F-RETRY-REGRESSION` 247, `F-MANAGED-BG` 275, `F-SEAL-§14` 277) — substance is generic; leave, optionally annotate. `F-USER-INTERACTIVITY` (271) activation gate says "AFTER ProgramBench-revival plan ratification" → one-line gate edit.
4. `docs/leverage-discipline.md` — lines 94, 120, 123 name ProgramBench as "the primary external benchmark" with per-minor capture: live policy, must be retired/replaced.
5. `docs/plans/harness-benchmark-build.md` — HARP benchmark plan using mini-SWE-agent as floor harness (lines 110, 166, 210, 222, 341). **Owner-rule needed:** mini-SWE-agent is on the retirement term list, but this plan is a broader benchmark programme, not PB itself. Flagged rather than auto-classified.
6. `docs/plans/research/harness-landscape-and-roadmap-rerank.md` (+ its `-plan.md`) — EV.1 ProgramBench submission + RR.3 SWE-bench items as future actions (lines 171–276) → mark RETIRED sections.
7. `docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md` — promotion plan whose source material is the pos3 `programbench-derivative` harness (lines 9–12, 189). Capability is generic; provenance is PB. Recommend mark RETIRED or owner re-scopes.
8. `docs/release-versioning-policy.md` — line 133 names both PB pyprojects in the PCVR exclusion prose; edit in lockstep with the A3.2 test edit.
9. `docs/plans/conventional-install-pypi-publish.md` (+ `.manifest.yaml`) — line 81 exclusion list `programbench-revival*`, line 203 "38-pyproject tree (… 1 realpb)" count goes stale on deletion; two one-line edits.

## Bucket C — SEALED HISTORY (mark RETIRED, never delete)

- Sealed plan-docs + manifests (8): `docs/plans/sealed/programbench-revival-v2.{md,manifest.yaml}`, `programbench-revival-real-pb.{md,manifest.yaml}`, `programbench-revival-realpb-denoise-and-cost-fix.{md,manifest.yaml}`, `v0-4-0-cycle-4-programbench-v0-docs-only-baseline.{md,manifest.yaml}`.
- Experiment reports (3): `docs/experiments/programbench-revival-v2.md`, `programbench-revival-real-pb.md`, `programbench-v0-docs-only.md`. (Note: `test_AC_PBR_7` asserts the v2 report exists — moot once that test is deleted in A2.)
- Seal records (4): `framework/hands-off-lifecycle/seals/SEAL_COMMIT.programbench-revival-{v2,real-pb,realpb-denoise-and-cost-fix}`, `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-4-0-cycle-4-programbench-v0-docs-only-baseline`. Amendment-machinery audit trail — do not delete.
- Committed run-evidence (10, listed in A1) — carve-out decision flagged there.
- Historical master plans: `docs/plans/v0-4-0-master-plan.md`, `v0-3-0-master-plan.md` — completed-work records living outside `sealed/`; leave content, optional RETIRED-scope banner.
- STATE.md change-log entries (lines 3, 171–175, 185, 219–244 region) are dated audit prose — leave verbatim per STATE.md's own retained-verbatim convention. Build-time check: verify line 3 doesn't claim PB as active work (plausible it's historical; unverified).

## Bucket D — INCIDENTAL (leave as-is)

- `framework/tools/handsoff-loop/src/handsoff_loop/{behavioral_selfcheck,orchestrator,cli,behavioral_refine_endtest}.py` — realpb appears in comments/docstrings explaining the BRC ACs' origin; no imports. Leave (comments are accurate history).
- `framework/hands-off-lifecycle/tests/test_AC_BRC_{1,2,3,4,5}_*.py` — generic loop tests; BRC_4's "programbench"/"structural_floor" are forbidden-token strings in a static negative check (lines 55–56, 114) and keep working after deletion. Leave.
- `framework/primary-persona/tests/test_AC_MSC_{1,2,4}_*.py` — "programbench" is inert fixture text in memory-content strings. Leave; renaming has zero retirement value.
- `framework/workspace-bootstrap/tests/test_AC_SLF_{1,2,3}.py`, `test_AC_LIPW_{5,6}.py` — comment citations of PB experiment reports + `pb-` workspace-slug fixtures. Leave.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/build_next.py:566` and `plugins/dev-sdlc/odd-extractor/tests/test_AC_V041_3_tie_breaker.py:10-11` — comments citing the PB Task-2 empirical motivation. Leave (provenance, not dependency).
- ~20 sealed plan-docs/manifests + ~7 experiment reports with passing mentions (telegram-5-fix, subloam-driver-fix, phase-b-intake-fix, loop-*, handsoff-*, memory-session-continuity, odd-paper-methodology-publish, next-scope-walker, release-roadmap-priority-queue-restructure, amendment-143, v0-2-5-1, v0-4-{1,2}, v0-7-0, general-build-from-intent, loam-init-*, per-component-pyproject-*, clean-state-review/release-publish-execution/release-integration-fbm) — sealed history, leave verbatim.
- Misc live plan-docs with audit-context mentions only: `release-roadmap-doc-plan.md`, `session-clear-safety-tracker-register-and-first-run-update-parity.md`, `release-integration-fbm-session-clear-safety-and-stale-status-corrections.md`, `swarming-extraction-composition{,-plan}.md`, `leverage-discipline-plan.md`, `loam-1.0-acceptance-smoke-harness.manifest.yaml` (comment line 31). Leave.
- `docs/plans/claude-p-to-insession-subagent-fanout-slice2-swarm.md` — matched only on AC.BRC (generic loop AC), not PB. Not in the footprint.

## .scratch/ (directory granularity)

Glob for `.scratch/**/*programbench*` under /Users/lukeivers/loam returned nothing — no PB material under canonical `.scratch/`.

## pos3-side references visible from loam files (not scanned; separate cleanup, dispatcher-owned)

1. `/Users/lukeivers/pos3/workspace/experiments/programbench-derivative/harness/` — LIPW_4's hardcoded default (lines 206–207), the promote-multi-channel plan's source material, F-INVERTED-FRAME's `run_agent.py` citation.
2. `<pos3>/workspace/.scratch/claude-output/programbench-*.md` — multiple plan/FIDRAFT pointers (benchmark-v0, v2-plan, leverage-plan, nontech-user-feasibility).
3. pos3 build-report paths cited in STATE.md entries.

## Research-agent findings (ruthless-feedback)

1. **Dispatch-gloss correction:** AC.BRC.* is the **generic behavioral-refine-cycle** of the live handsoff-loop (born from a realpb defect but serving any task) — NOT "benchmark-related ACs." Retiring "BRC" wholesale would delete live non-PB capability. Only `test_AC_BRC_6`'s two PB-coupled assertions retire.
2. **Nothing is cost-prohibitive.** The whole footprint retires in one amendment cycle + a docs pass. The only structural friction points are the three A3 surgical edits, all small.
3. **Two owner calls:** (a) `harness-benchmark-build.md` (HARP/mini-SWE) — in or out of the retirement scope; (b) committed run-evidence — delete with the tool dir (recommended) vs preserve as audit substrate.
