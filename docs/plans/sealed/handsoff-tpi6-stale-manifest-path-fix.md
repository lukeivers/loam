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
