# pOS v2 — CLAUDE.md

pOS v2 is a general-purpose harness for Claude-attached workflows. It
is explicitly *not* targeted at development as a primary use case —
dev-specific machinery (the methodology, conventions, and tooling that
govern how *we* build pOS v2 itself) lives behind a dev-mode auto-load
partition. DEV MODE workspaces additionally auto-load a dev-extension
fragment of these instructions; NORMAL USE workspaces never see it.

This file carries the always-on design lenses + output conventions
that shape every feature, proposal, and decision inside the pOS v2
codebase.

---

## Design lenses for every feature

Three principles must become part of the research of every future
feature — not one-time exercises, but always-on lenses. A feature
proposal that does not answer all three is incomplete.

### Lens 1 — Claude-leverage-first

> **pOS v2 is exclusively attached to Claude.** Every feature built
> on pOS v2 must actively consider what Claude Code / Claude SDK /
> Claude capabilities (slash commands, hook events, MCP, skills,
> plugins, background tasks, session primitives) can be leveraged to
> simplify, extend, or improve the feature — including capabilities
> the end user does not yet have configured but could adopt easily.
> If a Claude-native primitive already provides part of the feature,
> the design should compose on top of it rather than re-implement.

*Example:* Claude's skill ecosystem may already expose a legal-research
skill a user does not have enabled. A hypothetical legal plugin for pOS
v2 that composes with that skill is a different (and likely better)
shape than one that re-implements legal-research primitives inside the
plugin.

The required research question: **"What Claude capability does this
lean on or extend?"**

### Lens 2 — Harness + primary-persona value

> **The primary persona is a translation layer between the user's
> natural-language intent and AI-effective execution; the harness is
> the toolkit the primary persona draws from.** Every feature must
> reduce translation burden for the user and add to the toolkit the
> primary persona can invoke. Full detail in
> `docs/rebuild/VALUE_PROPOSITION.md`.

The two required research questions:

- **Primary-persona test:** does this reduce the translation burden
  between the user's natural-language intent and AI-effective
  execution?
- **Harness test:** does this add to the toolkit the primary persona
  can draw from?

A feature that fails either test needs redesign. A feature that fails
the harness test is almost always wrong.

### Lens 3 — ODD authoring

> **Work in pOS v2 is defined by its observable outcome, not by a
> sequence of steps.** Objective + constraints + acceptance criteria;
> method is the builder's call. ODD applies after the Lens 1 and Lens
> 2 research questions have been answered; it shapes the mechanical
> form of the feature's authoring, not whether the feature should
> exist.

---

## Output conventions

> *When any response produced by the primary persona or a dispatched
> agent would exceed roughly 40 lines or 400 words, the content is
> written to a predictable disk path and the path is referenced inline
> instead of inlining the content itself. The user opens the file with
> whatever tool fits the current interface — `open`, `less`, or `bat`
> from a terminal; an attachment through Telegram; the inline viewer
> or `open` from the Claude app.*

Context tokens are finite, expensive, and lost to compaction. Inlining
reports, plans, long analyses, and multi-section syntheses burns
context that could otherwise carry forward useful state, and
compaction discards the content regardless. Writing substantial output
to disk persists the artefact at a stable path and makes it
retrievable on demand without re-transmission. Short replies, direct
answers, status updates, and brief summaries stay inline; the rule
engages only when the content is large enough that a reader would
naturally prefer a dedicated viewer over scrolling chat.

In practice: when an output crosses the ~40-line / ~400-word
threshold, choose a sensible path for the artefact —
`<workspace>/.scratch/claude-output/<subject>.md` for ephemeral
material, a workspace-appropriate canonical path for plans / specs,
or a component-specific path for component-scoped artefacts — write
the file, then inline a brief description plus the path. Format
follows the content (markdown for prose and structure, plain text
for logs). Opening the file is the user's call. Ephemeral files
belong in the workspace's `.scratch/` (gitignored via
`.scratch/.gitignore`, already in place) so they're (a) visible to
the human operator while browsing the repo, (b) survive session
boundaries on disk, and (c) don't disappear on system reboot.
