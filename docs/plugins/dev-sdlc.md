# Dev/SDLC plugin

## What it is

The Dev/SDLC plugin is loam's reference plugin and the first
plugin shipped with v0.1.0. It defaults new projects authored
inside a loam workspace to **Objective-Driven Design** — a
research/spec/plan/build/review/verify flow with named
acceptance criteria for every declared behaviour. The plugin
demonstrates the workspace-bootstrap extension protocol while
delivering useful methodology to anyone building software inside
loam.

ODD is the methodology loam itself is built with (see
[`../design/odd.md`](../design/odd.md)). Shipping ODD as a
plugin rather than a hard-coded harness behaviour is intentional:
not every loam workspace is a software project. A project
manager, a writer, or an analyst running loam should not be
forced into ODD; the methodology is opt-in via the plugin.

## How it composes

The plugin contributes to the workspace via four extension
points:

- **A skill** — `start-project` is the user-facing entry point.
  When the persona detects "I want to start a project" intent,
  the skill opens an authoring flow that walks the user through
  research → spec → plan → build → review → verify, populating
  the objective tracker as it goes.
- **Hook contributions** — pre-commit and pre-push gates that
  enforce ODD-shaped validation on diffs (every code path maps
  to a backing AC; every AC has a test) when the workspace's
  active project is in ODD mode.
- **Settings contributions** — Claude Code settings fragments
  for the persona's prompt scaffolding around new-project
  authoring.
- **CLI contributions** — operator verbs for inspecting ODD
  state on a project (forward / reverse trace, AC verification
  status, plan-doc location).

The plugin's contribution metadata lives in the plugin's
`pyproject.toml` entry-points; `workspace-bootstrap` discovers
and composes them at `loam init` time.

## How a user experiences it

For a developer-leaning user, the path looks like:

1. **Start a new project.** Run `claude` in a fresh workspace
   directory. The persona greets you. You ask: "I want to
   start a new project — a CLI for X."
2. **Skill activation.** The persona invokes the
   `start-project` skill. The skill walks through research
   ("what does X already do well?"), spec ("write the
   objectives + ACs"), plan ("what are the named decisions?
   what halt triggers fire?"), and only then opens the build
   loop.
3. **Build with ODD on.** The plugin's pre-commit / pre-push
   gates enforce the forward / reverse AC trace; refusals
   surface in the persona's conversation; the
   `self-correction` component handles the refusal loop.
4. **Review and verify.** The skill closes with a verify pass
   that runs every AC's test and produces a structured
   completion report.

A user who prefers TDD or BDD opts the project out at step 1;
the plugin still provides the project-tracking surface but
without the ODD gate enforcement.

## Stable surfaces

The plugin's surfaces (the `start-project` skill, the contributed
hook handlers, the operator CLIs) are stable from v0.1.0. Future
plugin versions may extend the spec-authoring or plan-authoring
flows; the contribution shape itself is fixed.

## What the plugin demonstrates for plugin authors

The Dev/SDLC plugin is the canonical example of how to write a
loam plugin. If you are scoping a new plugin, read its source
alongside [`../architecture.md`](../architecture.md)'s plugin-
extension-protocol section. Specifically:

- **One contribution per extension point.** The plugin
  contributes to four extension points; each contribution is a
  small, self-contained module.
- **Plugin-shaped, not framework-shaped.** The plugin lives
  under its own `plugins/dev-sdlc/` tree, not inside
  `framework/`. New plugins follow the same shape.
- **Compose against the harness, do not duplicate it.** The
  plugin uses the objective-tracker, the safety-layer's gate
  surface, the cost-governance budget envelope, and the
  observability aggregator's emission pipeline — it does not
  reinvent any of them.

## Where to go next

- [`../design/odd.md`](../design/odd.md) — the methodology the
  plugin defaults new projects to.
- [`../architecture.md`](../architecture.md) — the plugin-
  extension protocol the plugin composes against.
- [`../components/objective-tracker.md`](../components/objective-tracker.md)
  — the substrate the plugin's authoring flow writes against.
