# pos-amend

Amendment-dispatch tooling for pos-v2. Mechanises the bookkeeping side of
the sealed-component amendment cycle: `BASELINE` literal advances, seal-
diff `allowed_prefixes` / `allowed_files` widening, `tests/SEAL_COMMIT`
sidecar bumps, and narrative-sidecar appends. Humans still author the
plan, the code, and the commit messages.

See `docs/rebuild/plans/amendment-22-pos-amend-cli.md` for the
authoring plan and `/tmp/claude-output/pos-v2-ritual-streamlining-
research.md` for the research doc that justified the tool.

## Run

`pos-amend` is invoked inside a pos-v2 workspace whose first-run has
completed. First-run already created the workspace's shared venv at
`<workspace>/.venv/`, installed Python 3.13 + `PyYAML`, and installed
`pos-amend` itself as a console script at `.venv/bin/pos-amend`. **You
do not need to install anything to use the tool.**

**Prerequisites:** macOS, plus a populated `.venv/` at the workspace
root (i.e. pos-v2 first-run has run on this checkout). To confirm,
from the pos-v2 workspace root:

```
.venv/bin/python --version
ls .venv/bin/pos-amend
```

You should see `Python 3.13.<something>` and a path to the
`pos-amend` script. If either command errors, run pos-v2 first-run
on this checkout before continuing (roughly two minutes the first
time, instant on a warm checkout).

### Primary invocation

From the pos-v2 workspace root, run `pos-amend` directly out of the
workspace venv. Estimated wall-clock: under one second per call.

```
.venv/bin/pos-amend --help
```

Use the same prefix for every subcommand, e.g.:

```
.venv/bin/pos-amend validate docs/rebuild/plans/amendment-N-<slug>.manifest.yaml
.venv/bin/pos-amend apply --dry-run docs/rebuild/plans/amendment-N-<slug>.manifest.yaml
```

If you would rather type bare `pos-amend`, activate the venv first
(`source .venv/bin/activate`); subsequent calls in that shell can
omit the `.venv/bin/` prefix.

### Fallback — if `.venv/bin/pos-amend` is missing

This shouldn't happen on a workspace where first-run completed, but
if `ls .venv/bin/pos-amend` errors, two no-blast-radius recovery
paths exist. Pick one.

1. **Run the source directly via `PYTHONPATH`** (no install
   performed; estimated wall-clock under one second). From the
   workspace root:

   ```
   PYTHONPATH=tools/pos-amend/src .venv/bin/python -m pos_amend --help
   ```

   Use the same prefix for any subcommand. PyYAML is already in the
   workspace venv, so this works without installing anything.

2. **Reinstall the console script into the workspace venv**
   (estimated wall-clock under fifteen seconds). From the workspace
   root:

   ```
   .venv/bin/pip install -e tools/pos-amend/
   .venv/bin/pos-amend --help
   ```

   Do not run a bare `pip install -e tools/pos-amend/` — on most
   macOS shells the default `pip` resolves to a Python below 3.11
   and the install fails with `Package 'pos-amend' requires a
   different Python` (or, on stock-macOS shells, a setuptools-shape
   error). Always name the workspace venv's `pip` explicitly.

## Subcommand surface

```
pos-amend validate <manifest.yaml>          # schema-lint
pos-amend apply --dry-run <manifest.yaml>   # simulate; exit 1 on missing admissions
pos-amend apply <manifest.yaml>             # perform file edits (no commit)
pos-amend seal <manifest.yaml>              # advance sidecars to HEAD; append narrative
```

All subcommands read the manifest; none commit. The human writes commits.

## Manifest schema (v1)

```yaml
schema_version: 1
amendment:
  number: 22
  slug: pos-amend-cli
  title: "pos-amend CLI + universal-paths retrofit"
baseline: 9559ca7
plan: docs/rebuild/plans/amendment-22-pos-amend-cli.md
components:
  - name: cost-governance
    seal_test: cost-governance/tests/test_no_sealed_amendments.py
    sidecar: cost-governance/tests/SEAL_COMMIT
    extra_allowed_prefixes: []
    extra_allowed_files: []
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true  # H19's BASELINE pinned at project-start
  # ... one entry per affected sealed component
universal_paths:
  prefixes: []       # empty for normal amendments
  files: []
narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run
  body: |
    # Amendment #22 — pos-amend CLI + universal-paths retrofit
    ...
```

### `frozen_baseline` (per-component, optional; introduced amendment #23)

Setting `frozen_baseline: true` on a component instructs `apply` to skip
the module-top `BASELINE = "<sha>"` literal bump for that component.
The sidecar still advances, tuple widenings still apply, and the seal
cycle is otherwise unchanged. Default is `false` — backward-compatible
with every pre-amendment-#23 manifest.

Use this when the test file's BASELINE has been frozen at a point-in-
time (e.g. hands-off-lifecycle's H19 check pinned at project-start per
amendment #23). See `docs/odd-in-pos.md` §10 for the convention.

### Schema-version compatibility

The tool fails loudly on any `schema_version` it does not know. Future
schema migrations ship as a schema-version bump plus a migration note
here. `frozen_baseline` is a backward-compatible extension to the v1
schema; no version bump.

## Usage example — normal amendment

1. Author the plan at `docs/rebuild/plans/amendment-N-<slug>.md`.
2. Author the manifest at `docs/rebuild/plans/amendment-N-<slug>.manifest.yaml`.
3. Make the source edits for the amendment.
4. `pos-amend apply <manifest>` — bumps every listed component's
   `BASELINE` to the manifest baseline, widens `allowed_prefixes` /
   `allowed_files` with the extras, writes the `SEAL_COMMIT` sidecar to
   the baseline SHA (empty-diff window at commit time).
5. `pos-amend apply --dry-run <manifest>` — verify clean.
6. `git add` + `git commit` the amendment. This is the amendment commit.
7. `pos-amend seal <manifest>` — advances every listed sidecar to the
   amendment SHA, appends the narrative block.
8. `git add` + `git commit` the seal. This is the seal commit.

The dry-run in step 5 replaces the reactive corrective-commit pattern
(see amendment #18's `8bdf194`).

## Idempotency

`apply` and `seal` are idempotent. Running either twice against an
already-applied tree produces no additional diff. This makes recovery
from a mid-apply interruption safe.

## Exit codes

```
0   ok
1   dry-run found missing admissions
2   manifest invalid
3   repo / git / io error
```

## Tests

From the pos-v2 workspace root, using the workspace venv:

```
.venv/bin/python -m pytest tools/pos-amend/tests/ -q
```

The integration test (`test_integration_universal_paths`) runs the
universal-paths retrofit manifest against a copy of the tree and checks
that every component's tuple widens as expected. Per the amendment-
dispatch-speedups CDC, other components' seal-diff tests are run as
part of the amendment's broader test scope, not here.
