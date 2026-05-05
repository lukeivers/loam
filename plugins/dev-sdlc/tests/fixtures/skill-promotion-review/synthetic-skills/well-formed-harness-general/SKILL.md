---
description: When the persona surfaces information to the owner, translate from internal vocabulary (commit SHAs, AC IDs, abbreviations the owner has not been introduced to) to plain English the owner can act on. Translation is bidirectional — both inbound (owner intent → AI-effective execution) and outbound (system state → owner-actionable English). Use whenever drafting a Telegram reply, a status surface, or any user-facing artefact.
---

# translation-discipline-fixture

Reference fixture for the `skill-promotion-review` SKILL covering
the **HARNESS-GENERAL** category. Universal-concept shape
(translation discipline applies across every loam workspace, not
just dev-mode), well-formed frontmatter + 6-section body, no
overlap with existing harness or dev-sdlc SKILLs.

Expected signal evaluation when run through skill-promotion-review:

- **Categorization** = HARNESS-GENERAL (universal concept;
  applies to every loam user, not just dev-mode).
- **Quality** = PASS (frontmatter parses; description non-empty
  ≤1536 chars; 6-section body present; key terms present).
- **Conflict** = NO-CONFLICT (no SKILL of this exact name under
  `plugins/loam-skills/skills/`; description-keywords focus on
  translation/owner-vocabulary which is distinct from the
  existing translation-discipline SKILL's broader scope).
- **Recommendation** = matrix row 1 (Promote-to-base
  `plugins/loam-skills/skills/`).

## What this skill captures

The bidirectional translation contract: inbound translates owner
intent into AI-effective execution; outbound translates system
state into owner-actionable English. Specifics: drop commit SHAs,
AC IDs, amendment numbers, internal abbreviations the owner has
not been introduced to.

## When to use

Whenever the persona surfaces any user-facing artefact (Telegram
reply, status surface, plan summary).

## How the persona applies it

1. Draft the surface internally with full vocabulary.
2. Translate-pass: replace internal terms with owner-facing
   equivalents.
3. Audit-pass: any remaining internal term needs a one-line
   gloss OR removal.

## Graceful degradation

When raw Claude Code without loam: the discipline still applies;
the audit-pass becomes manual.

## Composition

Composes with `owner-decision-summary` + `audit-block-on-telegram`.

## Out of scope

Auto-translation pipelines. Translation against non-English
audiences.
