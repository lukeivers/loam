# Amendment #22 — `pos-amend` CLI + universal-paths retrofit

Plan for the amendment-dispatch tooling introduction and its first self-
validation use. Rationale (bookkeeping cost, proposal shape, rejected
alternatives) lives in the research doc and is NOT restated here.

- **Research doc:** `/tmp/claude-output/pos-v2-ritual-streamlining-research.md`
  (authored 2026-04-22, five rulings accepted by Luke).
- **BASELINE:** `9559ca7` (CDC 2 tighten — teardowns must surface to
  observability).
- **Amendment number:** #22 (pre-assigned in dispatch brief).

## Scope recap (from brief + research rulings)

Five rulings from the research doc:

1. Build the tool.
2. Manifest is committed alongside the plan doc.
3. Universal admitted paths: `docs/plans/`,
   `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `CLAUDE.md`,
   `docs/FUTURE_IDEAS.md`. `data/` stays per-component
   (runtime artefact path, scope-bounded). `docs/archive/component-research/<comp>/`
   stays per-component.
4. Plan-doc threshold: `components > 1` OR `lines > 100`.
5. Post-amendment, `pos-amend apply --dry-run` green is a hard
   prereq before amendment commits.

## CLI file layout

```
tools/pos-amend/
  pyproject.toml              # package metadata + console_scripts entry
  README.md                   # one-page usage overview
  src/pos_amend/
    __init__.py               # package marker + __version__
    __main__.py               # `python -m pos_amend` dispatch
    cli.py                    # argparse + subcommand routing
    manifest.py               # schema + loader (YAML) + validation
    paths.py                  # repo discovery + universal-path constants
    seal_diff.py              # allowed_prefix tuple parser/editor (AST-free regex)
    baseline.py               # BASELINE constant parser/editor
    sidecar.py                # tests/SEAL_COMMIT reader/writer
    narrative.py              # seals/SEAL_COMMIT.* appender
    dry_run.py                # simulate seal-diff check without mutating
    commands/
      __init__.py
      validate.py
      apply.py
      seal.py
  tests/
    __init__.py
    conftest.py               # fixture repo helpers
    test_manifest.py
    test_seal_diff.py
    test_baseline.py
    test_sidecar.py
    test_narrative.py
    test_dry_run.py
    test_cli.py
    test_integration_universal_paths.py   # runs the retrofit
    fixtures/
      valid-minimal.yaml
      valid-multi-component.yaml
      invalid-unknown-schema-version.yaml
      invalid-missing-number.yaml
      universal-paths-retrofit.yaml       # real manifest used below
```

### Dependencies

- `PyYAML` — already installed in `.venv` (confirmed 6.0.3). YAML chosen
  per research doc §6 Q2 (readable, no logic-in-manifest risk).
- `tomllib` — stdlib (Python 3.11+). Not used by the tool itself but
  available if pyproject consumers need it.
- No other runtime deps. stdlib-only beyond PyYAML.

### Install

`pip install -e tools/pos-amend/` registers console-script `pos-amend`.
Entry point declared in `pyproject.toml` `[project.scripts]`.

## Manifest schema (v1)

`docs/plans/amendment-N-<slug>.manifest.yaml`:

```yaml
schema_version: 1
amendment:
  number: 22
  slug: pos-amend-cli
  title: "pos-amend CLI + universal-paths retrofit"
baseline: 9559ca7
plan: docs/plans/amendment-22-pos-amend-cli.md
components:
  - name: cost-governance
    seal_test: cost-governance/tests/test_no_sealed_amendments.py
    sidecar: cost-governance/tests/SEAL_COMMIT
    extra_allowed_prefixes: []
    extra_allowed_files: []
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    extra_allowed_prefixes: []
    extra_allowed_files: []
  # ... one entry per affected sealed component
universal_paths:
  prefixes: []                 # retrofit only — omitted for normal amendments
  files: []
narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run
  body: |
    # Amendment #22 — pos-amend CLI + universal-paths retrofit
    ...
```

### Schema rules (enforced by `manifest.py`)

1. `schema_version == 1` else fail with explicit `UnknownSchemaVersion`.
2. `amendment.number`, `amendment.slug`, `amendment.title` required strings.
3. `baseline` required 7–40-char hex SHA.
4. `plan` required path to an existing file under `docs/plans/`.
5. `components` non-empty list; each entry requires
   `name`, `seal_test`, `sidecar`.
6. `extra_allowed_prefixes` / `extra_allowed_files` default `[]`.
7. `universal_paths.prefixes` / `universal_paths.files` are the retrofit
   knob — when non-empty the tool widens every component's tuple /
   set, not just the manifest's components list.
8. `narrative` optional; if present, `target` must exist and `body` is
   appended verbatim at seal time.

## Dry-run semantics

`pos-amend apply --dry-run <manifest>`:

1. Parse + validate manifest (schema v1).
2. For each listed component, diff `manifest.baseline..HEAD` with git.
3. Union: current `allowed_prefixes` + current `allowed_files` +
   `universal_paths.*` (if retrofit) + per-component `extra_allowed_*`.
4. If any changed path falls outside the union, report as `MISSING_ADMISSION`
   and exit non-zero.
5. If any retrofit universal path is not already present in a component's
   tuple, report `WOULD_WIDEN` (info, non-failing).
6. No file writes; pure read + report.

Exit codes: `0` clean, `1` missing admissions, `2` manifest invalid,
`3` git/io error.

## Apply semantics

`pos-amend apply <manifest>`:

1. Same parse + validate.
2. For each component:
   - Bump `BASELINE = "..."` literal in the seal test to `manifest.baseline`
     (regex-anchored single-line replacement; fails loud if the file does
     not contain exactly one `BASELINE = "<hex>"` line).
   - Overwrite `tests/SEAL_COMMIT` sidecar with `manifest.baseline` (empty-diff
     window at amendment-commit time per the established pattern).
   - Extend the component's `allowed_prefixes` tuple with
     `universal_paths.prefixes + extra_allowed_prefixes`, de-duplicating.
     Extend `allowed_files` set with `universal_paths.files +
     extra_allowed_files`, de-duplicating. AST-free: locate the literal tuple
     via regex, parse + rewrite as formatted tuple literal preserving order
     stability (sort new entries alphabetically for determinism).
3. Does NOT commit. Leaves staged/unstaged per developer flow.
4. Idempotent: re-running produces zero additional diff.

## Seal semantics

`pos-amend seal <manifest>`:

1. Parse + validate.
2. Resolve seal SHA as `git rev-parse HEAD` (the amendment commit).
3. For each component: overwrite `tests/SEAL_COMMIT` with the seal SHA.
4. Append `narrative.body` to `narrative.target` (trimmed trailing newline
   behavior: one blank line between existing content and the new block).
5. Does NOT commit. Human writes the seal commit message.

## Subcommand surface

| cmd | purpose |
|---|---|
| `pos-amend validate <m>` | Schema-lints the manifest. Exit 0 iff valid. |
| `pos-amend apply --dry-run <m>` | Simulates apply; reports missing admissions. |
| `pos-amend apply <m>` | Performs file edits (BASELINE, sidecar, tuple widen). |
| `pos-amend seal <m>` | Advances sidecars to HEAD + appends narrative. |
| `pos-amend --help` | Standard argparse help. |
| `pos-amend --version` | Prints `__version__`. |

No `init`, no `status` in v1. Low-value surface creep per ODD §2.5.

## Acceptance criteria (named)

- **T1** — manifest parser accepts a valid v1 manifest.
- **T2** — manifest parser rejects an unknown `schema_version` with
  `UnknownSchemaVersion`.
- **T3** — manifest parser rejects missing required fields with explicit
  field names.
- **T4** — `pos-amend validate` exits 0 on valid manifest, non-zero on
  invalid.
- **T5** — `pos-amend apply` bumps the `BASELINE = "..."` literal.
- **T6** — `pos-amend apply` overwrites `tests/SEAL_COMMIT` with the
  manifest baseline SHA.
- **T7** — `pos-amend apply` extends `allowed_prefixes` tuple with
  universal + per-component extras, de-duplicated, alphabetically
  sorted for new entries.
- **T8** — `pos-amend apply` is idempotent (running twice yields the
  same tree state).
- **T9** — `pos-amend apply --dry-run` exits 0 on a clean manifest with
  all paths admitted.
- **T10** — `pos-amend apply --dry-run` exits non-zero and names the
  offending path when a changed file is unadmitted.
- **T11** — `pos-amend seal` overwrites sidecars to HEAD SHA.
- **T12** — `pos-amend seal` appends narrative body to target with a
  blank line separator.
- **T13** — integration: apply the `universal-paths-retrofit.yaml`
  fixture against a scratch repo copy and assert every sealed
  component's tuple now contains the universal paths.
- **T14** — `pos-amend --help` lists all subcommands.

Each T-id maps directly to one test function `test_T<N>_<slug>` in the
`tools/pos-amend/tests/` suite. No orphan tests; no orphan code.

## Universal-paths retrofit — first-use validation

The retrofit is authored as
`docs/plans/amendment-22-pos-amend-cli.manifest.yaml` with
`universal_paths.prefixes`:

- `docs/plans/`
- `docs/odd-methodology.md`
- `docs/odd-in-pos.md`
- `CLAUDE.md`
- `docs/FUTURE_IDEAS.md`

The last four are files, not prefixes; they belong in
`universal_paths.files`. Actual manifest entries:

```yaml
universal_paths:
  prefixes:
    - docs/plans/
  files:
    - docs/odd-methodology.md
    - docs/odd-in-pos.md
    - CLAUDE.md
    - docs/FUTURE_IDEAS.md
```

Affected components (10 sealed-component seal-diff tests + 1 cross-cutting):

1. cost-governance
2. graceful-degradation
3. memory-system
4. observability-aggregator
5. orchestrator
6. reversibility-primitive
7. self-correction
8. telegram-interface
9. workspace-bootstrap
10. hands-off-lifecycle (via `test_cross_cutting.py`; handled specially
    because its tuple is a `set` literal of top-level dirs, not a path-prefix
    tuple — universal-path retrofit appends the universal file names to its
    allowed set, but `docs/plans/` was already admitted through
    its `docs` top-level bucket entry).

**safety-layer is intentionally excluded** — its seal test is
import/structural, has no `BASELINE` / `allowed_prefixes` constructs, so
the retrofit is a no-op there. Safety-layer is flagged in the brief as
having a pre-existing ModuleNotFoundError independent of this work.

## Commit sequence

1. **Amendment commit** (`fix: introduce pos-amend CLI + universal-paths
   retrofit (amendment #22)`): the tool code, tool tests, plan doc,
   retrofit manifest, and the retrofit-produced tuple widenings +
   BASELINE advances + sidecar bumps-to-BASELINE. Tests green locally
   before commit.
2. **Seal commit** (`chore(seals): pos-amend-cli-and-universal-paths seal
   — <components> at <amendment-sha>`): runs `pos-amend seal` to bump
   every sidecar to the amendment SHA and append the narrative. Human
   writes the message.

Per the brief's speedup rules: pre-amendment tests = full suite for
`tools/pos-amend/` + seal-diff tests for every affected sealed
component. Post-seal = seal-diff-tests-only across all 10.

## ODD §2.5 compliance declaration

Every file added under `tools/pos-amend/` maps to an AC (T1–T14 above).
Every test asserts a named behaviour. The CLI surface is minimum-viable
per the brief §3. No orphan code.

## Documentation updates

- `tools/pos-amend/README.md` — usage, install, schema reference.
- `CLAUDE.md` "Where other guidance lives" section gains a
  `tools/pos-amend/` pointer.
- `docs/FUTURE_IDEAS.md` amendment-dispatch-speedups CDC note
  appended: "As of amendment #22, these speedups are mechanically
  enforced by `pos-amend apply --dry-run` which must be green before
  the amendment commit lands."

## Halt triggers (from brief §9)

Each flagged with its mitigation:

- **Dry-run false-positive/negative:** tool's seal-diff simulation must
  match the real test exactly. Mitigation: `test_integration_universal_paths`
  asserts tool's dry-run agrees with the real test result on the same
  tree state.
- **Structural allowed_prefixes incompatibility:** hands-off-lifecycle's
  `test_cross_cutting.py` uses a `set` of top-level dirs, not a path-prefix
  tuple. Handled explicitly — apply treats it as a separate case and
  only widens the `allowed_files` set-equivalent if such edits are
  scoped there. Plan §Universal-paths retrofit names this explicitly.
- **New transitive dependency:** none — PyYAML already in the venv.
- **Tool-install flow breaks:** `pip install -e tools/pos-amend/` runs
  in the venv. Verified in pre-amendment test step.
- **Sealed component test breaks on admission:** if a universal path
  causes any component's seal-diff test to flip red, halt — the path
  was not in fact universal. Post-amendment test run checks this.

## Open issues (none outstanding for dispatch)

All rulings per the research doc are accepted. Proceed.
