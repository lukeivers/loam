---
description: When surfacing a plan, research artefact, or design analysis to the owner for ruling, format the head as a Summary plus Named Decisions with Recommendations — never ask the owner to read the full doc to find the questions. Use when the persona has authored or received any document the owner needs to rule on (plan-doc, research artefact, vendor evaluation, design choice). The summary leads; named decisions follow with one-line recommendations and rationales; the doc is depth, not the entry-point. Prevents the doc-section-pointer regression where a reply says "see §3 of the plan" without the answer.
---

# owner-decision-summary

Loam's primary persona is the owner's translation layer. When the
persona produces (or relays) a long artefact that needs owner
ruling — a plan-doc, a research synthesis, a vendor comparison —
the wrong shape is "I authored it; please read it." The right
shape is a Summary at the top + Named Decisions with explicit
Recommendations, each one a sentence the owner can rule on without
opening the file. The document is depth; the summary is the
entry-point. This skill captures the format.

## What this skill captures

Any artefact that needs owner ruling carries (or is relayed with)
a head section in this shape:

```
## Summary
<2-5 sentences naming the artefact's outcome>

## Named decisions for ruling

### Decision A — <one-line description>
- Question: <one-line>
- Recommendation: <one-line + 1 sentence rationale>
- Cost of being wrong: <one-line>

### Decision B — ...
```

The required parts:

1. **Summary first**, never last. The owner should be able to
   stop reading after the summary if no decisions need ruling.
2. **Each decision is named** (Decision A, B, C). Avoids "the
   first thing", "the other thing" — the owner can reference
   the named decision in their reply.
3. **Each decision has a Recommendation, not just a Question.**
   The persona has already done the work; surfacing without a
   recommendation is asking the owner to do the work again. If
   the persona genuinely cannot recommend, that itself is a
   surfacable finding ("Recommendation: cannot rule from
   evidence; need owner judgment because X").
4. **Rationale is one sentence.** Long rationales belong in the
   doc body. The recommendation line is for the owner's first
   pass.
5. **Cost-of-being-wrong is named.** "If we pick A and it turns
   out to be wrong, the cost is N hours of rework" — calibrates
   the owner's attention budget across multiple decisions.

The **anti-pattern** (the regression this skill prevents):

> "I've put my analysis in `docs/rebuild/plans/X.md` — please review §3 for the open questions."

This forces the owner to read the doc to find the questions. The
persona has hidden its conclusions inside the artefact and
abdicated the recommendation step. The right shape inverts: the
named decisions surface inline; the doc is the depth surface for
when the owner wants to verify the persona's reasoning.

## When to use

Trigger conditions:

- The persona has authored a plan-doc / research artefact /
  design note that needs owner approval.
- A sub-agent has produced an artefact with embedded decisions
  the persona is relaying.
- The owner asks "what did you find?" about an investigation that
  surfaced multiple choice points.
- A vendor evaluation, library comparison, or architecture
  decision needs ratification.

Skip when:

- The artefact is for internal context (sub-agent dispatch brief,
  status file the next-session persona reads) — that has its own
  shape.
- The artefact has zero decisions — it is reference content. A
  reference doc gets a one-line summary, no named-decisions block.

## How the persona applies it

1. **Identify the decisions in the artefact.** Walk the doc; mark
   every place that says "we could go A or B" / "open question" /
   "TBD" / "needs ruling".
2. **For each, draft a one-line Question + one-line Recommendation
   + one-line Rationale + one-line Cost-of-being-wrong.** Four
   short lines per decision; the persona owns the recommendation
   step. If the recommendation is "needs owner judgment", say
   that — but only after attempting.
3. **Author the Summary.** 2-5 sentences naming the artefact's
   outcome shape, the major recommendations, the time / cost
   sketch.
4. **Format and surface.** Summary at the top of the
   message body; Named decisions block after the summary; doc
   path at the bottom as a depth-handle.
5. **If the artefact is ≥40 lines** (the loam output-to-disk
   threshold), the artefact stays at the path; the Summary +
   Named Decisions block is what lands in chat. The reverse
   pattern (full artefact in chat, no summary) is a regression.

## Graceful degradation

When raw Claude Code (no loam patterns):

- The same shape applies to any owner-relay artefact. Surface
  the summary + named questions in chat; reference the file as
  the depth surface.
- The minimal version: 3 lines of summary + a numbered list of
  questions, each with a recommendation. Even a degraded version
  still has the "recommendation per question" anchor.
- Anthropic's general guidance on long-context summarisation
  applies: reader attention is the scarce resource; structure
  the artefact so the reader can stop at the surface and only
  drill in when the surface raises a question.

## Composition

- **`translation-discipline` skill** — the summary obeys the
  anti-pattern checklist; the doc-section pointer regression IS
  the failure mode this skill prevents.
- **`audit-block-on-telegram` skill** — entries under
  `Deferred-to-owner:` use the named-decision-with-recommendation
  shape from this skill (one-line per entry, with the
  recommendation embedded).
- **Loam's `feedback_summarize_and_surface_decisions`** — the
  feedback memory that motivated this skill; "Luke rules from
  the summary, not by reading the doc" is the load-bearing
  constraint.
- **Loam's `feedback_locked_design_not_license_for_bad_outcomes`**
  — when revisiting a locked decision, the named-decisions block
  is how the persona surfaces the revisit + recommends keep-or-
  change.

## Out of scope

- Status updates without decisions (those are reference content;
  one-line summary + path is correct).
- Sub-agent dispatch briefs (different shape; see
  `dispatch-with-gates`).
- Real-time decision-making during execution (this skill is for
  asynchronous owner-relay, not live chat where the user can
  rule turn-by-turn).
- The audit-block trailer (different surface; see
  `audit-block-on-telegram`).
