---
description: Capture a future idea, deferred feature, RF surface, or improvement opportunity into `docs/rebuild/FUTURE_IDEAS_DRAFT.md` at point-of-occurrence. Each entry carries timestamp + named idea + provenance (cycle / context / file) + composes-with + recommended next step (graduate to FUTURE_IDEAS.md / merge into existing entry / discard). Daily-rigor reviews graduate qualifying entries; the draft file is the no-overhead capture surface that prevents "I'll remember next session" failures. Use whenever any future-shaped surface appears mid-flow in a loam dev-mode workspace.
---

# fidraft-capture

`feedback_future_ideas_draft_workflow` operationalised. Every
non-trivial cycle in v0.1.8 surfaced 3–10 future-idea surfaces
that didn't belong in the current scope but were worth not-
losing. The draft file is the capture surface; this skill is
the entry shape + the routing rule. Without the skill, future-
ideas leak into chat closing-bullets (the regression
`feedback_task_tracking_discipline` prevents) or evaporate
across sessions (the regression
`feedback_durable_capture_for_planned_work` prevents).

## What this skill captures

The `docs/rebuild/FUTURE_IDEAS_DRAFT.md` entry shape:

```
### <YYYY-MM-DD HH:MM TZ> — <idea-name-in-kebab-or-prose>

**Source:** <cycle-slug or session context or file path>.
**Provenance:** <one-line context — what triggered the surface>.
**Idea:** <2–5 sentence description of the idea + why it's
worth capturing>.
**Composes with:** <bulleted list of related FIDRAFT entries,
FUTURE_IDEAS.md graduations, feedback memories, or sealed
components — OR `(none)` if standalone>.
**Recommended next step:**
- `graduate` — promote to `docs/rebuild/FUTURE_IDEAS.md` at
  next daily-rigor review; ready for parent-plan inclusion.
- `merge` — combine with FIDRAFT entry `<other-entry-slug>`
  on review.
- `discard` — surfaced once but not load-bearing; review may
  drop.
- `defer-to-<version>` — ready, but explicitly held until a
  named future version (e.g., `defer-to-v0.2.1`).
```

The required parts:

1. **Timestamp + idea-name header** — `### <date-time> —
   <name>`. Date-time is ISO-ish (YYYY-MM-DD HH:MM TZ);
   idea-name is human-readable (kebab-case OR prose;
   whichever scans).
2. **Source line** — names where the surface occurred.
   Cycle slug for in-cycle surfaces; session context for
   ad-hoc; file path for grep-driven discoveries.
3. **Provenance line** — one-line trigger context. What
   was the persona doing when the idea surfaced.
4. **Idea body** — 2–5 sentences. Explain the idea + why
   it's worth capturing. Don't write a full proposal here
   (graduate to FUTURE_IDEAS.md if it warrants a proposal).
5. **Composes-with line** — composition pointers. If the
   idea ties to existing FIDRAFT entries / FUTURE_IDEAS.md
   entries / feedback memories / sealed components, link
   them. Marks "this isn't standalone — it's part of a
   pattern."
6. **Recommended next step** — one of `graduate` / `merge`
   / `discard` / `defer-to-<version>`. The persona's
   recommendation; daily-rigor reviewer rules.

## When to use

Trigger conditions:

- A future-shaped surface appears mid-flow in any
  cycle / session / dispatch:
  - "we could improve X by ..." (improvement opportunity).
  - "this depends on Y which doesn't exist yet" (dependency
    gap).
  - "the user mentioned wanting Z" (feature ask).
  - "this code pattern repeats" (DRY surface).
  - "we deferred this in §10 RF" (explicit RF deferral).
- Reviewing a draft cycle plan / dispatch / research
  artefact — apply the FIDRAFT lens to anything labelled
  "deferred", "future", "out of scope", "TBD".
- A dispatched agent's halt-and-surface finding identifies
  a non-blocking improvement; persona triages to FIDRAFT
  via this skill (per `audit-finding-triage` skill).

Skip when:

- The idea is already captured (verify by skimming
  FIDRAFT for keyword overlap before adding).
- The idea is in-scope for the current cycle (it belongs
  in the plan-doc's AC family or §10 RF, not FIDRAFT).
- The idea is a question to the user, not a future surface
  (different shape; surface as a decision request).

## How the persona applies it

1. **Recognise the surface.** Notice the future-shaped
   trigger phrase ("we could", "future", "out of scope",
   "TBD", "deferred", "improvement opportunity",
   "this would be better if").
2. **Check for duplicates.** `grep -i <keyword>
   docs/rebuild/FUTURE_IDEAS_DRAFT.md` before authoring
   a new entry. If a duplicate exists, append to the
   existing entry's idea body or composes-with line —
   never create a parallel entry.
3. **Author the entry inline.** Don't defer authoring to
   "later in this turn" — the moment-of-occurrence is
   the no-overhead capture point. Use the entry shape
   above.
4. **Cite provenance.** The Source + Provenance lines
   give future-self enough context to evaluate the idea
   without re-reading the original cycle.
5. **Cite composes-with.** Even one composition pointer
   ("relates to FIDRAFT entry `<slug>`") makes the
   draft-review pass faster.
6. **Recommend next step.** Default is `graduate` for
   ideas that feel actionable; `defer-to-<version>` for
   ideas pinned to a future release; `discard` is rare
   (entries surface for a reason) but acceptable.
7. **Don't surface in chat.** The capture is the
   important act; the chat doesn't need to mention every
   FIDRAFT addition unless the user asks. Persona may
   reference the entry in the audit-block (per
   `audit-block-on-telegram` skill in loam-skills) when
   the FIDRAFT addition is materially relevant to the
   user-visible turn.
8. **Daily-rigor review.** Periodically (typically daily
   in active dev sessions; weekly in ambient work) walk
   FIDRAFT entries and execute the recommended next step.
   `graduate` entries move to `FUTURE_IDEAS.md` with a
   parent-plan ready shape; `merge` entries consolidate;
   `discard` entries get a one-line dropped reason;
   `defer-to-<version>` entries stay until the version
   lands.

## Graceful degradation

When raw Claude Code without loam:

- Substitute `docs/rebuild/FUTURE_IDEAS_DRAFT.md` with
  any project-local capture surface (`TODO.md`,
  `IDEAS.md`, `BACKLOG.md` at the workspace root).
- The entry shape collapses to: timestamp + idea + one-line
  provenance + recommended next step. Drop composes-with if
  no graduation rubric exists.
- The capture-at-point-of-occurrence rule is universal:
  even without dev-sdlc, any future-idea that doesn't get
  written down is lost across sessions.

## Composition

- **`feedback_future_ideas_draft_workflow`** — the
  workflow ancestor. This skill operationalises the entry
  shape; the feedback memory carries the daily-rigor +
  graduation rubric.
- **`feedback_durable_capture_for_planned_work`** —
  durable-capture for ALL planned work; FIDRAFT is one
  of the durable surfaces (alongside memory feedback files
  and plan-docs). This skill applies for pos-v2 ideas
  specifically.
- **`feedback_task_tracking_discipline`** — pending items
  go to the task list, not chat closing-bullets. FIDRAFT
  is the durable companion to the in-session task list.
- **`audit-finding-triage` skill** — when a dispatched
  agent's halt-and-surface finding is non-blocking + worth
  capturing, the triage routes to FIDRAFT via this skill.
- **`session-handoff` skill (loam-skills plugin)** — the
  end-of-session checklist includes "any uncaptured
  future-ideas?" — FIDRAFT is the answer.
- **`feedback_summarize_and_surface_decisions`** —
  graduated ideas that need owner ruling carry the named-
  decisions-with-recommendations shape.
- **The §10 F2 RF section in plan-docs** — RF gaps that
  defer to future cycles are FIDRAFT-eligible; this skill
  routes them.

## Out of scope

- The graduation rubric (lives in
  `feedback_future_ideas_draft_workflow` and the dev-mode
  CLAUDE.md fragment).
- The FUTURE_IDEAS.md entry shape (different shape; lives
  in the workspace's existing
  `docs/rebuild/FUTURE_IDEAS.md` conventions).
- The parent-plan inclusion rubric (when does a graduated
  idea become a sub-plan? — lives in master-plan
  authoring discipline, not in this skill).
- Cross-workspace idea portability (FIDRAFT is workspace-
  local; portable patterns belong in feedback memories or
  SKILLs).
- Real-time decision-making during execution (this skill
  is asynchronous capture, not live-call routing — see
  `audit-finding-triage` for live-call shape).
