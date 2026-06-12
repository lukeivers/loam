# programbench-full-retirement — sub-plan-doc

Status: PLAN AUTHORED 2026-06-11 — awaiting owner ratification of
  D-PBRET.1 (HARP verdict, §10) before the build dispatch; all other
  legs execute owner rulings already recorded.
WD: /Users/lukeivers/loam (canonical loam; LOCAL only, NO push).
Class: PATCH/MIXED (DEV) — one code amendment cycle + a docs pass,
  per roadmap §4 Candidate 1.
Parent context: docs/release-roadmap.md §4 Candidate 1
  (`programbench-full-retirement`; owner-calls section RULED at
  `9bf9099c`, 2026-06-11).
Predecessors (load-bearing, Tier-0 re-verified this authoring pass):
  - `9a7723aa` — classified retirement inventory landed
    (docs/plans/research/programbench-retirement-inventory-2026-06-11.md)
    + Candidate 1 replacement; `9bf9099c` — the three owner calls RULED.
  - Owner rulings: Discord 1514747695972094165 (full retirement) +
    1514752072900284416 (the three calls); decision records
    `<pos3>/workspace/.loam/memory/decisions/2026-06-11-programbench-full-retirement.md`
    and `…/2026-06-11-programbench-retirement-three-owner-rulings.md`.
  - Sealed PB lineage (bucket C anchors, never reopened by this cycle):
    seals `e273966` (v2), `5694ff2` (real-pb), `bfe76fc` (denoise),
    v0-4-0 C4 baseline seal record under plugins/dev-sdlc/seals/.
BASELINE candidate: `95068b35` (main tip at plan-authoring; builder
  re-walks if HEAD has moved — not the apply-time pin).
Quality bar: retirement must not regress any live capability — the
  generic behavioral-refine-cycle (AC.BRC.*) and every non-PB suite
  stay green; sealed history stays byte-meaning-intact under banners.

## §1 Objective / TL;DR

Outcome (roadmap Candidate 1, verbatim): **no live loam artefact treats
ProgramBench as current or future work.** PB-purpose code and tests are
deleted via the house amendment process; live docs/queue/policy
references are removed or marked RETIRED; sealed history (plan-docs,
manifests, seal records, experiment reports) is banner-marked RETIRED
and never deleted or rewritten; incidental passing mentions are removed
unless a given removal is genuinely expensive, with each kept mention
justified in this plan (§10 D-PBRET.6 register).

Tier-0 re-verified state at `95068b35` (re-run this authoring pass, not
taken from the inventory):

1. **Bucket A counts CONFIRMED.** `git ls-files
   framework/tools/programbench-revival/` = 40 tracked files (inventory
   band 38–42). Exactly 20 PB-purpose test files
   (`test_AC_{PBR,RPB,PBD}_*`) under
   framework/hands-off-lifecycle/tests/. The ONLY other live `.py`
   importing `programbench_revival` is
   test_AC_BRC_6_generic_true_replacement.py.
2. **The three default-run breakage points CONFIRMED still the only
   three:** (a) the 20 A2 tests (import failures on deletion); (b)
   test_AC_BRC_6's PB-coupled tests; (c) test_AC_PCVR's
   `EXCLUDED_PYPROJECTS` lines 113–114 + line-235 `path.is_file()`
   assert. LIPW_4 breaks only under its `PB_SUBLOAM_REAL_CLAUDE=1`
   opt-in flag (lines 206–207 hardcode the pos3 PB-derivative path).
3. **Inventory correction (named, §16.1):** test_AC_BRC_6 has FIVE
   tests, not three. THREE are PB-coupled and retire (lines 47, 58, 76 —
   all read `arms.py` via the `ARMS` constant; the third also imports
   `programbench_revival.arms`). TWO are generic and survive (line 96
   `construct_is_generic_not_realpb_specific`, line 115
   `no_op_in_loop_check_is_refused` — both import only
   `handsoff_loop.behavioral_selfcheck`). The constraint's substance
   (generic AC.BRC.6 coverage survives) is unchanged; the counts in the
   inventory/roadmap gloss ("two of three", "two PB-coupled
   assertions") were wrong.
4. **HARP usefulness assessment run (owner call #1):** verdict **KILL**
   — full evidence at §10 D-PBRET.1. Zero live consumers; never
   started; dormant since 2026-05-08.
5. **Case-sensitivity finding:** PB mentions appear as `programbench`,
   `ProgramBench`, AND `realpb` (e.g. test_AC_MSC_2 carries only the
   capitalized form; handsoff-loop docstrings carry only `realpb`). The
   AC.PBRET.5 sweep MUST be case-insensitive over both stems or it
   under-counts.

AC family: AC.PBRET.* (6 ACs; AC.PBRET.5 outcome-altitude). Fence:
single anchor `dev-sdlc` + sweep-precedent universal admissions (§5).

## §2 Placement decisions

| Surface | Placement | Rationale |
|---|---|---|
| Tool-tree deletion | `framework/tools/programbench-revival/` removed whole (40 tracked files incl. both pyprojects + 10 committed run-evidence files per owner call #2) | A1; run-evidence DELETE ruled (Discord 1514752072900284416 call 2) — bucket C experiment reports remain the audit record |
| Test deletions/trims | framework/hands-off-lifecycle/tests/ (20 files + BRC_6 trim), plugins/dev-sdlc/tests/ (PCVR edit), framework/workspace-bootstrap/tests/ (LIPW_4 edit) | A2/A3 — the three breakage points (§1.2) |
| Incidental-mention removals | framework/primary-persona/tests/, framework/workspace-bootstrap/tests/, framework/tools/handsoff-loop/src/, plugins/dev-sdlc/odd-extractor/ | Bucket D widened per owner call #3; dispositions in §10 D-PBRET.6 |
| Docs/queue/policy edits | docs/release-roadmap.md, release-roadmap-dependency-map.md, FUTURE_IDEAS_DRAFT.md, leverage-discipline.md, release-versioning-policy.md, docs/plans/* live docs | Bucket B |
| RETIRED banners | docs/plans/sealed/ (8), docs/experiments/ (3), seals/ narratives (4), v0-3-0/v0-4-0 master plans (optional banner per inventory) | Bucket C — banner only, content otherwise unchanged |
| Sweep test | builder's call on path; recommended under plugins/dev-sdlc/tests/ (repo-hygiene class, runs in default suite) | AC.PBRET.5 carrier |
| Plan pair + sealed narrative | docs/plans/ universal admission | house convention |

## §3 Scope

In scope:

- Bucket A: tool-tree deletion (run-evidence included, RULED); 20 test
  deletions; the three surgical edits (BRC_6 trim, PCVR exclusion-pair
  removal + docstring, LIPW_4 opt-in-leg retirement per D-PBRET.4).
- Bucket B: all 9 inventory items (the HARP item resolves per
  D-PBRET.1's owner ruling) — treat the inventory's line numbers as
  hints, term-search each file; roadmap line refs have already drifted
  ~10 lines since the inventory (Tier-0 observed this pass).
- Bucket C: RETIRED banners on the 8 sealed plan-pair files, 3
  experiment reports, 4 seal-record narratives (D-PBRET.8), and the two
  historical master plans.
- Bucket D (WIDENED per owner call #3): remove incidental mentions per
  the §10 D-PBRET.6 disposition register; kept mentions are ONLY those
  in the register, each with its justification.
- The AC.PBRET.5 sweep + standard `loam amend apply`/`seal` bookkeeping
  (the named bookkeeping mechanism for this cycle) + §9 items.

Out of scope (deferred / not this fence):

- pos3-side PB material (inventory "pos3-side" section: the
  `programbench-derivative` experiment tree, `.scratch/claude-output`
  PB files, the HARP companion survey at
  `<pos3>/workspace/.scratch/claude-output/harness-benchmark-survey-2026-05-04.md`)
  — dispatcher-owned cleanup, named here so it isn't lost.
- Replacing the external-benchmark policy slot that
  docs/leverage-discipline.md loses (the edit REMOVES PB as "primary
  external benchmark"; naming a successor benchmark is a separate
  owner-class decision — see §10 F2.2).
- git history rewriting of any kind; deleting/rewriting anything under
  docs/plans/sealed/, docs/experiments/, or seals/.
- docs/spec/ (outside any cycle's fence) and version assignment
  (derives at release time; this plan pre-assigns nothing).
- Pushing (LOCAL only).

## §4 Acceptance criteria

| ID | Outcome | Verification |
|---|---|---|
| AC.PBRET.1 | **PB-purpose code is gone.** `framework/tools/programbench-revival/` has zero tracked files; the 20 `test_AC_{PBR,RPB,PBD}_*` files and BRC_6's three PB-coupled tests are gone; test_AC_PCVR carries no PB pyproject entries; test_AC_LIPW_4 carries no PB path/fixture. | `git ls-files` over the tree empty; targeted greps over the named test surfaces return zero PB hits. |
| AC.PBRET.2 | **No live capability regressed.** The default framework test run (per-component pytest suites across framework/ + plugins/) is GREEN, including the surviving generic AC.BRC suite (BRC_1–5 + BRC_6's two generic tests) and the surviving SLF/LIPW/MSC/PCVR siblings. | Full default run exit 0; surviving BRC_6 generic tests assert the live handsoff-loop construct, collected + passing. |
| AC.PBRET.3 | **Live docs/queue/policy carry no PB-as-current-or-future-work.** Every bucket B surface reads correctly post-edit: no queue row, dependency edge, policy designation, public-action row, or forward-looking sentence treats PB (or the retired binary-usage-observation-harness candidate) as pending work. | Term-search over the bucket B file set: remaining hits are only §10-registered keeps or RETIRED-marked text. |
| AC.PBRET.4 | **Sealed history bannered, not rewritten.** Each bucket C file carries a dated RETIRED banner (YAML-comment form in manifests) and its pre-existing content is otherwise byte-unchanged. | Per-file diff = banner hunk only; banner present in all enumerated files. |
| AC.PBRET.5 (outcome-altitude: true) | **Zero unaccounted live PB references, structurally enforced.** A sweep executed from the production test entry-point (part of the default run, no pre-arranged state) walks the tracked tree case-insensitively for the `programbench` and `realpb` stems and passes ONLY when every hit is inside sealed/bannered history (docs/plans/sealed/, docs/experiments/, seals/, the historical-record surfaces) or an explicitly enumerated justified-keep from the §10 register; an injected stray live mention makes it fail. | The sweep test runs green in the default suite at seal; a mutation fixture (temp tree or equivalent) proves it goes RED on an unregistered live mention (per `feedback_test_outcome_altitude_required` — not a no-op). |
| AC.PBRET.6 | **HARP disposition executed as ruled.** Under the recommended-and-ratified KILL: `docs/plans/harness-benchmark-build.md` is deleted (recoverable from git history). If the owner overrides to KEEP: the file instead carries a banner scoping it as PB-independent, with its PB/mini-SWE-floor references retired-marked, and it enters the §10 register. | File absent (KILL) or bannered + registered (KEEP); sweep (AC.PBRET.5) consistent with the ruling either way. |

Method-in-AC check passed per AC: each pins WHAT (tree absent, suites
green, docs clean, banners present, sweep closed, ruling executed) and
is satisfiable by any mechanism — e.g. the sweep could be a pytest
walking `git ls-files`, a subprocess `git grep` wrapper, or a manifest-
driven allowlist check; the LIPW_4 edit could trim or restructure the
opt-in leg so long as no PB path/fixture remains and siblings stay
green.

Ladder-up: AC.PBRET.* → roadmap §4 Candidate 1 objective (no live
artefact treats PB as current/future work) → Lens 0 protection floor
(the failure that prompted the ruling was stale context betraying the
owner: a cancelled candidate kept resurfacing as next-build because the
cancellation was never recorded into the artefacts agents read) →
AC.PO.2.

## §5 Sealed-component fence

- Fence anchor: `dev-sdlc` (seal_test
  `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`, sidecar
  `plugins/dev-sdlc/tests/SEAL_COMMIT`), per the
  per-component-pyproject-lockstep sweep precedent (roadmap §2: single
  fence-anchor + universal_paths admitting `framework/` + `plugins/`
  for a many-component sweep) — named decision D-PBRET.2.
- Universal admissions: `framework/`, `plugins/`, `docs/plans/`,
  `docs/experiments/` prefixes + the named docs files (roadmap,
  dependency map, FUTURE_IDEAS_DRAFT, STATE, leverage-discipline,
  release-versioning-policy). See the manifest.
- Sealed-component surfaces whose FILES change under the sweep
  admission: hands-off-lifecycle, workspace-bootstrap, primary-persona,
  handsoff-loop (tool), odd-extractor — test/comment/fixture surfaces
  only; zero production-logic changes outside deletions named in §3.
  `framework/tools/programbench-revival/` itself has no seal sidecar
  (Tier-0: no tests/SEAL_COMMIT) — it was always admitted via its
  consuming amendments' fences.
- NOT in fence: docs/spec/; any content change (beyond banners) under
  docs/plans/sealed/, docs/experiments/, seals/.

## §6 Halt triggers (build-time)

1. Tier-0 re-check at the build's HEAD contradicts §1 (a NEW live
   consumer of `programbench_revival*` appeared; a fourth default-run
   breakage point) — halt, the inventory is stale.
2. Any non-banner byte change would be needed inside docs/plans/sealed/,
   docs/experiments/, or seals/ to satisfy an AC — halt; sealed history
   is owner-locked ("I don't mind leaving the sealed stuff").
3. A surviving generic test (BRC_1–5, BRC_6 generic pair, SLF, LIPW_5/6,
   MSC) cannot stay green without weakening its assertion — halt;
   retirement must not regress live capability (quality bar).
4. A bucket-D removal turns out genuinely expensive beyond the §10
   register's anticipation — do NOT silently keep it; add it to the
   register via halt-and-surface (the register is the owner-visible
   keep list).
5. `docs/FUTURE_IDEAS_DRAFT.md` is dirty at build time (it is the
   dispatcher's live capture surface and was dirty at plan-authoring) —
   halt-and-surface for the dispatcher to land their capture, then
   apply the B3 edits; never stash-edit a file another role is writing.
   At SEAL time, a dirty FIDRAFT follows the release-flow §14 precedent
   (stash → seal → stash-pop + sha256 verify, autonomous, record in
   §14) ONLY if this cycle made no FIDRAFT edits in the same window;
   otherwise halt.
6. D-PBRET.1 (HARP) not yet owner-ratified when the build reaches the
   HARP leg — execute everything else, hold that leg, surface.
7. Any other dirty state at dispatch/seal beyond the expected FIDRAFT —
   halt.

## §7 Build steps (method-level guidance; mechanics are the builder's call)

1. `cd /Users/lukeivers/loam && pwd && git log -1 --oneline` — verify
   WD; re-walk BASELINE if HEAD moved past `95068b35`.
2. Author the AC.PBRET.5 sweep test FIRST against the current tree —
   expect RED with a hit-list that should reconcile with the inventory
   ±the §16 corrections (this is the build's own Tier-0 re-count; halt
   trigger 1 checks against it).
3. Bucket A: delete the tool tree + 20 tests; trim BRC_6 to its two
   generic tests (drop the `PBR_SRC`/`ARMS` plumbing, lines 36–44, with
   the three PB-coupled tests); PCVR surgical edit (two tuple entries +
   line-28 docstring mention); LIPW_4 per D-PBRET.4.
4. Bucket D code surfaces per the D-PBRET.6 register.
5. Bucket B docs pass (term-search per file; line numbers are hints
   only). Roadmap bookkeeping per §9.
6. Bucket C banners (dated, uniform wording; YAML-comment form in
   manifests; D-PBRET.8 for seal narratives).
7. Default framework test run GREEN (AC.PBRET.2) + sweep GREEN
   (AC.PBRET.5, including its mutation-detection fixture).
8. `loam amend apply` + `loam amend seal` against this plan's manifest;
   §14 register backfill. LOCAL only — no push. Commit ladder small +
   frequent (stall-resume discipline).

## §9 Bookkeeping (rides the cycle)

- docs/release-roadmap.md: remove queue row (`binary-usage-observation-
  harness`) + public-actions PB-leaderboard row + the live forward
  mention in the calibration line (§4 keep-rules apply to §2 historical
  rows); collapse/mark Candidate 1 per the §7 roadmap protocol at seal.
- docs/release-roadmap-dependency-map.md: drop the
  binary-usage-observation-harness HARD-dependency rows + soft-halt
  note (inventory B2 lines re-verified shapes, not numbers).
- docs/STATE.md: change-log entries stay verbatim (KEEP class, §10
  register); add this cycle's entry at seal per house convention.
- FIDRAFT (after halt-trigger-5 coordination): mark RETIRED
  `F-REALPB-RUNNER-NO-AUTO-REPORT`,
  `F-REALPB-EVAL-EMULATION-TIMEOUT-BLOCKS-SCORE`, `F-INVERTED-FRAME`;
  one-line gate edit on `F-USER-INTERACTIVITY-ADAPTIVE-SCOPE-DIAL`
  (drop the "AFTER ProgramBench-revival plan ratification" gate);
  PB-provenance-only entries get the D-PBRET.6 pointer rule.

## §10 Named decisions (recommendations are the decision; owner rules only where flagged)

### D-PBRET.1 — HARP (`docs/plans/harness-benchmark-build.md`): **KILL** — owner call #1's conditional resolved by Tier-0 evidence. OWNER-GATED: surface with this plan's summary; build executes only the ratified verdict (AC.PBRET.6, halt trigger 6).

Owner ruling (Discord 1514752072900284416): "If the harness is
genuinely useful to us then we can keep it but otherwise kill it."
Usefulness test run this pass, all Tier-0:

1. **Zero live consumers.** Repo-wide grep for
   `harness-benchmark-build` / `HARP` / `PRISM` / `harp-eval`: every
   hit outside the plan itself is (a) the roadmap owner-call line, (b)
   the retirement inventory, or (c) three sealed PB plan-docs/manifests
   referencing it as "deferred HARP scope" — bucket C history. No code,
   test, hook, SKILL, or live doc consumes it.
2. **Not planned-to-consume.** No roadmap candidate, priority-queue
   row, work-stream, or dependency-map edge names a benchmark
   programme. Its only roadmap tie-in was the ProgramBench-leaderboard
   public-action row — removed by this same cycle as PB scope.
3. **Never started, never green-lit.** Authored 2026-05-03 as
   "RESEARCH PLAN (not a sealed amendment)"; its own Decision #6 gated
   any build on an explicit owner go that was never given. No `harp/`
   repo, adapter, or task artefact exists on this machine.
4. **Dormant.** Last touched 2026-05-08, and that touch was a
   path-scrub in a docs-collapse cycle, not substantive — untouched
   across the entire amendment lineage since (~#100s→#183).
5. **Premise entanglement.** Its floor harness (mini-SWE-agent),
   substrate framing, and public-leaderboard mechanics were authored
   around the benchmark programme the owner is retiring.

Counter-evidence weighed (F2): harness-COMPARATIVE benchmarking is
generically valuable and not PB-specific — but value-in-principle is
not the ruled test ("genuinely useful TO US": consuming or planned to
consume, serving a current objective — it fails all three). Kill is
cheap-to-reverse: the plan stays in git history (`87403522`) and the
companion survey persists on pos3. NOT ambiguous → no coin-flip halt
needed; recommendation stands as KILL (delete the file).

### D-PBRET.2 — Fence shape: single anchor `dev-sdlc` + sweep universal admissions. AUTONOMOUS.

Per the per-component-pyproject-lockstep ratified precedent (roadmap §2
line ~92: "multi-component PATCH fence … single fence-anchor `dev-sdlc`
+ universal_paths admitting `framework/` + `plugins/`"). Alternative
(enumerate all six touched components, advance each sidecar) rejected:
each component's seal-diff window would then include the other
components' changes, forcing per-component admission lists — exactly
the coordination overhead the sweep precedent exists to avoid.

### D-PBRET.3 — BRC_6 shape: trim the file to its two generic tests. AUTONOMOUS.

Keep `test_AC_BRC_6_generic_true_replacement.py` carrying
`construct_is_generic_not_realpb_specific` + `no_op_in_loop_check_is_
refused` (continuous AC.BRC.6 coverage under its established AC name);
delete the three ARMS-coupled tests + the `PBR_SRC`/`ARMS` plumbing.
Alternative (delete file + salvage into another BRC module) rejected:
breaks the one-test-file-per-AC discipline and the AC.BRC.6 audit
thread for zero gain. Inside the trimmed file, the PB tokens in the
generic tests' forbidden-token loop are REMOVED (the loop's no-op
guards stay): post-retirement those tokens guard against a package that
no longer exists, and leaving them would force sweep allowlist noise.
Same rule for BRC_4's forbidden-token strings (lines 55–56, 114) — the
scorer-independence assertion stays, the PB token spellings go.

### D-PBRET.4 — LIPW_4: retire the opt-in frozen-PB-prompt leg. AUTONOMOUS (was "owner-visible choice" in the inventory; resolved by owner call #3's widening — the alternative requires keeping PB material).

Remove `_resolve_frozen_build_prompt` + the `PB_SUBLOAM_REAL_CLAUDE`
end-test leg (env-gated; never in the default run). Grounds: the
inventory's alternative ("re-point to a non-PB frozen prompt") has no
existing non-PB frozen prompt to point at — building one is new fixture
work for an opt-in leg whose substance (PTY multi-turn driving) stays
covered by the file's default-run tests + LIPW_5/6. The default-run
behavior of the file is unchanged (AC.PBRET.2 guards it).

### D-PBRET.5 — Run-evidence files: DELETE with the tool dir. RULED (owner call #2) — recorded, not re-opened.

The 10 committed evidence files go with the tree; bucket C experiment
reports remain the audit record. The reports' RETIRED banners (§10
D-PBRET.8 wording) note that the reproducibility substrate was deleted
at retirement so a future reader doesn't chase orphaned paths.

### D-PBRET.6 — Bucket D disposition register (owner call #3: REMOVE unless genuinely expensive; every keep justified here).

Removal rule: a live-artefact PB mention is removed/reworded. A mention
may survive ONLY as a RETIRED-marked pointer into owner-kept sealed
history, and ONLY if listed here. The sweep (AC.PBRET.5) enforces this
register mechanically.

REMOVE (cheap, executed this cycle):

| Group | Files | Edit shape |
|---|---|---|
| D-R1 handsoff-loop docstrings | behavioral_selfcheck.py, orchestrator.py, cli.py, behavioral_refine_endtest.py | reword origin-story comments generically ("a consumer harness wired the in-loop check to a literal no-op") — the defect narrative survives without the PB name |
| D-R2 BRC forbidden tokens | test_AC_BRC_4, trimmed test_AC_BRC_6 | per D-PBRET.3 |
| D-R3 MSC fixture text | test_AC_MSC_{1,2,4} | reword fixture strings + their lockstep assertions (MSC_2:110/153, MSC_4:168) to neutral subjects; test semantics unchanged |
| D-R4 workspace-bootstrap | test_AC_SLF_{1,2,3} comments; test_AC_LIPW_{5,6} `pb-` slug fixtures | drop/reword comments; rename slugs (e.g. `pb-subloam-one` → `iso-subloam-one`) with assertions in lockstep |
| D-R5 FIDRAFT PB-substance | per §9 | RETIRED markers + gate edit |
| D-R6 live-docs passing mentions | any bucket-B-adjacent live doc hit the sweep finds outside the keep groups | remove/reword |

KEEP (each with its justification — the owner-visible list):

| Group | Files | One-line justification |
|---|---|---|
| D-K1 sealed plan-docs/manifests (~20 w/ passing mentions + the 8 PB pair files) | docs/plans/sealed/ | sealed history — owner carve-out ("I don't mind leaving the sealed stuff"); editing = rewriting the audit trail |
| D-K2 experiment reports (~7 passing + 3 PB reports) | docs/experiments/ | same sealed-history class; the 3 PB reports get banners (bucket C), passing mentions stay verbatim |
| D-K3 seal-record narratives (4) | framework/hands-off-lifecycle/seals/, plugins/dev-sdlc/seals/ | amendment-machinery audit trail; banner-only per D-PBRET.8 |
| D-K4 roadmap §2 shipped rows + struck-through closed public-action rows | docs/release-roadmap.md (v0.4.x, v0.9.0, v0.12.0, lockstep rows; F-DESIGN-1/2 closed rows) | shipped-state records — rewriting them falsifies release history (sealed-history class) |
| D-K5 STATE.md change-log entries | docs/STATE.md | retained-verbatim convention (the file's own rule); dated audit prose; header line 3 Tier-0-verified to claim no active PB work |
| D-K6 completed-work plan-docs still in docs/plans/ | v0-4-0/v0-3-0 master plans; release-roadmap-doc-plan.md; session-clear-safety-…; release-integration-fbm-…; swarming-extraction-composition{,-plan}.md; leverage-discipline-plan.md; loam-1.0-acceptance-smoke-harness.manifest.yaml | their §14 registers anchor seal SHAs — functionally sealed history that never moved to sealed/; editing audit prose = history edit (the ruling's named "expensive" class). Master plans get the inventory's optional RETIRED-scope banner |
| D-K7 provenance citations into kept sealed history | plugins/dev-sdlc/odd-extractor/build_next.py:566 + test_AC_V041_3_tie_breaker.py:10–11 | the only why-record for a live tie-breaker design; reworded to past-tense + "(RETIRED)"-marked citation — the stem then survives only inside the cited sealed path (long-term-path weighting: deleting provenance is the worse outcome) |
| D-K8 the retirement record itself | this plan pair; the inventory; roadmap Candidate 1 text until collapse | the artefacts ARE the retirement record; sweep-allowlisted explicitly |
| D-K9 (BUILD-TIME additions via the halt-trigger-4 mechanism — surfaced in the build report) | docs/plans/conventional-install-pypi-publish.{md,manifest.yaml}; docs/plans/research/harness-landscape-and-roadmap-rerank{,-plan}.md; docs/plans/promote-multi-channel-extractor-and-iteration-loop-family.md; docs/FUTURE_IDEAS_DRAFT.md | pypi pair: completed-work plan pair (D-K6 class — §14 register anchors seal SHAs; PB mentions are historical exclusion-list records). Rerank pair: completed research records (2026-05-08) whose PB-submission recommendations are superseded — RETIRED-SCOPE bannered, content verbatim. Promote-multi-channel: PLAN-ONLY pending plan whose PB-derivative pos3 experiment paths are load-bearing migration-source addresses (removal breaks the plan's function) — RETIRED-PROVENANCE bannered + the one cheap PB fixture-option reworded out. FIDRAFT: D-R5's RETIRED markers / pointer rule keep the stems in entry IDs + provenance (renaming IDs breaks cross-references) — file-level allowlist with the header retirement note |

### D-PBRET.7 — Sweep permanence: ship AC.PBRET.5 as a permanent default-run test, not a one-shot script. AUTONOMOUS.

A retired-work mention regressing INTO live artefacts is exactly the
stale-context failure that caused this candidate (§4 ladder-up);
structural enforcement over discipline per the house frame rule. Cost:
one allowlist to maintain — kept minimal by D-PBRET.3/.6 removing
live-code tokens rather than allowlisting them.

### D-PBRET.8 — Seal-record narrative banners: banner, verified safe. AUTONOMOUS.

Roadmap objective text includes seal records in the banner list.
Tier-0: `loam_amend/narrative.py` only ever APPENDS to
`seals/SEAL_COMMIT.*` files; nothing in loam-amend or loam-cli parses
them back (grep over both src trees) — a leading banner line is
machinery-safe. The sidecar `tests/SEAL_COMMIT` SHA files are NOT
banner targets (machinery-read).

### §10-F2 Ruthless Feedback / honest doubts

1. **The inventory's BRC_6 miscount (§16.1) means its "two PB-coupled
   assertions retire" gloss propagated into ratified roadmap constraint
   text.** Evidence: file source lines 47/58/76 vs roadmap §4
   Candidate 1 constraints. The constraint's INTENT (generic capability
   survives) is honored exactly; this plan executes intent over the
   wrong number and names it rather than silently complying — if the
   owner reads "two" as load-bearing, rule at ratification.
2. **leverage-discipline.md loses its external-benchmark policy with no
   successor.** Evidence: lines 94/120/123 name PB as "the primary
   external benchmark" with per-minor capture. Removing without
   replacement leaves the leverage-evidence policy weaker — named, not
   silently absorbed; successor-benchmark selection is out of scope
   (§3) and would be its own owner-class decision.
3. **The D-K6 "functionally sealed" classification is a judgment call**
   widening "sealed history" beyond docs/plans/sealed/. Evidence: those
   plan-docs carry §14 SHA registers identical in role to archived
   ones. Alternative if the owner wants a harder line: archive them to
   sealed/ first (a separate housekeeping cycle), then this rule
   collapses to the directory test.
4. **Roadmap/dep-map line numbers in the inventory are already stale**
   (~10-line drift observed at lines 547-vs-557). Mitigated: the plan
   instructs term-search-per-file; the sweep is the closure guarantee,
   not the line refs.
5. **Estimate band (estimate, not measured):** inventory's 80–160 min
   midpoint ~110 was pre-widening; bucket D's widening adds ~6 code
   files + assertion-lockstep edits → **95–190 min, midpoint ~130** of
   builder AI-time, single dispatch, serialized in this tree.

## §14 Method-decision register (populated at build + seal time)

SHA register: TBD-AT-SEAL (code …; apply …; seal …) — backfilled per
`loam amend seal --plan-doc`.

Build-time method decisions (builder's call within D-PBRET.1–8):

1. **BASELINE re-pinned** `95068b35` → `b739d0f8` (two docs commits landed
   between plan-authoring and build: the plan pair `a2d84086` + the FIDRAFT
   capture `b739d0f8` that resolved halt trigger 5) so the seal window
   carries only this cycle.
2. **Sweep mechanism:** `git grep -I -i -l` over both stems, compared
   against SEALED_HISTORY_PREFIXES + a `*/seals/SEAL_COMMIT.*` narrative
   rule + the REGISTERED_KEEPS register mirror; mutation fixture is a
   temp `git init` tree proving RED on a stray live mention in either
   stem, mixed case, while a sealed-history mention stays accounted.
3. **D-K9 register additions** (halt-trigger-4 mechanism; rows in §10).
4. **BRC_6 survivor rename:** `construct_is_generic_not_realpb_specific`
   → `construct_is_generic_not_consumer_specific` (the function NAME
   carried the stem; AC name/file unchanged); its PB-token genericness
   loop removed with the package it guarded (D-PBRET.3's removal rule),
   location assertion retained.
5. **test_d1 byte-content ROOT-CAUSE ride-along (laddered to
   AC.PBRET.2):** two pre-existing d1 failures at BASELINE (stale
   pyproject SHAs — the v1.4.0 rebaseline predates the v1.5.0 lockstep
   bump) were the SEVENTH recurrence of a drift the test file itself
   names with its owed fix; executed the named fix (pyproject entries
   removed from the byte-content sample; AC.D.1.5 ≥15-sample floor kept
   via two stable module-body replacements) instead of an eighth
   rebaseline, per the long-term-path weighting.
6. **Untracked run-evidence remnants** (gitignored transcripts under the
   deleted tool tree) moved to `/tmp/programbench-revival-retired-2026-06-11`
   (the blast-radius guard correctly refuses `rm -rf` outside carve-outs;
   `mv` achieves the ruled deletion from the tree, recoverable until /tmp
   clears).
7. **HARP leg executed LAST** among destructive legs per the dispatch's
   sequencing requirement; no hold message arrived.

### Commit SHAs

- Amendment commit: `86848e29faf1177fc4f6f8f0e4f26f8058e40a90` —
  `chore(amend): programbench-full-retirement manifest+apply — dev-sdlc BASELINE+sidecar bump to b739d0f`
- Seal commit: `e7323f2cf189bf6a2c2941bff83d3499dde002e9` —
  `chore(seals): programbench-full-retirement — dev-sdlc at 86848e2`
## §15 Backwards-compat verification

- Default framework test run GREEN (AC.PBRET.2): in particular
  BRC_1–5 + trimmed BRC_6 (generic loop capability), SLF_1–3 +
  LIPW_4-default-leg + LIPW_5/6 (bootstrap), MSC_1/2/4 (memory
  surfacing), PCVR in-scope lockstep assertions (27 in-scope pyprojects
  unaffected; only the EXCLUDED list shrinks), and the dev-sdlc +
  loam-cli suites untouched by content.
- No production-source logic changes anywhere except deletions (the
  handsoff-loop edits are docstring/comment-only — byte-meaning of code
  unchanged; builder verifies via diff inspection).
- Sealed-history file diffs: banner hunks only (AC.PBRET.4).

## §16 Halt-and-surface findings at plan-authoring

1. **Inventory correction — BRC_6 test count.** Five tests, not three;
   three PB-coupled retire, two generic survive (§1.3, F2.1). Substance
   of the constraint unchanged; surfaced, no halt.
2. **Inventory correction (minor) — case sensitivity.** MSC_2's mention
   is `ProgramBench` (capitalized only) — a lowercase-only sweep misses
   it; AC.PBRET.5 specifies case-insensitive matching (§1.5).
3. **The three breakage points re-verified still the only three**
   (§1.2) — the dispatch's named halt condition did NOT fire.
4. **HARP assessment NOT ambiguous** (D-PBRET.1) — the dispatch's
   coin-flip halt condition did NOT fire; clear KILL on five
   evidence legs.
5. **FIDRAFT dirty at plan-authoring** (dispatcher capture surface) —
   handled as build-time halt trigger 5 rather than a plan-time block.
6. Operational-objective test run on all eight named decisions: only
   D-PBRET.1 is owner-gated (the ruling itself made it conditional);
   D-PBRET.5 is already RULED; the rest are autonomous-and-recorded.
   No public actions, no financial surface; LOCAL only.

Build-time findings (2026-06-11 build):

7. **Pre-existing default-run failures at BASELINE, neither caused by
   retirement (Tier-0 proven):** (a) two test_d1 byte-content SHA
   failures — root-cause-fixed in-band (§14 decision 5); (b)
   `test_AC_DCG_OA_genuinely_open_question_passes_live` — its
   "genuinely open question" fixture (frame-kernel dispatch-pack
   activation timing) was RULED in the live pos3 ledger 2026-06-10, so
   the gate now CORRECTLY steers on it; the live-coupled fixture went
   stale by design. Fix needs a design call (live-coupled vs fixture
   ledger) — OUT of this fence; surfaced as a deferred follow-up.
8. **Inventory over-listing:** D-R1 listed handsoff-loop `cli.py`, which
   carries no PB token at HEAD (live grep governed; no edit needed);
   `behavioral_refine_endtest.py`'s PB-lineage mention was the
   `AC.RPB.7` precedent citation (reworded).

## §17 Provenance trail

- Roadmap: docs/release-roadmap.md §4 Candidate 1 + "Owner calls —
  RULED 2026-06-11" (`9bf9099c`).
- Inventory: docs/plans/research/programbench-retirement-inventory-2026-06-11.md
  (landed `9a7723aa`).
- Owner rulings: Discord 1514747695972094165 (full retirement),
  1514752072900284416 (three calls); decision records under
  `<pos3>/workspace/.loam/memory/decisions/2026-06-11-*.md`.
- BRC_6 source: framework/hands-off-lifecycle/tests/
  test_AC_BRC_6_generic_true_replacement.py:36–44 (ARMS plumbing),
  :47/:58/:76 (PB-coupled), :96/:115 (generic survivors).
- PCVR: plugins/dev-sdlc/tests/test_AC_PCVR_pyproject_version_lockstep.py
  :113–114 (EXCLUDED pair), :235 (`is_file` assert), :28 (docstring).
- LIPW_4: framework/workspace-bootstrap/tests/
  test_AC_LIPW_4_pty_driver_interactive_multiturn.py:198–230
  (`_resolve_frozen_build_prompt`), :206–207 (pos3 PB path), :234
  (env gate).
- HARP: docs/plans/harness-benchmark-build.md (created `87403522`
  2026-05-03; last touched `66bf8696` 2026-05-08); consumer grep
  results §10 D-PBRET.1.
- Fence precedent: roadmap §2
  per-component-pyproject-version-lockstep-regression-closure row;
  manifest schema v3 exemplar
  docs/plans/release-flow-partial-publish-repair.manifest.yaml.
- Conventions: plugins/dev-sdlc/docs/conventions/plan-docs.md.

# programbench-full-retirement — apply ladder

Roadmap §4 Candidate 1. Plan:
`docs/plans/programbench-full-retirement.md`.

Executes the 2026-06-11 owner ruling (Discord
1514747695972094165): every ProgramBench artefact retired unless
truly cost-prohibitive, with the three follow-on calls RULED
(Discord 1514752072900284416) — HARP conditional-on-usefulness
(plan D-PBRET.1 verdict executed as owner-ratified), run-evidence
DELETED with the tool tree, bucket-D incidental mentions REMOVED
unless genuinely expensive with every keep justified in the plan
§10 register.

Shape: framework/tools/programbench-revival/ deleted whole; the
20 PB-purpose hands-off-lifecycle tests deleted; BRC_6 trimmed to
its two generic survivors (generic AC.BRC.* capability preserved
— three PB-coupled tests retired, an inventory miscount corrected
at plan §16.1); PCVR + LIPW_4 surgically PB-freed; live
docs/queue/policy edits; sealed history banner-marked RETIRED,
content otherwise byte-unchanged; a permanent case-insensitive
sweep test enforces closure structurally (AC.PBRET.5,
outcome-altitude with a mutation-detection fixture).

AC family AC.PBRET.1-6 (plan §4). Ladders to roadmap §4
Candidate 1 -> Lens 0 protection floor (a cancelled candidate
kept resurfacing as next-build because the cancellation was never
recorded into the artefacts agents read) -> AC.PO.2.
