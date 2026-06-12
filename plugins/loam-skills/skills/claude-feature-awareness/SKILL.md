---
description: "When the persona needs to recall which Claude Code primitive exists before picking one — what a hook event does, how the scheduling primitives compare (/schedule vs /loop vs launchd vs CronCreate), which background-dispatch mechanism fits, what a SKILL frontmatter lever offers — load this SKILL. It is a thin catalogue-lookup: it does NOT carry its own capability claims, it points at the refresh-kept capability corpus under docs/capability-corpus/ so the facts are always the current ones. Invoke during a dispatch decision when the answer to 'is there a primitive for this' is not already obvious. Composes with tool-selection-rubric (which DECIDES which primitive); this SKILL is the index INTO the corpus that holds the facts."
---

# claude-feature-awareness

A thin **catalogue lookup** over loam's capability corpus. When the
persona is about to do something and wants to know whether a Claude
Code primitive already covers it, this SKILL says *where the answer
lives* — it does not hold the answer itself.

This is the deliberate design of the graduated SKILL: it carries **no
independently-maintained capability claims**. Every fact about a
primitive lives in exactly one place — the corpus entry — which the
loam capability-refresh machinery keeps current. A SKILL that copied
those facts into its own body would go stale the moment an upstream
release shipped; pointing at the corpus instead means the lookup is
always reading the maintained surface.

## When to load me

- About to author a hook and unsure which event fires when.
- About to dispatch scheduled work and unsure whether `/schedule`,
  `/loop`, CronCreate, or a launchd plist fits.
- About to dispatch background work and unsure which mechanism
  (Task / `run_in_background` Bash / Monitor) is the right reach.
- Trying to remember "is there a primitive for X" — load me, then
  read the corpus entry I point you at.

## What the primitive does

This SKILL maps a work-shape to the corpus entry that describes the
matching primitive. The corpus root is `docs/capability-corpus/`. The
Claude-Code primitive entries live under
`docs/capability-corpus/claude-code/`:

| Work-shape | Corpus entry to read |
|---|---|
| Structural enforcement / lifecycle handler (which hook event, what envelope, what output disposition) | `docs/capability-corpus/claude-code/hooks.md` |
| Cross-session scheduled / recurring work (cron-shaped, machine-off) | `docs/capability-corpus/claude-code/schedule.md` |
| In-session recurring or self-paced execution ("keep checking", poll-on-cadence) | `docs/capability-corpus/claude-code/loop.md` |
| Background / parallel dispatch (Task tool, `run_in_background` Bash, Monitor, sub-agent nesting) | `docs/capability-corpus/claude-code/background-agents.md` |

Each entry carries the primitive's surface, its inputs/outputs, its
composition notes, and a natural-language-phrasings overlay the
persona's leverage check routes against. The corpus authoring contract
(`docs/capability-corpus/AUTHORING.md`) defines those sections.

**Currency.** The corpus is refresh-kept by loam's capability-refresh
machinery (the currency slice of the claude-leverage program). When an
upstream release lands a change, the refresh updates the corpus entry
and stamps its `Source` block; this lookup automatically reads the new
truth because it never cached the old one. If a corpus entry's `Source`
block shows a `stale` status, the entry self-declares that its last
fetch failed — trust the staleness marker over the body.

## Composition

- **`tool-selection-rubric`** — the decision framework that picks WHICH
  primitive. This SKILL is the catalogue it consults; rubric decides,
  awareness indexes.
- **`primitive-rationale-check`** — once the primitive is chosen, the
  rationale-check records WHY in an audit line.
- **The capability corpus** — the single maintained claims surface.
  This SKILL adds zero claims of its own on top of it; it is pure
  routing.

## Anti-patterns

- **Copying a corpus fact into this SKILL body.** That re-creates the
  staleness failure this graduation exists to fix. Point at the entry;
  never inline its claims.
- **Treating this SKILL as the decision-maker.** It only tells you
  where to read. The rubric decides; the rationale-check records.

## Example invocation

> Persona is about to wire a recurring digest. Loads
> `claude-feature-awareness`, reads the table, follows the pointer to
> `docs/capability-corpus/claude-code/schedule.md`, learns `/schedule`
> is cron-shaped and runs while the machine is off, and reads the
> composition note that `/schedule` does not nest with `/loop`. The
> facts came from the corpus; the SKILL only routed there.
