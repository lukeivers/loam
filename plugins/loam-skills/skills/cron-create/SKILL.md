---
description: "When the persona needs to schedule work to fire at specific clock times — every weekday at 9am, every 30 minutes, at :00 and :30 of each hour — use the CronCreate tool to register a session-scoped cron task. CronCreate is the right primitive for recurring fires within the current Claude session. It is NOT durable across sessions (despite the `durable: true` flag — empirical finding pos3 task #77); for cross-session persistence reach for `launchd-plist` instead. Use when: a recurring intra-session check is needed, scheduled refresh of an artifact, periodic reminder firing during a long session. Composes with `schedule-wakeup` (one-shot vs recurring) and `launchd-plist` (session-bound vs durable cross-session)."
---

# cron-create

Register a 5-field cron expression with the harness. Fires within
the current Claude session at the specified times.

## When to load me

- Persona needs a recurring fire at specific clock times (every
  weekday at 9am, every hour at :00, every 30 minutes).
- Persona is starting a long session and wants periodic checks.
- Persona needs N tasks each with their own cron expression (up
  to 50 per session).
- Persona is about to write a `/loop` for a clock-aligned trigger
  — CronCreate is the better fit for "at 9am" patterns; `/loop`
  is for self-paced "every-N-minutes" without clock alignment.

## What the primitive does

CronCreate registers a task with:

- A 5-field cron expression (minute hour day month weekday).
- An 8-character task ID assigned by the harness.
- A prompt or slash-command to fire each time it triggers.
- Optional `durable: true` flag (see Anti-patterns — flag does not
  achieve cross-session durability despite the name).

The task fires within the current Claude session. On `/clear` the
task is cleared. On `--resume`, the task is restored if not
expired. Recurring tasks have a 7-day expiry (one final fire then
auto-delete). One-shots at :00 / :30 can fire up to 90s early;
recurring can be up to 30m late (or half-interval if sub-hourly).
Max 50 tasks per session.

## Composition

- **`schedule-wakeup`** (sibling SKILL) — ScheduleWakeup is
  one-shot; CronCreate is recurring. Pick by cardinality.
- **`launchd-plist`** (sibling SKILL) — launchd is durable cross-
  session; CronCreate is session-bound. Pick by lifetime
  requirement. If the work must survive Claude session
  boundaries, launchd, not CronCreate.
- **`loop-command`** (sibling SKILL) — `/loop` is self-paced
  iteration with a judge; CronCreate is clock-aligned. Pick by
  whether the cadence is owned by the model (`/loop`) or by the
  clock (CronCreate).
- **`claude-feature-awareness`** SKILL — full scheduling-
  comparison table; this SKILL covers CronCreate specifically.

## Anti-patterns

- **`durable: true` does NOT make CronCreate cross-session.**
  Empirical finding pos3 task #77 (2026-05-14): the flag exists
  but does not deliver true cross-session durability. For genuinely
  persistent recurring work that must survive Claude session
  boundaries, use launchd. CronCreate's session-scoping is a
  feature, not a bug — but only when the work is session-scoped.
- Using CronCreate for "fire once in 20 minutes" — ScheduleWakeup
  is one-shot; CronCreate is recurring.
- Stacking >50 tasks per session — harness limit; consolidate.
- Using CronCreate when `/loop`'s self-paced cadence would be
  cheaper (the model can decide when to re-check; clock alignment
  is unnecessary).

## Example invocation

```
CronCreate:
  expression: "0 9 * * 1-5"
  task: "/check-deploy-status"
```

Fires every weekday at 9am within the current session.

```
CronCreate:
  expression: "*/30 * * * *"
  task: "Probe /tmp/build-status and surface any changes."
```

Fires every 30 minutes. Note the recurring 7-day expiry — for
work that must persist beyond 7 days, use launchd.
