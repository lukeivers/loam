# Plan — ODD-as-default-framing future idea

## Objective

Append a new Idea (Idea 6) to
`docs/rebuild/FUTURE_IDEAS.md` in `/Users/lukeivers/ivers-corp-pos-v2/`
capturing Luke's 2026-04-22 framing: the primary persona should think
in ODD objectives as the default way of framing requests inside any
pos-v2 conversation, while translating carefully to and from
non-technical user language so tight ODD bounds help users who cannot
yet articulate ODD themselves.

## Context (Luke's framing, 2026-04-22)

> "how to get the primary persona to consistently 'think in
> objectives'. ODD should almost become the default way of framing all
> thoughts, or at least all requests, within any pos v2 conversation.
> but it also can't be overly technical and specific or it will make
> it impossible for nontechnical users to use. but i think enforcing
> tight bounds like with ODD in a transparent way will actually
> massively improve outcomes for non-tech users. they just won't know
> how to talk about it so clearly as a technical person might. so it
> would have to be carefully translate to and from the internal
> modeling into the way it discusses with users until they're able to
> learn more about what ODD is and what it means so they can start
> using it more impactfully."

The idea composes two existing load-bearing pieces:

- `VALUE_PROPOSITION.md` — the primary persona is the translation
  layer between the user's natural-language intent and AI-effective
  execution.
- `odd-methodology.md` — work is defined by objectives + constraints
  + acceptance.

New framing: the translation layer's internal model should be
ODD-shaped; the user surface stays natural-language. Tight ODD bounds
help non-tech users more than tech users even though they cannot
articulate it.

## Acceptance criteria

1. `docs/rebuild/FUTURE_IDEAS.md` gains a new `## Idea 6 — ...`
   section appended after Idea 5 and before the `## Catalogue
   discipline` section.
2. The new Idea preserves Luke's framing, quoting the direct passage
   where it carries weight, and does not elaborate beyond what he
   said.
3. The Idea explicitly calls out:
   - internal model is ODD-shaped (objective + constraints +
     acceptance),
   - user surface is natural language, no technical vocabulary
     required,
   - translation is the primary persona's responsibility, same
     translation layer as `VALUE_PROPOSITION.md`,
   - tight bounds + transparency from ODD help non-tech users more
     than tech users even though they cannot articulate it,
   - connection to Idea 2 (light-touch education) — as the user
     engages, they gradually gain ODD vocabulary and move up the
     sophistication curve.
4. Cross-references to `VALUE_PROPOSITION.md` and
   `odd-methodology.md` are present.
5. Idea stays in "future" register — not scoped, not timelined, not
   attached to a component. No implementation prescriptions (no
   component design, no concrete prompts, no training-data shapes).

## Files changed

- `docs/rebuild/FUTURE_IDEAS.md` (additive only — new Idea 6
  appended; Ideas 1–5 untouched; CDC block untouched; Catalogue
  discipline untouched).
- `docs/rebuild/plans/odd-as-default-framing-idea.md` (this plan).

## Validation

1. `grep -n "Idea 6" docs/rebuild/FUTURE_IDEAS.md` returns at least
   one hit at an `## Idea 6` header.
2. `grep -n "VALUE_PROPOSITION.md" docs/rebuild/FUTURE_IDEAS.md` and
   `grep -n "odd-methodology.md" docs/rebuild/FUTURE_IDEAS.md` each
   return a hit within the new Idea 6 section.
3. `grep -n "Idea 2" docs/rebuild/FUTURE_IDEAS.md` returns the
   existing Idea 2 header plus at least one cross-reference from
   within Idea 6.
4. `git diff --name-only HEAD` after the edit lists exactly two
   paths: `docs/rebuild/FUTURE_IDEAS.md` and
   `docs/rebuild/plans/odd-as-default-framing-idea.md`.
5. Existing Ideas 1–5 and the CDC block are unchanged (grep their
   headers, still present, no prose edits).

## Halt triggers

- If authoring drifts into prescribing *how* to implement the idea
  (concrete component design, specific prompts, specific
  training-data shapes), halt — this is a future idea, not a
  proposal.
- If the diff touches any file outside the two listed above, halt.
- If any existing Idea's prose changes, halt.

## ODD compliance

Doc-only change; prose idea capture; no method prescription; no code;
no silent exception branches; no non-objective code; stays in the
"future directions" register the catalogue is explicitly scoped to.
ODD-clean.

## Execution

Execution (the file edit + commit) runs through a background
subagent per the "Run all execution work through background agents /
subagents" CDC. This plan is the subagent's instruction set.
