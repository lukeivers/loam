# FBM per-project STATE record + project registry + Cairn probe (Slice C)

**Author:** build agent · **Date:** 2026-06-02 · **Owner:** Luke (greenlit 13582)
**Parent plan:** `workspace/.scratch/claude-output/loam-fbm-quality-and-accuracy-unified-plan.md` (Slice C, P4-1).
**Diagnosis:** `workspace/.scratch/claude-output/loam-fbm-project-status-accuracy-diagnosis-and-fix.md`.
**Mode:** plan-before-code; single-component amendment on the EXISTING `loam-cli` component
(`framework/tools/loam`). Read-only against `/Users/lukeivers/cairn` (never modified).

---

## Objective

A **project registry** maps a project name → its repo root + a ground-truth STATE
derivation, so the persona can derive ANY registered project's real status from ground
truth instead of stale prose. Two projects are registered:

1. **`loam`** → the existing `default_state_record` (loam's seal-sidecar markers), unchanged.
2. **`cairn`** → a new STATE derivation keyed on **Cairn's REAL ground-truth markers**
   (the merged feature-PR commit that introduced each module is an ancestor of HEAD, AND
   the module is present on disk with ≥1 non-stub impl file) — NOT loam seal sidecars,
   which Cairn does not have.

The accuracy anchor: run against the LIVE `/Users/lukeivers/cairn` with no pre-arranged
state, the derivation classifies Cairn's actually-built modules (verify / ledger /
execute / pilot / cause) as **built** — automatically reproducing the verdict the persona
got WRONG ("the engine isn't usable, verify/execute/ledger remain") from ground truth.

## Scope (Slice C ONLY)

IN: project registry + per-project STATE derivation seam + Cairn probe spec + the
outcome-altitude live-Cairn AC. OUT (next serialized slices, NOT this build): Slice D
(inject derived STATE into the keep-pace lens), E (multi-repo work-visibility snapshot),
F (BrainBench), the junk purge.

## Composition — reuse, do NOT re-implement

The derivation ENGINE (`audit/record.py::generate_record`, the `ComponentState` /
`StateOfLoam` rows, the renderer, the `Liveness` classes) is **already repo-agnostic** and
is reused verbatim. Two facts make Cairn's build classifier different from loam's, and they
are the ONLY genuinely new logic:

- **Cairn has NO seal sidecars.** loam's `classify_build_status` reads a `SEAL_COMMIT`
  sidecar SHA and tests git ancestry. Cairn's durable build markers (Tier-0, verified at
  build time) are: each `src/cairn/<module>/` directory is present with ≥1 non-`__init__`
  impl file, and the git commit that FIRST added that module is an ancestor of HEAD (the
  module landed on the mainline via its merged feature PR). The 8 BUILD-PLAN docs the
  diagnosis cited were removed by the professionalism scrub (commit `c0e750a`, "scrub
  private-harness internals"); the plan anticipated this ("or what remains after the
  professionalism scrub"). So the load-bearing, durable markers are present-modules +
  merged-introducing-commit, both Tier-0 git/disk facts that cannot drift.

So Slice C adds a **module-presence + introducing-commit-ancestry** build classifier for
Cairn, parallel to loam's seal-sidecar classifier, reusing the SAME `Liveness` enum,
`ComponentState` row shape, `StateOfLoam` record, and `merge-base --is-ancestor` git probe.

## Tier-0 ground truth (verified at build time, live `/Users/lukeivers/cairn`)

| module  | present (≥1 impl file) | first-add commit | ancestor of HEAD | derived class |
|---------|:----------------------:|:----------------:|:----------------:|:-------------:|
| verify  | yes (7)                | `61a55b0`        | yes              | **merged**    |
| ledger  | yes (7)                | `61a55b0`        | yes              | **merged**    |
| execute | yes (8)                | `61a55b0`        | yes              | **merged**    |
| pilot   | yes (4)                | `61a55b0`        | yes              | **merged**    |
| cause   | yes (4)                | `e0c278f` (#1)   | yes              | **merged**    |

(`61a55b0` = "Initial commit: Cairn engine (Layer A)"; `e0c278f` = "feat: cause layer (#1)".)

## Method (builder's call, recorded for the seal)

New files in `framework/tools/loam/src/loam_cli/audit/`:

- **`cairn_state.py`** — `ModuleProbeSpec(name, module_relpath)` + `classify_module_build_status(repo_root, module_relpath)`
  (present-with-impl-file AND introducing-commit-ancestor → MERGED; present but introducing
  commit not on HEAD → SEALED; absent → UNBUILT; git-indeterminate → UNKNOWN, fail-safe) +
  `default_cairn_module_specs()` (verify/ledger/execute/pilot/cause) + `cairn_state_record(repo_root)`
  that assembles `ComponentState` rows into a `StateOfLoam` reusing the engine's record type.
- **`registry.py`** — `ProjectStateSpec(name, repo_root, derive)` + a `PROJECT_REGISTRY`
  (`loam` → `default_state_record`, `cairn` → `cairn_state_record`) + `resolve_project(name)`
  returning the spec or `None` for an unregistered name + `derive_project_state(name)`
  generating the fresh record (or `None` for unregistered — clean, not a crash).

`cairn`'s repo root defaults to `/Users/lukeivers/cairn` (the live repo, per the diagnosis
+ owner mandate), overridable for tests. Engine + loam path untouched except a re-export.

## ODD ACs (each maps to a named test; ≥1 outcome-altitude)

- **AC-CAIRN-REG-1** (C1): the registry resolves `loam` and `cairn` to distinct repo roots
  + derivations; an unregistered name returns a clean "not registered" result (`None`), not
  a crash. Test: `test_AC_CAIRN_REG_1_registry_resolution.py`.
- **AC-CAIRN-MARKER-2** (C2): Cairn's build classifier keys on Cairn's real markers
  (module presence + introducing-commit ancestry) with NO loam seal-sidecar dependency — a
  fixture repo with present modules + a merged introducing commit classifies MERGED with NO
  `SEAL_COMMIT` file anywhere; an absent module classifies UNBUILT. Proves generalization,
  not a second hardcode. Test: `test_AC_CAIRN_MARKER_2_real_markers_no_seal_sidecar.py`.
- **AC-CAIRN-LIVE-3 (OUTCOME-ALTITUDE)** (C3): run the production derivation
  (`derive_project_state("cairn")`) against the LIVE `/Users/lukeivers/cairn` with NO
  pre-arranged state; the returned record classifies verify / ledger / execute / pilot /
  cause as **built** (MERGED) — reproducing from ground truth the verdict the persona got
  WRONG. Invokes the production entry point, no fixtures, no pre-arranged state. Test:
  `test_AC_CAIRN_LIVE_3_outcome_altitude.py`.

## Outcome match (verify on completion)

The live-Cairn derivation (production entry point, no fixtures) returns MERGED for all five
target modules — automatically; AC-CAIRN-LIVE-3 green proves the generalization on a
separate repo, which is the whole point of this slice (accuracy anchor, before any
lens-injection in Slice D).

## HALT / design-fork note

The diagnosis named "BUILD-PLAN presence" + "`pytest --collect-only`" as candidate markers.
Tier-0 at build time: BUILD-PLANs were scrubbed (commit `c0e750a`); `pytest --collect-only`
on a cairn module returns "no tests collected" (rootdir/conftest config makes it fragile and
env-dependent — not a durable ground-truth signal). I picked the two DURABLE markers
(present modules + merged introducing-commit ancestry) — both Tier-0 git/disk facts that
cannot drift and that directly mirror loam's own ancestry-based classifier. This is a
sensible documented probe spec per the constraint's "pick a sensible probe spec + document
it" clause; not a true ambiguity requiring owner halt.
