---
description: "When the persona needs to inspect the inventory of currently-running background agents — what's in flight, what's done, what's wedged — open the native `claude agents` view (Claude Code v2.1.139+). It is the supervised inventory surface for background agents: each agent is file-isolated via auto-worktrees under `.claude/worktrees/`, surface-detached, and the view supports peek + reply without attach, with Haiku-driven summary refreshes every 15s. Use when: checking 'what background agents are running right now,' deciding whether to dispatch another, recovering after a session restart, or auditing background-agent activity. Composes with the background-agents-by-default memory rule and the dead-agent-detection memory rule (artifact-probe over poller-cadence inference)."
---

# claude-agents-view

The native Claude Code surface for inspecting background-agent
inventory.

## When to load me

- Persona needs to know what background agents are currently
  running.
- Persona has dispatched multiple agents in parallel and needs to
  check progress across all of them.
- Persona is recovering after a session restart and needs to
  enumerate surviving background work.
- Persona is deciding whether to dispatch another agent — `claude
  agents` gives the inventory view first.
- Persona is auditing a wedge or stale agent and needs the actual
  surfaced state from the harness, not inferred from log files.

## What the primitive does

`claude agents` is a native Claude Code view (added in v2.1.139).
It surfaces:

- The full inventory of background agents associated with the
  current Claude install.
- Each agent's working directory (file-isolated under
  `.claude/worktrees/<agent-id>/` by default).
- Status (running / completed / wedged / errored).
- A Haiku-generated summary refreshed every 15s.
- Peek + reply controls (no need to attach to the agent's session
  to inspect or send a message).

The view is supervised: agents are file-isolated by default, so
inspecting one agent does not interfere with others. Reply is
surface-level (you can send a message without `claude attach`
pulling you into the agent's session).

## Composition

- **`feedback_background_agents.md`** (memory) — background agents
  by default; `claude agents` is the inventory view for what's
  running.
- **`feedback_dead_agent_detection_via_artifact_probe.md`**
  (memory) — Tier-0 artifact probe (mtime, ps, worktree state)
  outranks the view's status field for liveness verdicts. Use
  `claude agents` for the inventory; cross-check status with the
  artifact when correctness matters.
- **`feedback_background_default_for_authoring.md`** (memory) —
  multi-artifact authoring routes to background agents; `claude
  agents` is how to inspect what's in flight.
- **`run-in-background-bash`** (sibling SKILL) — a backgrounded
  Bash subprocess is NOT a Claude agent and does not appear in
  `claude agents`; use Monitor or artifact-probe for those.

## Anti-patterns

- Trusting `claude agents` status as definitive when an agent is
  potentially wedged — the surface refresh is 15s; a recently-
  wedged agent may still show "running." Always cross-check with
  artifact mtime + ps.
- Using `claude agents` to inspect non-agent background work
  (Bash subprocesses, launchd jobs, cron tasks) — those don't
  appear in this view.
- Skipping `claude agents` and re-dispatching when an existing
  agent is doing the work — the view exists to prevent this
  duplication.

## Example invocation

From a terminal with `claude` installed:

```
claude agents
```

Opens the inventory view. Each agent shows:

- Agent ID + working directory.
- Status line.
- Haiku summary (refreshed every 15s).
- Peek / Reply controls.

To probe one agent's artifact directly (for the Tier-0 cross-
check):

```
ls -la .claude/worktrees/<agent-id>/
ps -p <agent-pid>
```

The `claude agents` view is the inventory; the artifact probe is
the liveness ground-truth.
