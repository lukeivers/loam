# The shape of loam — what gets scaffolded, and why

loam is a Claude-attached harness. It ships fifteen Python components,
a primary-persona contract enforced through Claude Code's lifecycle
hooks, an opinionated workspace bootstrap, and a plugin extension
protocol. By any measure, loam is a lot of code for a system whose
core conceit is "you talk to Claude and Claude does the work."

There is a real and respectable design philosophy that points the
other direction: keep the agent thin, lean on the model, delete code
each release as the model improves. It is not a strawman; we will
spend a section on it. This note explains the choice we actually made
and what it is in service of.

---

## What loam scaffolds

Concretely, loam adds six things on top of a raw `claude` session:

1. **A persistent memory substrate.** Raw Claude sessions start blank.
   The `memory` component reads relevant entries at SessionStart and
   UserPromptSubmit and writes salient observations at Stop. v0.1.0 is
   plain text on disk; a graph-backed substrate is planned as a
   plugin. The user does not manage the boundary.

2. **A primary-persona contract.** One persona per workspace, loaded
   into every session, owns greetings, owns memory, owns the channel
   the user actually reads. Specialists exist behind the scenes;
   the user talks to one voice. The persona is not a system prompt —
   it is a contract the harness enforces through hooks.

3. **Structural safety gates.** Every Agent dispatch routes through a
   PreToolUse chain — kill-switch, always-ask classifications,
   reversibility classification with bound compensations, cost
   ceiling, objective binding. A misunderstanding cannot exceed
   declared bounds, because the bounds are enforced outside the
   session.

4. **Cost governance.** Token, time, and money ceilings per scope.
   Drift detection. The user does not have to think about token
   budgets, because the harness does.

5. **Autonomous continuity.** Background work, scheduled scopes, and
   dormancy policy survive session boundaries. Work happens between
   conversations, not only inside them, and the next session greets
   the user with what completed and what is waiting.

6. **A plugin extension protocol.** New capabilities arrive as
   contributions composed at workspace-bootstrap time — hook handlers,
   settings fragments, components, skills, CLI subcommands. The
   protocol is stable from v0.1.0; the Dev/SDLC plugin is the
   reference example.

None of these is a feature in the consumer sense. They are
infrastructure — the kind of thing that has to exist somewhere if
the user is ever going to express intent in natural language and
have the right thing happen.

---

## Why scaffold at all

The motivating observation, articulated in `docs/VALUE_PROPOSITION.md`,
is that AI's capabilities are accessible to a user in proportion to
how much the user already knows about how to use AI — not in
proportion to the model's raw power. The gap between what the AI can
do and what the user can get it to do is a translation problem.

Raw Claude requires the user to perform that translation themselves,
every session. They have to pick the modality (one-shot reply,
scheduled scope, background agent), pick the specialist, manage the
context window, remember the syntax, and re-explain context that
yesterday's session already understood. A technically competent user
can do this; a user with ADHD, or no engineering background, or
limited patience for boilerplate, often cannot — or can but at a
cost that erodes the value.

loam absorbs the translation into a long-lived primary persona and
gives that persona a toolkit. The user expresses intent in natural
language; the persona picks the execution path; the harness handles
persistence, governance, and continuity underneath. The 12-hour
example in `VALUE_PROPOSITION.md` makes this concrete: the user says
"do this every 12 hours," the persona recognises the scheduling shape
and invokes the right primitive, and the user never learns what a
scheduled scope is.

That absorption is what the scaffolding is for. Memory exists so the
persona has continuity. Safety gates exist so the persona can be
trusted with autonomy. Cost governance exists so the user does not
have to think about tokens. The plugin protocol exists so the toolkit
the persona draws from can grow without rewriting the harness.

---

## What gets scaffolded vs what gets composed

loam composes against Claude-native primitives wherever they exist —
hooks, MCP servers, skills, plugins, the settings hierarchy, the
SDK. The scaffolding is a *layer*, not a replacement. The
SessionStart hook is Claude's; loam owns the handler. Skills are
Claude's; loam contributes them through plugins. The CLI is Claude
Code's; loam adds a workspace-bootstrap on top.

This is the first design lens: if a Claude primitive already does the
job, loam uses it. loam-specific machinery exists only where the
primitive does not reach. That is why the harness is roughly fifteen
components rather than fifty — most of what an agent system needs is
already in the box; loam is the long-lived shape around it.

The scaffolding is the answer to questions Claude does not answer for
you on its own: who owns the memory, what guarantees the persona, how
the safety gates compose, where the costs are bounded, how a plugin
contributes new behaviour without rewriting the workspace.

---

## The alternative philosophy

There is a coherent and well-defended view that says: the model is
the product. The agent should be thin. As the model improves, delete
code — every line of harness is a line that has to be deprecated when
the next model handles it natively. Capability is not the bottleneck;
plumbing is. So minimise the plumbing.

This view has real merits and we want to be honest about them:

- **Less to deprecate.** Each model release subsumes more of what the
  harness used to do. A thin agent surfs the improvement curve; a
  thick one fights it.
- **Less surface for the model to behave around.** The more rules the
  harness enforces, the more the model is steering through a maze
  instead of solving the user's problem directly.
- **Simpler debugging.** When the agent is a thin loop over the
  model, failures are model failures. When the agent is a fifteen-
  component composition, failures can come from any of the seams.
- **Lower complexity tax on contributors.** A small system is faster
  to read, faster to extend, and harder to break.

These pressures are real, and a system optimised for them looks very
different from loam. There are useful agents in the world built that
way. We are not claiming the minimalist philosophy is wrong.

---

## Why we chose differently

loam is solving a problem the minimalist philosophy does not address:
the translation gap, persistent across sessions, for users who do not
want to be prompt engineers. The variables that make this hard —
session boundaries, autonomy under structural safety, persistent
memory, governance under cost limits, a single trusted relationship
that survives reboots — do not improve when the model improves.
A smarter model still cannot remember last week's session if there is
no memory substrate to write to. A smarter model still cannot dispatch
work that survives a session close if there is no long-lived
orchestrator. A smarter model still cannot be safely autonomous if
nothing outside the session enforces "never call X without
confirmation."

These problems are independent of model capability. They are shape
problems — what kind of relationship the user has with the system
across time — and shape problems require structure regardless of how
capable the model becomes.

The minimalist philosophy is right when the unit of work is a single
prompt-and-response. The user knows what they want, asks for it, and
gets it. No persistence required, no autonomy required, no governance
required. For that shape, harness is overhead.

loam's unit of work is the relationship: a user expressing intent over
weeks and months, with the system holding context, scheduling, doing
background work, and surfacing what matters. That shape is not
something a thinner agent can grow into by getting smarter. It is a
different design problem, and the scaffolding is what the different
problem requires.

---

## What we are not claiming

A few non-claims, to keep the scope honest:

- We are not claiming this scales to massive teams. loam today is a
  one-person foundation; the bus factor is honestly one and the
  positioning doc says so.
- We are not claiming this is right for every use case. If your bar
  is "ask one question, get one answer," raw Claude already does that
  fine.
- We are not claiming the minimalist philosophy is incoherent or
  unwise. It is a genuine alternative pointing at a different
  problem.
- We are not claiming the fifteen-component count is the right number
  forever. Components are shaped by the problems they solve; the count
  follows the problem, not the other way around. If a future plugin
  protocol or a future Claude capability subsumes a component, that
  component should retire.

The choice we made is the choice that follows from the problem we are
solving. Anyone solving a different problem should make a different
choice — and that is the honest framing.
