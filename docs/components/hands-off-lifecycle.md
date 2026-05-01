# hands-off-lifecycle

## What it does

`hands-off-lifecycle` is the component that lets you walk away
from a loam workspace and come back to find it still running.
It owns three responsibilities:

- **SessionStart greeting.** When you run `claude` in a loam
  workspace, this component fires the SessionStart hook, runs
  the primary persona's greeting routine, and ensures the
  background-work surface (orchestrator, memory primitive,
  observability aggregator) is alive before the conversation
  starts.
- **Supervisor.** Background services (the orchestrator's
  asyncio host, the memory substrate, the aggregator) are
  watched by a supervisor loop that restarts them on crash and
  marks them dormant if the upstream they depend on (Claude
  itself, network, host) is unreachable.
- **Drain and recovery.** When a session is interrupted —
  the user closes the terminal mid-turn, the host reboots, the
  network drops — the component drains in-flight state to
  durable storage and runs a recovery pass on the next
  SessionStart so nothing is silently lost.

## How to invoke

You do not invoke `hands-off-lifecycle` directly. It is wired by
`workspace-bootstrap` at `loam init` time. The relevant Claude
Code seam is **SessionStart**: every `claude` invocation in a
loam workspace fires this component first.

The supervisor is launched by per-host launchd labels on macOS
(or systemd units on Linux) installed during `loam init`; you
can inspect its state with the host's standard tools (`launchctl
list`, `systemctl status`).

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.hands_off_lifecycle.*` namespace. The
  SessionStart greeting emits a `greeting` span; the supervisor
  emits `supervisor.tick` heartbeats; recovery passes emit
  `recovery` spans listing what was recovered.
- **Supervisor log.** Per-host log under `~/.loam/<workspace>/
  supervisor.log`; tails what the supervisor saw and acted on.
- **launchd / systemd state.** `launchctl list | grep com.loam`
  on macOS lists the loam supervisor labels. State changes
  (load, unload, crash-restart) are visible there.
- **Greeting history.** Each SessionStart appends to
  `~/.loam/<workspace>/greetings.jsonl` so you can audit what
  was surfaced when.

## Stable surfaces (for plugin authors)

Plugin contributions to the SessionStart greeting are merged into
the same span and surfaced in the same greeting flow as the
persona's own status. Plugins that need a supervised background
service can register a service contribution; the supervisor
handles the lifecycle uniformly.

For internal implementation detail see
[`framework/hands-off-lifecycle/README.md`](../../framework/hands-off-lifecycle/README.md).
