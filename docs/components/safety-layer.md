# safety-layer

## What it does

The safety layer is loam's structural floor: the set of refusals
that fire **before** any tool call leaves the workspace, regardless
of what Claude or the user asked for. It composes three kill
switches, an always-ask list, and a dangerous-op gate into a single
PreToolUse hook that intercepts every tool invocation Claude
generates and routes it through the chain.

The design preference (see [`design/odd.md`](../design/odd.md))
is **structural** over advisory: a forbidden state is unreachable,
not described in prose. The safety layer is where loam enforces
that preference for the most consequential class of failures —
running an external tool that should not have been run.

## How to invoke

The layer is wired automatically by `workspace-bootstrap` at
`loam init` time. There is no user-facing "enable safety" step —
it is always on inside a loam workspace. The relevant Claude Code
seam is **PreToolUse**: every tool call goes through the layer's
gate chain, in order:

1. **Kill-switch check.** Three independent kill switches (process,
   scope, workspace) — any active switch refuses every tool until
   manually cleared.
2. **Always-ask check.** A configured list of tools that always
   require explicit user approval, even mid-session.
3. **Dangerous-op gate.** Pattern-matched detection of high-blast-
   radius operations (force-push to main, mass file deletion,
   network operations to unfamiliar hosts, anything irreversible
   per [`reversibility-primitive.md`](reversibility-primitive.md))
   that surfaces the operation for ruling before it lands.

Operators can also fire the kill switches directly through the
per-component CLI:

```bash
loam-kill --scope <scope-id>     # scope-level kill
loam-kill --workspace            # workspace-level kill
loam-kill --process <pid>        # process-level kill
```

A killed scope cancels its TERMINATE-policy children within
500ms p95 and emits a structured kill event — see the
observable-surface section.

## Observable surface

What you can `tail` / `cat` / `grep` to see the layer working:

- **OTel spans.** `loam.safety.*` namespace. Every refusal
  emits a span with `level` + `reason` + `source` attributes;
  the kill events emit `loam.safety.scope_kill`.
- **Audit ledger.** Refusals and kill events are written to
  the safety layer's local SQLite store; visible via
  `loam-cost`-style query CLIs and through the
  observability aggregator's structured queries.
- **`kill_events` table.** Every kill (process, scope,
  workspace) appends a row with timestamp, scope id, source
  identity, and kill-class.
- **Always-ask UX.** When the always-ask gate fires
  mid-session, the layer surfaces the pending tool call in
  the conversation surface (terminal or Telegram channel)
  and waits for explicit approval; rejection writes the
  refusal to the audit ledger.

For internal implementation detail see the component source under
`framework/safety-layer/`.
