---
description: "When the persona needs self-paced iteration — repeatedly run a prompt or slash command until a judge says stop, with the model deciding the cadence between 1m and 1h — invoke the `/loop` slash command. `/loop` is the right primitive for 'keep checking until X' patterns where the model is the cadence-decider (not the clock) and where each iteration is itself meaningful work. Use when: monitoring a deploy until it's healthy, iterating on a draft until quality passes a judge, running `/babysit-prs` style watchers, repeatedly running a check that the model decides when to repeat. Composes with `goal-command` (`/goal` is the autonomous-halt sibling; `/loop` keeps running) and `cron-create` (clock-aligned vs self-paced)."
---

# loop-command

Repeatedly run a prompt or slash command, with the model
self-pacing the iteration cadence.

## When to load me

- Persona needs to run the same check repeatedly with the model
  deciding when to re-check.
- Persona is about to set up a watcher whose cadence is best
  decided by the model (cadence depends on observed state, not
  the clock).
- Persona is monitoring a deploy / build / process and wants
  per-iteration intelligence about whether to continue.
- Persona is iterating on a draft / artifact and wants a judge
  to decide when "done."
- Persona is about to write a `while true; do check; sleep; done`
  shell loop — that's the anti-pattern this primitive replaces.

## What the primitive does

`/loop` is a slash command that runs a prompt (or another slash
command) on a recurring basis. Two modes:

- **With explicit interval:** `/loop 5m /foo` runs `/foo` every
  5 minutes.
- **Self-paced (no interval):** `/loop /check-deploy` lets the
  model decide the cadence between 1 minute and 1 hour based on
  its read of progress.

Each iteration is a full model turn — the model sees prior
iterations' context, decides whether to continue, schedules the
next iteration. The loop exits when the model decides "done" or
when explicit halt criteria fire.

Compared to CronCreate: CronCreate is clock-aligned (fire at
specific times); `/loop` is self-paced (model owns the cadence).
Compared to `/goal`: `/goal` is goal-directed and halts on its
own when the goal is met; `/loop` is iteration-shaped and keeps
running until the model decides stop.

## Composition

- **`goal-command`** (sibling SKILL) — `/goal` is the autonomous-
  halt sibling; `/loop` is iteration without an explicit goal
  state. Pick by whether the work shape is "iterate until judge
  passes" (`/loop`) or "drive to a specific goal" (`/goal`).
- **`cron-create`** (sibling SKILL) — CronCreate for clock-aligned
  fires; `/loop` for self-paced. The difference is who owns the
  cadence: clock (CronCreate) vs model (`/loop`).
- **`schedule-wakeup`** (sibling SKILL) — ScheduleWakeup is one-
  shot; `/loop` is many. If only one wake-up is needed, prefer
  ScheduleWakeup.
- **`handsoff-loop`** (sibling SKILL) — handsoff-loop is loam's
  packaged build methodology; it uses `/goal` internally to drive
  the keep-going leg, NOT `/loop`. Don't confuse the two.

## Anti-patterns

- Using `/loop` for a one-off task — ScheduleWakeup is cheaper.
- Using `/loop` when CronCreate's clock-alignment is what's
  actually needed (e.g., "every weekday at 9am" — that's
  CronCreate, not `/loop 24h`).
- Using `/loop` without a clear halt condition the model can
  observe — the loop will run until session ends or rate-limit.
- Setting an interval shorter than the work itself can complete —
  `/loop 1m` with a 5-minute prompt will queue up infinitely.

## Example invocation

```
/loop /babysit-prs
```

Self-paced: model decides when to re-check open PRs based on
their activity.

```
/loop 5m /check-deploy-health
```

Every 5 minutes, run the deploy health check. Model decides per-
iteration whether to continue or halt.

Plain prompt:

```
/loop Keep checking /tmp/build.log for completion or errors.
       Stop when the build is done.
```

Self-paced; the model picks the cadence based on what it sees.
