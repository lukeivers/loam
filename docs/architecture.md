# loam architecture

This page explains how loam's pieces compose. It is the page to read
once you are past [`getting-started.md`](getting-started.md) and want
to know what is actually going on under the hood — what loam owns,
what Claude Code already provides, and where the seams are.

The audience is anyone who:

- wants to understand why a specific session behaviour happened,
- is considering writing a plugin against loam's extension protocol,
- is reviewing or contributing to the runtime components.

You should be comfortable with Claude Code's general shape (hooks,
slash commands, MCP servers, settings.json hierarchy, the SDK)
before reading on. The [Claude Code
docs](https://docs.claude.com/en/docs/claude-code/overview) cover
those primitives in depth.

For the canonical definitions of the recurring vocabulary on this
page (harness, primary persona, contract, objective, capability,
substrate / seed / cultivar / growth) consult
[`glossary.md`](glossary.md). This page is the authority source for
"harness" and "primary persona"; the glossary cross-references back
here. The remaining terms have their own authority docs and the
glossary records them centrally.

---

## The one-line shape

loam is a **harness** — a long-running structure built on Claude
Code's native primitives that gives a single **primary persona**
the toolkit it needs to translate your natural-language intent
into AI-effective execution across sessions, time, and reboots.

Two halves:

1. **The harness.** Persistent infrastructure that survives session
   boundaries: memory, safety gates, cost governance,
   observability, reversibility, dormancy. Mostly Python
   components, mostly running outside any one Claude Code session,
   composed by a workspace-level bootstrap layer.
2. **The primary persona.** The single voice you talk to when you
   run `claude` inside a loam workspace. The persona is *not* a
   model — it is a contract about how Claude Code behaves inside
   loam: what it greets you with, what it dispatches, what it
   refuses to dispatch, what it remembers, how it reports.

The harness is the toolkit; the primary persona is the consumer of
the toolkit. Both halves are loam's contribution; everything else
in the stack — the Claude model, the Claude Code CLI, the operating
system, the Python runtime — is borrowed.

---

## What loam composes against

loam is **exclusively attached to Claude** (see CLAUDE.md design
lens 1) and composes against five Claude-native primitives. If a
Claude primitive already does the job, loam uses it; loam-specific
machinery exists only where the primitive does not reach.

### Hooks

Claude Code supports lifecycle hooks (SessionStart, PreToolUse,
PostToolUse, UserPromptSubmit, Stop, and others). loam owns hook
handlers at:

- **SessionStart** — primary persona's greeting, memory load,
  background-work catchup. Owned by `hands-off-lifecycle`.
- **UserPromptSubmit** — context-gathering pre-pass, retrieval
  routing, scope identification. Owned by `primary-persona`.
- **PreToolUse on `Task`** — interception of Agent dispatches into
  loam's four-gate chain (safety / cost / reversibility /
  objective-binding). Owned by `safety-layer` + `cost-governance`
  + `reversibility-primitive` + `objective-tracker`.
- **Stop** — memory-write contributor, observability-emit flush,
  dormancy-state persistence. Owned by `primary-persona` +
  `observability-aggregator` + `dormancy`.

### MCP

Claude Code talks to MCP servers via `.mcp.json`. loam ships no
required MCP servers in v0.1.0; the Dev/SDLC plugin and the
Telegram channel adapter both compose against existing MCP
servers (the user's own choices).

### Skills

Skills are Claude-native domain capabilities the user can opt into.
loam ships two SKILL-contributing plugins: `loam-skills` (20 layered
SKILLs capturing loam's load-bearing translation patterns) and
`dev-sdlc` (15 layered SKILLs covering plan-doc authoring, amendment-
cycle discipline, audit-finding triage, and related dev workflows).
Both plugins' layered SKILLs are auto-discovered via Claude Code's
`.claude/skills/` directory after `loam init` symlinks them at
scaffold time (`_symlink_plugin_skills` in
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`).
SKILL counts grow as the corpus grows; the numbers cited here are
plan-time anchors, not contract values.

The Dev/SDLC plugin additionally contributes a user-facing
`start-project` SKILL (at `plugins/dev-sdlc/skills/start-project/SKILL.md`)
for first-click intent routing — auto-symlinked into
`<workspace>/.claude/skills/start-project/` at scaffold time by the
same `_symlink_plugin_skills` mechanism.

### Plugins

Plugins extend the workspace at the
`workspace-bootstrap` extension protocol — a plugin contributes
contributions (hook handlers, settings fragments, components) the
bootstrap composes into the workspace's effective configuration.
The Dev/SDLC plugin (shipped at v0.1.0) is the canonical example.

### Settings hierarchy

Claude Code reads `.claude/settings.json` at workspace, user, and
project levels. loam writes the workspace-level fragment during
`loam init` (idempotent); user-level and project-level edits are
yours.

---

## The 18 runtime components

The harness ships eighteen Python components. Each has a stable
package name (`loam.<component>`), a per-component CLI where it
makes sense, an OTel emission surface, and a per-component
reference page under [`components/`](components/).

The full list, grouped by role:

| Group | Components |
|-------|------------|
| **User-facing surface** | [`primary-persona`](components/primary-persona.md), [`telegram-interface`](components/telegram-interface.md) |
| **Composition + lifecycle** | [`workspace-bootstrap`](components/workspace-bootstrap.md), [`loam-init`](components/loam-init.md), [`hands-off-lifecycle`](components/hands-off-lifecycle.md), [`workspace-sync`](components/workspace-sync.md), [`self-upgrade`](components/self-upgrade.md), [`orchestrator`](components/orchestrator.md) |
| **Safety + governance** | [`safety-layer`](components/safety-layer.md), [`cost-governance`](components/cost-governance.md), [`reversibility-primitive`](components/reversibility-primitive.md), [`self-correction`](components/self-correction.md), [`dormancy`](components/dormancy.md) |
| **Memory + observability** | [`memory`](components/memory.md), [`observability-aggregator`](components/observability-aggregator.md) |
| **Work tracking** | [`scope-of-work`](components/scope-of-work.md), [`objective-tracker`](components/objective-tracker.md), [`per-project-pm`](components/per-project-pm.md) |

The `memory` component's implementation lives inside
`framework/primary-persona/`; there is no standalone
`framework/memory/` directory. See
[`components/memory.md`](components/memory.md) for the rationale.

A summary table with the one-line "what it does" for each lives at
[`components/index.md`](components/index.md).

Each component is independently versioned and independently testable.
A component can be replaced in a workspace by a plugin contribution
(provided the contribution honours the component's contract).

---

## The primary-persona contract

The primary persona is **not a system prompt**. It is a contract
loam enforces about how each Claude Code turn happens inside a loam
workspace. Concretely:

- **One persona per workspace.** A workspace declares one persona;
  the persona owns the conversation; specialists are dispatched
  behind the scenes by the persona, never user-facing.
- **Greeting is mandatory.** SessionStart fires the persona's
  greet-and-status routine: memory load, background-work
  catchup, anything waiting on the user. The persona never starts
  cold.
- **Memory is automatic.** The persona writes salient observations
  to memory at Stop without being asked; it loads relevant memory
  at SessionStart and UserPromptSubmit without being asked. The
  user does not manage the memory boundary.
- **Dispatch goes through the gates.** When the persona decides
  to dispatch background or specialist work, the dispatch
  routes through safety + cost + reversibility +
  objective-binding gates before reaching Claude's `Task` primitive.
- **Channel rules are honoured.** If the workspace declares a
  user-visible channel (Telegram, terminal, etc.), the persona's
  reply uses that channel exclusively; the terminal output is
  diagnostics, not conversation.

The contract is implemented across `primary-persona`,
`hands-off-lifecycle`, `safety-layer`, and `workspace-bootstrap`.
None of those components individually IS the persona; the persona
emerges from their composition.

---

## Session lifecycle (end-to-end)

A useful frame: walk through a session from start to finish and
name which component owns each transition.

1. **You run `claude`.** Claude Code reads
   `.claude/settings.json` (written by `workspace-bootstrap` at
   `loam init` time).
2. **SessionStart hook fires.** `hands-off-lifecycle` runs the
   greeting routine: load memory snapshot
   (`primary-persona`), check for completed background work
   (`scope-of-work`), check for unresumed dormant scopes
   (`dormancy`), assemble the greeting.
3. **You type a prompt.**
4. **UserPromptSubmit hook fires.** `primary-persona` runs the
   context-gathering pre-pass: retrieve relevant memory, identify
   the active scope (or create one), bind the turn to the
   scope's budget envelope
   (`cost-governance`).
5. **Claude generates a response.** Inline reply, or tool use, or
   an Agent dispatch.
6. **If Agent dispatch — PreToolUse hook fires.** `safety-layer`
   runs the kill-switch + always-ask + dangerous-op chain.
   `cost-governance` confirms budget. `reversibility-primitive`
   classifies and binds compensations. `objective-tracker` binds
   the dispatch to a named objective.
7. **Tool runs.** Output flows back into the turn.
8. **Stop hook fires.** `primary-persona` writes memory.
   `observability-aggregator` flushes the turn's spans.
   `dormancy` checkpoints state. `scope-of-work` updates the
   active scope's budget consumption.
9. **You close the session.** `orchestrator` keeps any
   long-running background work alive across the session
   boundary; `hands-off-lifecycle`'s supervisor watches for
   recovery if anything died.

If something interrupts mid-turn (Claude is unreachable, the
user's network drops, the host reboots), `dormancy` decides
whether to pause-and-resume or fail-loud per the policy the
workspace declared.

---

## The plugin extension protocol

A plugin is a Python package the workspace pulls in alongside the
framework, and contributes to the workspace via
`workspace-bootstrap`'s registered extension points. A
contribution is one of:

- a **hook contribution** — a callable wired to a Claude Code
  lifecycle hook,
- a **component-adapter contribution** — alternative
  implementation behind a component's contract (rare),
- a **settings contribution** — a fragment merged into
  `.claude/settings.json`,
- a **skill contribution** — a Claude-native skill registered
  with the workspace,
- a **CLI contribution** — a subcommand registered under the
  `loam` console-script entry-point.

Plugins declare contributions via Python entry-points
(`pyproject.toml`). `workspace-bootstrap` discovers and composes
them at `loam init` time; the composed view is what the workspace
runs against.

The reference plugin is **Dev/SDLC** — see
[`plugins/dev-sdlc.md`](plugins/dev-sdlc.md) for what it
contributes and how. v0.2 will ship additional plugins; the
protocol is stable from v0.1.0.

---

## What is *not* in v0.1.0

To set expectations:

- **No multi-LLM-provider abstraction.** Claude only.
- **No cloud back-end.** Memory, observability, scope state — all
  local to your machine.
- **No web UI.** Claude Code (terminal) is the conversation
  surface; the optional Telegram channel adapter is a remote
  conversation surface, not a dashboard.
- **No second plugin in v0.1.0.** Dev/SDLC ships; everything else
  is v0.2 or later.
- **No remote agent execution.** Background work runs on your
  host; loam does not dispatch to a cloud worker pool in v0.1.0.

---

## Where to go next

- [`components/index.md`](components/index.md) — one-line
  summaries of all 18 components in a single table.
- [`components/<name>.md`](components/) — per-component reference,
  one page per component.
- [`plugins/dev-sdlc.md`](plugins/dev-sdlc.md) — the reference
  plugin; how to read its contributions; how to model your own
  after it.
- [`design/odd.md`](design/odd.md) — Objective-Driven Design,
  the methodology loam is itself built with.
