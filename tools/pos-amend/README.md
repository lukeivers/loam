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
pos-amend validate <manifest.yaml>            # schema-lint
pos-amend apply --dry-run <manifest.yaml>     # simulate; exit 1 on missing admissions
pos-amend apply <manifest.yaml>               # perform file edits (no commit)
pos-amend seal <manifest.yaml>                # finalise the amendment cycle in one shot
pos-amend seal --no-finalize <manifest.yaml>  # legacy: advance sidecars + append narrative only
pos-amend seal --scoped-sweep <manifest.yaml> # restrict sweep to manifest-listed components
pos-amend seal --plan-doc <plan.md> <manifest.yaml>
                                              # also append §14 SHA backfill + follow-up commit
pos-amend template list                       # enumerate registered markdown templates
pos-amend template render <family>/<id> ...   # render a template (stdout or --out)
pos-amend template validate <family>/<id>     # parse-check a template + report its variables
```

`validate`, `apply`, and `apply --dry-run` do not commit. **`seal` does
commit by default** — it finalises the amendment cycle (see below). To
restore the pre-extension non-committing behaviour, pass
`--no-finalize`.

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

## Manifest schema (v2) — `objectives` block (tracker integration)

Schema v2 adds an optional `objectives` block. v2 manifests
additionally register `ObjectiveSpec` records into the workspace's
tracker DB at `apply` time and update each record's
`lifted_from.source_commit` at `seal` time.

```yaml
schema_version: 2
amendment:
  number: 41
  slug: example
  title: "..."
baseline: abcdef0
plan: docs/rebuild/plans/amendment-41-example.md
components:
  - name: example-component
    seal_test: example-component/tests/test_no_sealed_amendments.py
    sidecar: example-component/tests/SEAL_COMMIT
objectives:
  - goal: "Reduce caller translation burden via X"
    parent_id: "value-prop-root"   # OR `parent_root: true`, exactly one
    acceptance_criteria:
      - kind: prose
        criterion_id: AC41.1
        prose: "Caller path A produces outcome B."
      - kind: prose
        criterion_id: AC41.2
        prose: "..."
    time_bound:
      evergreen: true               # OR `deadline: "2026-12-31T00:00:00Z"`
      review_cadence: "amendment-driven"   # only with evergreen=true
    authored_by: "user"             # any string; persona handles permitted
    lifted_from:
      source_doc: "docs/rebuild/plans/amendment-41-example.md"
      source_ac: "AC41.1"
      # source_commit is reserved — `pos-amend seal` writes it.
```

### Schema-version gate

- `schema_version: 1` MUST NOT carry an `objectives` block.
- `schema_version: 2` MUST carry an `objectives` block.

Mismatches reject at `pos-amend validate` / `pos-amend apply` parse
time with `InvalidField` / `MissingField`.

### `apply` semantics with `objectives` block

`pos-amend apply <v2-manifest>` registers each `objectives` entry as
an `ObjectiveSpec` record in the workspace's tracker DB
(`<workspace>/objective_tracker.sqlite`) BEFORE performing its
existing manifest operations (BASELINE bump, allowed_prefixes /
allowed_files widening, sidecar bumps). Idempotent — entries whose
`(lifted_from.source_doc, lifted_from.source_ac)` pair is already
present in the tracker are skipped (no duplicate records, no extra
events).

If the tracker DB is unreadable (missing parent dir, corrupt SQLite,
permission error, schema mismatch), `apply` exits 3 with a structured
diagnostic naming the failure class. No partial registration; no
manifest edits land.

### `seal` semantics with `objectives` block

`pos-amend seal <v2-manifest>` updates each registered record's
`lifted_from.source_commit` to the amendment's HEAD SHA after
sidecar/narrative advance and before running the touched-component
tests. Idempotent against a stable HEAD. v1 manifests + the
`--no-finalize` legacy path are byte-identical to pre-extension
behaviour (no tracker interaction).

### Reserved field — `lifted_from.source_commit`

Manifest authors MUST NOT set `lifted_from.source_commit` — the seal
step writes it. Setting it in the manifest YAML rejects at parse
time. Backwards-compat for v1 manifests is total: every existing
manifest under `docs/rebuild/plans/amendment-*.manifest.yaml` parses
and applies unchanged.

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
7. `pos-amend seal --plan-doc <plan> <manifest>` — finalises the cycle:
   advances every listed sidecar to the amendment SHA, appends the
   narrative, runs the touched components' pytest suite, runs the
   cross-component seal-diff sweep, creates the seal commit with the
   deterministic message, verifies post-seal `apply --dry-run` is green,
   and (with `--plan-doc`) backfills the plan-doc §14 SHA subsection +
   `docs(plans):` follow-up commit.

The dry-run in step 5 replaces the reactive corrective-commit pattern
(see amendment #18's `8bdf194`). The single-invocation finalisation in
step 7 replaces the five hand-run commands the build agent ran before
the `pos-amend seal` extension landed.

### `pos-amend seal` finalisation behaviour

By default `pos-amend seal` performs the following sequence in one
invocation (per `docs/rebuild/plans/pos-amend-seal-automation-extension.md`
ACs D-sa.1 – D-sa.7):

1. Refuses to proceed if the working tree carries unrelated dirty
   paths (anything outside the sidecars + narrative target).
2. Advances every manifest-listed component's `tests/SEAL_COMMIT`
   sidecar to the current HEAD SHA.
3. Appends the `narrative.body` to `narrative.target`.
4. Runs `pytest <comp>/tests/` for every manifest-listed component.
5. Runs `pytest <comp>/tests/test_no_sealed_amendments.py` (or
   `test_cross_cutting.py` for hands-off-lifecycle) for every sealed
   component in the workspace (the cross-component sweep). Use
   `--scoped-sweep` to restrict this to the manifest-listed components
   only.
6. Stages the sidecar(s) + narrative file(s).
7. Creates a deterministic seal commit with subject
   `chore(seals): <description> — <comp1>[+<comp2>...] at <amendment-sha-short>`.
   `<description>` is sourced from the manifest's optional
   `seal_description:` field, falling back to `slug` when absent. The
   `Co-Authored-By:` trailer is included only when invoked under a
   Claude-Code-attributed environment (env-var-detected).
8. Verifies post-seal `pos-amend apply --dry-run <manifest>` exits 0.
9. (Optional, when `--plan-doc <path>` is supplied) appends a
   deterministic `### Commit SHAs` subsection under the plan doc's
   `## 14.` heading, then creates a follow-up commit with the
   subject `docs(plans): record amendment #N commit SHAs in
   method-decision register`.

#### Failure-mode (recoverable checkpoint)

A failing component pytest, a failing sweep target, or a failing
`git add`/`git commit` halts before the seal commit is created and
leaves the sidecar + narrative changes uncommitted. A non-zero
post-seal `apply --dry-run` leaves the seal commit **in place** (per
the no-amend CDC); the operator inspects the diagnostic and authors a
corrective commit. Per-AC details and the failure-class taxonomy live
in `docs/rebuild/plans/pos-amend-seal-automation-extension.md`.

#### Optional manifest field — `seal_description`

```yaml
schema_version: 1
amendment:
  number: 41
  slug: example-slug
  title: "..."
seal_description: "tracker-context contributor"
# ...
```

When set, replaces `slug` in the seal-commit subject's `<description>`
slot. Backwards-compatible — the field is optional, no schema-version
bump.

## Idempotency

`apply` and `seal` are idempotent. Running either twice against an
already-applied tree produces no additional diff. This makes recovery
from a mid-apply interruption safe.

For schema-v2 manifests carrying an `objectives` block, idempotency
extends to the tracker: `apply` skips already-registered records
(matched by `lifted_from.source_doc + lifted_from.source_ac`); `seal`
no-ops the source-commit rewrite when the SHA already matches.

## Exit codes

```
0   ok
1   dry-run found missing admissions
2   manifest invalid
3   repo / git / io error
```

## `template` subcommand — markdown template engine

Renders authored-artefact boilerplate (dispatch prompts, plan-doc
skeletons, future families) from per-template markdown files with
`{{KEY}}` placeholders. Drives the dispatch + plan-doc speedups
described in `docs/rebuild/plans/dispatch-prompt-template-extension.md`.

### Modes

```
pos-amend template list
pos-amend template render <family>/<id> [--var KEY=VALUE]... [--vars-file PATH] [--out PATH] [--force]
pos-amend template validate <family>/<id>
```

`--templates-root <PATH>` (before the mode) overrides the default
templates root (the package's bundled `templates/` directory). Tests
inject an alternate root via this flag; normal use does not.

### Authoring a template

A template is a UTF-8 markdown file at
`tools/pos-amend/templates/<family>/<id>.md` carrying a YAML
frontmatter block with the variables contract:

```markdown
---
description: "One-line summary; appears in `template list`."
required:
  - VAR_A
  - VAR_B
optional:
  VAR_C: "default value"
  VAR_D: ""
---
Body text. Substitute {{VAR_A}}, {{VAR_B}}, optionally {{VAR_C}} / {{VAR_D}}.

Use \{{ literal \}} to embed literal double braces.
```

Every `{{NAME}}` placeholder in the body must appear in either
`required` or `optional`. Variables provided at render time but not
declared in the contract reject as `unrecognised-variable`. Missing
required variables reject as `missing-required-variable`. Substitution
is one-pass — defaults are not recursively expanded.

### Rendering — variable sources

Variables come from `--var KEY=VALUE` flags (repeatable) or a YAML
`--vars-file <path>` carrying a flat mapping. When both are provided,
`--var` flags override `--vars-file` entries.

```bash
# Inline flags:
.venv/bin/pos-amend template render dispatch/sealed-component-build \
  --var COMPONENT=alpha --var AMENDMENT_NUMBER=42 \
  --var AC_PREFIX=AC.A.x --var PLAN_PATH=docs/rebuild/plans/amendment-42.md \
  --var OBJECTIVE='...' --var SCOPE_FENCE='...'

# YAML vars-file (preferred for templates with many variables):
.venv/bin/pos-amend template render dispatch/sealed-component-build \
  --vars-file /tmp/dispatch-vars.yaml

# Render to file (refuses overwrite without --force):
.venv/bin/pos-amend template render plan/dev-discipline \
  --vars-file /tmp/plan-vars.yaml \
  --out docs/rebuild/plans/new-plan.md
```

Default output is stdout. `--out <path>` writes to the named path,
creating parent directories as needed; an existing file at the target
rejects with exit 3 unless `--force` is passed.

### Initial templates shipped at v1

```
templates/dispatch/sealed-component-build.md   # sealed-component build dispatch boilerplate
templates/plan/dev-discipline.md               # 13-section dev-discipline plan-doc skeleton
```

Run `pos-amend template list` for the current registry; run
`pos-amend template validate <family>/<id>` for any template's
`required` / `optional` / placeholder list.

### Failure modes

Exit codes follow the existing pos-amend taxonomy:

```
0 — render succeeded
2 — template/vars contract failure (unknown id, malformed template,
    missing required variable, unrecognised variable, malformed
    --var flag, malformed --vars-file)
3 — IO error (--out target exists without --force, write failed)
```

Every failure mode emits a structured diagnostic to stderr in
`template error [<failure-class>]: <detail>` form; rendering halts
before any output reaches stdout or the `--out` target.

### What's out of scope at v1

- Rendered-output schema validation (e.g. "every plan template's
  rendered output contains a §14 heading"). The engine validates the
  template + the variables contract; output-shape validation is
  future work.
- Memory-doc and commit-message template families — additive
  (drop a new `<family>/<id>.md` under `templates/`; no engine work).
- Auto-population of variables from external state (manifest, current
  HEAD, etc.) — author the vars-file by hand.
- Template versioning — git history is the version trail.

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
