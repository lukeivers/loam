---
description: "When the persona needs to watch a long-running local subprocess for completion or stream events from it without burning conversation turns on busy-waiting, reach for the Monitor tool. Monitor is event-driven (wakes the agent when the watched condition fires), strictly more token-efficient than a `/loop` poll, and the right primitive for 'wait until X happens' on local artifacts (file mtime, ps liveness, log-line match, port-open). Use when: waiting for a background-agent build to finish, watching a log file for an error pattern, blocking on a port becoming available, or any 'fire when condition holds' pattern against local state. Composes with `run-in-background-bash` (which detaches the work; Monitor watches it) and the dead-agent-detection memory rule (which obligates probe-the-artifact over poller-cadence inference)."
---

# monitor-tool

Event-driven wait on a local condition. Wakes the agent when the
predicate fires; idle otherwise.

## When to load me

- Persona has dispatched a background subprocess (build, agent,
  long-running command) and needs to act when it completes.
- Persona needs to wait for a file to appear / change mtime / pass
  a content predicate.
- Persona needs to wait for a process to exit (`ps` not-found, PID
  liveness check).
- Persona needs to wait for a port to open or a service health-
  endpoint to return 200.
- Persona is about to author a `while sleep; do check; done` loop
  in bash — that's the anti-pattern this primitive replaces.

## What the primitive does

Monitor takes a predicate (an `until`-style condition check) and
suspends the agent's turn until the predicate evaluates true.
Compared to `/loop` polling: Monitor wakes once on the event;
`/loop` runs the model on every interval tick. For waiting on
local state with a clear boolean predicate, Monitor is strictly
cheaper.

The predicate is whatever the agent can probe: a bash one-liner
that exits 0 when the condition holds, a file-existence check, a
log-content match. The agent author specifies the probe; Monitor
runs it on its own cadence and returns when it succeeds.

## Composition

- **`run-in-background-bash`** — detaches the work; Monitor is the
  natural companion for waiting on it.
- **`feedback_dead_agent_detection_via_artifact_probe.md`**
  (memory) — obligates Tier-0 probe of artifact mtime / ps
  liveness over Tier-2/3 poller-cadence inference. Monitor IS the
  artifact-probe primitive.
- **`schedule-wakeup`** (sibling SKILL) — for waiting on external
  state I cannot event-stream (an API endpoint, a remote build, a
  time-bound condition). Monitor handles local; ScheduleWakeup
  handles remote.
- **`feedback_long_running_subprocess_dispatch_owns_the_wait.md`**
  (memory) — when the agent that dispatched the subprocess is the
  one that should wait. Monitor is the wait mechanism.

## Anti-patterns

- Polling with `/loop 1m`-style cadence when an event-driven probe
  exists — Monitor is cheaper.
- Foreground `sleep` calls in Bash (blocked by the harness anyway)
  — use Monitor with an until-loop instead.
- Using Monitor for "decide when to re-check": that's
  ScheduleWakeup territory. Monitor is for "fire when X is true,"
  not "consider re-evaluating later."
- Watching remote / network state where the network call itself
  costs more than running the model on a cadence — use polling.

## Example invocation

```
Monitor with until-condition:
  test -f /tmp/build.done

Returns when the file appears. Agent resumes its turn with the
condition satisfied.
```

Or watching for a build log to contain a completion marker:

```
Monitor with until-condition:
  grep -q "BUILD SUCCESS" /tmp/build.log
```
