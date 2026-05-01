# orchestrator

## What it does

`orchestrator` is loam's session-resilient process host. Claude
Code sessions are ephemeral — every `claude` invocation starts
and ends a process — but loam's harness needs to outlive any
single session: long-running scopes, scheduled work, the memory
substrate, the supervisor itself. The orchestrator is where that
state lives.

Concretely it provides:

- **Asyncio event loop** that hosts long-running tasks
  independent of any session.
- **Unix-socket JSON-RPC** as the cross-process surface;
  components inside and outside Claude Code sessions reach the
  orchestrator through the same socket.
- **bind_scope dispatch layer** that routes incoming work to
  the right scope and threads the safety / cost / reversibility
  / objective-binding gates underneath every dispatch.
- **Compaction-survival** — when Claude Code compacts the
  conversation context, the orchestrator's state is unaffected;
  the persona reconstructs its view from the orchestrator's
  surface.

## How to invoke

The orchestrator is launched by `hands-off-lifecycle`'s
supervisor on first session and kept alive across sessions. You
do not start it manually. Components and plugin authors interact
with it through the JSON-RPC surface; the
`workspace-bootstrap` adapter exposes a Python client that
wraps the socket for normal use.

For diagnostic inspection from a shell:

```bash
ls ~/.loam/<workspace>/orchestrator.sock      # socket path
```

The orchestrator's rpc verbs are documented in its component
README; most users never need to call them directly.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.orchestrator.*` namespace. Each rpc
  call emits a span; each scope dispatch emits a `dispatch`
  span; each compaction-survival event emits a `survive` span.
- **Process state.** The orchestrator runs as a supervised
  background process; standard host tools (`ps`, `launchctl
  list`, `systemctl status`) show it. Its log lives at
  `~/.loam/<workspace>/orchestrator.log`.
- **Active scopes.** The orchestrator's `scopes.list` rpc verb
  returns currently active scopes; `loam-cost ls` and the
  observability aggregator's queries also surface this.
- **Socket health.** The supervisor writes the socket's
  liveness state to its log; if the orchestrator crashes the
  supervisor restarts it and the resume sequence is visible
  there.

## Stable surfaces (for plugin authors)

Plugin authors writing specialists or background workers register
their dispatchable units with the orchestrator's `dispatch_with_scope`
path; the four-gate chain wraps every dispatch automatically.
Custom rpc verbs (a plugin-specific control surface) can be
contributed via the orchestrator's rpc-extension contract.

For internal implementation detail see the component source under
`framework/orchestrator/`.
