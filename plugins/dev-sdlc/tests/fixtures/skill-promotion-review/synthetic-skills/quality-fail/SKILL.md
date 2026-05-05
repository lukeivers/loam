---
description:
---

# malformed-skill-fixture

Reference fixture for the `skill-promotion-review` SKILL covering
the **Quality=FAIL** path. The frontmatter `description` is empty
(violates the AC.SKILLS-DSDLC1.1 structural-test convention which
requires `description` to be a non-empty string ≤1536 chars).
This fixture is intentionally malformed to exercise the
Author-time-fix recommendation path.

Expected signal evaluation when run through skill-promotion-review:

- **Quality** = FAIL (frontmatter description is empty; fails
  the structural-test convention from
  `test_AC_SKILLS_DSDLC1_*_skill_present.py`).
- **Recommendation** = matrix row 5 (Author-time-fix before any
  promotion).

The body is also intentionally short — it is missing the full
6-section convention (no `## When to use`, no `## How the persona
applies it`, no `## Graceful degradation`, no `## Composition`,
no `## Out of scope`). Either failure mode (empty description OR
missing required sections) routes the candidate to
Author-time-fix per the matrix.

## What this skill captures

A malformed SKILL exercising the Quality=FAIL path. Intentionally
incomplete.
