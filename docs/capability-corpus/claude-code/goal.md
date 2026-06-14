# `/goal` — drive-to-checkable-outcome with autonomous halt

## Surface

The `/goal` slash command sets a completion condition and keeps
Claude working across turns until that condition is met, then
halts on its own. It is the persona's reach for any single-task
work shaped as "drive THIS to THIS state" — iterate a build
toward a frozen acceptance, re-run a fix until the failing test
passes, keep going on a multi-step problem until a checkable
success predicate holds. The halt criterion is the goal state,
not "when the model feels done".

`/goal` is the autonomous-loop sibling of `/loop`: `/loop` keeps
running until the model (or the session) stops; `/goal` halts the
instant the goal predicate passes. It works in interactive, `-p`,
and Remote Control sessions and shows live elapsed / turns /
tokens while it drives.

`/goal` is loam's keep-going leg inside the `handsoff-loop` build
methodology — the orchestrator dispatches each sub-task as a real
`claude -p` sub-agent with `/goal` driving the iteration and an
independent loam check deciding "done" (`/goal` drives, loam
decides).

## Inputs/outputs

**Trigger.** Invoked when the persona has a checkable success
predicate and wants the model to iterate until it passes — e.g.
"keep working until the build is green", "drive this to a passing
acceptance", "iterate on the fix until the test passes", "don't
come back until it's done". Not for cadence-shaped polling (that
is `/loop`), not for cross-session cron (that is `/schedule`),
not for fan-out parallel work (that is background-agent dispatch).

**Inputs.** The stated goal condition (the checkable completion
predicate) plus the work to drive. The condition is the halt
criterion; each iteration the model acts, then a halt evaluator
checks the surfaced predicate output.

**Outputs.** Iterative progress across turns with a clean halt at
goal-met (or a terminal when a leg ceiling is hit). Live
elapsed / turns / tokens are surfaced during the drive.

## Composition notes

`/goal` composes with **`/loop`** as its sibling: pick `/goal`
when the work is to *reach a state* (the goal predicate is the
halt); pick `/loop` when the *iteration itself* is the work and
there is no single success state to halt on. They are not
nestable — one or the other expresses the keep-going shape.

`/goal` composes with **background-agent dispatch** — the
`handsoff-loop` orchestrator dispatches each `/goal`-driven
sub-task as a spawn-isolated sub-agent; `/goal` drives the leg,
the independent judge decides done. `/goal` drives a *single*
task to its predicate; it does NOT express "pick the next item
off a durable cross-turn queue" (that cross-turn workstream-queue
dispatch is a distinct shape `/goal` does not cover — D-ADOPT.1,
recorded in `docs/plans/claude-leverage-program-s3-adoptions.md`
§14: native `/goal` is the default keep-going leg for single-task
drive-to-checkable-outcome; a bespoke queue-dispatcher is retained
only for its distinct cross-turn-queue shape).

`/goal` does **not** compose with `/schedule` — `/schedule` is
owner-managed cron across sessions; `/goal` is in-session (or
`-p`) drive-to-state. The persona picks one based on whether the
work is "reach a checkable outcome now" (`/goal`) or "run
cron-shaped across sessions" (`/schedule`).

## [user-intent phrasings]

- "keep working until the build is green"
- "drive this to a passing acceptance"
- "iterate on the fix until the test passes"
- "don't come back until it's done"
- "keep going until the goal is met"
- "re-run until the check passes"
- "drive to the outcome and halt when you reach it"

## Source

```
source_url: https://code.claude.com/docs/en/commands
source_fetch_ts: 2026-06-14T00:00:00Z
source_status: current
```
