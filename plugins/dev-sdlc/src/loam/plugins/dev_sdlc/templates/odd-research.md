---
objective: "<one-sentence goal of the research stage for {{slug}}>"
acceptance_criteria:
  - "<observable outcome 1>"
# Set lens_research: true for a loam FEATURE-research plan — it opts the
# artefact into the four-lens-research gate (AC.PFSE.3): the plan cannot
# advance until all four lens-research questions below carry a non-empty
# answer. Generic (non-loam-feature) ODD research omits this flag.
lens_research: true
---

# {{slug}} — research

## Objective

State the research stage's outcome in one sentence.

## Acceptance Criteria

- One observable outcome that closes the research stage.

## Research questions (required — four lens questions, AC.PFSE.3)

Every loam feature-research plan answers all four below with a non-empty
section. The gate refuses to advance until each is filled (the four
questions are canonicalised in `docs/FUTURE_IDEAS.md` Step 3).

### Claude-leverage

What existing Claude capabilities does this feature lean on, extend, or
replace? (Lens 1.)

### Primary-persona

Does this reduce the translation burden between the user's
natural-language intent and AI-effective execution? (Lens 2.)

### Harness

Does this add to the toolkit the primary persona can draw from? (Lens 2.)

### ODD

Does the proposal state objectives + constraints + acceptance without
prescribing method? (Lens 3.)

## Notes

Free-form research findings live below. Once the gate passes, run
`loam project advance {{slug}}` to move into spec.
