# dormancy

## What it does

`dormancy` is the policy layer that decides what loam does when
its upstream — Claude itself, the network, the host machine —
is unreachable or unhealthy. The component owns three named
policies plus per-mode finite state machines for each, so a
workspace's behaviour during outage is structural, not improvised
turn by turn.

The three policies:

- **pause** — in-flight scopes pause; no new dispatches; the
  persona surfaces the outage and waits. State is persisted so
  resume is loss-free.
- **resume** — the auto-recovery path the supervisor walks when
  upstream returns. Verifies the outage is genuinely over before
  un-pausing.
- **fail-loud** — when an outage exceeds its policy's tolerance,
  scopes fail loudly with structured reasons rather than
  retrying silently.

The scope-of-work component delegates lifecycle decisions to
dormancy whenever an upstream-failure signal is detected;
`primary-persona` consumes dormancy's notification surface in its
greeting and turn loops.

## How to invoke

You do not invoke dormancy directly. It is composed into the
workspace by `workspace-bootstrap`; its policies are configured
through the workspace's settings (the per-mode FSM declarations
live in dormancy's own component data). Outage detection is
driven by signals from `orchestrator` (process-host upstream
checks) where applicable. Future memory-substrate plugins (post-
v0.1.0) compose against the same dormancy contract by surfacing
their own health probes.

The per-host migration helper (used at upgrade time) is the
only operator-facing surface most users encounter:

```bash
loam-migrate-dormancy-config    # one-shot upgrade of dormancy config
```

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.dormancy.*` namespace. Outage detection
  emits `outage.start` and `outage.end` spans; policy dispatch
  emits a `policy.dispatch` span naming which policy fired.
- **State store.** Per-workspace dormancy state in a local
  SQLite database (filename declared by config). Visible by
  hand-inspection if needed.
- **Notification surface.** Dormancy emits structured
  notifications the persona surfaces in the conversation:
  "upstream paused at <timestamp>; resume expected when X." The
  notifications are also written to the workspace's audit
  ledger for after-the-fact review.
- **Greeting status.** SessionStart greeting includes any
  unresumed dormant scopes so the user sees them on session
  open.

## Stable surfaces (for plugin authors)

Plugin authors writing scopes that consume external services
declare the service's outage class in scope metadata; dormancy
applies the workspace's policy uniformly. Custom outage
detectors (e.g. a domain-specific upstream you want to monitor)
can be contributed via a detector contribution.

For internal implementation detail see the component source under
`framework/dormancy/`.
