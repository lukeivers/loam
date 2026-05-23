# Dev/SDLC plugin for loam

The first plugin authored under loam's contribution-based extension
protocol (M6a, OSS v0.1.0). Establishes the `plugins/<name>/`
directory pattern that v0.2+ plugins inherit.

## What it does

- Scaffolds methodology-shaped projects (default: ODD with
  research → spec → plan → build → review/verify) under
  `<workspace>/projects/<slug>/`.
- Enforces structural gates between stages — `loam project advance`
  refuses unless the current stage's artefact carries an objective
  + at least one acceptance criterion.
- Composes against scope-of-work and objective-tracker — every
  project is a parent scope; every stage is a child scope with its
  own objective.
- Methodology opt-out via `--methodology=tdd|bdd|adhoc` preserves an
  internal ODD mirror at `<project>/.dev-sdlc-odd-mirror.yaml` so the
  persona's review path still has the structural shape ODD provides.
- Surfaces five operator verbs as subcommands of the unified `loam`
  CLI (`loam project new|status|advance|list|gate`).
- Exposes a persona-invocable Python API at
  `loam.plugins.dev_sdlc.api`.
- Ships the `/start-project` Claude skill at
  `plugins/dev-sdlc/skills/start-project/SKILL.md` (subdirectory
  shape) for first-click intent routing — auto-symlinked into
  `<workspace>/.claude/skills/start-project/` at scaffold time by
  `_symlink_plugin_skills` (per AC.LAYERED.2).

## Quickstart

Add `dev_sdlc` to the workspace's `bootstrap.yaml`:

```yaml
contributions:
  - dev_sdlc
```

Then:

```sh
loam project new my-feature
loam project status my-feature
# author the research artefact at projects/my-feature/research/my-feature.md
loam project advance my-feature
```

Per-project state lives in workspace-local SQLite at
`<workspace>/.loam/dev-sdlc.sqlite` (single source of truth);
`<project>/.dev-sdlc.yaml` is a derived human-readable mirror.

## Architecture

Composes against existing harness primitives — does not invent new
ones:

- workspace-bootstrap's `loam.bootstrap.contributions` entry-point
  group (the plugin ships a `DevSdlcContribution` class).
- workspace-bootstrap's NEW `loam.cli.subcommands` entry-point group
  (introduced at M6a; the plugin ships `project`).
- scope-of-work's `ScopeRuntime.create()` — projects + stages.
- objective-tracker's `ObjectiveTracker.create()` — project objective
  + per-stage objectives.

## Status

v0.1.0 — pattern-establishing release. v0.1.1+ extends with the
existing-repo on-ramp (objective-extraction skill) and per-plugin
depth (workflow-state-machine engine, contradiction detection,
external issue-tracker integration, multi-project orchestration,
roadmap tooling). v0.1.0 ships the WORKFLOW SHAPE.

## Sub-packages

The dev-sdlc plugin contains separately-pyproject'd sub-packages
under its sealed fence:

- `odd-extractor/` (v0.1.8) — ODD reverse-engineering. Reads a target
  repo and emits a confidence-banded contract draft (VERIFIED /
  PLAUSIBLE / HYPOTHESISED bands). CLI: `loam odd-extract`. Composes
  with `framework/per-project-pm` for ratification flow.
- `pr-safety/` (v0.1.9 Cycle 1 + Cycle 2) — PR-safety gate. Reads the
  banded contract; classifies a git diff against it; decides per the
  3-band × 4-shape × 3-profile decision matrix; HARD-BLOCKs
  regressions on VERIFIED ACs; surfaces PLAUSIBLE-touched diffs for
  ratification. Cycle 1 ships the engine + CLI (`loam pr-safety
  gate`); Cycle 2 ships hook installers (`loam pr-safety install
  pre-commit / pre-push`) + 3 CI templates (GitHub Actions / GitLab
  CI / CircleCI) + provenance-traceable PR description template
  (`loam pr-safety install pr-template`; gate's
  `--render-pr-description` flag renders from gate output + audit
  log).
- `tools/loam-amend/` (M-FBM) — amendment-dispatch tooling for
  sealed-component bookkeeping. CLI: `loam amend`.
- `tools/loam-mode/` (M-FBM) — partition-rule + mode auditor. Used
  by canonical pos-v2's seal tests.
