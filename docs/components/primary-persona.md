# primary-persona

## What it does

The primary persona is the single voice you talk to inside a loam
workspace. It is not a model — it is a contract loam enforces about
how Claude Code behaves: how the session starts, how memory is
loaded and written, how user-visible output is routed, when work
is dispatched in the background, and what the persona refuses to
do without explicit ruling.

A loam workspace declares one persona. The persona owns the
conversation; specialists (researcher, planner, builder, reviewer,
domain experts) are dispatched behind the scenes by the persona,
never user-facing. Trust compounds in one relationship in a way
that distributed trust across many specialists cannot, and the
persona contract is what makes the one-relationship model
operational.

## How to invoke

You do not invoke the primary persona explicitly. It is the
default surface of a `claude` session inside a loam workspace.
Specifically, the persona is wired through three Claude Code
hooks:

- **SessionStart** — runs the persona's greeting routine: load
  the relevant memory snapshot, check for completed background
  work, check for unresumed dormant scopes, summarise what is
  waiting on the user. Owned jointly with `hands-off-lifecycle`.
- **UserPromptSubmit** — runs the context-gathering pre-pass:
  retrieve scope-relevant memory, identify or create the active
  scope, bind the turn to its budget envelope.
- **Stop** — runs the memory-write contributor: writes the
  turn's salient observations to memory; flushes
  observability spans; checkpoints any in-flight scope state.

Plugin authors can contribute additional pre-pass or post-pass
behaviours through the workspace-bootstrap extension protocol;
the persona itself stays the user-visible voice.

## Observable surface

What you can `tail` / `cat` / `grep` to see the persona working:

- **Memory writes.** Per-workspace memory store under
  `framework/primary-persona/`'s data area (file-based
  substrate at v0.1.0 — see [`memory.md`](memory.md)). Each Stop
  hook appends one or more memory entries; persistence is plain
  files you can read.
- **OTel spans.** `loam.primary_persona.*` namespace. Visible
  through `loam-observability` queries (see
  [`observability-aggregator.md`](observability-aggregator.md))
  or by tailing the aggregator's local store directly.
- **Greeting log.** SessionStart writes the greeting it produced
  to the workspace's session log; useful when a greeting was
  unexpected or absent.
- **Channel-rule enforcement.** If the workspace declares a
  user-visible channel (e.g. Telegram via
  [`telegram-interface.md`](telegram-interface.md)), the persona
  routes user-visible replies through that channel; reply
  failures surface as `loam.primary_persona.channel.*` spans.

## Stable surfaces (for plugin authors)

- The Stop-hook memory-write contributor accepts plugin
  contributions through `workspace-bootstrap`'s extension
  protocol — a plugin can add structured observations to the
  same memory write that the persona produces.
- The greeting routine accepts pre-greeting status contributions;
  a plugin can surface "X needs your attention" alongside the
  persona's own surfacing.
- The dispatch wrapper `dispatch_with_scope` is the persona's
  Agent-dispatch path; plugin authors writing a new specialist
  use it directly.

For internal implementation detail see the component source under
`framework/primary-persona/`.
