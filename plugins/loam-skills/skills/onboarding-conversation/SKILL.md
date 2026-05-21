---
description: "When a user-facing session opens fresh, structure the first turn as a context-restoration greeting — surface what is in flight, what needs attention, what just completed. Use when the persona detects a session-start state (fresh CLAUDE.md load, no prior conversation memory) or when the user explicitly asks 'where are we?' or 'what's the state?'. Replaces the bare 'How can I help?' greeting with a useful one."
---

# onboarding-conversation

The first turn of a fresh session is the moment with the highest
ambiguity. The user already has context the persona doesn't. A
useful opening greeting surfaces what's in flight + what needs
attention + what completed, so the user can pick up where they
left off without re-explaining. This skill captures the
context-restoration shape so the persona doesn't default to a
bare "Hi, how can I help?".

## What this skill captures

Loam's primary persona is a single named persistent identity —
not a multi-agent system, not a stateless chat. Across sessions
the identity persists; within any given session, the first turn
is a re-attachment. The persona's job at session-start is to
restore enough state that the user can continue working without
restating context.

Three categories of state worth surfacing on first turn:

1. **In flight** — work that started in a prior session and
   hasn't completed. Active dispatches, pending verifications,
   open questions, partial artefacts.
2. **Needs attention** — work that completed but waits on the
   user's gate-review. Sealed amendments awaiting tag, plans
   awaiting approval, decisions surfaced but not yet ruled.
3. **Just completed** — work that landed since the user last
   touched the session. Sealed commits, merged PRs, applied
   amendments — useful for the user's mental model of "what
   moved while I was away".

## When to use

Trigger conditions:

- Fresh session detected (no prior conversation memory, fresh
  CLAUDE.md load).
- User opens with a vague greeting ("hey", "morning", "ok") and
  no specific question.
- User explicitly asks "where are we?", "what's the state?",
  "what's in flight?", "what's pending?".
- After a long pause (user returns mid-session after >24h gap).

Skip when:

- User opens with a specific question or task — answer that
  directly, save the state-summary for later.
- User opens in execution mode (short message, clear intent).
- Session is mid-conversation (no re-greeting needed).

## How the persona applies it

1. **Read the durable surfaces.** Standard locations for
   in-flight state: `<workspace>/workspace/.scratch/` for
   ephemeral status files; `docs/plans/` for plans;
   FIDRAFT entries for pending captures; `STATE.md` for
   component-level state.
2. **Read the recent commit log.** Last 5-10 commits give the
   shape of "just completed" work.
3. **Read the task list / pending captures.** Anything tagged as
   "needs attention" surfaces here.
4. **Author the greeting.** Lead with the answer (the user's
   ADHD-friendly default per loam's communication rules):
   - One paragraph naming the most-load-bearing in-flight item.
   - Numbered list of pending items.
   - One-line "just completed" summary.
   - One clear next-action question.
5. **Stay terse.** The greeting is a re-attachment, not a
   project status report. Maximum 8-10 lines unless the user
   asks for more.
6. **Mirror execution mode.** If the user replies tersely, mirror
   that. Don't pad subsequent responses with re-introductions.

## Graceful degradation

When raw Claude Code (no loam workspace, no `.scratch/` durable
state):

1. Look for state in standard places: project README, recent
   git log, open files in the editor (if accessible),
   conversation memory if any persists.
2. If nothing useful is reachable, ask the user one direct
   question: "what would you like to work on?" — a specific
   prompt beats a vague greeting.
3. Mirror Anthropic's standard skill-discovery shape — Claude
   Code's bundled `/init` skill and similar give a similar
   re-attachment surface for projects without loam.

## Composition

- **Loam's primary persona shape** (per
  `docs/design/primary-persona-shape.md` — sealed at `7ae346d`)
  — single named identity is a different shape than a multi-agent
  system; this skill is the session-start ritual that maintains
  that identity across resets.
- **`session-handoff` skill** — the inverse of this one. Where
  `onboarding-conversation` re-attaches at session start,
  `session-handoff` writes the durable surfaces this skill reads
  back. The two skills share the same "files are the only
  memory" assumption.
- **`memory-recall` skill** — when the user references prior
  context that needs deeper retrieval than the greeting can
  carry, escalate to `memory-recall`.
- **Loam's tracker-context contributor** (v0.1.4 V11.B #40) —
  surfaces in-flight work via the persona's session-start
  contributor. This skill formalises the user-facing surfacing
  of the same data.

## Out of scope

- Periodic mid-session status check-ins (different cadence;
  conversational interruption pattern).
- Task creation / grooming (separate workflow, often via
  `/start-project` or task-list edits).
- Memory writes (writes happen at Stop-hook time; this skill is
  read-side at session-start).
- The very first onboarding-ever (raw Claude Code's `/init`
  skill handles project-scaffolding onboarding; this skill
  handles per-session re-attachment, which is different).
