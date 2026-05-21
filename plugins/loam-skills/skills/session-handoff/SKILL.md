---
description: "Before a session closes (or a long task is being deferred), capture every pending item, blocker, follow-up, and newly-identified work to a durable surface — never session-locked storage. Use when the user signals end-of-session ('ok bye', 'let's pick this up later', 'going to bed'), when a task hits a natural pause point, or when work is being deferred to a future session. Prevents 'I'll remember next session' failures."
---

# session-handoff

Files are the only memory. Anything not written down by session
end is gone. This skill captures the durable-handoff pattern that
makes work resumable across the session boundary — without
session-locked storage that vanishes on reset.

## What this skill captures

Loam's "files are the only memory" rule applied at session
boundaries. The closing minutes of a session are when most
durable-capture failures happen — work feels "obvious enough to
remember" but the next session starts cold. This skill names the
durable surfaces and the writing discipline.

Three categories of session-end capture:

1. **Pending work the user owns.** Tasks awaiting the user's
   decision, gate-review, or external action.
2. **In-flight work the persona owns.** Active dispatches that
   haven't completed; partial artefacts; verifications pending.
3. **Newly-identified work.** Ideas, hazards, follow-ups, edge
   cases surfaced during this session that don't belong in the
   immediate task scope.

## When to use

Trigger phrases / shapes:

- User signals end-of-session ("ok bye", "later", "going to
  bed", "wrap up", "let's pick this up later").
- User signals deferral ("not now", "save this for later",
  "remind me about this").
- Long task hits a natural pause point with deferred follow-ups.
- Pre-emptive: before any context-heavy turn, ensure prior
  state is captured so /compact or session-end won't lose it.

Apply continuously throughout long sessions, not just at the
literal end — the goal is "nothing is session-locked", which
means writing as work surfaces, not batching at the end.

## How the persona applies it

Per category:

### Pending work the user owns

Write to the workspace's task list / TODO surface
(`<workspace>/workspace/.scratch/`, project-specific TODO files,
or platform task surfaces). Each entry is one line:
`<verb> <subject> — <reason / context link>`.

### In-flight work the persona owns

Write a status file at
`<workspace>/workspace/.scratch/claude-output/<task>-status-<date>.md`.
The status file carries:

- Current state (last completed step, current step, next step).
- Open decisions awaiting user input.
- Halt-and-surface items for the dispatcher.
- Path to the plan-doc + manifest if applicable.

### Newly-identified work

Write to the project's idea-capture surface. For loam:
`docs/FUTURE_IDEAS_DRAFT.md` — point-of-occurrence
capture, no overhead. Each entry is a paragraph: name + brief +
provenance + composes-with.

For non-loam projects: equivalent durable surface
(`IDEAS.md`, `BACKLOG.md`, GitHub issues with a `idea` label,
etc.). Match the project's existing convention.

## How to recognise session-end

Persona heuristics for "session is wrapping up":

1. User's last several turns are short (execution mode → wrap-up
   transition).
2. User mentions a future-tense return ("tomorrow", "next time",
   "later this week").
3. User has been on the platform for >2h and signals fatigue
   ("tired", "long day").
4. /compact has been invoked recently (suggesting context is
   approaching limits).

When detected, surface a pre-emptive checkpoint: "Before we wrap,
here's what's captured + what's still in flight. Anything else
to add?"

## Graceful degradation

When raw Claude Code (no loam workspace):

1. Find or create a project-local `.scratch/`,
   `notes/`, or `TODO.md` for ephemeral capture.
2. For ideas worth keeping cross-session, recommend the user
   commit a small `IDEAS.md` or use GitHub issues.
3. The discipline matters more than the specific surface. Any
   durable file beats memory-only.
4. Default to per-project paths (`./TODO.md`, `./.scratch/`)
   rather than global ones (`~/notes/`) so the capture stays
   with the project.

## Composition

- **`onboarding-conversation` skill** — the inverse. This skill
  writes the durable surfaces; `onboarding-conversation` reads
  them at the next session-start. The two together close the
  cross-session loop.
- **Loam's M-FBM (file-based memory)** — the per-turn episode
  files at `<workspace>/.loam/memory/episodes/` are the
  conversation-level handoff. This skill is task-level handoff
  (status files, FIDRAFT entries, task lists) — different
  granularity, complementary surfaces.
- **Loam's task-tracking discipline** — `feedback_task_tracking_discipline`
  (every pending item goes to the task list, not chat) is the
  in-session shape; this skill is the session-boundary shape.
- **Loam's `feedback_durable_capture_for_planned_work`** —
  direct ancestor of this skill. The discipline that "task list
  is the in-session surface, FIDRAFT is the cross-session
  surface, both required" is what this skill externalizes.
- **`memory-recall` skill** — at the next session start,
  `memory-recall` may surface what `session-handoff` wrote, in
  addition to what `onboarding-conversation` reads.

## Out of scope

- Specific platform-task-surface integrations (GitHub Projects,
  Linear, Jira) — out of fence at v0.1.3; convention-only.
- Persistent agent / scheduled task creation (separate
  primitive; lives in `schedule` / `loop` skills if available).
- Memory writes via the Stop-hook (loam-internal mechanism, not
  the user-visible surface this skill captures).
- Re-running long-deferred work (resumption is a separate
  pattern; this skill covers capture, not resume).
