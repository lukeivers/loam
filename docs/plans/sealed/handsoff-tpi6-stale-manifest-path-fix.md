# handsoff-loop AC.TPI.6 — repair the stale manifest path (sweep-archive follow-on)

## Objective

`framework/tools/handsoff-loop/tests/test_AC_TPI_6_fence_integrity.py`
reads the telegram-poller-isolation-fix manifest to recover the diff
BASELINE it fences against. Amendment #143's retroactive sweep
(`loam amend sweep-archive`) moved that manifest from `docs/plans/` to
`docs/plans/sealed/`. The test still points at the OLD location, so its
`_baseline()` helper raises `FileNotFoundError` and every parametrised
case errors. This amendment re-points the path at the sealed location so
the fence test resolves its BASELINE again.

This is pure maintenance: a path string moved, nothing about the fence
SEMANTICS changes. The BASELINE the test recovers is identical; only the
file it reads it from moved.

## Tier-0 ground truth (verified this cycle)

- The manifest is at `docs/plans/sealed/telegram-poller-isolation-fix.manifest.yaml`
  (`ls` confirmed); it is NOT at `docs/plans/telegram-poller-isolation-fix.manifest.yaml`
  (`ls` confirmed absent).
- The test currently FAILS with `FileNotFoundError` on that old path
  (`pytest` run confirmed) — so the fix is observably load-bearing.
- The sealed manifest still carries a `baseline:` line (`38b8f0f`), so
  `_baseline()` will parse correctly once the path points at the right file.

## Scope

- ONE edit: in `test_AC_TPI_6_fence_integrity.py`, the `_MANIFEST` path
  constant gains the `"sealed"` path segment
  (`docs/plans/` → `docs/plans/sealed/`).
- Nothing else in the test changes — the fence assertions, the §1a/§1c
  site tuples, the diff-window logic are all unchanged.

## Acceptance

- AC.TPI.6 (re-greened) — the fence-integrity test resolves its BASELINE
  from the sealed manifest path and PASSES. The diff-window logic is
  unchanged; only the manifest's on-disk location is corrected. This is
  an outcome-altitude check: running the real test file against the real
  tree (no pre-arranged state) goes from erroring on a missing file to
  green.

## Seal fence

Single-component fence: `framework/workspace-bootstrap/`
(`framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`),
the same anchor the original telegram-poller-isolation-fix amendment
sealed against — the handsoff-loop test lives under the
workspace-bootstrap fence's admitted `framework/tools/` prefix; the
plan-doc + manifest land under the admitted `docs/plans/` prefix.

LOCAL SEAL ONLY — not merged, not pushed, not published, not tagged.
NEW commits only; never `--amend`. No version bump (versions derive at
release time).

## §14 — method-decision record (as built)

The fix as built is TWO parts, not one. The original Scope/Acceptance
above described only part 1 (the stale manifest path). During the build
(owner-greenlit, Luke 13579) a second, load-bearing fault was confirmed
and fixed in the same amendment:

1. **Stale path (maintenance).** `_MANIFEST` re-pointed at
   `docs/plans/sealed/` — the location amendment #143's
   `sweep-archive` moved the manifest to. Verified Tier-0 (`ls`
   present at sealed path, absent at old path).

2. **Unbounded diff window (load-bearing).** The test computed
   `git diff {baseline}..HEAD` with NO upper bound. The TPI amendment
   sealed at `e0b71cbc`; HEAD is ~462 commits past it, so the
   unbounded window swept in every later unrelated amendment — and
   `2edf2f43` (a post-seal amendment) touched
   `framework/hands-off-lifecycle/hooks/first_run_dispatch.py`, a
   fenced §1c site, falsely tripping 3/8 cases. (Today all 8 errored
   first on the stale path, masking this.)

   **Method decision** (builder's call, per ODD): bound the window at
   the SEAL commit via the **SEAL_COMMIT-sidecar pattern** the sibling
   fence tests (`protection-matrix` /
   `workspace-bootstrap/tests/test_AC_E_S_seal_diff_single_component_scope.py`)
   already use — a new `framework/tools/handsoff-loop/tests/SEAL_COMMIT`
   sidecar holds the seal SHA
   `e0b71cbc40d000c53a0c1c953bdd4678a3fdae04`; `_seal_commit()` reads
   the sidecar, else a pinned seal SHA, else `HEAD` (pre-seal). Chosen
   over hardcoding the SHA inline because the sibling pattern is the
   established convention and keeps the seal-mechanism uniform.
   Verified `38b8f0f..e0b71cbc` is a clean window (no §1a/§1c fenced
   file inside) → the fence is permanent.

**Outcome-altitude AC** satisfied: the real fence test runs green
across all 8 cases AND `_seal_commit()` resolves to the full seal SHA
(durability proof: the §1c offender `first_run_dispatch.py` is NOT in
the bounded window). Durable, not just today-green.

**Scope-discipline:** the other seal-hardening findings (tracked-ness,
chicken-egg, ref-advance, parallel-collision, stale-baseline) were NOT
touched — the seal-bounded-window change exposed none of them as
needing a change here.
