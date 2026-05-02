# loam — positioning

## One sentence

**loam is the substrate you cultivate a Claude agent in — a long-running
harness that lets a single primary persona translate your natural-language
intent into AI-effective execution, with persistent memory, structural
safety, and autonomous continuity that raw Claude alone cannot reach.**

## What loam is

loam is a Claude-attached harness. You open a Claude Code session in a
loam workspace; loam's primary persona greets you, surfaces what needs
attention, and routes whatever you ask into the most effective execution
path the underlying toolkit supports — a single-shot reply, a scheduled
recurring scope, a background agent, a guarded external action, a
cross-domain synthesis.

loam is not a Claude replacement and not a chatbot wrapper. The Claude
session is still where you do the talking; loam is what extends that
session beyond goldfish memory and single-prompt action. Persistent
memory, scheduled and background work, structural safety gates, cost
governance, and audit trail are the toolkit; the primary persona is the
single voice that draws from that toolkit on your behalf.

The design is opinionated: loam is for people who want one trusted voice
that gets work done across long horizons — not a tool-belt of specialist
chatbots they switch between. Trust compounds in one relationship in
ways that distributed trust across many specialists cannot. Specialists
exist behind the scenes; the user talks to the persona, the persona
dispatches the specialist, the persona owns the outcome.

## Who loam is for

Three audiences, in priority order.

**1. Operators with high agency and low patience for AI translation
work.** People who already know AI is powerful but find raw Claude
frustrating because every useful action requires them to translate
their intent into the right prompt, remember the right tool, manage
the context window, and re-explain themselves every session. loam
absorbs that translation burden into the primary persona; the user
expresses intent, the persona handles execution.

**2. Builders adopting an Objective-Driven Design (ODD) workflow.**
loam ships a Dev/SDLC plugin that defaults new projects to ODD —
research, spec, plan, build, review, verify against named acceptance
criteria. ODD treats a unit of work as an *observable outcome* (state
of the world that must be true) rather than a sequence of steps; the
methodology is documented at `docs/design/odd.md` and lived inside
loam itself. Builders who prefer TDD or BDD opt out per project.

**3. Contributors interested in a Claude-native harness pattern.**
loam composes against Claude's native primitives — slash commands, hook
events, skills, plugins, MCP, background tasks — rather than re-
implementing them. The harness is the toolkit the primary persona
draws from; new capabilities arrive as plugins that compose against
the workspace-bootstrap extension protocol.

## Non-goals

loam is explicitly **not**:

- a multi-LLM-provider abstraction. Claude only. The harness composes
  on Claude's native capabilities; portability would lose the leverage.
- a no-code agent builder. loam is for users comfortable with a CLI
  and willing to keep one Claude Code session open at a time.
- a cloud platform. loam runs locally; your workspace, your machine,
  your data. Memory state, the orchestrator, and the primary persona
  all live on your hardware as files and processes you control.
- a ChatGPT replacement. If your bar is "I want to ask one question
  and get one answer," raw Claude already does that fine. loam earns
  its keep when the work spans sessions, requires governance, or
  needs persistent context.
- a productivity-app shell. loam ships infrastructure components
  (memory, safety, reversibility, cost governance, observability) and
  one demonstration plugin (Dev/SDLC). Domain-specific overlays —
  finance, communications, knowledge management, creative — are
  follow-on plugins, not v0.1.0 scope.

## Design principles

Three lenses every feature must answer:

1. **Claude-leverage-first.** loam is exclusively attached to Claude.
   What Claude capability does this feature lean on or extend? If a
   Claude-native primitive already provides part of the feature, loam
   composes on top rather than re-implementing.
2. **Harness + primary-persona value.** Does this reduce the
   translation burden between the user's natural-language intent and
   AI-effective execution (primary-persona test)? Does this add to
   the toolkit the primary persona can draw from (harness test)? A
   feature that fails the harness test is almost always wrong.
3. **ODD authoring.** Work in loam is defined by its observable
   outcome, not by a sequence of steps. Method is the builder's call
   inside the constraint envelope. See `docs/design/odd.md`.

## Where to go next

- **Architecture:** `docs/architecture.md` (component map + how the
  pieces compose).
- **Getting started:** `docs/getting-started.md` (clone → first
  session).
- **ODD methodology:** `docs/design/odd.md` (~200 lines, contributor-
  first).
- **Component reference:** `docs/components/<name>.md` for each
  shipping component (memory-system, primary-persona, safety-layer,
  reversibility-primitive, cost-governance, observability-aggregator,
  workspace-bootstrap, hands-off-lifecycle).
- **Contributing:** `CONTRIBUTING.md` at the repo root.

## A note on bus factor

loam is a one-person foundation today. The maintainer is honest about
this: the project is run from a personal account (`lukeivers/loam`),
the development cadence is shaped by a real human's energy budget, and
the pre-launch review circle is small and named privately. If loam
helps you, the most useful thing you can do is open a small,
well-scoped issue or PR — not because the project demands community
contribution, but because review-circle expansion is the project's
biggest non-technical need.
