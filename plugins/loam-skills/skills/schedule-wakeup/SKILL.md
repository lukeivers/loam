---
description: "When the persona needs to re-check external state at a known cadence — an API endpoint, a remote build, a poll-only resource I can't event-stream — use ScheduleWakeup to register a future wake-up. ScheduleWakeup also handles long idle ticks (re-engage in N minutes regardless of state) and 'staleness threshold' patterns for dispatched background work. Use when: polling a remote API for a status change, waiting on something I cannot Monitor locally, re-checking a dispatched agent's progress every K minutes, or recovering from a 'something might be wedged' uncertainty. Composes with `monitor-tool` (Monitor for local; ScheduleWakeup for remote) and the dead-agent-detection memory rule (which obligates concrete artifact probe over implicit poller-cadence trust)."
---

# schedule-wakeup

Register a future wake-up at a specific time or interval. The
harness re-invokes the agent when the wakeup fires.

## When to load me

- Persona needs to poll an external resource (API, remote build,
  network service) where no local event-stream exists.
- Persona needs a long idle tick — "come back in 20 minutes
  regardless of state" — to re-verify a dispatched task.
- Persona needs a staleness-threshold probe: dispatched X; expect
  X to land within bound; re-check at bound + slack to catch
  wedge.
- Persona has a "consider re-evaluating later" requirement that
  Monitor cannot express (Monitor fires on a true predicate;
  ScheduleWakeup fires on a clock).
- Persona is recovering from a dead-agent detection: the prior
  agent is suspected wedged, schedule a wakeup at the next
  decision point.

## What the primitive does

ScheduleWakeup registers a future re-invocation of the agent. The
agent's current turn ends; the harness wakes the agent at the
scheduled time. On wake, the agent's context is restored (within
session lifetime) and it can probe state, decide next action,
schedule another wakeup, or finish.

Compared to Monitor: Monitor wakes on a predicate becoming true;
ScheduleWakeup wakes on a clock. Both are event-driven (no
busy-wait); the choice is whether the trigger is state-based or
time-based. Compared to `/loop`: ScheduleWakeup is one-shot per
registration; `/loop` is an autonomous self-paced iteration with a
judge. Use ScheduleWakeup when each wake-up should be a discrete
decision; use `/loop` when the iteration is itself the work.

## Composition

- **`monitor-tool`** (sibling SKILL) — Monitor for local
  predicates; ScheduleWakeup for remote / time-based. Pick by
  trigger source.
- **`feedback_dead_agent_detection_via_artifact_probe.md`**
  (memory) — obligates Tier-0 artifact-probe over Tier-2/3
  poller-cadence inference. ScheduleWakeup is the wake-up
  primitive; the wake-up handler MUST do the artifact probe, not
  trust the wake-up itself as a liveness signal.
- **`cron-create`** (sibling SKILL) — for recurring fires (cron
  pattern), CronCreate is the session-scoped primitive.
  ScheduleWakeup is for one-shot wakes; CronCreate is for
  recurring.
- **`launchd-plist`** (sibling SKILL) — for cross-session durable
  scheduling. ScheduleWakeup is session-bound; launchd survives
  the session.

## Anti-patterns

- Using ScheduleWakeup for a local predicate Monitor could handle
  — Monitor is event-driven on the actual condition, no clock
  guesswork.
- Treating the wake-up itself as proof the watched thing is alive.
  The wake-up just fires the agent; the agent must probe the
  artifact. (This is the dead-agent-detection failure mode.)
- Stacking too many ScheduleWakeups when CronCreate fits — use
  CronCreate for recurring patterns.
- Using ScheduleWakeup across session boundaries — it doesn't
  survive `/clear` or session restart. Use launchd for durable.

## Example invocation

```
ScheduleWakeup at 2026-05-21 14:30:00 — probe-dispatched-build
```

On wake, the agent's handler runs:

```
1. Probe artifact: check /tmp/dispatch-<id>/output for mtime + content.
2. If complete: process result, finish.
3. If still running but progressing: ScheduleWakeup at +20min.
4. If wedged (no progress past expected bound): surface to user.
```

Staleness-threshold pattern:

```
dispatched at T; expected duration ~30min;
ScheduleWakeup at T+45min (30min + 50% slack).
On wake: artifact probe + decide continue / wedge / done.
```
