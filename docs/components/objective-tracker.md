# objective-tracker

## What it does

`objective-tracker` is the forest-of-trees structure where loam
keeps named objectives and the work that ladders up to them.
Every dispatched scope binds to an objective; every objective
binds to a parent objective (or is a root). The tracker's job
is to make that hierarchy queryable, persistent, and integrated
with the methodology layer ([`design/odd.md`](../design/odd.md))
that the Dev/SDLC plugin defaults new projects to.

Three properties matter:

- **Forest, not tree.** Multiple disjoint root objectives can
  exist in one workspace (a personal project, an open-source
  contribution, an admin chore are all separate roots).
- **Event-sourced.** Objective state changes are appended;
  the tracker's history is replayable.
- **ODD integration.** Objectives carry acceptance criteria;
  acceptance criteria carry tests; the tracker is where the
  forward / reverse ODD trace (every code path → backing AC,
  every AC → covering test) is computed.

The objective tracker is what lets the primary persona answer
"what am I trying to achieve right now?" with structure, not
prose.

## How to invoke

You do not normally invoke the tracker directly. It is composed
into the workspace by `workspace-bootstrap`; the dispatch
wrapper in `orchestrator` binds every dispatched scope to an
objective. The persona's UserPromptSubmit hook identifies the
objective for each turn.

The Dev/SDLC plugin (when active) is the surface most users
interact with the tracker through — its `start-project` skill
authors objectives + acceptance criteria as part of the
research/spec/plan flow. Outside the plugin, plugin authors
work with the tracker programmatically through the bootstrap-
exposed Python client.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.objective_tracker.*` namespace.
  Objective creation emits `objective.create`; binding emits
  `objective.bind`; AC verification emits `objective.verify`
  with pass/fail.
- **Event store.** Per-workspace objective + AC event log under
  the tracker's data area.
- **Greeting integration.** SessionStart greeting can surface
  active objectives waiting on user input or AC verification.
- **Forward / reverse trace.** The tracker computes the ODD
  trace on demand; visible through its query surface or by
  hand-walking the event log.

## Stable surfaces (for plugin authors)

Plugin authors register new objective kinds (a research-shaped
objective, a delivery-shaped objective) through the tracker's
objective-class contribution. AC kinds are similarly extensible.
The Dev/SDLC plugin is the canonical example of a plugin that
treats the tracker as its primary substrate.

For internal implementation detail see
[`framework/objective-tracker/README.md`](../../framework/objective-tracker/README.md).
