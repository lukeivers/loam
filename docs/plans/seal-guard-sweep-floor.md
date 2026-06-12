# seal-guard-sweep-floor — mandatory cross-component GUARD-SWEEP FLOOR at every seal

Working directory: /Users/lukeivers/loam (canonical loam, main)

Provenance: FIDRAFT F-SEAL-GUARD-SWEEP-FLOOR (docs/FUTURE_IDEAS_DRAFT.md,
ac05a12b) — pattern proven SIX times 2026-06-11/12 (plan-state §16b
findings 3/4; broken-suite §16b findings 5/6 + inventory red #1; the
currency cycle's two sibling breaches at root). Owner-ratified step 3
of 3, Discord 1514954288089006211 ("Do it"). Three-strikes doctrine:
this build IS the prevention leg.

## §1 Objective / TL;DR

A cycle whose narrow fence runs only its own component's tests can
silently land content that breaches a SIBLING component's guard; the
breach bites the next innocent seal. After this cycle, `loam amend
seal` runs a designated GUARD-SWEEP FLOOR — the cross-component
protection sweep set — at EVERY seal regardless of the amendment's
fence, in addition to the fenced suite. A breach of any floor guard
blocks the seal AT THE INTRODUCING CYCLE. The narrow-test-scope
speedup survives for everything else (step (d) still runs touched
components' full suites only).

Root-cause mechanics being fixed (all Tier-0 verified at HEAD
056b75e9):

1. `_discover_sealed_components` (seal.py) globs ONLY
   `framework/*/tests/SEAL_COMMIT` — `framework/tools/*` (one level
   deeper: capability-refresh, handsoff-loop, loam-acceptance-smoke,
   loam) and `plugins/*` (dev-sdlc, loam-skills) are invisible to the
   cross-component sweep. 6 of 26 sealed components were never swept.
2. The sweep runs ONLY fence tests (`test_no_sealed_amendments.py` /
   `test_cross_cutting.py`) — the sweep-class guards (banned-stem
   AC.PBRET.5, capability-marker AC.alpha.8, manifest-conformance
   AC.DPS1.13, decision/claim gates AC.DCG/CLG, version lockstep
   AC.PCVR, manifest roots AC.PMR.3, protection-matrix suite,
   fence-integrity AC.PROMO.6/AC.TPI.5) never run at a foreign seal.
3. `--scoped-sweep` lets a seal skip even the fence-test sweep.

## §2 Scope

IN: loam-amend seal machinery (new floor-discovery module + seal-step
rewiring + CLI flag removal), the repo-local floor registry
(`docs/plans/guard-floor.yaml`), loam-amend tests (new AC tests +
adaptation of the 8 `--scoped-sweep` call sites + AC.D-sa.3 sweep
tests), the loam CLI README's `loam amend` section (doc-only — it
documents `--scoped-sweep` and the sweep semantics, both changed),
the dev-sdlc amendment-cycle convention doc (floor described).

OUT: any weakening of an existing guard test (HARD halt trigger);
`--no-finalize` legacy path (pre-extension byte-compat contract per
AC.D-sa family — named residual hole, see D-GFLOOR.3); the pos3-side
owner memory item `feedback_amendment_dispatch_speedups` (lives
outside this repo — modification SURFACED for the dispatcher, see
D-GFLOOR.4); docs/spec/.

## §3 Halt triggers (pre-build)

- Any floor design that would require weakening an existing guard.
- A pre-existing floor breach at plan time. CHECKED: full floor run
  Tier-0 GREEN at 056b75e9 pre-plan (41 files + protection-matrix
  suite, ~135 tests, 0 red, 18.5s wall).

## §4 Acceptance criteria (scope-descriptive: AC.GFLOOR.*)

- **AC.GFLOOR.1 — location-agnostic fence-class discovery.** The
  seal's cross-component sweep covers every tracked fence test
  (`*/tests/test_no_sealed_amendments.py` +
  `*/tests/test_cross_cutting.py`) regardless of tree location
  (framework/*, framework/tools/*, plugins/*), excluding
  `docs/archive/`. Verified on a synthetic repo carrying fence tests
  in all three tree shapes plus an archive decoy that must NOT run.
- **AC.GFLOOR.2 — registry-driven sweep-class floor.** When the repo
  carries `docs/plans/guard-floor.yaml`, every registry pattern is
  resolved against tracked files at seal time and every resolved
  target runs as part of the floor; a red floor target halts the
  seal before the seal commit is created.
- **AC.GFLOOR.3 — staleness is loud, never silent.** In a
  registry-carrying repo: a registry pattern resolving to zero
  tracked files halts the seal with a diagnostic naming the stale
  pattern; an empty fence-discovery result also halts. In a
  registry-LESS repo (synthetic fixtures, derived workspaces using
  the published plugin): empty discovery proceeds with a printed
  note (no false halt).
- **AC.GFLOOR.4 — no bypass.** The finalize-mode seal exposes no
  flag or parameter that skips the floor: `--scoped-sweep` is
  removed from the CLI and `scoped_sweep` from the seal API.
  (`--no-finalize` remains the documented pre-extension legacy mode
  and runs no tests at all — named residual per D-GFLOOR.3.)
- **AC.GFLOOR.5 — floor-failure UX.** A floor breach emits a HALT
  diagnostic that names (a) the breached guard target, (b) the
  pytest failure output, (c) the introducing diff window
  `<baseline>..<amendment-sha>` with an explicit statement that this
  cycle's diff is the introducing diff, and (d) a ready-to-run
  inspection command.
- **AC.GFLOOR.6 — loam's registry covers the inventoried classes.**
  The loam repo's `docs/plans/guard-floor.yaml` covers the 11
  guard classes of the 2026-06-12 inventory; a guard test in
  loam-amend's suite asserts every registry pattern resolves to ≥1
  tracked file at HEAD (the floor guards its own registry between
  seals).
- **AC.GFLOOR.7 — docs truthful.** The loam CLI README `loam amend`
  section and the dev-sdlc amendment-cycle convention describe the
  floor; no live doc still claims `--scoped-sweep` exists.
- **AC.GFLOOR.S ★ (outcome-altitude: true).** On a synthetic repo
  via the production `loam amend seal` entry point (CLI main, no
  pre-arranged internal state): an amendment whose fence is
  component A but whose diff introduces a known breach of component
  B's floor guard is BLOCKED at its own seal with the
  guard-floor-breach diagnostic; the identical amendment without
  the breach seals green. This is the FIDRAFT's named outcome: the
  breach is caught at the introducing cycle, not a later one.

Floor runtime (measured, not an AC — machine-specific): full floor at
HEAD = 42 pytest invocations (26 fence + 15 sweep-class files + the
protection-matrix suite dir), 18.5s wall on the build machine
(.venv python, per-target invocation; single batched invocation is
not viable — cross-component `tests.conftest` basename collision,
reproduced under `--import-mode=importlib` too). Today's sweep
already spends ~8s of that; net added seal latency ≈ +10s.

## §5 Fence + named decisions

Fence: dev-sdlc (loam-amend src + tests under plugins/dev-sdlc/) +
loam (CLI README doc-only). Universal admissions: docs/plans/
prefix (carries the plan pair AND the new guard-floor.yaml — the
registry deliberately lives in already-universally-admitted space so
future registry edits never breach any fence), docs/STATE.md,
CLAUDE.md.

### D-GFLOOR.1 — designated-set mechanism: hybrid runtime discovery

RULED: (a) fence-class floor members are discovered at runtime by
convention — every tracked `*/tests/test_no_sealed_amendments.py` +
`*/tests/test_cross_cutting.py` outside `docs/archive/`, via
`git ls-files` (tracked-only: `.scratch/` smoke trees are excluded
for free) — zero registry, cannot go stale; (b) sweep-class floor
members are declared as GLOB PATTERNS (not exact paths) in a
repo-local registry `docs/plans/guard-floor.yaml`, resolved against
tracked files at seal time, with zero-match-HALTS (AC.GFLOOR.3) so a
moved/renamed guard surfaces loudly at the very next seal instead of
rotting silently.

Alternatives weighed:
- Full enumeration / curated hardcoded list in tool source: stale on
  every rename AND wrong for the published dev-sdlc plugin (loam-
  specific paths inside a tool that runs in foreign repos). Rejected.
- Pure runtime discovery for sweep-class (the dispatch's
  recommendation-to-beat): adopted wholesale for the fence class
  where a naming convention exists; for sweep-class guards there is
  no machine-recognizable signature (content heuristics are fragile),
  so the closest non-stale shape is patterns + loud staleness.
- In-file pytest markers (`pytestmark`): genuinely move-proof, but
  seeding requires editing ~15 test files across 5+ sealed sibling
  components — a cross-component diff requiring permanent foreign-
  path admissions in five fences, i.e. this cycle would itself
  practice the disease it cures. Rejected; revisitable later as
  individual components naturally reseal.

The 36-vs-41 reconciliation (Tier-0): the inventory's "36 files" and
the close-out's "41 files" are two snapshots of the SAME class set at
different commits/counting granularity (the close-out counts the
protection-matrix suite per-file and the capability-refresh fence
landed mid-window). Derived from the discovery rules at HEAD
056b75e9 the floor is 26 fence files + 15 sweep-class files + the
protection-matrix tests dir. The count is emergent from the rules —
which is precisely why a hardcoded list goes stale and the designated
set is defined BY the rules, not by a count.

### D-GFLOOR.2 — floor-failure UX

RULED: HALT diagnostic `klass="guard-floor-breach"` in the existing
seal diagnostic format, carrying the breached target path, the pytest
output, the introducing window `<baseline>..<amendment_sha>`, the
sentence "this cycle's diff is the introducing diff — the floor
blocks the breach at the introducing cycle", and a ready-to-run
`git diff <baseline>..<sha> --stat` inspection line. Stale-pattern
halts use `klass="guard-floor-stale"` naming the unresolvable
pattern.

### D-GFLOOR.3 — escape hatch policy: NONE

RULED: no bypass flag. `--scoped-sweep` (CLI) and `scoped_sweep`
(API) are REMOVED — under the floor doctrine they are precisely a
floor bypass; argparse now rejects the flag loudly. The flag's
original raison d'être (synthetic fixture repos halting on
"sweep-discovery-empty") is subsumed by AC.GFLOOR.3's registry-less
semantics. AC.D-sa.3's scoped-sweep clause is SUPERSEDED by
AC.GFLOOR.* (documented here per
feedback_loose_AC_text_fix_AC_not_implementation — the AC family
changes with its plan, not silently). `--no-finalize` is the one
remaining mode that runs no tests: it is the pre-extension
byte-compat contract, unchanged, and named here as the residual
hole — it advances sidecars only and has never been part of the
test-gated ritual.

### D-GFLOOR.4 — named modification of the approved speedups memory

The owner-approved memory item `feedback_amendment_dispatch_speedups`
(pos3, outside this repo) approves "narrow test scope" as a
dispatch-level speedup. This plan MODIFIES that clause, not silently:
the narrow scope survives for unit suites (seal step (d) still runs
touched components' full suites only), but every seal now pays the
measured ~18.5s floor (~+10s net) unconditionally. The memory item's
update is surfaced to the dispatcher at cycle close (it lives in
pos3, outside this fence).

## §6 Build steps (order)

1. Plan pair (this doc + manifest) committed — baseline for the
   cycle.
2. `loam_amend/guard_floor.py`: registry load + pattern resolution +
   fence-class discovery (git ls-files based) + floor dataclass.
3. `docs/plans/guard-floor.yaml`: the loam repo's registry (11
   classes as patterns).
4. seal.py step (e) rewired to the floor; `scoped_sweep` removed;
   `_discover_sealed_components`/`_seal_diff_test_path` replaced by
   floor discovery; D-GFLOOR.2 diagnostics.
5. cli.py: `--scoped-sweep` removed.
6. Tests: new `test_AC_GFLOOR_*.py` per AC; adapt the 8
   `--scoped-sweep` call sites + AC.D-sa.3 sweep tests + README
   section.
7. Touched suites green locally → feat/fix commits →
   `loam amend validate` → `apply` → `seal --plan-doc` (the seal of
   THIS cycle is the floor's first production run — if it catches a
   new pre-existing breach, that is the floor WORKING; in-fence →
   fix in-cycle, out-of-fence → halt-and-surface).
8. Backfill: STATE.md change-log row.

## §8 In-flight halt triggers

- Any floor design step that would require weakening an existing
  guard test.
- A NEW pre-existing breach (sixth-finding-class) surfacing at this
  cycle's own seal: in-fence → fix in-cycle; out-of-fence →
  halt-and-surface to dispatcher (three-strikes: do not silently
  extend).
- 5-hour wall-clock ceiling.

## §14 Method-decision register (populated at build + seal time)

- D-GFLOOR.1/2/3/4 ruled above at plan time.
