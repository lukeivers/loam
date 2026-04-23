# pos-amend

Amendment-dispatch tooling for pos-v2. Mechanises the bookkeeping side of
the sealed-component amendment cycle: `BASELINE` literal advances, seal-
diff `allowed_prefixes` / `allowed_files` widening, `tests/SEAL_COMMIT`
sidecar bumps, and narrative-sidecar appends. Humans still author the
plan, the code, and the commit messages.

See `docs/rebuild/plans/amendment-22-pos-amend-cli.md` for the
authoring plan and `/tmp/claude-output/pos-v2-ritual-streamlining-
research.md` for the research doc that justified the tool.

## Install

```
pip install -e tools/pos-amend/
```

Registers the `pos-amend` console script. Requires Python 3.11+ and
`PyYAML` (declared dep; already present in the repo venv).

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

### Schema-version compatibility

The tool fails loudly on any `schema_version` it does not know. Future
schema migrations ship as a schema-version bump plus a migration note
here.

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

```
cd tools/pos-amend && pytest -q
```

The integration test (`test_integration_universal_paths`) runs the
universal-paths retrofit manifest against a copy of the tree and checks
that every component's tuple widens as expected. Per the amendment-
dispatch-speedups CDC, other components' seal-diff tests are run as
part of the amendment's broader test scope, not here.
