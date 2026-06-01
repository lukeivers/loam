# protection-matrix follow-on — track the catalogue + add the two owed rows

**Single-component amendment, component: `protection-matrix`.** Sequenced after
the self-recovery seal (now on main `ca0241b1`) so both new guard symbols exist
and resolve. Captured by the primary persona 2026-05-31; origin = two findings
surfaced by the defined-workflow + self-recovery builds.

## Objective

Close three protection-matrix defects/owed-items in one cycle:

1. **Catalogue-untracked bug (correctness).** The matrix's source-of-truth
   catalogue `framework/protection-matrix/data/failure-mode-guard-matrix.yaml`
   exists on disk but is **gitignored** by the over-broad `.gitignore:46 data/`
   rule (the `*/data/` rules at lines 17-21 target *generated runtime* dirs;
   line 46's blanket `data/` wrongly swept this *hand-authored* catalogue). The
   flagship matrix loads locally only because the file is physically present; on
   a fresh clone `default_catalogue_path()` resolves to a missing file. Fix:
   narrow the ignore so this catalogue is tracked, force-add it, and prove a
   clean checkout loads it.

2. **FM.PROCESS-DRIFT row (owed from the defined-workflow build).** Add the
   process-drift failure-mode row with a `guard_ref` that resolves to the merged
   defined-workflow re-injection/cursor symbol (the workflow-position guard).

3. **FM.COMMS-PATH-DEAD row + narration-row fold (self-recovery F-4, deferred
   here).** Add the comms-path-dead row with a `guard_ref` resolving to the
   merged self-recovery watchdog/comms-liveness symbol; fold the narration row
   per the self-recovery plan §13 so its guard points at the distress-detector.

## Scope / fence

`framework/protection-matrix/` only (catalogue YAML, the catalogue/derive code
if a tracking-assert needs a helper, tests), the repo-root `.gitignore` (the
negation line — a universal-path edit, admitted), and the generated
`docs/design/protection-matrix.md` (regenerated, not hand-edited). Do NOT touch
the other components whose symbols the rows reference — only point `guard_ref`
at their existing public paths.

## AC ladder (outcome-shape; method the builder's)

- **AC.PMTRACK.1 (outcome-altitude):** from a list of *git-tracked* files only
  (no reliance on the working-tree copy), the catalogue is present AND
  `load_catalogue(default_catalogue_path())` parses it into the full row set —
  i.e. a fresh clone can load the matrix. The test must fail if the file is
  untracked/gitignored.
- **AC.PMROW.1:** the FM.PROCESS-DRIFT row exists, schema-conformant, and its
  `guard_ref` resolves to a real importable symbol (real-guard-binding check,
  not a string).
- **AC.PMROW.2:** the FM.COMMS-PATH-DEAD row exists, schema-conformant, and its
  `guard_ref` resolves to a real importable symbol; the narration row's guard
  resolves to the distress-detector symbol.
- **AC.PMGEN.1:** the generated `docs/design/protection-matrix.md` is in sync
  with the catalogue (the existing md↔yaml sync test stays green after refresh).

## Forks — ruled

- **F-a (how to un-ignore) →** add a negation line
  `!framework/protection-matrix/data/failure-mode-guard-matrix.yaml` after the
  blanket `data/` rule and `git add -f` the catalogue. Keeps the path the code
  already resolves (`default_catalogue_path`); least-disruption vs relocating the
  file out of a `data/` dir. The builder may instead narrow the line-46 rule if
  that's cleaner, provided no *generated* runtime `data/` dir becomes tracked.
- **F-b (one cycle vs three) →** ONE cycle. All three are protection-matrix,
  same fence; the rows' guard symbols exist on main now; the catalogue-fix is a
  prerequisite for the rows' md regeneration anyway.

## Structural gap (surfaced, NOT fixed here — separate candidate)

The seal-fence verifies committed **diff scope** but NOT that every
runtime-required file is **git-tracked** — a gitignored source file passes seal
silently. This cycle's AC.PMTRACK.1 catches it for *this* file; the general fix
is a seal-time check ("every path the component resolves at runtime is tracked").
First occurrence → captured as a structural-enforcement candidate, not built
here.

---

*Build is a dispatched single-component `loam amend apply` / `loam amend seal`
cycle on `protection-matrix`, off current main.*
