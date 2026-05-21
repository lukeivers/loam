---
description: "When the persona needs to launch a Bash command that should outlive the current turn — a long build, a watcher, a service, a multi-minute test — pass `run_in_background: true` to the Bash tool so the command detaches cleanly and the harness re-invokes the agent on exit. The flag replaces the `&` shell-detach pattern (which doesn't survive turn boundaries) AND replaces the 'shell out + busy-wait' pattern. Use when: dispatching a long-running build, starting a watcher process, running a multi-minute test suite, or any command whose duration would otherwise block the main session. Composes with `monitor-tool` (background + Monitor = detached wait) and the background-agents-by-default memory rule."
---

# run-in-background-bash

Detach a Bash call from the current turn so it keeps running, and
have the harness re-invoke the agent when it exits.

## When to load me

- Persona is about to issue a Bash command that will take >30s.
- Persona wants the agent freed to do other work while the command
  runs.
- Persona is about to write `command &` in a shell — that's the
  anti-pattern (the `&` detaches from the shell, not from the
  turn).
- Persona needs fire-on-exit notification (the harness re-invokes
  the agent when the backgrounded command finishes).
- Persona is starting a watcher / server / daemon that should
  outlive the dispatching turn.

## What the primitive does

The Bash tool accepts `run_in_background: true`. When set:

- The command starts detached from the current turn.
- The current turn returns immediately (the agent can continue
  with other tool calls).
- When the command exits, the harness re-invokes the agent (or
  posts the result to the next turn, depending on harness
  configuration).
- Output is captured and delivered alongside the re-invocation,
  not interleaved with the rest of the current turn.

The detachment is at the harness level, not the shell level —
which is why this primitive replaces the `&` pattern. A
shell-level `&` ends with the turn; a `run_in_background: true`
call persists across turn boundaries.

## Composition

- **`monitor-tool`** (sibling SKILL) — Monitor watches the
  detached subprocess for a condition. Background dispatches the
  work; Monitor decides when to wake.
- **`feedback_background_agents.md`** (memory) — Luke wants long
  research/build work in background so the main session stays
  interactive. This primitive is the Bash-level instantiation.
- **`feedback_long_running_subprocess_dispatch_owns_the_wait.md`**
  (memory) — the dispatching agent owns the wait, but the wait
  itself goes through Monitor or fire-on-exit notification, never
  busy-loop in foreground.
- **`feedback_dead_agent_detection_via_artifact_probe.md`**
  (memory) — when probing for backgrounded-command status, check
  the artifact (PID file, output file mtime) over the harness's
  poller-cadence inference.

## Anti-patterns

- `command &` in a Bash one-liner — does not survive turn
  boundaries; the harness will reap the shell.
- Foreground `sleep` to wait for background work — `sleep` is
  blocked in this environment; use Monitor with an until-loop.
- Using `run_in_background: true` for commands that finish in <5s
  — the overhead of detachment + re-invocation isn't worth it
  versus an inline call.
- Spawning a full background agent (Task tool / claude subprocess)
  when a backgrounded Bash command would suffice — agents cost
  more tokens than a script that does the same work.

## Example invocation

```
Bash tool call:
  command: "make all 2>&1 | tee /tmp/build.log"
  run_in_background: true
  description: "Build the full target set in background"
```

The current turn returns immediately. When `make all` exits,
the harness re-invokes the agent with the build's exit code +
captured output.

Combined with Monitor for explicit wait:

```
1. Bash run_in_background: "build.sh > /tmp/build.log 2>&1"
2. (turn continues with other work)
3. Monitor until-condition: test -f /tmp/build.done
4. (agent resumes when build completes)
```
