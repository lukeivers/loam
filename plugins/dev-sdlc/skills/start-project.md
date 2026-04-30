---
name: start-project
description: Start a new project under loam's Dev/SDLC plugin — methodology-shaped 5-stage workflow (research → spec → plan → build → review/verify) with structural gate enforcement. Use when the user asks to start work on something new, kick off a project, or scaffold a feature with structured stages. Composes on the loam Dev/SDLC plugin (plugins/dev-sdlc/) which must be enabled in the workspace's bootstrap.yaml.
---

# /start-project — Dev/SDLC plugin first-click intent routing

This skill is the user-facing entry-point for loam's Dev/SDLC
plugin. When the user says "let's start work on X" or "kick off a
project for X", route through this skill.

## What this skill does

1. Asks the user for a project slug (a short, kebab-case name).
2. Asks (or assumes) the methodology — default `odd`. Other
   choices: `tdd`, `bdd`, `adhoc`.
3. Invokes `loam.plugins.dev_sdlc.api.start_project(slug=<slug>,
   methodology=<methodology>, workspace_root=<workspace>)`.
4. Reports the created project tree path + the user's next step
   (authoring the research stage's artefact at
   `<project>/research/<slug>.md`).

## Underlying mechanics

- The plugin scaffolds `<workspace>/projects/<slug>/research/`,
  `spec/`, `plan/`, `build/`, `review/`.
- Records the project in
  `<workspace>/.loam/dev-sdlc.sqlite` (single source of truth).
- Authors a derived YAML mirror at `<project>/.dev-sdlc.yaml`.
- For non-ODD methodologies, additionally authors an internal ODD
  mirror at `<project>/.dev-sdlc-odd-mirror.yaml` so the persona's
  review path retains structural shape.

## Operator surface

The same flow is available via the unified `loam` CLI:

    loam project new <slug> [--methodology=odd|tdd|bdd|adhoc]

After authoring the research artefact, advance with:

    loam project advance <slug>

The advance gate refuses unless the artefact carries an objective
+ at least one acceptance criterion.

## Composition

This skill assumes:

- The Dev/SDLC plugin is installed at `plugins/dev-sdlc/`.
- The workspace's `bootstrap.yaml` enables it (lists `dev_sdlc`
  under `contributions:`).
- The unified `loam` CLI is available on `PATH` (registers `loam
  project` via the `loam.cli.subcommands` entry-point group).

When any prerequisite is unmet, the skill falls back to surfacing
the gap to the user with a corrective hint (add `dev_sdlc` to
`bootstrap.yaml`; install the plugin).
