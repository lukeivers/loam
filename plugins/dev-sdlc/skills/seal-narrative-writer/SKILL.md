---
description: Write the short-form seal narrative for a sealed-component amendment cycle — title + slug + components + baseline + amendment SHA + plan_doc_ref + ac_count + smoke_outcome, synthesized from the schema-v3 manifest by `loam amend seal`. The seal narrative is a 5–15 line summary that points at the plan-doc as the source of truth, NOT a duplicate of the plan-doc body. Use whenever the persona is about to seal a cycle, reviewing a draft seal commit, or repairing a seal narrative that drifted from the short-form shape post-amendment-2 (sealed at `df3f50f`). Composes on `loam-amend-cycle` (the wider amendment ladder) and the schema-v3 manifest's `plan_doc_ref` + `ac_count` + `smoke_outcome` fields.
---

# seal-narrative-writer

The short-form seal narrative is the deterministic 5–15 line
summary that lands in `plugins/<plugin>/seals/SEAL_COMMIT.<slug>`
when `loam amend seal` runs. Pre-amendment-2, seal narratives
duplicated the plan-doc body — verbose, redundant, drift-prone.
Post-amendment-2 (dev-pattern-simplifications-2 sealed at
`df3f50f`), the seal narrative is a pointer + summary: it
references the plan-doc rather than re-stating it.

This skill captures the post-amendment-2 short-form shape so a
session-fresh persona authoring a manifest, reviewing a seal
commit, or repairing a drifted narrative knows what the seal
narrative IS and what it ISN'T.

## What this skill captures

The short-form seal narrative shape, line-by-line:

```
<slug> — <amendment title>

Slug:           <slug>
Components:     <comma-separated component names>
Baseline:       <BASELINE SHA — the source-edit feat commit>
Amendment SHA:  <APPLY SHA — the manifest+apply commit>
Plan doc:       <relative path from repo root>
ACs:            <ac_count from manifest>
Smoke:          <smoke_outcome from manifest, one line>
```

The required parts:

1. **Header line** — `<slug> — <amendment title>`. The slug
   matches `amendment.slug` in the manifest; the title matches
   `amendment.title`. The em-dash separates (per
   dev-pattern-simplifications-2 convention).
2. **Slug field** — restated for grep-discoverability when
   walking `plugins/<plugin>/seals/` directories.
3. **Components field** — every component named in
   `manifest.components[].name`, comma-separated. Single-
   component cycles list one name; multi-component cycles list
   each.
4. **Baseline field** — the source-edit feat commit SHA (the
   `manifest.baseline:` field's value). Pinpoints which commit
   the cycle's source changes are anchored to.
5. **Amendment SHA field** — the apply commit SHA (the
   `chore(amend):` commit that landed the manifest+apply
   merge). Different from baseline; the apply commit comes
   AFTER the source-edit feat. `loam amend seal` writes this
   automatically post-apply.
6. **Plan doc field** — the path to the plan-doc, matching
   `manifest.plan_doc_ref`. The plan-doc is the source of
   truth for the cycle; the seal narrative just points at it.
7. **ACs field** — the count from `manifest.ac_count`. Numeric
   only; the AC family/family-name/per-AC text lives in the
   plan-doc.
8. **Smoke field** — one-line summary from
   `manifest.smoke_outcome`. Captures the smoke-test outcome
   in a single line; full per-dimension detail lives in the
   plan-doc §6.

What the seal narrative does NOT contain:

- Per-AC text (lives in plan-doc §4).
- Per-dimension smoke detail (lives in plan-doc §6).
- Halt-and-surface findings (lives in status file +
  plan-doc §10 RF).
- Provenance trail (lives in plan-doc §11).
- Method-decision register (lives in plan-doc §14).
- §10 / §12 / any plan-doc body section.

The narrative is a pointer + summary, NOT a duplicate.

## When to use

Trigger conditions:

- Authoring the schema-v3 manifest's `plan_doc_ref` +
  `ac_count` + `smoke_outcome` fields — these three fields
  are what `loam amend seal` synthesizes the narrative from,
  so authoring them correctly is the upstream work.
- About to run `loam amend seal --plan-doc <abs path>
  <manifest>` — verify the manifest's three narrative-input
  fields are accurate before seal lands.
- Reviewing a draft seal commit's narrative target file at
  `plugins/<plugin>/seals/SEAL_COMMIT.<slug>` — verify the
  shape matches the post-amendment-2 short form.
- Repairing a drifted narrative — if a prior cycle's seal
  narrative duplicates plan-doc body content (pre-
  amendment-2 shape), this skill informs the corrective
  rewrite (in a new amendment, never via `--amend`).

Skip when:

- The change is not a sealed-component cycle (no manifest /
  no seal commit; this skill doesn't apply).
- The manifest is schema v1 or v2 — those schemas pre-date
  the short-form shape; migrate to v3 first per
  `dev-pattern-simplifications-1.md` + `-2.md`.

## How the persona applies it

1. **Verify the manifest is schema v3.** Check
   `schema_version: 3` at the top of the manifest.
2. **Author `plan_doc_ref` accurately.** Path is from repo
   root, no leading slash, matching the actual plan-doc
   filename. Example: `docs/plans/v0-1-9-cycle-3-
   skills-and-cleanup.md`.
3. **Author `ac_count` as the integer total of named ACs in
   the plan-doc §4.** Count carefully — every named AC across
   every AC family. The narrative shows this number, so
   incorrect count is visible in every grep against the
   sealed component.
4. **Author `smoke_outcome` as a single line summary.** No
   newlines. Cover the headline outcome (which dimensions
   exercised + test count + key witness). Example: `"All 6
   dimensions exercised; 183 tests green (105 inherited +
   78 new)"`.
5. **Run `loam amend apply --plan-doc <abs path> <manifest>`**
   — lands the manifest+apply merged commit per AC.DPS1.6.
6. **Run `loam amend seal --plan-doc <abs path> <manifest>`**
   — synthesizes the short-form narrative from manifest +
   commit graph + sweep result; writes to
   `plugins/<plugin>/seals/SEAL_COMMIT.<slug>`; creates the
   `chore(seals): <slug> — <component> at <BASELINE>` commit.
7. **Verify the narrative on disk matches the expected
   short-form shape.** `cat
   plugins/<plugin>/seals/SEAL_COMMIT.<slug>` post-seal;
   confirm 5–15 lines, no plan-doc duplication, all 7 fields
   present.
8. **Halt + RF if the narrative is verbose or duplicates
   plan-doc body.** A drifted narrative says either (a) the
   manifest's three narrative-input fields are over-filled
   (smoke_outcome wrapped to multiple paragraphs), or (b)
   the seal command was run against a v1/v2 manifest
   (migrate first).

## Graceful degradation

When raw Claude Code without loam dev-sdlc plugin (`loam amend
seal` unavailable):

- The short-form shape applies to any manual seal-equivalent
  commit (e.g., a `chore: pin <feature> at <SHA>` rollup
  commit). Author the same 7 fields by hand in the commit
  message body.
- Substitute `plan_doc_ref` with the equivalent project
  paper-trail surface (CHANGELOG.md entry / GitHub release
  notes / Notion doc).
- Substitute `ac_count` with whatever scope-tracking the
  project uses (issue count / requirement count / tested
  scenarios).
- The substance — `narrative is a pointer, not a duplicate`
  — applies regardless of tooling.

If detection fires (a seal narrative is being authored that
LOOKS like plan-doc content rather than a summary), surface
the drift inline: "this seal narrative is duplicating the
plan-doc; the post-amendment-2 short form is a 7-field
summary." See `graceful-fallthrough-with-detection` skill
for the broader detection-on-fallback pattern.

## Composition

- **`loam-amend-cycle` skill** — the wider amendment ladder.
  This skill drills into step 6 (the seal command's
  narrative output); the wider skill walks plan-doc →
  manifest → apply → seal → backfill end-to-end.
- **`plan-docs-author` skill** — the upstream surface. The
  plan-doc is what the seal narrative points AT, so plan-doc
  shape determines what the narrative summarises.
- **`loam-amend-status-quick` skill** — the diagnostic
  surface. When a cycle's seal narrative is missing /
  drifted, the quick-status walk surfaces the gap.
- **`feedback_no_amend_in_agent_dispatches`** — if a seal
  narrative needs repair, create a NEW corrective amendment
  cycle, never `git commit --amend` the prior seal commit.
- **`dev-pattern-simplifications-2` (sealed at `df3f50f`)** —
  the canonical decision that introduced the short form.
  Reference this provenance when explaining the shape to a
  fresh-session persona.
- **`audit-finding-triage` skill** — if narrative drift is
  surfaced as a halt-and-surface finding from a build agent,
  the triage walks routing.

## Out of scope

- Schema v1 / v2 narrative formats — these pre-date the
  short form; migrate via dev-pattern-simplifications
  amendments before applying this skill.
- The narrative-template engine internals (`loam amend
  template`) — this skill captures the OUTPUT shape; the
  engine's render-validate path is internal to loam-amend.
- Multi-component-cycle narrative shape variations —
  multi-component cycles use the same 7-field shape with
  comma-separated component names; no shape change required.
- Master-plan-level rollup narratives — those live in the
  master plan §9 method-decision register, not in
  per-cycle seal narratives.
- Repair commits that update prior seal narratives — out of
  scope for this skill; route to a new amendment cycle that
  re-seals the affected component.
