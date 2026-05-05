---
description: When authoring a sealed-component plan-doc, walk the loam-amend ladder structurally — name the single-component fence, enumerate the AC family with explicit pytest mapping per ODD §2.5 plan-before-code discipline, name halt-and-surface triggers, name out-of-scope, name bookkeeping (pos-amend apply / loam amend seal / §14 backfill). Use when the persona is starting any sealed-component amendment cycle and needs the structural skeleton before authoring per-AC content.
---

# sealed-component-plan-skeleton-fixture

Reference fixture for the `skill-promotion-review` SKILL covering
the **DEV-SPECIFIC** category. Mentions loam-amend / plan-before-code
/ sealed-component / cycle / pos-amend / ODD §2.5 — all dev-mode
vocabulary. Well-formed frontmatter + 6-section body, no overlap
with existing dev-sdlc SKILLs (distinct from
`plan-before-code-author` which is the entry-point; this one is
the plan-doc structural skeleton specifically for sealed-component
amendments).

Expected signal evaluation when run through skill-promotion-review:

- **Categorization** = DEV-SPECIFIC (mentions loam-amend,
  plan-before-code, sealed-component, ODD §2.5 — all dev-mode
  partition keywords).
- **Quality** = PASS (frontmatter parses; description non-empty;
  6-section body present; key terms present).
- **Conflict** = NO-CONFLICT (distinct from
  `plan-before-code-author` and `loam-amend-cycle`; this one is
  the plan-doc structural skeleton specifically for
  sealed-component amendments).
- **Recommendation** = matrix row 2 or 3 (Promote-to-plugin
  `plugins/dev-sdlc/skills/`).

## What this skill captures

The structural skeleton for sealed-component plan-docs:
single-component fence + AC family + halt-and-surface + out-of-scope
+ bookkeeping (pos-amend apply, loam amend seal, §14 backfill).

## When to use

The persona is starting any sealed-component amendment cycle and
needs the plan-doc structural skeleton before authoring per-AC
content.

## How the persona applies it

1. Name the single-component fence.
2. Enumerate the AC family — every AC explicit per ODD §2.5.
3. Name halt-and-surface triggers (in-flight conditions).
4. Name out-of-scope.
5. Name bookkeeping ladder.

## Graceful degradation

When raw Claude Code without loam-amend: substitute pos-amend
apply with a manual feat commit; the rest of the skeleton stands.

## Composition

Composes with `loam-amend-cycle` + `plan-before-code-author` +
`dispatch-brief-authoring`.

## Out of scope

Multi-component fence semantics (covered by `loam-amend-cycle`).
Per-AC content authoring (each cycle's specific concern).
