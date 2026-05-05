---
description: Walk a sealed-component amendment cycle end-to-end — author the plan-doc, author the manifest, commit the source-edit feat as BASELINE, run loam amend apply to merge manifest plus sidecar bumps, run loam amend seal to land the seal commit plus run scoped sweep tests, then backfill the §14 method-decision register with the apply plus seal SHAs. Use when the persona is about to start a sealed-component amendment cycle in a loam dev-mode workspace.
---

# amend-runner-fixture

Reference fixture for the `skill-promotion-review` SKILL covering
the **Conflict=DUPLICATE** path. The description-keywords overlap
heavily with the existing `loam-amend-cycle` SKILL — same domain
(sealed-component amendment cycle), same step ladder (plan-doc /
manifest / apply / seal / backfill), same vocabulary.
Well-formed frontmatter + 6-section body, but the candidate is a
duplicate of an existing dev-sdlc SKILL.

Expected signal evaluation when run through skill-promotion-review:

- **Categorization** = DEV-SPECIFIC (mentions loam-amend /
  sealed-component / cycle / amendment).
- **Quality** = PASS (frontmatter parses; body well-formed).
- **Conflict** = DUPLICATE (description keyword overlap >70%
  with existing `loam-amend-cycle` SKILL; same domain + same
  step ladder).
- **Recommendation** = matrix row 8 (Deprecate workspace-local).

## What this skill captures

Sealed-component amendment cycle: plan-doc + manifest + loam
amend apply + loam amend seal + §14 backfill.

## When to use

The persona starts any sealed-component amendment cycle in a
loam dev-mode workspace.

## How the persona applies it

1. Author the plan-doc.
2. Author the manifest.
3. Commit the source-edit feat (BASELINE).
4. Run loam amend apply.
5. Run loam amend seal.
6. Backfill §14.

## Graceful degradation

When raw Claude Code without loam-amend tooling: substitute with
manual git commits; the discipline still applies.

## Composition

Composes with plan-before-code authoring + dispatch-brief shape.

## Out of scope

Multi-component fence semantics. Schema-version migration.
